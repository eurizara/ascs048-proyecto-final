# LabReserva UMG — Proyecto Final ASCS-048

Sistema de reservas de laboratorios y préstamo de equipo (API REST en Python/FastAPI) sobre el que usted realizará el aseguramiento de la calidad del Proyecto Final. **El sistema contiene defectos.** Su trabajo es encontrarlos, demostrarlos, analizarlos y corregirlos, siguiendo el **enunciado publicado en Canvas**.

| Documento | Para qué |
|---|---|
| [`docs/ERS_LabReserva.md`](docs/ERS_LabReserva.md) | Especificación oficial: lo que el sistema **debe** hacer (oráculo de prueba) |
| [`docs/aclaraciones.md`](docs/aclaraciones.md) | Respuestas oficiales del docente a las consultas |
| [`qa/LEEME.md`](qa/LEEME.md) | Qué archivo de documentación llenar y con qué mínimo |

Funciona en **Windows, macOS y Linux**.

## 1. Instale lo necesario

| Herramienta | Windows 10/11 | macOS | Linux |
|---|---|---|---|
| Git | Git for Windows (git-scm.com) | Viene con el sistema: ejecute `git --version` y acepte la instalación | Paquete `git` de su distribución |
| Docker (opción A, recomendada) | Docker Desktop (usa WSL 2; el instalador lo configura) | Docker Desktop (elija Apple chip o Intel) | Docker Engine con el plugin `compose` |
| Python 3.12 (opción B y para ejecutar pruebas) | python.org; marque **"Add python.exe to PATH"** | python.org o Homebrew | Paquete `python3.12` |
| Postman o Bruno | Aplicación de escritorio | Aplicación de escritorio | Aplicación de escritorio |
| Node.js 20 o superior (opcional) | nodejs.org | nodejs.org | nodejs.org | 

Node.js solo se necesita para ejecutar su colección por línea de comandos en su equipo; el pipeline de GitHub ya lo trae.

## 2. Cree SU repositorio privado (no haga fork)

1. En esta página: **Use this template → Create a new repository**.
2. Propietario: su cuenta. Nombre: `ascs048-pf-<su-carné>`. Visibilidad: **Private**.
3. En su repositorio: **Settings → Collaborators → Add people** e invite al docente: **`eurizara`**.
4. Clónelo en su equipo. Como es privado, GitHub no acepta la contraseña de su cuenta: use **GitHub Desktop** (*File → Clone repository*) o GitHub CLI (`gh auth login` y luego `gh repo clone <usuario>/<repositorio>`).

> No use *Fork*: un fork de un repositorio público no puede hacerse privado y su trabajo quedaría visible para sus compañeros.

## 3. Configure su carné

Desde la carpeta del repositorio, copie la plantilla de configuración:

| Windows (PowerShell) | Windows (CMD) | macOS / Linux |
|---|---|---|
| `Copy-Item .env.example .env` | `copy .env.example .env` | `cp .env.example .env` |

Abra `.env` con un editor de texto (Bloc de notas, VS Code, `nano`) y escriba su carné **exactamente** como en Canvas: `CARNE=7690-14-9834`. Sus parámetros de negocio dependen de él (ERS, sección 2).

## 4. Levante el sistema

**Opción A — Docker (igual en los tres sistemas).** Abra Docker Desktop y espere a que termine de iniciar.

```
docker compose up -d --build
docker compose logs labreserva
docker compose down            # para apagarlo
```

**Opción B — Python 3.12 local.** Ejecute siempre desde la raíz del repositorio.

| Paso | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Crear entorno | `py -3.12 -m venv .venv` | `python3.12 -m venv .venv` |
| Activarlo | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| Instalar | `pip install -r requirements-dev.txt` | `pip install -r requirements-dev.txt` |
| Carné | `$env:CARNE="7690-14-9834"` | `export CARNE=7690-14-9834` |
| Arrancar | `uvicorn labreserva.main:app --port 8000` | `uvicorn labreserva.main:app --port 8000` |

## 5. Verifique

- `http://localhost:8000/api/parametros` → sus parámetros y su **huella**. Anótelos en `qa/estudiante.yaml`.
- `http://localhost:8000/docs` → documentación interactiva (informativa; el oráculo es la ERS).
- Usuarios y contraseñas de prueba: ERS, Anexo C.

