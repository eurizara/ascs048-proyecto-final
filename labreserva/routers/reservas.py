from fastapi import APIRouter, Depends

from .. import config, db, reglas, reloj
from ..errores import ErrorNegocio, conflicto, invalido, no_encontrado
from ..modelos import ReservaIn
from ..seguridad import exigir_admin, usuario_actual

router = APIRouter(prefix="/api/reservas", tags=["Reservas"])
LIMITE_RESERVAS_ESTUDIANTE = 2


def serializar(fila) -> dict:
    return {"id": fila["id"], "usuario_id": fila["usuario_id"],
            "laboratorio_id": fila["laboratorio_id"],
            "inicio": fila["inicio"], "fin": fila["fin"],
            "asistentes": fila["asistentes"], "estado": fila["estado"],
            "penalidad": db.a_quetzales(fila["penalidad_centavos"])}


def _obtener(con, reserva_id: int, usuario: dict):
    fila = con.execute("SELECT * FROM reservas WHERE id=?", (reserva_id,)).fetchone()
    if fila is None:
        raise no_encontrado("La reserva")
    if usuario["rol"] != "ADMIN" and fila["usuario_id"] != usuario["id"]:
        raise no_encontrado("La reserva")
    return fila


@router.post("", status_code=201, summary="Crear reserva (RN-06 a RN-12)")
def crear(datos: ReservaIn, usuario: dict = Depends(usuario_actual)):
    if usuario["rol"] not in ("ESTUDIANTE", "DOCENTE"):
        raise ErrorNegocio(403, "SIN_PERMISO", "Solo ESTUDIANTE o DOCENTE reservan")
    p = config.obtener()
    inicio, fin = reloj.a_gt(datos.inicio), reloj.a_gt(datos.fin)
    con = db.conectar()
    try:
        lab = con.execute("SELECT * FROM laboratorios WHERE id=?",
                          (datos.laboratorio_id,)).fetchone()
        if lab is None:
            raise no_encontrado("El laboratorio")
        if lab["estado"] != "DISPONIBLE":
            raise conflicto("LABORATORIO_NO_DISPONIBLE", "Laboratorio no disponible")
        for error in (reglas.validar_horario(inicio, fin),
                      reglas.validar_duracion(inicio, fin, usuario["rol"],
                                              p["MAX_HORAS_RESERVA"]),
                      reglas.validar_anticipacion(inicio, reloj.ahora(),
                                                  p["ANTICIPACION_MIN_H"])):
            if error:
                raise invalido(error, "La reserva no cumple las reglas de horario")
        if not 1 <= datos.asistentes <= lab["capacidad"]:
            raise invalido("ASISTENTES_INVALIDOS", "Número de asistentes fuera de rango")
        if usuario["rol"] == "ESTUDIANTE":
            vigentes = con.execute(
                "SELECT COUNT(*) FROM reservas WHERE usuario_id=? "
                "AND estado NOT IN ('FINALIZADA','NO_SHOW')", (usuario["id"],)).fetchone()[0]
            if vigentes >= LIMITE_RESERVAS_ESTUDIANTE:
                raise conflicto("LIMITE_RESERVAS", "Límite de reservas vigentes alcanzado")
        activas = con.execute(
            "SELECT inicio, fin FROM reservas WHERE laboratorio_id=? "
            "AND estado IN ('PENDIENTE','CONFIRMADA','EN_USO')",
            (datos.laboratorio_id,)).fetchall()
        for otra in activas:
            if reglas.se_traslapan(inicio, fin, reloj.desde_texto(otra["inicio"]),
                                   reloj.desde_texto(otra["fin"])):
                raise conflicto("TRASLAPE", "El laboratorio ya está reservado en ese horario")
        estado = "CONFIRMADA" if usuario["rol"] == "DOCENTE" else "PENDIENTE"
        cur = con.execute(
            "INSERT INTO reservas(usuario_id,laboratorio_id,inicio,fin,asistentes,estado)"
            " VALUES (?,?,?,?,?,?)",
            (usuario["id"], datos.laboratorio_id, inicio.isoformat(), fin.isoformat(),
             datos.asistentes, estado))
        return serializar(con.execute("SELECT * FROM reservas WHERE id=?",
                                      (cur.lastrowid,)).fetchone())
    finally:
        con.close()


