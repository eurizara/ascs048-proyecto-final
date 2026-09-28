import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from .. import db, reglas, reloj
from .prestamos import estado_efectivo
from ..seguridad import exigir_admin, usuario_actual

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])
ENCABEZADO = ["id", "usuario", "equipo", "fecha_prestamo", "vencimiento",
              "fecha_devolucion", "estado", "multa", "observaciones"]


@router.get("/prestamos.csv", summary="Exportar préstamos a CSV (RN-25), solo ADMIN")
def exportar(usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        filas = con.execute(
            "SELECT p.*, u.nombre, e.codigo FROM prestamos p "
            "JOIN usuarios u ON u.id = p.usuario_id JOIN equipos e ON e.id = p.equipo_id "
            "ORDER BY p.id").fetchall()
    finally:
        con.close()
    registros = [[f["id"], f["nombre"], f["codigo"], f["fecha_prestamo"], f["vencimiento"],
                  f["fecha_devolucion"] or "", estado_efectivo(f),
                  f"{db.a_quetzales(f['multa_centavos']):.2f}", f["observaciones"]]
                 for f in filas]
    lineas = [",".join(ENCABEZADO)] + [",".join(str(v) for v in r) for r in registros]
    contenido = "\r\n".join(lineas) + "\r\n"
    return Response(content=contenido.encode("utf-8"),
                    media_type="text/csv; charset=utf-8")


@router.get("/estadisticas", summary="Estadísticas de devoluciones (RN-26), solo ADMIN")
def estadisticas(desde: date | None = Query(None), hasta: date | None = Query(None),
                 usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        filas = con.execute("SELECT * FROM prestamos WHERE estado='DEVUELTO'").fetchall()
    finally:
        con.close()
    devueltos = a_tiempo = multas = 0
    for f in filas:
        devuelto = reloj.desde_texto(f["fecha_devolucion"])
        if desde and devuelto.date() < desde:
            continue
        if hasta and devuelto.date() > hasta:
            continue
        devueltos += 1
        multas += f["multa_centavos"]
        if devuelto <= reloj.desde_texto(f["vencimiento"]):
            a_tiempo += 1
    return {"devueltos": devueltos, "a_tiempo": a_tiempo,
            "tasa_puntualidad": reglas.tasa_puntualidad(a_tiempo, devueltos),
            "multas_total": db.a_quetzales(multas)}
