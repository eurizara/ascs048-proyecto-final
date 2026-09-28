from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from .. import config, db, reglas, reloj
from ..errores import ErrorNegocio, conflicto, no_encontrado
from ..modelos import DevolucionIn, PrestamoIn
from ..seguridad import exigir_admin, usuario_actual

router = APIRouter(prefix="/api/prestamos", tags=["Préstamos"])


def estado_efectivo(fila) -> str:
    if fila["estado"] == "ACTIVO" and reloj.ahora() > reloj.desde_texto(fila["vencimiento"]):
        return "ATRASADO"
    return fila["estado"]


def serializar(fila) -> dict:
    return {"id": fila["id"], "usuario_id": fila["usuario_id"], "equipo_id": fila["equipo_id"],
            "fecha_prestamo": fila["fecha_prestamo"], "vencimiento": fila["vencimiento"],
            "fecha_devolucion": fila["fecha_devolucion"], "estado": estado_efectivo(fila),
            "multa": db.a_quetzales(fila["multa_centavos"]), "danio": bool(fila["danio"]),
            "observaciones": fila["observaciones"]}


@router.post("", status_code=201, summary="Registrar préstamo (RN-16 a RN-20)")
def crear(datos: PrestamoIn, usuario: dict = Depends(usuario_actual)):
    if usuario["rol"] not in ("ESTUDIANTE", "DOCENTE"):
        raise ErrorNegocio(403, "SIN_PERMISO", "Solo ESTUDIANTE o DOCENTE solicitan préstamos")
    p = config.obtener()
    ahora = reloj.ahora()
    con = db.conectar()
    try:
        equipo = con.execute("SELECT * FROM equipos WHERE id=?", (datos.equipo_id,)).fetchone()
        if equipo is None:
            raise no_encontrado("El equipo")
        if equipo["estado"] != "DISPONIBLE":
            raise conflicto("EQUIPO_NO_DISPONIBLE", "El equipo no está disponible")
        if equipo["tipo"] == "OSCILOSCOPIO" and usuario["rol"] != "DOCENTE":
            raise ErrorNegocio(403, "EQUIPO_RESTRINGIDO", "Equipo exclusivo para DOCENTE")
        saldo = Decimal(usuario["saldo_centavos"]) / 100
        if not reglas.puede_prestar(saldo, p["UMBRAL_SALDO"]):
            raise conflicto("SALDO_PENDIENTE", "Tiene saldo pendiente igual o mayor al umbral")
        activos = con.execute(
            "SELECT vencimiento FROM prestamos WHERE usuario_id=? AND estado='ACTIVO'",
            (usuario["id"],)).fetchall()
        activos = [f for f in activos if reloj.desde_texto(f["vencimiento"]) >= ahora]
        if len(activos) >= reglas.limite_prestamos(usuario["rol"], p["MAX_PRESTAMOS_EST"]):
            raise conflicto("LIMITE_PRESTAMOS", "Límite de préstamos simultáneos alcanzado")
        vence = reglas.calcular_vencimiento(ahora, usuario["rol"], p["DIAS_PRESTAMO_EST"])
        con.execute("BEGIN")
        cur = con.execute(
            "INSERT INTO prestamos(usuario_id,equipo_id,fecha_prestamo,vencimiento,estado)"
            " VALUES (?,?,?,?,'ACTIVO')",
            (usuario["id"], datos.equipo_id, ahora.isoformat(), vence.isoformat()))
        con.execute("UPDATE equipos SET estado='PRESTADO' WHERE id=?", (datos.equipo_id,))
        con.execute("COMMIT")
        return serializar(con.execute("SELECT * FROM prestamos WHERE id=?",
                                      (cur.lastrowid,)).fetchone())
    finally:
        con.close()


