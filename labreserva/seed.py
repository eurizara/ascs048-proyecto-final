"""Datos semilla (ERS, Anexo C). Se generan relativos a la fecha del reloj."""
import functools
from datetime import datetime, time, timedelta
from decimal import Decimal

from . import config, db, reloj
from .reloj import GT
from .seguridad import hash_password

USUARIOS = [
    # id, nombre, email, rol, estado, password
    (1, "Administración LabReserva", "admin@labreserva.test", "ADMIN", "ACTIVO", "Admin2026!"),
    (2, "Marta Julieta Pérez", "mperez@labreserva.test", "DOCENTE", "ACTIVO", "Docente2026"),
    (3, "Óscar Iván Castañeda", "ocastaneda@labreserva.test", "DOCENTE", "ACTIVO", "Docente2026"),
    (4, "Ana Lucía Gómez", "agomez@labreserva.test", "ESTUDIANTE", "ACTIVO", "Estudiante2026"),
    (5, "José Andrés Peña", "jpena@labreserva.test", "ESTUDIANTE", "ACTIVO", "Estudiante2026"),
    (6, "María Fernanda López", "mlopez@labreserva.test", "ESTUDIANTE", "ACTIVO", "Estudiante2026"),
    (7, "Luis Carlos Hernández", "lhernandez@labreserva.test", "ESTUDIANTE", "ACTIVO", "Estudiante2026"),
    (8, "Sofía Alejandra Ramírez", "sramirez@labreserva.test", "ESTUDIANTE", "ACTIVO", "Estudiante2026"),
    (9, "Carlos Eduardo Toj", "ctoj@labreserva.test", "ESTUDIANTE", "SUSPENDIDO", "Estudiante2026"),
    (10, "Diego Armando Xicará", "dxicara@labreserva.test", "ESTUDIANTE", "BAJA", "Estudiante2026"),
    (11, "Gabriela Beatriz Sic", "gsic@labreserva.test", "ESTUDIANTE", "ACTIVO", "Estudiante2026"),
]

LABORATORIOS = [
    (1, "Laboratorio de Redes", 20, "DISPONIBLE"),
    (2, "Laboratorio de Software", 30, "DISPONIBLE"),
    (3, "Laboratorio de Electrónica", 15, "DISPONIBLE"),
    (4, "Sala de Proyectos", 8, "MANTENIMIENTO"),
]

EQUIPOS = [
    (1, "LAP-001", "LAPTOP", "Laptop Dell Latitude 5440", "4500.00", "DISPONIBLE"),
    (2, "LAP-002", "LAPTOP", "Laptop Dell Latitude 5440", "4500.00", "PRESTADO"),
    (3, "LAP-003", "LAPTOP", "Laptop Lenovo ThinkPad E14", "4500.00", "DISPONIBLE"),
    (4, "LAP-004", "LAPTOP", "Laptop Lenovo ThinkPad E14", "4500.00", "DISPONIBLE"),
    (5, "LAP-005", "LAPTOP", "Laptop HP ProBook 440", "4500.00", "PRESTADO"),
    (6, "LAP-006", "LAPTOP", "Laptop HP ProBook 440", "4500.00", "BAJA"),
    (7, "LAP-007", "LAPTOP", "Laptop de alto rendimiento", "6200.00", "DISPONIBLE"),
    (8, "PRY-001", "PROYECTOR", "Proyector Epson PowerLite", "3800.00", "DISPONIBLE"),
    (9, "PRY-002", "PROYECTOR", "Proyector Epson PowerLite", "3800.00", "PRESTADO"),
    (10, "PRY-003", "PROYECTOR", "Proyector BenQ", "3800.00", "DISPONIBLE"),
    (11, "ARD-001", "KIT_ARDUINO", "Kit Arduino Uno con sensores", "650.00", "DISPONIBLE"),
    (12, "ARD-002", "KIT_ARDUINO", "Kit Arduino Uno con sensores", "650.00", "DISPONIBLE"),
    (13, "ARD-003", "KIT_ARDUINO", "Kit Arduino Mega", "650.00", "PRESTADO"),
    (14, "OSC-001", "OSCILOSCOPIO", "Osciloscopio digital 100 MHz", "8500.00", "DISPONIBLE"),
    (15, "OSC-002", "OSCILOSCOPIO", "Osciloscopio digital 100 MHz", "8500.00", "MANTENIMIENTO"),
    (16, "ARD-004", "KIT_ARDUINO", "Kit Arduino Mega", "650.00", "DISPONIBLE"),
    (17, "PRY-004", "PROYECTOR", "Proyector BenQ", "3800.00", "DISPONIBLE"),
]

