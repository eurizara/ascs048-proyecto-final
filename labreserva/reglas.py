"""Reglas de negocio puras (ERS, Anexo B). Sin acceso a base de datos."""
import math
import re
from datetime import datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from .reloj import GT

APERTURA = time(7, 0)
CIERRE = time(21, 0)
MAX_DIAS_ANTICIPACION = 30
VENTANA_CHECKIN = timedelta(minutes=15)
PENALIDAD_CANCELACION = Decimal("25.00")
VALOR_RECARGO = Decimal("5000.00")
FACTOR_RECARGO = Decimal("1.15")
ESTADOS_RESERVA = ("PENDIENTE", "CONFIRMADA", "EN_USO", "FINALIZADA",
                   "CANCELADA", "NO_SHOW")


# ---------------------------------------------------------------- reservas
def validar_horario(inicio: datetime, fin: datetime) -> str | None:
    """RN-06: lunes a sábado, 07:00-21:00, mismo día, múltiplos de 30 min."""
    if inicio.date() != fin.date():
        return "FUERA_DE_HORARIO"
    if inicio.weekday() == 6:
        return "FUERA_DE_HORARIO"
    if inicio.time() < APERTURA or fin.time() > CIERRE:
        return "FUERA_DE_HORARIO"
    for momento in (inicio, fin):
        if momento.minute not in (0, 30) or momento.second or momento.microsecond:
            return "HORA_NO_VALIDA"
    return None


def validar_duracion(inicio: datetime, fin: datetime, rol: str,
                     max_horas: int) -> str | None:
    """RN-07: mínimo 1 h; máximo max_horas (DOCENTE: max_horas + 2)."""
    horas = (fin - inicio).total_seconds() / 3600
    limite = max_horas + 2 if rol == "DOCENTE" else max_horas
    if horas < 1:
        return "DURACION_INVALIDA"
    if not horas < limite:
        return "DURACION_INVALIDA"
    return None


def validar_anticipacion(inicio: datetime, ahora: datetime,
                         min_horas: int) -> str | None:
    """RN-08: inicio >= ahora + min_horas y a no más de 30 días."""
    diferencia = (inicio.replace(tzinfo=None)
                  - ahora.astimezone(timezone.utc).replace(tzinfo=None))
    if diferencia < timedelta(hours=min_horas):
        return "ANTICIPACION_INSUFICIENTE"
    if diferencia > timedelta(days=MAX_DIAS_ANTICIPACION):
        return "ANTICIPACION_EXCESIVA"
    return None


def se_traslapan(a_inicio: datetime, a_fin: datetime,
                 b_inicio: datetime, b_fin: datetime) -> bool:
    """RN-10: intervalos semiabiertos [inicio, fin)."""
    return a_inicio <= b_fin and b_inicio <= a_fin


def siguiente_estado(estado: str, accion: str) -> str | None:
    """RN-13: devuelve el nuevo estado o None si la transición no es válida."""
    if accion == "confirmar":
        return "CONFIRMADA" if estado in ("PENDIENTE", "CANCELADA") else None
    if accion == "cancelar":
        return "CANCELADA" if estado in ("PENDIENTE", "CONFIRMADA") else None
    if accion == "checkin":
        return "EN_USO" if estado == "CONFIRMADA" else None
    if accion == "no_show":
        return "NO_SHOW" if estado == "CONFIRMADA" else None
    if accion == "checkout":
        return "FINALIZADA" if estado == "EN_USO" else None
    return None


def en_ventana_checkin(inicio: datetime, ahora: datetime) -> bool:
    """RN-13: desde 15 min antes hasta 15 min después del inicio."""
    return inicio - VENTANA_CHECKIN <= ahora


def puede_marcar_no_show(inicio: datetime, ahora: datetime) -> bool:
    """RN-13: solo después de inicio + 15 min."""
    return ahora > inicio + VENTANA_CHECKIN


def penalidad_cancelacion(inicio: datetime, ahora: datetime,
                          quien_cancela: str, horas_limite: int) -> Decimal:
    """RN-14: Q25.00 si el dueño cancela con menos de horas_limite de anticipación."""
    faltan = (inicio - ahora).seconds / 3600
    if faltan < horas_limite:
        return PENALIDAD_CANCELACION
    return Decimal("0.00")


# ---------------------------------------------------------------- préstamos
def limite_prestamos(rol: str, max_est: int) -> int:
    """RN-17."""
    return max_est + 2 if rol == "DOCENTE" else max_est


def puede_prestar(saldo: Decimal, umbral: int) -> bool:
    """RN-18: con saldo pendiente >= umbral no se permiten préstamos."""
    return saldo <= Decimal(umbral)


def calcular_vencimiento(fecha_prestamo: datetime, rol: str,
                         dias_prestamo: int) -> datetime:
    """RN-19: fecha + días (DOCENTE: doble); si cae domingo pasa al lunes; 21:00."""
    dias = dias_prestamo * 2 if rol == "DOCENTE" else dias_prestamo
    fecha = fecha_prestamo.astimezone(GT).date() + timedelta(days=dias)
    if fecha.weekday() == 5:
        fecha += timedelta(days=1)
    return datetime.combine(fecha, CIERRE, tzinfo=GT)


def dias_atraso(vencimiento: datetime, devolucion: datetime) -> int:
    """RN-21: diferencia en días calendario (hora de Guatemala)."""
    segundos = (devolucion - vencimiento).total_seconds()
    return max(0, math.ceil(segundos / 86400))


def multa_diaria(valor_equipo: Decimal, multa_base: Decimal) -> Decimal:
    """RN-21: recargo de 15 % para equipos con valor >= Q5,000.00."""
    if Decimal(valor_equipo) >= VALOR_RECARGO:
        return Decimal(str(round(float(multa_base) * 1.15, 2)))
    return Decimal(multa_base).quantize(Decimal("0.01"))


def calcular_multa(vencimiento: datetime, devolucion: datetime,
                   valor_equipo: Decimal, multa_base: Decimal,
                   dias_gracia: int, tope_dias: int) -> Decimal:
    """RN-21: días cobrables = max(0, atraso - gracia), con tope de días."""
    dias = dias_atraso(vencimiento, devolucion)
    dias = min(dias, tope_dias)
    cobrables = max(0, dias - dias_gracia)
    return (multa_diaria(valor_equipo, multa_base) * cobrables).quantize(
        Decimal("0.01"))


# ---------------------------------------------------------------- reportes
def total_paginas(total: int, tamanio: int) -> int:
    """RN-24."""
    return total // tamanio


def tasa_puntualidad(a_tiempo: int, devueltos: int) -> float:
    """RN-26: porcentaje con 1 decimal; 0.0 si no hay devoluciones."""
    return round(a_tiempo * 100 / devueltos, 1)


# ---------------------------------------------------------------- usuarios
_PATRON_NOMBRE = re.compile(r"^[A-Za-z' ]{3,60}$")
_PATRON_PASSWORD = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")
_PATRON_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_nombre(nombre: str) -> str | None:
    """RN-04."""
    return None if _PATRON_NOMBRE.match((nombre or "").strip()) else "NOMBRE_INVALIDO"


def validar_password(password: str) -> str | None:
    """RN-04."""
    return None if _PATRON_PASSWORD.match(password or "") else "PASSWORD_DEBIL"


def normalizar_email(email: str) -> str:
    """RN-01/RN-04: sin espacios extremos y en minúsculas."""
    return (email or "").strip().lower()


def validar_email(email: str) -> str | None:
    return None if _PATRON_EMAIL.match(normalizar_email(email)) else "EMAIL_INVALIDO"
