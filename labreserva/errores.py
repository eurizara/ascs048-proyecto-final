"""Errores de negocio con el formato de respuesta de la ERS (RN-29)."""


class ErrorNegocio(Exception):
    def __init__(self, estado_http: int, codigo: str, detalle: str):
        super().__init__(detalle)
        self.estado_http = estado_http
        self.codigo = codigo
        self.detalle = detalle


def no_encontrado(recurso: str) -> ErrorNegocio:
    return ErrorNegocio(404, "NO_ENCONTRADO", f"{recurso} no existe")


def conflicto(codigo: str, detalle: str) -> ErrorNegocio:
    return ErrorNegocio(409, codigo, detalle)


def invalido(codigo: str, detalle: str) -> ErrorNegocio:
    return ErrorNegocio(400, codigo, detalle)
