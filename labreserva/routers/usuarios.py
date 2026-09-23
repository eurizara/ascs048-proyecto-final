from decimal import Decimal

from fastapi import APIRouter, Depends

from .. import db, reglas, reloj
from ..errores import ErrorNegocio, conflicto, invalido, no_encontrado
from ..modelos import PagoIn, UsuarioIn
from ..seguridad import exigir_admin, hash_password, usuario_actual

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])
ROLES = ("ESTUDIANTE", "DOCENTE", "ADMIN")


def perfil(fila) -> dict:
    return {"id": fila["id"], "nombre": fila["nombre"], "email": fila["email"],
            "rol": fila["rol"], "estado": fila["estado"],
            "saldo_pendiente": db.a_quetzales(fila["saldo_centavos"])}


@router.get("/me", summary="Perfil del usuario autenticado (RN-05)")
def mi_perfil(usuario: dict = Depends(usuario_actual)):
    return perfil(usuario)


@router.get("/{usuario_id}", summary="Consultar un perfil (RN-05)")
def ver_usuario(usuario_id: int, usuario: dict = Depends(usuario_actual)):
    if usuario["rol"] != "ADMIN" and usuario["id"] != usuario_id:
        raise no_encontrado("El usuario")
    con = db.conectar()
    try:
        fila = con.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
    finally:
        con.close()
    if fila is None:
        raise no_encontrado("El usuario")
    datos = perfil(fila)
    datos["password_hash"] = fila["password_hash"]
    return datos


@router.post("", status_code=201, summary="Registrar usuario (RN-04), solo ADMIN")
def crear_usuario(datos: UsuarioIn, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    for error in (reglas.validar_nombre(datos.nombre), reglas.validar_email(datos.email),
                  reglas.validar_password(datos.password)):
        if error:
            raise invalido(error, "Datos de usuario inválidos")
    if datos.rol not in ROLES:
        raise invalido("ROL_INVALIDO", "Rol no reconocido")
    email = datos.email.strip()
    con = db.conectar()
    try:
        if con.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone():
            raise conflicto("EMAIL_DUPLICADO", "El correo ya está registrado")
        cur = con.execute(
            "INSERT INTO usuarios(nombre,email,rol,estado,password_hash,saldo_centavos)"
            " VALUES (?,?,?,'ACTIVO',?,0)",
            (" ".join(datos.nombre.split()), email, datos.rol, hash_password(datos.password)))
        fila = con.execute("SELECT * FROM usuarios WHERE id=?", (cur.lastrowid,)).fetchone()
        return perfil(fila)
    finally:
        con.close()


@router.post("/{usuario_id}/pagos", summary="Registrar pago de saldo (RN-23), solo ADMIN")
def registrar_pago(usuario_id: int, datos: PagoIn, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    monto = datos.monto
    if monto <= 0 or monto != monto.quantize(Decimal("0.01")):
        raise invalido("MONTO_INVALIDO", "El monto debe ser positivo y con máximo 2 decimales")
    con = db.conectar()
    try:
        fila = con.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
        if fila is None:
            raise no_encontrado("El usuario")
        centavos = db.a_centavos(monto)
        if centavos > fila["saldo_centavos"]:
            raise ErrorNegocio(409, "MONTO_EXCEDE_SALDO", "El monto excede el saldo pendiente")
        con.execute("UPDATE usuarios SET saldo_centavos = saldo_centavos - ? WHERE id=?",
                    (centavos, usuario_id))
        con.execute("INSERT INTO pagos(usuario_id,monto_centavos,fecha) VALUES (?,?,?)",
                    (usuario_id, centavos, reloj.iso(reloj.ahora())))
        fila = con.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
        return perfil(fila)
    finally:
        con.close()
