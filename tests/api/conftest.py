"""Apoyo para pruebas de API. Úselo tal cual; puede agregar sus propias fixtures.

Contrato (enunciado, sección 8): la URL del sistema se lee de la variable de
entorno SUT_URL (por defecto http://localhost:8000).
"""
import os

import httpx
import pytest

SUT_URL = os.environ.get("SUT_URL", "http://localhost:8000").rstrip("/")
CREDENCIALES_ADMIN = ("admin@labreserva.test", "Admin2026!")


class Api:
    """Cliente de la API con utilidades para dejar el sistema en un estado conocido."""

    def __init__(self, cliente: httpx.Client):
        self.cliente = cliente

    def sesion(self, email: str, password: str) -> dict:
        """Inicia sesión y devuelve el encabezado Authorization listo para usar."""
        r = self.cliente.post("/api/auth/login", json={"email": email, "password": password})
        assert r.status_code == 200, f"No se pudo iniciar sesión con {email}: {r.text}"
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def admin(self) -> dict:
        return self.sesion(*CREDENCIALES_ADMIN)

    def preparar(self, ahora: str = "2026-10-05T08:00:00") -> None:
        """Fija el reloj del sistema (hora de Guatemala) y restablece los datos semilla.

        Después de preparar(), los tokens anteriores dejan de servir (ERS, RN-31):
        vuelva a iniciar sesión.
        """
        h = self.admin()
        r = self.cliente.put("/api/soporte/reloj", json={"ahora": ahora}, headers=h)
        assert r.status_code == 200, r.text
        r = self.cliente.post("/api/soporte/reset", headers=h)
        assert r.status_code == 200, r.text

    def parametros(self) -> dict:
        """Sus parámetros de negocio (ERS, sección 2)."""
        return self.cliente.get("/api/parametros").json()


@pytest.fixture(scope="session")
def api():
    with httpx.Client(base_url=SUT_URL, timeout=60) as cliente:
        yield Api(cliente)
