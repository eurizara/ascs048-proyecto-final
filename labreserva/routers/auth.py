from fastapi import APIRouter

from .. import db, reglas
from ..errores import ErrorNegocio
from ..modelos import LoginIn
from ..seguridad import emitir_token, verificar_password

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", summary="Iniciar sesión (RN-01, RN-02)")
def login(datos: LoginIn):
    con = db.conectar()
    try:
        fila = con.execute("SELECT * FROM usuarios WHERE lower(email) = ?",
                           (reglas.normalizar_email(datos.email),)).fetchone()
        if fila is None or not verificar_password(datos.password, fila["password_hash"]):
            raise ErrorNegocio(401, "CREDENCIALES_INVALIDAS", "Credenciales inválidas")
        if fila["estado"] != "ACTIVO":
            raise ErrorNegocio(403, "USUARIO_INACTIVO", "El usuario no está activo")
        token = emitir_token(con, fila["id"])
        return {"token": token,
                "usuario": {"id": fila["id"], "nombre": fila["nombre"], "rol": fila["rol"]}}
    finally:
        con.close()
