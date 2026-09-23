# LabReserva UMG — Objeto de prueba del Proyecto Final ASCS-048

Sistema de reservas de laboratorios y préstamo de equipo (API REST en Python/FastAPI) sobre el que usted ejecutará el aseguramiento de la calidad del Proyecto Final. **El sistema contiene defectos.** Su trabajo es encontrarlos, demostrarlos, analizarlos y corregirlos, siguiendo el enunciado publicado en Canvas.

- **Especificación oficial (oráculo):** [`docs/ERS_LabReserva.md`](docs/ERS_LabReserva.md)
- **Aclaraciones oficiales:** [`docs/aclaraciones.md`](docs/aclaraciones.md)
- **Plantillas de entregables:** [`plantillas/`](plantillas/)

## 1. Cree SU repositorio privado (no haga fork)

1. En esta página, pulse **Use this template → Create a new repository**.
2. Propietario: su cuenta. Nombre sugerido: `ascs048-pf-<su-carné>`. Visibilidad: **Private**.
3. En su repositorio: **Settings → Collaborators → Add people** e invite al docente.

> No use *Fork*: un fork de un repositorio público no puede hacerse privado y su trabajo quedaría visible para sus compañeros.

## 2. Configure su carné

```bash
cp .env.example .env        # en Windows: copy .env.example .env
```
Edite `.env` y escriba su carné **exactamente** como en Canvas, por ejemplo `CARNE=7690-14-9834`. Sus parámetros de negocio dependen de él (ERS, sección 2).

## 3. Levante el sistema

**Opción A — Docker (recomendada)**
```bash
docker compose up -d --build
docker compose logs -f labreserva      # Ctrl+C para salir de los logs
```

**Opción B — Python 3.12 local**
```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate    Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Linux/macOS: export CARNE=7690-14-9834    Windows PowerShell: $env:CARNE="7690-14-9834"
uvicorn labreserva.main:app --port 8000
```

## 4. Verifique

- `http://localhost:8000/api/parametros` → sus parámetros y su **huella**. Anótela en `qa/estudiante.yaml`.
- `http://localhost:8000/docs` → documentación interactiva (informativa; el oráculo es la ERS).
- Credenciales de prueba: ERS, Anexo C.

## 5. Reglas del repositorio

| Regla | Detalle |
|---|---|
| El código de `labreserva/` no se modifica en `main` | Las correcciones van **solo** en la rama `correcciones`. |
| La bitácora no se edita | `bitacora/ejecucion.jsonl` se versiona tal como la genera el sistema (ERS, RN-30). |
| Contrato de pruebas | Pruebas de API con la variable `SUT_URL` (por defecto `http://localhost:8000`); pruebas unitarias importando `labreserva.reglas`; ejecutar con `python -m pytest` desde la raíz. |
| Consultas | Grupo de Telegram del curso, hasta el 17 de octubre de 2026. Pregunte por el **requisito**, nunca publique defectos, pruebas, código ni resultados (es un trabajo individual). Solo la respuesta del docente es oficial y se publica en `docs/aclaraciones.md`. |

## 6. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `failed to connect to the docker API` o `Cannot connect to the Docker daemon` | Abra Docker Desktop y espere a que termine de iniciar antes de ejecutar `docker compose`. |
| macOS: `You have not agreed to the Xcode and Apple SDKs license` | Ejecute `sudo xcodebuild -license accept` e ingrese la contraseña de su Mac (requiere usuario administrador). |
| No puedo clonar mi repositorio privado (pide usuario y contraseña) | GitHub no acepta la contraseña de la cuenta. Use **GitHub Desktop** (Clone repository), o GitHub CLI: `gh auth login` y luego `gh repo clone <usuario>/<repositorio>`. |
| `env file ... .env not found` | Copie `.env.example` como `.env` (paso 2). |
| El contenedor se detiene y los logs dicen `Carné inválido` | Revise `CARNE=` en `.env` y ejecute de nuevo `docker compose up -d --build`. |
| `port is already allocated` | Otro programa usa el puerto 8000; ciérrelo (macOS/Linux: `lsof -i :8000`). |

Para recibir nuevas aclaraciones en su repositorio, consulte `docs/aclaraciones.md` en este repositorio público (se actualiza aquí).