## 6. Ejecute las pruebas

Con el sistema levantado y el entorno de la opción B activado (`pip install -r requirements-dev.txt`):

| Qué | Comando |
|---|---|
| Todas las pruebas pytest | `python -m pytest` |
| Con cobertura de `reglas.py` | `python -m pytest --cov=labreserva --cov-branch` y luego `coverage report --include=labreserva/reglas.py` |
| Otra URL o puerto | PowerShell: `$env:SUT_URL="http://localhost:8080"` · macOS/Linux: `export SUT_URL=http://localhost:8080` |
| Colección Postman | `npx newman run api-collection/postman/LabReserva.postman_collection.json -e api-collection/postman/local.postman_environment.json` |
| Colección Bruno | `cd api-collection/bruno` y luego `npx @usebruno/cli run --env local` |
| Análisis estático | `ruff check labreserva tests` y `bandit -r labreserva` |

Las pruebas y la colección incluidas son **ejemplos de formato** (`EJ01`, `EJ02`, `EJ03`) y no cuentan para los mínimos.

## 7. Estructura y reglas del repositorio

```
labreserva/              Sistema (NO se modifica en main; las correcciones van en la rama correcciones)
docs/                    ERS y aclaraciones oficiales
qa/                      Su documentación (plantillas listas para llenar)
tests/unit/  tests/api/  Sus pruebas pytest
api-collection/          Su colección: deje solo la carpeta postman/ o bruno/
.github/workflows/ci.yml Pipeline listo (lee su carné de qa/estudiante.yaml)
bitacora/                Bitácora de ejecución generada por el sistema (no se edita)
```

| Regla | Detalle |
|---|---|
| `main` no se corrige | El código de `labreserva/` no se modifica en `main`. Las correcciones van **solo** en la rama `correcciones`. |
| La bitácora no se edita | `bitacora/ejecucion.jsonl` se versiona tal como la genera el sistema (ERS, RN-30). |
| Formato fijo | Las plantillas de `qa/` no cambian de columnas ni campos. |
| Consultas | Grupo de Telegram del curso, hasta el 17 de octubre de 2026. Pregunte por el **requisito**; nunca publique defectos, pruebas, código ni resultados (es un trabajo individual). Solo la respuesta del docente es oficial y se publica en `docs/aclaraciones.md`. |

Para recibir nuevas aclaraciones, consulte `docs/aclaraciones.md` en este repositorio público (se actualiza aquí).

## 8. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Mi primera ejecución en **Actions** falló (❌) en el paso "Leer carné" | Es normal: aún no ha llenado `qa/estudiante.yaml`. Escriba su carné y su huella, envíe el cambio y el pipeline avanzará. En `main` es esperado que termine en rojo mientras sus pruebas detecten defectos o la cobertura de `reglas.py` sea menor al 80 %: revise qué paso aparece en rojo. |
| `failed to connect to the docker API` o `Cannot connect to the Docker daemon` | Abra Docker Desktop y espere a que termine de iniciar. |
| Windows: Docker Desktop pide WSL o virtualización | Acepte la instalación de WSL 2 que ofrece el instalador y reinicie; si pide virtualización, actívela en la BIOS. |
| Windows: `Activate.ps1 cannot be loaded because running scripts is disabled` | Ejecute una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelva a activar el entorno. |
| Windows: `py` o `python` no se reconoce | Reinstale Python marcando "Add python.exe to PATH". |
| macOS: `You have not agreed to the Xcode and Apple SDKs license` | Ejecute `sudo xcodebuild -license accept` (requiere usuario administrador). |
| No puedo clonar mi repositorio privado | Use GitHub Desktop o GitHub CLI (sección 2); la contraseña de la cuenta no sirve para clonar. |
| `env file ... .env not found` | Copie `.env.example` como `.env` (sección 3). |
| El contenedor se detiene y los logs dicen `Carné inválido` | Revise `CARNE=` en `.env` y ejecute de nuevo `docker compose up -d --build`. |
| `port is already allocated` o, en Windows, `access permissions` al usar el puerto 8000 | Cambie `PUERTO=8000` por `PUERTO=8080` en `.env` y use `http://localhost:8080` en `SUT_URL` y en `base_url` de su colección. |
| Tildes rotas al abrir un CSV en Excel | Guarde como "CSV UTF-8 (delimitado por comas)". |