@router.get("/mios", summary="Préstamos del usuario autenticado")
def mios(usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        filas = con.execute("SELECT * FROM prestamos WHERE usuario_id=? ORDER BY id",
                            (usuario["id"],)).fetchall()
    finally:
        con.close()
    return [serializar(f) for f in filas]


ORDEN = "p.fecha_prestamo DESC, p.id"


@router.get("", summary="Listado paginado de préstamos (RN-24, RN-28), solo ADMIN")
def listar(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50),
           usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    con = db.conectar()
    try:
        total = con.execute("SELECT COUNT(*) FROM prestamos").fetchone()[0]
        filas = con.execute(
            "SELECT p.*, e.codigo AS equipo_codigo FROM prestamos p "
            f"JOIN equipos e ON e.id = p.equipo_id ORDER BY {ORDEN}").fetchall()
        items = []
        for fila in filas:
            dueno = db.conectar()
            nombre = dueno.execute("SELECT nombre FROM usuarios WHERE id=?",
                                   (fila["usuario_id"],)).fetchone()["nombre"]
            dueno.close()
            fecha = reloj.desde_texto(fila["fecha_prestamo"])
            numero = 0
            for otra in filas:
                otra_fecha = reloj.desde_texto(otra["fecha_prestamo"])
                mismo_usuario = dict(otra)["usuario_id"] == fila["usuario_id"]
                if mismo_usuario and (
                        otra_fecha < fecha or (otra_fecha == fecha and otra["id"] <= fila["id"])):
                    numero += 1
            item = serializar(fila)
            item.update({"usuario_nombre": nombre, "equipo_codigo": fila["equipo_codigo"],
                         "numero_prestamo_usuario": numero})
            items.append(item)
        items = items[(page - 1) * size: page * size]
        return {"page": page, "size": size, "total": total,
                "pages": reglas.total_paginas(total, size), "items": items}
    finally:
        con.close()


@router.get("/{prestamo_id}", summary="Consultar un préstamo")
def ver(prestamo_id: int, usuario: dict = Depends(usuario_actual)):
    con = db.conectar()
    try:
        fila = con.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
    finally:
        con.close()
    if fila is None or (usuario["rol"] != "ADMIN" and fila["usuario_id"] != usuario["id"]):
        raise no_encontrado("El préstamo")
    return serializar(fila)


@router.post("/{prestamo_id}/devolucion", summary="Registrar devolución (RN-21, RN-22), solo ADMIN")
def devolver(prestamo_id: int, datos: DevolucionIn, usuario: dict = Depends(usuario_actual)):
    exigir_admin(usuario)
    p = config.obtener()
    ahora = reloj.ahora()
    con = db.conectar()
    try:
        fila = con.execute("SELECT * FROM prestamos WHERE id=?", (prestamo_id,)).fetchone()
        if fila is None:
            raise no_encontrado("El préstamo")
        if fila["estado"] == "DEVUELTO":
            raise conflicto("PRESTAMO_CERRADO", "El préstamo ya fue devuelto")
        equipo = con.execute("SELECT * FROM equipos WHERE id=?", (fila["equipo_id"],)).fetchone()
        multa = reglas.calcular_multa(
            reloj.desde_texto(fila["vencimiento"]), ahora,
            Decimal(equipo["valor_centavos"]) / 100, p["MULTA_DIARIA"],
            p["DIAS_GRACIA"], p["TOPE_DIAS_MULTA"])
        centavos = db.a_centavos(multa)
        estado_equipo = "DISPONIBLE"
        con.execute("BEGIN")
        con.execute(
            "UPDATE prestamos SET fecha_devolucion=?, estado='DEVUELTO', multa_centavos=?,"
            " danio=?, observaciones=? WHERE id=?",
            (ahora.isoformat(), centavos, int(datos.danio), datos.observaciones.strip(),
             prestamo_id))
        con.execute("UPDATE equipos SET estado=? WHERE id=?", (estado_equipo, fila["equipo_id"]))
        if centavos:
            con.execute("UPDATE usuarios SET saldo_centavos = saldo_centavos + ? WHERE id=?",
                        (centavos, fila["usuario_id"]))
        con.execute("COMMIT")
        return serializar(con.execute("SELECT * FROM prestamos WHERE id=?",
                                      (prestamo_id,)).fetchone())
    finally:
        con.close()