@router.get("", summary="Listar reservas propias (ADMIN: todas)")
def listar(usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        if usuario["rol"] == "ADMIN":
            filas = con.execute("SELECT * FROM reservas ORDER BY inicio, id").fetchall()
        else:
            filas = con.execute("SELECT * FROM reservas WHERE usuario_id=? ORDER BY inicio, id",
                                (usuario["id"],)).fetchall()
    finally:
        con.close()
    return [serializar(f) for f in filas]


@router.get("/{reserva_id}", summary="Consultar una reserva (RN-15)")
def ver(reserva_id: int, usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        fila = con.execute("SELECT * FROM reservas WHERE id=?", (reserva_id,)).fetchone()
        if fila is None:
            raise no_encontrado("La reserva")
        return serializar(fila)
    finally:
        con.close()


def _transicion(con, fila, accion: str) -> str:
    nuevo = reglas.siguiente_estado(fila["estado"], accion)
    if nuevo is None:
        raise conflicto("TRANSICION_INVALIDA",
                        f"No se puede '{accion}' una reserva en estado {fila['estado']}")
    return nuevo


def _guardar(con, reserva_id: int, estado: str, penalidad_centavos: int = 0):
    con.execute("UPDATE reservas SET estado=?, penalidad_centavos=? WHERE id=?",
                (estado, penalidad_centavos, reserva_id))
    return serializar(con.execute("SELECT * FROM reservas WHERE id=?",
                                  (reserva_id,)).fetchone())


@router.post("/{reserva_id}/confirmar", summary="Confirmar reserva (RN-13), solo ADMIN")
def confirmar(reserva_id: int, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        fila = _obtener(con, reserva_id, usuario)
        return _guardar(con, reserva_id, _transicion(con, fila, "confirmar"))
    finally:
        con.close()


@router.post("/{reserva_id}/cancelar", summary="Cancelar reserva (RN-13, RN-14)")
def cancelar(reserva_id: int, usuario: dict = Depends(usuario_actual)):
    p = config.obtener()
    con = db.conectar()
    try:
        fila = _obtener(con, reserva_id, usuario)
        nuevo = _transicion(con, fila, "cancelar")
        penalidad = reglas.penalidad_cancelacion(
            reloj.desde_texto(fila["inicio"]), reloj.ahora(), usuario["rol"],
            p["CANCELACION_H"])
        centavos = db.a_centavos(penalidad)
        if centavos:
            con.execute("UPDATE usuarios SET saldo_centavos = saldo_centavos + ? WHERE id=?",
                        (centavos, fila["usuario_id"]))
        return _guardar(con, reserva_id, nuevo, centavos)
    finally:
        con.close()


@router.post("/{reserva_id}/checkin", summary="Registrar ingreso (RN-13)")
def checkin(reserva_id: int, usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        fila = _obtener(con, reserva_id, usuario)
        if fila["usuario_id"] != usuario["id"]:
            raise ErrorNegocio(403, "SIN_PERMISO", "Solo el titular registra ingreso")
        nuevo = _transicion(con, fila, "checkin")
        if not reglas.en_ventana_checkin(reloj.desde_texto(fila["inicio"]), reloj.ahora()):
            raise conflicto("FUERA_DE_VENTANA", "Fuera de la ventana de ingreso")
        return _guardar(con, reserva_id, nuevo)
    finally:
        con.close()


@router.post("/{reserva_id}/checkout", summary="Registrar salida (RN-13)")
def checkout(reserva_id: int, usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        fila = _obtener(con, reserva_id, usuario)
        return _guardar(con, reserva_id, _transicion(con, fila, "checkout"))
    finally:
        con.close()


@router.post("/{reserva_id}/no-show", summary="Marcar inasistencia (RN-13), solo ADMIN")
def no_show(reserva_id: int, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        fila = _obtener(con, reserva_id, usuario)
        nuevo = _transicion(con, fila, "no_show")
        if not reglas.puede_marcar_no_show(reloj.desde_texto(fila["inicio"]), reloj.ahora()):
            raise conflicto("FUERA_DE_VENTANA", "Aún no se puede marcar inasistencia")
        return _guardar(con, reserva_id, nuevo)
    finally:
        con.close()