OBSERVACIONES = [
    "",
    "Pantalla con rayón, teclado OK",
    'Incluye cable "HDMI" adicional',
    "Sin novedad",
    "Batería al 80 %; cargador incluido",
]


@functools.lru_cache(maxsize=None)
def _hash_fijo(usuario_id: int, password: str) -> str:
    return hash_password(password, sal=f"semilla{usuario_id:03d}")


def _habil(fecha):
    return fecha + timedelta(days=1) if fecha.weekday() == 6 else fecha


def _momento(fecha, hora: int, minuto: int = 0) -> datetime:
    return datetime.combine(fecha, time(hora, minuto), tzinfo=GT)


def _vencimiento(fecha_prestamo: datetime, dias: int) -> datetime:
    fecha = fecha_prestamo.date() + timedelta(days=dias)
    if fecha.weekday() == 6:
        fecha += timedelta(days=1)
    return _momento(fecha, 21)


def _multa_historica(vence: datetime, devuelto: datetime, valor: Decimal,
                     p: dict) -> int:
    dias = max(0, (devuelto.date() - vence.date()).days)
    cobrables = min(max(0, dias - p["DIAS_GRACIA"]), p["TOPE_DIAS_MULTA"])
    diaria = p["MULTA_DIARIA"]
    if valor >= Decimal("5000.00"):
        diaria = (diaria * Decimal("1.15")).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
    return db.a_centavos(diaria * cobrables)


