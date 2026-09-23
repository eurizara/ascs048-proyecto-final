"""Reloj del sistema. Admite una fecha simulada para pruebas (ERS, RN-31)."""
from datetime import datetime, timedelta, timezone

GT = timezone(timedelta(hours=-6), "America/Guatemala")
_estado = {"simulado": None}


def ahora() -> datetime:
    if _estado["simulado"] is not None:
        return _estado["simulado"]
    return datetime.now(GT).replace(microsecond=0)


def fijar(momento: datetime) -> None:
    _estado["simulado"] = a_gt(momento)


def liberar() -> None:
    _estado["simulado"] = None


def es_simulado() -> bool:
    return _estado["simulado"] is not None


def a_gt(momento: datetime) -> datetime:
    """Interpreta fechas sin zona como hora de Guatemala."""
    if momento.tzinfo is None:
        return momento.replace(tzinfo=GT)
    return momento.astimezone(GT)


def iso(momento: datetime | None) -> str | None:
    return None if momento is None else a_gt(momento).isoformat()


def desde_texto(texto: str | None) -> datetime | None:
    if texto is None:
        return None
    return a_gt(datetime.fromisoformat(texto))
