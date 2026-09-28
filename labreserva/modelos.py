"""Modelos de entrada (cuerpos JSON)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str
    password: str


class UsuarioIn(BaseModel):
    nombre: str
    email: str
    rol: str
    password: str


class PagoIn(BaseModel):
    monto: Decimal


class ReservaIn(BaseModel):
    laboratorio_id: int
    inicio: datetime
    fin: datetime
    asistentes: int


class PrestamoIn(BaseModel):
    equipo_id: int


class DevolucionIn(BaseModel):
    danio: bool = False
    observaciones: str = Field(default="", max_length=200)


class RelojIn(BaseModel):
    ahora: datetime


class VolumenIn(BaseModel):
    cantidad: int = Field(ge=1, le=2000)