def cargar(con) -> None:
    p = config.obtener()
    hoy = reloj.ahora().date()
    db.vaciar(con)
    con.execute("BEGIN")
    for uid, nombre, email, rol, estado, pwd in USUARIOS:
        con.execute(
            "INSERT INTO usuarios(id,nombre,email,rol,estado,password_hash,saldo_centavos)"
            " VALUES (?,?,?,?,?,?,0)",
            (uid, nombre, email, rol, estado, _hash_fijo(uid, pwd)))
    con.executemany("INSERT INTO laboratorios VALUES (?,?,?,?)", LABORATORIOS)
    for eid, codigo, tipo, desc, valor, estado in EQUIPOS:
        con.execute("INSERT INTO equipos VALUES (?,?,?,?,?,?)",
                    (eid, codigo, tipo, desc, db.a_centavos(Decimal(valor)), estado))
    valores = {e[0]: Decimal(e[4]) for e in EQUIPOS}
    roles = {u[0]: u[3] for u in USUARIOS}

    def dias_de(uid):
        base = p["DIAS_PRESTAMO_EST"]
        return base * 2 if roles[uid] == "DOCENTE" else base

    # Historial de préstamos devueltos (estadísticas y reportes).
    historial_usuarios = [4, 8, 11, 5, 3, 2]
    historial_equipos = [1, 3, 4, 8, 10, 11, 12, 7, 14, 16, 17]
    for i in range(24):
        uid = historial_usuarios[i % len(historial_usuarios)]
        eid = historial_equipos[i % len(historial_equipos)]
        if eid == 14 and roles[uid] != "DOCENTE":
            eid = 16
        prestado = _momento(_habil(hoy - timedelta(days=70 - 2 * i)), 8 + i % 5)
        vence = _vencimiento(prestado, dias_de(uid))
        if i % 4 == 0:
            devuelto = _momento(vence.date() + timedelta(days=p["DIAS_GRACIA"] + 2), 11)
        else:
            devuelto = _momento(vence.date() - timedelta(days=1), 10)
        multa = _multa_historica(vence, devuelto, valores[eid], p)
        con.execute(
            "INSERT INTO prestamos(usuario_id,equipo_id,fecha_prestamo,vencimiento,"
            "fecha_devolucion,estado,multa_centavos,danio,observaciones)"
            " VALUES (?,?,?,?,?,?,?,0,?)",
            (uid, eid, prestado.isoformat(), vence.isoformat(), devuelto.isoformat(),
             "DEVUELTO", multa, OBSERVACIONES[i % len(OBSERVACIONES)]))

    # Préstamo atrasado de José (id 5).
    prestado = _momento(_habil(hoy - timedelta(days=p["DIAS_PRESTAMO_EST"] + 4)), 10)
    con.execute(
        "INSERT INTO prestamos(usuario_id,equipo_id,fecha_prestamo,vencimiento,"
        "estado,observaciones) VALUES (5,2,?,?,'ACTIVO','')",
        (prestado.isoformat(), _vencimiento(prestado, p["DIAS_PRESTAMO_EST"]).isoformat()))

    # Tres préstamos activos registrados en el mismo instante.
    mismo = _momento(hoy - timedelta(days=1), 8)
    for uid, eid in ((8, 5), (11, 9), (3, 13)):
        con.execute(
            "INSERT INTO prestamos(usuario_id,equipo_id,fecha_prestamo,vencimiento,"
            "estado,observaciones) VALUES (?,?,?,?,'ACTIVO','')",
            (uid, eid, mismo.isoformat(), _vencimiento(mismo, dias_de(uid)).isoformat()))

    # Saldo pendiente de Luis (id 7) igual al umbral.
    umbral = db.a_centavos(Decimal(p["UMBRAL_SALDO"]))
    prestado = _momento(_habil(hoy - timedelta(days=40)), 9)
    vence = _vencimiento(prestado, p["DIAS_PRESTAMO_EST"])
    con.execute(
        "INSERT INTO prestamos(usuario_id,equipo_id,fecha_prestamo,vencimiento,"
        "fecha_devolucion,estado,multa_centavos,observaciones)"
        " VALUES (7,11,?,?,?,'DEVUELTO',?,'Devolución tardía')",
        (prestado.isoformat(), vence.isoformat(),
         _momento(vence.date() + timedelta(days=12), 9).isoformat(), umbral))
    con.execute("UPDATE usuarios SET saldo_centavos=? WHERE id=7", (umbral,))

    # Reservas.
    reservas = [
        (6, 1, _habil(hoy + timedelta(days=3)), 8, 9, 5, "CANCELADA"),
        (6, 3, _habil(hoy + timedelta(days=4)), 15, 16, 4, "CANCELADA"),
        (2, 2, _habil(hoy + timedelta(days=3)), 10, 12, 25, "CONFIRMADA"),
        (8, 1, _habil(hoy + timedelta(days=5)), 14, 16, 10, "PENDIENTE"),
        (11, 3, _habil(hoy + timedelta(days=2)), 9, 10, 6, "CONFIRMADA"),
        (8, 2, _habil(hoy - timedelta(days=6)), 13, 15, 12, "FINALIZADA"),
    ]
    for uid, lab, fecha, h_ini, h_fin, asist, estado in reservas:
        con.execute(
            "INSERT INTO reservas(usuario_id,laboratorio_id,inicio,fin,asistentes,estado)"
            " VALUES (?,?,?,?,?,?)",
            (uid, lab, _momento(fecha, h_ini).isoformat(),
             _momento(fecha, h_fin).isoformat(), asist, estado))
    con.execute("COMMIT")


def generar_volumen(con, cantidad: int) -> int:
    """Inserta préstamos devueltos adicionales para pruebas de desempeño."""
    hoy = reloj.ahora().date()
    usuarios = [4, 5, 8, 11, 2, 3]
    filas = []
    for i in range(cantidad):
        uid = usuarios[i % len(usuarios)]
        prestado = _momento(_habil(hoy - timedelta(days=200 + i % 150)), 7 + i % 12, (i % 2) * 30)
        vence = _vencimiento(prestado, 5)
        devuelto = _momento(vence.date() - timedelta(days=1), 12)
        filas.append((uid, 1 + i % 13, prestado.isoformat(), vence.isoformat(),
                      devuelto.isoformat(), "DEVUELTO", 0, "Registro de volumen"))
    con.execute("BEGIN")
    con.executemany(
        "INSERT INTO prestamos(usuario_id,equipo_id,fecha_prestamo,vencimiento,"
        "fecha_devolucion,estado,multa_centavos,observaciones) VALUES (?,?,?,?,?,?,?,?)",
        filas)
    con.execute("COMMIT")
    return cantidad
