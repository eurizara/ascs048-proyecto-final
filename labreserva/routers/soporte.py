from fastapi import APIRouter, Depends

from .. import config, db, reloj, seed
from ..modelos import RelojIn, VolumenIn
from ..seguridad import exigir_admin, usuario_actual

router = APIRouter(prefix="/api", tags=["Soporte de pruebas"])


@router.get("/parametros", summary="Parámetros de negocio del estudiante (ERS, sección 3)")
def parametros():
    return config.parametros_publicos(config.obtener())


@router.get("/soporte/reloj", summary="Consultar el reloj del sistema (RN-31)")
def ver_reloj():
    return {"ahora": reloj.iso(reloj.ahora()), "simulado": reloj.es_simulado()}


@router.put("/soporte/reloj", summary="Fijar fecha simulada (RN-31), solo ADMIN")
def fijar_reloj(datos: RelojIn, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    reloj.fijar(datos.ahora)
    return {"ahora": reloj.iso(reloj.ahora()), "simulado": True}


@router.delete("/soporte/reloj", summary="Volver al reloj real (RN-31), solo ADMIN")
def liberar_reloj(usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    reloj.liberar()
    return {"ahora": reloj.iso(reloj.ahora()), "simulado": False}


@router.post("/soporte/reset", summary="Restablecer datos semilla (RN-31), solo ADMIN")
def restablecer(usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        seed.cargar(con)
    finally:
        con.close()
    return {"resultado": "datos restablecidos", "reloj": reloj.iso(reloj.ahora())}


@router.post("/soporte/volumen", summary="Generar préstamos de volumen (RN-31), solo ADMIN")
def volumen(datos: VolumenIn, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        insertados = seed.generar_volumen(con, datos.cantidad)
    finally:
        con.close()
    return {"insertados": insertados}
