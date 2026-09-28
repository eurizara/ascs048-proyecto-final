"""EJEMPLO de formato de una prueba de API. No cuenta para los mínimos.

Nombre de cada prueba: test_<ID del caso en qa/casos_prueba.csv>_<descripción>.
"""


def test_EJ01_usuario_suspendido_no_inicia_sesion(api):
    # Preparación: reloj fijo y datos semilla conocidos (ERS, Anexo C).
    api.preparar()
    # Ejecución
    r = api.cliente.post("/api/auth/login",
                         json={"email": "ctoj@labreserva.test", "password": "Estudiante2026"})
    # Verificación contra la ERS (RN-02 y RN-29)
    assert r.status_code == 403
    assert r.json()["error"] == "USUARIO_INACTIVO"
