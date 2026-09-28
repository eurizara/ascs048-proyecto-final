"""Contraseñas, tokens y control de acceso (RN-01, RN-02, RN-27)."""
import hashlib
import secrets

from fastapi import Header

from . import db
from .errores import ErrorNegocio

_ITERACIONES = 60_000


def hash_password(password: str, sal: str | None = None) -> str:
    sal = sal or secrets.token_hex(8)
    derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                   sal.encode("utf-8"), _ITERACIONES)
    return f"pbkdf2${sal}${derivado.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        _, sal, _ = almacenado.split("$")
    except ValueError:
        return False
    return secrets.compare_digest(hash_password(password, sal), almacenado)


def emitir_token(con, usuario_id: int) -> str:
    token = secrets.token_hex(20)
    con.execute("INSERT INTO tokens(token, usuario_id) VALUES (?, ?)",
                (token, usuario_id))
    return token


def usuario_actual(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise ErrorNegocio(401, "NO_AUTENTICADO", "Se requiere token Bearer")
    token = authorization[len("Bearer "):].strip()
    con = db.conectar()
    try:
        fila = con.execute(
            "SELECT u.* FROM tokens t JOIN usuarios u ON u.id = t.usuario_id "
            "WHERE t.token = ?", (token,)).fetchone()
    finally:
        con.close()
    if fila is None:
        raise ErrorNegocio(401, "NO_AUTENTICADO", "Token inválido")
    if fila["estado"] != "ACTIVO":
        raise ErrorNegocio(403, "USUARIO_INACTIVO", "El usuario no está activo")
    return dict(fila)


def exigir_admin(usuario: dict) -> None:
    if usuario["rol"] != "ADMIN":
        raise ErrorNegocio(403, "SIN_PERMISO", "Operación exclusiva de ADMIN")
