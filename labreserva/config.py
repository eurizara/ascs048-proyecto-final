"""Parámetros de negocio derivados del carné del estudiante (ERS, sección 3)."""
import hashlib
import os
import re
from decimal import Decimal

PATRON_CARNE = re.compile(r"^\d{4}-\d{2}-\d{3,6}$")
_SAL = "ASCS-048|LabReserva|2026"

_OPCIONES = {
    "MAX_HORAS_RESERVA": [2, 3, 4, 5, 6],
    "ANTICIPACION_MIN_H": [12, 18, 24, 36, 48],
    "MAX_PRESTAMOS_EST": [2, 3, 4],
    "DIAS_PRESTAMO_EST": [3, 4, 5, 6, 7],
    "DIAS_GRACIA": [1, 2, 3],
    "MULTA_DIARIA": ["5.50", "6.50", "7.50", "8.50", "9.50",
                     "10.50", "11.50", "12.50", "13.50", "14.50"],
    "TOPE_DIAS_MULTA": [10, 12, 15, 20],
    "UMBRAL_SALDO": [50, 75, 100, 125, 150],
    "CANCELACION_H": [2, 3, 4, 6, 8, 12],
}


class CarneInvalido(ValueError):
    pass


def normalizar_carne(carne: str) -> str:
    valor = (carne or "").strip()
    if not PATRON_CARNE.match(valor):
        raise CarneInvalido(
            "Carné inválido: use el formato de Canvas, p. ej. 7690-14-9834")
    return valor


def derivar_parametros(carne: str) -> dict:
    """Devuelve los parámetros de negocio del estudiante con ese carné."""
    carne = normalizar_carne(carne)
    digest = hashlib.sha256(f"{_SAL}|{carne}".encode("utf-8")).digest()
    params = {}
    for i, (nombre, opciones) in enumerate(_OPCIONES.items()):
        valor = opciones[digest[i] % len(opciones)]
        params[nombre] = Decimal(valor) if nombre == "MULTA_DIARIA" else valor
    params["HUELLA"] = hashlib.sha256(
        f"huella|{carne}".encode("utf-8")).hexdigest()[:8].upper()
    params["CARNE"] = carne
    return params


def parametros_publicos(params: dict) -> dict:
    salida = {}
    for clave, valor in params.items():
        salida[clave] = f"{valor:.2f}" if isinstance(valor, Decimal) else valor
    return salida


_CACHE: dict = {}


def obtener() -> dict:
    carne = os.environ.get("CARNE", "")
    if _CACHE.get("carne") != carne:
        _CACHE["carne"] = carne
        _CACHE["params"] = derivar_parametros(carne)
    return _CACHE["params"]


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 2:
        print("Uso: python -m labreserva.config 7690-14-9834")
        sys.exit(1)
    try:
        print(json.dumps(parametros_publicos(derivar_parametros(sys.argv[1])),
                         indent=2, ensure_ascii=False))
    except CarneInvalido as exc:
        print(exc)
        sys.exit(2)
