from fastapi import APIRouter, Depends

from .. import db
from ..seguridad import usuario_actual

router = APIRouter(prefix="/api/laboratorios", tags=["Laboratorios"])


@router.get("", summary="Listar laboratorios")
def listar(usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        filas = con.execute("SELECT * FROM laboratorios ORDER BY id").fetchall()
    finally:
        con.close()
    return [dict(f) for f in filas]
