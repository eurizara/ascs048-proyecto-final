from fastapi import APIRouter, Depends

from .. import db
from ..seguridad import usuario_actual

router = APIRouter(prefix="/api/equipos", tags=["Equipos"])


def serializar(fila) -> dict:
    return {"id": fila["id"], "codigo": fila["codigo"], "tipo": fila["tipo"],
            "descripcion": fila["descripcion"],
            "valor": db.a_quetzales(fila["valor_centavos"]), "estado": fila["estado"]}


@router.get("", summary="Listar equipos")
def listar(usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        filas = con.execute("SELECT * FROM equipos ORDER BY id").fetchall()
    finally:
        con.close()
    return [serializar(f) for f in filas]
