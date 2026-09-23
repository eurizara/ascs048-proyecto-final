"""Punto de entrada de la API LabReserva UMG."""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import __version__, bitacora, config, db, seed
from .errores import ErrorNegocio
from .routers import (auth, equipos, laboratorios, prestamos, reportes, reservas,
                      soporte, usuarios)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    params = config.obtener()
    con = db.conectar()
    try:
        db.crear_esquema(con)
        if con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            seed.cargar(con)
    finally:
        con.close()
    print(f"LabReserva {__version__} | carné {params['CARNE']} | huella {params['HUELLA']}")
    yield


app = FastAPI(title="LabReserva UMG", version=__version__, lifespan=ciclo_de_vida,
              description="API del sistema de reservas de laboratorios y préstamo de "
                          "equipo. La especificación oficial es docs/ERS_LabReserva.md.")


@app.exception_handler(ErrorNegocio)
async def manejar_negocio(request: Request, exc: ErrorNegocio):
    return JSONResponse(status_code=exc.estado_http,
                        content={"error": exc.codigo, "detalle": exc.detalle})




_CODIGOS_HTTP = {404: ("NO_ENCONTRADO", "Recurso no encontrado"),
                 405: ("METODO_NO_PERMITIDO", "Método no permitido")}


@app.exception_handler(StarletteHTTPException)
async def manejar_http(request: Request, exc: StarletteHTTPException):
    codigo, detalle = _CODIGOS_HTTP.get(exc.status_code, ("ERROR_HTTP", str(exc.detail)))
    return JSONResponse(status_code=exc.status_code,
                        content={"error": codigo, "detalle": detalle})


@app.exception_handler(Exception)
async def manejar_inesperado(request: Request, exc: Exception):
    return JSONResponse(status_code=500,
                        content={"error": "ERROR_INTERNO", "detalle": "Error interno"})


class MiddlewareBitacora:
    """Registra cada petición a /api en la bitácora de ejecución."""

    def __init__(self, aplicacion):
        self.aplicacion = aplicacion

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api"):
            await self.aplicacion(scope, receive, send)
            return
        partes = []
        estado = {"codigo": 500}

        async def recibir():
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                partes.append(mensaje.get("body", b""))
            return mensaje

        async def enviar(mensaje):
            if mensaje["type"] == "http.response.start":
                estado["codigo"] = mensaje["status"]
            await send(mensaje)

        try:
            await self.aplicacion(scope, recibir, enviar)
        finally:
            crudo = b"".join(partes)
            try:
                cuerpo = json.loads(crudo) if crudo else None
            except ValueError:
                cuerpo = {"_bytes": len(crudo)}
            bitacora.registrar(scope["method"], scope["path"],
                               scope.get("query_string", b"").decode("latin-1"),
                               estado["codigo"], cuerpo)


app.add_middleware(MiddlewareBitacora)
for modulo in (auth, usuarios, laboratorios, reservas, equipos, prestamos, reportes, soporte):
    app.include_router(modulo.router)
