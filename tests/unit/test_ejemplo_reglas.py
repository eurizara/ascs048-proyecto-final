"""EJEMPLO de formato de una prueba unitaria sobre labreserva/reglas.py. No cuenta para los mínimos.

Use solo las funciones del Anexo B de la ERS. Las fechas llevan zona horaria (GT).
"""
from datetime import datetime

from labreserva.reglas import validar_horario
from labreserva.reloj import GT


def test_EJ02_reserva_en_domingo_fuera_de_horario():
    inicio = datetime(2026, 10, 11, 9, 0, tzinfo=GT)   # domingo
    fin = datetime(2026, 10, 11, 10, 0, tzinfo=GT)
    assert validar_horario(inicio, fin) == "FUERA_DE_HORARIO"
