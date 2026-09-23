"""Bitácora de ejecución encadenada (ERS, RN-30).

Cada línea registra una petición y un hash encadenado con la línea anterior.
Alterar, borrar o reordenar líneas rompe la cadena y es detectable.
No modifique este archivo ni la bitácora generada.
"""
import hashlib
import json
import os
import threading
from datetime import datetime

from . import config, reloj

_CANDADO = threading.Lock()
_CAMPOS_OCULTOS = {"password", "password_actual", "password_nueva"}


def ruta() -> str:
    return os.environ.get("BITACORA_PATH",
                          os.path.join("bitacora", "ejecucion.jsonl"))


def _clave(carne: str) -> bytes:
    return hashlib.sha256(f"bitacora|ASCS-048|{carne}".encode()).digest()


def _ultimo_hash(archivo: str) -> tuple[int, str]:
    if not os.path.exists(archivo):
        return 0, "0" * 64
    ultima = None
    with open(archivo, "r", encoding="utf-8") as fh:
        for linea in fh:
            if linea.strip():
                ultima = linea
    if ultima is None:
        return 0, "0" * 64
    dato = json.loads(ultima)
    return dato["n"], dato["hash"]


def enmascarar(cuerpo):
    if isinstance(cuerpo, dict):
        return {k: ("***" if k in _CAMPOS_OCULTOS else enmascarar(v))
                for k, v in cuerpo.items()}
    if isinstance(cuerpo, list):
        return [enmascarar(v) for v in cuerpo]
    return cuerpo


def firmar(clave: bytes, previo: str, registro: dict) -> str:
    contenido = json.dumps(registro, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(clave + previo.encode() + contenido.encode("utf-8")).hexdigest()


def registrar(metodo: str, ruta_http: str, consulta: str, estado: int,
              cuerpo) -> None:
    params = config.obtener()
    archivo = ruta()
    carpeta = os.path.dirname(archivo)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with _CANDADO:
        n, previo = _ultimo_hash(archivo)
        registro = {
            "n": n + 1,
            "ts": datetime.now().astimezone().isoformat(timespec="milliseconds"),
            "reloj": reloj.iso(reloj.ahora()),
            "simulado": reloj.es_simulado(),
            "huella": params["HUELLA"],
            "metodo": metodo,
            "ruta": ruta_http,
            "consulta": consulta,
            "estado": estado,
            "cuerpo": enmascarar(cuerpo),
            "prev": previo,
        }
        registro["hash"] = firmar(_clave(params["CARNE"]), previo,
                                  {k: v for k, v in registro.items() if k != "hash"})
        with open(archivo, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(registro, ensure_ascii=False) + "\n")
