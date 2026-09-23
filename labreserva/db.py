"""Acceso a datos (SQLite). Los montos se guardan en centavos."""
import os
import sqlite3
from decimal import Decimal

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL,
    rol TEXT NOT NULL,
    estado TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    saldo_centavos INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS laboratorios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    capacidad INTEGER NOT NULL,
    estado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    valor_centavos INTEGER NOT NULL,
    estado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    laboratorio_id INTEGER NOT NULL,
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,
    asistentes INTEGER NOT NULL,
    estado TEXT NOT NULL,
    penalidad_centavos INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS prestamos (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    equipo_id INTEGER NOT NULL,
    fecha_prestamo TEXT NOT NULL,
    vencimiento TEXT NOT NULL,
    fecha_devolucion TEXT,
    estado TEXT NOT NULL,
    multa_centavos INTEGER NOT NULL DEFAULT 0,
    danio INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    monto_centavos INTEGER NOT NULL,
    fecha TEXT NOT NULL
);
"""

TABLAS = ["pagos", "prestamos", "reservas", "equipos", "laboratorios",
          "tokens", "usuarios"]


def ruta_db() -> str:
    return os.environ.get("DB_PATH", os.path.join("data", "labreserva.db"))


def conectar() -> sqlite3.Connection:
    ruta = ruta_db()
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    con = sqlite3.connect(ruta, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    return con


def crear_esquema(con: sqlite3.Connection) -> None:
    con.executescript(ESQUEMA)


def vaciar(con: sqlite3.Connection) -> None:
    for tabla in TABLAS:
        con.execute(f"DELETE FROM {tabla}")


def a_centavos(monto: Decimal) -> int:
    return int((Decimal(monto) * 100).to_integral_value())


def a_quetzales(centavos: int) -> float:
    return float(Decimal(centavos) / 100)
