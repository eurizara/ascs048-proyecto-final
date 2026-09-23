# Especificación de Requisitos del Software (ERS) — LabReserva UMG

| Campo | Valor |
|---|---|
| Sistema | LabReserva UMG — Reservas de laboratorios y préstamo de equipo |
| Versión de la ERS | 1.0 |
| Fecha | 26 de septiembre de 2026 |
| Curso | ASCS-048 Aseguramiento de la Calidad del Software — UMG |
| Carácter | **Esta ERS es el oráculo de prueba oficial.** Ante cualquier diferencia entre la ERS y el código, la documentación automática de la API (`/docs`) o los mensajes del sistema, **prevalece la ERS**. |
| Aclaraciones | Las respuestas oficiales a consultas se publican en `docs/aclaraciones.md` (ACL-01, ACL-02…) y forman parte de esta ERS. |

> El sistema, sus datos y sus reglas son ficticios y existen solo con fines académicos.

---

## 1. Introducción

### 1.1 Propósito
LabReserva permite a estudiantes y docentes reservar laboratorios y solicitar préstamos de equipo, y al personal administrativo gestionar confirmaciones, devoluciones, multas y reportes. Se expone como una API REST (JSON).

### 1.2 Convenciones y definiciones

| Término | Definición |
|---|---|
| Hora de Guatemala | Zona America/Guatemala, UTC−06:00, sin horario de verano. **Todas las reglas de fecha y hora se evalúan en hora de Guatemala.** |
| Formato de fecha y hora | ISO 8601. Si la entrada no indica zona, se interpreta como hora de Guatemala. Las respuestas incluyen el desfase `-06:00`. |
| Día calendario | Fecha (día/mes/año) en hora de Guatemala, sin considerar la hora. |
| Montos | Quetzales (Q), con 2 decimales. |
| Reloj del sistema | Momento "actual" usado por todas las reglas. Puede fijarse con la interfaz de soporte de pruebas (RN-31). |
| Titular | Usuario que creó la reserva o el préstamo. |
| Reserva vigente | Reserva en estado PENDIENTE o CONFIRMADA. |
| Reserva activa | Reserva en estado PENDIENTE, CONFIRMADA o EN_USO. |
| Préstamo no devuelto | Préstamo en estado ACTIVO o ATRASADO. |
| Saldo pendiente | Suma de multas y penalidades del usuario menos sus pagos registrados. |

### 1.3 Roles

| Rol | Descripción |
|---|---|
| ESTUDIANTE | Reserva laboratorios y solicita préstamos, con los límites de esta ERS. |
| DOCENTE | Igual que ESTUDIANTE, con límites ampliados indicados en cada regla. |
| ADMIN | Administra usuarios, confirma reservas, registra devoluciones y pagos, consulta reportes y usa la interfaz de soporte de pruebas. No crea reservas ni solicita préstamos. |

Estados de usuario: ACTIVO, SUSPENDIDO, BAJA. Estados de laboratorio: DISPONIBLE, MANTENIMIENTO. Estados de equipo: DISPONIBLE, PRESTADO, MANTENIMIENTO, BAJA.

---

## 2. Parámetros de negocio por carné

Cada estudiante del curso trabaja con **sus propios valores** para las reglas parametrizadas. Los valores se derivan de su carné universitario (formato `7690-14-9834`), que se configura en la variable de entorno `CARNE` antes de iniciar el sistema. Así, los valores esperados de las pruebas son distintos para cada estudiante.

| Parámetro | Significado | Rango posible |
|---|---|---|
| `MAX_HORAS_RESERVA` | Duración máxima de una reserva de ESTUDIANTE (horas) | 2 a 6 |
| `ANTICIPACION_MIN_H` | Anticipación mínima para reservar (horas) | 12 a 48 |
| `MAX_PRESTAMOS_EST` | Préstamos no devueltos simultáneos de ESTUDIANTE | 2 a 4 |
| `DIAS_PRESTAMO_EST` | Plazo del préstamo de ESTUDIANTE (días calendario) | 3 a 7 |
| `DIAS_GRACIA` | Días de atraso que no se cobran | 1 a 3 |
| `MULTA_DIARIA` | Multa por día cobrable (Q) | 5.50 a 14.50 |
| `TOPE_DIAS_MULTA` | Máximo de días cobrables por préstamo | 10 a 20 |
| `UMBRAL_SALDO` | Saldo pendiente a partir del cual se bloquean préstamos (Q) | 50 a 150 |
| `CANCELACION_H` | Horas antes del inicio a partir de las cuales cancelar genera penalidad | 2 a 12 |

Consulta de sus valores:
- `GET /api/parametros` (no requiere autenticación), o
- `python -m labreserva.config <su-carné>` desde la raíz del repositorio.

La respuesta incluye una **huella** (8 caracteres) que identifica su configuración. Anótela en `qa/estudiante.yaml`; si no coincide con la de su carné, su trabajo no es calificable.

---

## 3. Requisitos funcionales

### 3.1 Autenticación y usuarios

**RN-01 Inicio de sesión.** `POST /api/auth/login` con `email` y `password`. El correo se compara sin espacios al inicio o al final y sin distinguir mayúsculas de minúsculas. Si el correo no existe o la contraseña es incorrecta, responde 401 `CREDENCIALES_INVALIDAS` con el **mismo mensaje** en ambos casos. Si las credenciales son correctas, responde 200 con un token y los datos básicos del usuario (`id`, `nombre`, `rol`).

**RN-02 Usuarios inactivos.** Un usuario SUSPENDIDO o de BAJA con credenciales correctas no puede iniciar sesión: 403 `USUARIO_INACTIVO`. Un token de un usuario que deja de estar ACTIVO también recibe 403 `USUARIO_INACTIVO`.

**RN-03 Autorización.** Todas las operaciones, salvo el inicio de sesión, `GET /api/parametros` y `GET /api/soporte/reloj`, requieren el encabezado `Authorization: Bearer <token>`. Sin token o con un token inválido: 401 `NO_AUTENTICADO`. Operación reservada a otro rol: 403 `SIN_PERMISO`.

**RN-04 Registro de usuarios.** Solo ADMIN registra usuarios (`POST /api/usuarios`). Se validan en este orden:

| # | Campo | Regla | Error (400) |
|---|---|---|---|
| 1 | `nombre` | Tras quitar espacios al inicio y al final, de 3 a 60 caracteres. Solo letras (incluidas las vocales con tilde, la ü y la ñ, en mayúscula o minúscula), espacios y apóstrofo. Los espacios internos repetidos se guardan como uno solo. | `NOMBRE_INVALIDO` |
| 2 | `email` | Formato `usuario@dominio.ext`. Se guarda sin espacios extremos y en minúsculas. | `EMAIL_INVALIDO` |
| 3 | `password` | Mínimo 8 caracteres, con al menos una letra y al menos un dígito. | `PASSWORD_DEBIL` |
| 4 | `rol` | ESTUDIANTE, DOCENTE o ADMIN. | `ROL_INVALIDO` |

Si el correo ya existe (sin distinguir mayúsculas de minúsculas): 409 `EMAIL_DUPLICADO`. El usuario se crea ACTIVO, con saldo 0.00, y se responde 201 con su perfil.

**RN-05 Perfiles.** `GET /api/usuarios/me` devuelve el perfil propio. `GET /api/usuarios/{id}` devuelve el perfil indicado si es el propio o si quien consulta es ADMIN; en otro caso responde 404 `NO_ENCONTRADO`. El perfil contiene exactamente: `id`, `nombre`, `email`, `rol`, `estado`, `saldo_pendiente`.

### 3.2 Reservas de laboratorio

**RN-06 Horario.** Los laboratorios atienden de lunes a sábado, de 07:00 a 21:00. Una reserva debe iniciar y terminar el mismo día, con inicio ≥ 07:00 y fin ≤ 21:00; si no: 400 `FUERA_DE_HORARIO`. Inicio y fin deben caer en punto o a la media hora (minutos 00 o 30, sin segundos ni fracciones); si no: 400 `HORA_NO_VALIDA`. Solo se reservan laboratorios existentes (404 `NO_ENCONTRADO`) y en estado DISPONIBLE (409 `LABORATORIO_NO_DISPONIBLE`).

**RN-07 Duración.** Mínimo 1 hora. Máximo `MAX_HORAS_RESERVA` horas para ESTUDIANTE y `MAX_HORAS_RESERVA + 2` horas para DOCENTE. Fuera de estos límites: 400 `DURACION_INVALIDA`.

**RN-08 Anticipación.** El inicio debe ser al menos `ANTICIPACION_MIN_H` horas posterior al reloj del sistema; si no: 400 `ANTICIPACION_INSUFICIENTE`. No se aceptan reservas con más de 30 días de anticipación: 400 `ANTICIPACION_EXCESIVA`.

**RN-09 Asistentes.** El número de asistentes debe estar entre 1 y la capacidad del laboratorio; si no: 400 `ASISTENTES_INVALIDOS`.

**RN-10 Traslape.** Un laboratorio no puede tener dos reservas activas que se traslapen: 409 `TRASLAPE`. Los intervalos se consideran semiabiertos `[inicio, fin)`.

**RN-11 Límite de reservas.** Un ESTUDIANTE puede tener como máximo **2 reservas vigentes** (PENDIENTE o CONFIRMADA). Si ya tiene 2: 409 `LIMITE_RESERVAS`. DOCENTE no tiene este límite.

**RN-12 Creación y estado inicial.** Solo ESTUDIANTE y DOCENTE crean reservas (`POST /api/reservas`); ADMIN recibe 403 `SIN_PERMISO`. La reserva de ESTUDIANTE nace PENDIENTE y la de DOCENTE nace CONFIRMADA. Se responde 201.

**RN-13 Ciclo de vida.** Transiciones permitidas:

| Acción (endpoint) | Quién | Estado actual | Estado nuevo | Condición adicional |
|---|---|---|---|---|
| `POST /api/reservas/{id}/confirmar` | ADMIN | PENDIENTE | CONFIRMADA | — |
| `POST /api/reservas/{id}/cancelar` | Titular o ADMIN | PENDIENTE o CONFIRMADA | CANCELADA | Ver RN-14 |
| `POST /api/reservas/{id}/checkin` | Solo el titular | CONFIRMADA | EN_USO | Reloj entre inicio − 15 min e inicio + 15 min, ambos inclusive |
| `POST /api/reservas/{id}/no-show` | ADMIN | CONFIRMADA | NO_SHOW | Reloj posterior a inicio + 15 min |
| `POST /api/reservas/{id}/checkout` | Titular o ADMIN | EN_USO | FINALIZADA | — |

Cualquier otra combinación de acción y estado: 409 `TRANSICION_INVALIDA`. Si la transición es válida pero no se cumple la condición de tiempo: 409 `FUERA_DE_VENTANA`. Un ADMIN que intenta el check-in de una reserva ajena recibe 403 `SIN_PERMISO`.

**RN-14 Penalidad por cancelación tardía.** Si el **titular** cancela cuando faltan **menos** de `CANCELACION_H` horas para el inicio, se registra una penalidad de Q25.00 en la reserva (`penalidad`) y se suma a su saldo pendiente. Cuando faltan exactamente `CANCELACION_H` horas o más, no hay penalidad. La cancelación realizada por ADMIN nunca genera penalidad.

**RN-15 Privacidad de reservas.** Un usuario que no es ADMIN solo puede consultar u operar sus propias reservas. Una reserva ajena se trata como inexistente: 404 `NO_ENCONTRADO`. `GET /api/reservas` devuelve las reservas propias (ADMIN: todas), ordenadas por inicio y luego por id.

### 3.3 Préstamos de equipo

**RN-16 Solicitud.** Solo ESTUDIANTE y DOCENTE solicitan préstamos (`POST /api/prestamos`); ADMIN recibe 403 `SIN_PERMISO`. El equipo debe existir (404 `NO_ENCONTRADO`) y estar DISPONIBLE (409 `EQUIPO_NO_DISPONIBLE`). Al registrarse, el préstamo queda ACTIVO, la fecha del préstamo es el reloj del sistema y el equipo pasa a PRESTADO. Se responde 201.

**RN-17 Límite de préstamos.** Un usuario no puede superar sus préstamos **no devueltos** simultáneos: `MAX_PRESTAMOS_EST` para ESTUDIANTE y `MAX_PRESTAMOS_EST + 2` para DOCENTE. Si ya alcanzó el límite: 409 `LIMITE_PRESTAMOS`.

**RN-18 Bloqueo por saldo.** Un usuario con saldo pendiente **mayor o igual** a `UMBRAL_SALDO` no puede solicitar préstamos: 409 `SALDO_PENDIENTE`.

**RN-19 Vencimiento.** Fecha de vencimiento = día calendario del préstamo + `DIAS_PRESTAMO_EST` días (DOCENTE: el doble). Si ese día es domingo, el vencimiento pasa al lunes siguiente. La hora de vencimiento es siempre las 21:00 de ese día.

**RN-20 Equipo restringido.** Los equipos de tipo OSCILOSCOPIO solo se prestan a DOCENTE: 403 `EQUIPO_RESTRINGIDO`.

**RN-21 Multa por atraso.** Al registrar la devolución se calcula:

1. `dias_atraso` = días calendario entre el día del vencimiento y el día de la devolución (mínimo 0). Una devolución hecha el mismo día del vencimiento tiene 0 días de atraso, aunque ocurra después de las 21:00.
2. `dias_cobrables` = `dias_atraso − DIAS_GRACIA` (mínimo 0), con un máximo de `TOPE_DIAS_MULTA`.
3. `multa_diaria` = `MULTA_DIARIA`. Si el valor del equipo es **mayor o igual a Q5,000.00**, `multa_diaria` = `MULTA_DIARIA × 1.15`, redondeada a 2 decimales con redondeo **mitad hacia arriba** (0.005 sube a 0.01).
4. `multa` = `multa_diaria × dias_cobrables`. La multa se registra en el préstamo y se suma al saldo pendiente del titular.

*Ejemplo con valores ilustrativos que no corresponden a ningún carné:* `MULTA_DIARIA` = Q8.00, `DIAS_GRACIA` = 2 y `TOPE_DIAS_MULTA` = 10. Un equipo de Q4,500.00 con vencimiento el lunes a las 21:00 se devuelve el sábado a las 09:00: `dias_atraso` = 5, `dias_cobrables` = 3 y la multa es Q24.00. Si el equipo valiera Q6,000.00, la `multa_diaria` sería Q9.20 y la multa Q27.60.

**RN-22 Estados del préstamo y devolución.** Un préstamo ACTIVO se considera ATRASADO mientras no se devuelva y el reloj sea posterior a su vencimiento; este estado se muestra al consultarlo. Solo ADMIN registra devoluciones (`POST /api/prestamos/{id}/devolucion`, con `danio` verdadero o falso y `observaciones` de hasta 200 caracteres). Un préstamo ya devuelto responde 409 `PRESTAMO_CERRADO`. Al devolverse, el préstamo pasa a DEVUELTO y el equipo a DISPONIBLE; si se reporta daño, el equipo pasa a MANTENIMIENTO.

**RN-23 Pagos.** Solo ADMIN registra pagos (`POST /api/usuarios/{id}/pagos`). El monto debe ser mayor que 0 y tener como máximo 2 decimales (400 `MONTO_INVALIDO`), y no puede exceder el saldo pendiente (409 `MONTO_EXCEDE_SALDO`). El saldo nunca es negativo.

### 3.4 Reportes

**RN-24 Listado paginado.** `GET /api/prestamos` (solo ADMIN) acepta `page` (≥ 1, por defecto 1) y `size` (de 1 a 50, por defecto 10). Responde `page`, `size`, `total`, `pages` e `items`, donde `pages` = total de páginas necesarias para mostrar `total` elementos con `size` por página (0 si no hay elementos). Los elementos se ordenan por fecha del préstamo descendente y, a igual fecha, por id descendente. Cada elemento incluye, además de los campos del préstamo, `usuario_nombre`, `equipo_codigo` y `numero_prestamo_usuario`: la posición cronológica del préstamo entre los préstamos del mismo usuario (1 = el primero; a igual fecha, el de menor id va primero). Una página sin elementos devuelve `items` vacío.

**RN-25 Exportación CSV.** `GET /api/reportes/prestamos.csv` (solo ADMIN) devuelve un archivo CSV en UTF-8 conforme a RFC 4180: separador coma, una fila de encabezado `id,usuario,equipo,fecha_prestamo,vencimiento,fecha_devolucion,estado,multa,observaciones` y una fila por préstamo ordenada por id. Los campos que contienen comas, comillas o saltos de línea van entre comillas dobles, y las comillas internas se duplican. `usuario` es el nombre completo tal como está registrado (con tildes y ñ), `estado` es el estado mostrado según RN-22, `multa` lleva 2 decimales y `fecha_devolucion` va vacía si no hay devolución.

**RN-26 Estadísticas.** `GET /api/reportes/estadisticas` (solo ADMIN), con filtros opcionales `desde` y `hasta` (fechas, inclusive) sobre el día de devolución, responde: `devueltos` (préstamos devueltos en el rango), `a_tiempo` (devueltos cuya devolución fue anterior o igual al instante de vencimiento), `tasa_puntualidad` = `a_tiempo / devueltos × 100` redondeada a 1 decimal (0.0 si no hay devoluciones en el rango) y `multas_total`.

### 3.5 Requisitos de calidad

**RN-27 Protección de credenciales.** Las contraseñas se almacenan únicamente como hash. Ninguna respuesta de la API ni la bitácora de ejecución puede contener contraseñas ni sus hashes.

**RN-28 Desempeño.** Con al menos 1,000 préstamos registrados, `GET /api/prestamos` con `size` ≤ 50 debe responder en menos de 1 segundo (percentil 95 de al menos 10 mediciones, API ejecutándose localmente).

**RN-29 Formato de errores.** Toda respuesta de error, incluidas rutas inexistentes (404 `NO_ENCONTRADO`) y métodos no admitidos (405 `METODO_NO_PERMITIDO`), tiene el cuerpo `{"error": "<CODIGO>", "detalle": "<texto en español>"}`. Los datos de entrada con formato o tipo inválido, o faltantes, en el cuerpo o en los parámetros, responden 400 `VALIDACION`. Un error no controlado responde 500 `ERROR_INTERNO`.

**RN-30 Bitácora de ejecución.** Cada petición a `/api` se registra en `bitacora/ejecucion.jsonl` con un encadenamiento criptográfico que permite detectar ediciones, eliminaciones o reordenamientos. La bitácora es evidencia de ejecución: no debe editarse ni borrarse.

### 3.6 Soporte de pruebas

**RN-31 Interfaz de soporte de pruebas.** Para permitir pruebas repetibles:

| Endpoint | Rol | Efecto |
|---|---|---|
| `GET /api/soporte/reloj` | Cualquiera | Muestra el reloj del sistema y si está simulado. |
| `PUT /api/soporte/reloj` con `{"ahora": "<fecha-hora>"}` | ADMIN | Fija el reloj en ese instante. El reloj simulado **no avanza** hasta que se cambie o se libere. |
| `DELETE /api/soporte/reloj` | ADMIN | Vuelve al reloj real. |
| `POST /api/soporte/reset` | ADMIN | Restablece los datos semilla (Anexo C), con fechas relativas al reloj actual. **Invalida todos los tokens.** |
| `POST /api/soporte/volumen` con `{"cantidad": n}` (1 a 2000) | ADMIN | Agrega `n` préstamos devueltos antiguos, para pruebas de desempeño. |
| `GET /api/parametros` | Cualquiera | Parámetros de negocio de la sección 2 y la huella. |

---

## 4. Interfaz de la API

URL base local: `http://localhost:8000`. Documentación interactiva generada automáticamente: `/docs` (informativa; **no es oráculo**).

| Método y ruta | Rol | Éxito | Reglas |
|---|---|---|---|
| `POST /api/auth/login` | — | 200 | RN-01, RN-02 |
| `GET /api/usuarios/me` | Autenticado | 200 | RN-05 |
| `GET /api/usuarios/{id}` | Titular o ADMIN | 200 | RN-05, RN-27 |
| `POST /api/usuarios` | ADMIN | 201 | RN-04 |
| `POST /api/usuarios/{id}/pagos` | ADMIN | 200 | RN-23 |
| `GET /api/laboratorios` | Autenticado | 200 | — |
| `POST /api/reservas` | ESTUDIANTE, DOCENTE | 201 | RN-06 a RN-12 |
| `GET /api/reservas` | Autenticado | 200 | RN-15 |
| `GET /api/reservas/{id}` | Titular o ADMIN | 200 | RN-15 |
| `POST /api/reservas/{id}/{accion}` | Según RN-13 | 200 | RN-13, RN-14 |
| `GET /api/equipos` | Autenticado | 200 | — |
| `POST /api/prestamos` | ESTUDIANTE, DOCENTE | 201 | RN-16 a RN-20 |
| `GET /api/prestamos/mios` | Autenticado | 200 | RN-22 |
| `GET /api/prestamos/{id}` | Titular o ADMIN | 200 | RN-22 |
| `GET /api/prestamos` | ADMIN | 200 | RN-24, RN-28 |
| `POST /api/prestamos/{id}/devolucion` | ADMIN | 200 | RN-21, RN-22 |
| `GET /api/reportes/prestamos.csv` | ADMIN | 200 | RN-25 |
| `GET /api/reportes/estadisticas` | ADMIN | 200 | RN-26 |
| Interfaz de soporte | Según RN-31 | 200 | RN-31 |

Campos de una reserva: `id`, `usuario_id`, `laboratorio_id`, `inicio`, `fin`, `asistentes`, `estado`, `penalidad`.
Campos de un préstamo: `id`, `usuario_id`, `equipo_id`, `fecha_prestamo`, `vencimiento`, `fecha_devolucion`, `estado`, `multa`, `danio`, `observaciones`.

---

## Anexo A. Orden de validación

Cuando una petición incumple varias reglas, se informa **la primera** según este orden:

| Operación | Orden de verificación |
|---|---|
| `POST /api/reservas` | 1) Formato del cuerpo (400 `VALIDACION`) → 2) rol (403) → 3) laboratorio existe (404) → 4) laboratorio disponible (409) → 5) horario RN-06 (400) → 6) duración RN-07 (400) → 7) anticipación RN-08 (400) → 8) asistentes RN-09 (400) → 9) límite RN-11 (409) → 10) traslape RN-10 (409) |
| `POST /api/prestamos` | 1) Formato del cuerpo → 2) rol (403) → 3) equipo existe (404) → 4) equipo disponible (409) → 5) equipo restringido RN-20 (403) → 6) saldo RN-18 (409) → 7) límite RN-17 (409) |
| `confirmar`, `no-show` | 1) Rol ADMIN (403) → 2) reserva existe (404) → 3) transición válida (409 `TRANSICION_INVALIDA`) → 4) condición de tiempo (409 `FUERA_DE_VENTANA`) |
| `cancelar`, `checkout` | 1) Reserva visible para el usuario (404) → 2) transición válida (409 `TRANSICION_INVALIDA`) |
| `checkin` | 1) Reserva visible para el usuario (404) → 2) es el titular (403) → 3) transición válida (409) → 4) ventana de ingreso (409 `FUERA_DE_VENTANA`) |
| `POST /api/prestamos/{id}/devolucion` | 1) Formato del cuerpo → 2) rol ADMIN (403) → 3) préstamo existe (404) → 4) no devuelto (409 `PRESTAMO_CERRADO`) |

## Anexo B. Interfaz del módulo de reglas (pruebas unitarias)

El módulo `labreserva/reglas.py` contiene las reglas de negocio como funciones puras, sin base de datos. Sus pruebas unitarias deben importar estas funciones; las firmas no cambian entre versiones del sistema.

| Función | Regla | Devuelve |
|---|---|---|
| `validar_horario(inicio, fin)` | RN-06 | `None` o `"FUERA_DE_HORARIO"` / `"HORA_NO_VALIDA"` |
| `validar_duracion(inicio, fin, rol, max_horas)` | RN-07 | `None` o `"DURACION_INVALIDA"` |
| `validar_anticipacion(inicio, ahora, min_horas)` | RN-08 | `None` o `"ANTICIPACION_INSUFICIENTE"` / `"ANTICIPACION_EXCESIVA"` |
| `se_traslapan(a_inicio, a_fin, b_inicio, b_fin)` | RN-10 | `bool` |
| `siguiente_estado(estado, accion)` | RN-13 | Nuevo estado o `None`; `accion` ∈ `confirmar`, `cancelar`, `checkin`, `no_show`, `checkout` |
| `en_ventana_checkin(inicio, ahora)` | RN-13 | `bool` |
| `puede_marcar_no_show(inicio, ahora)` | RN-13 | `bool` |
| `penalidad_cancelacion(inicio, ahora, quien_cancela, horas_limite)` | RN-14 | `Decimal`; `quien_cancela` es el rol de quien cancela |
| `limite_prestamos(rol, max_est)` | RN-17 | `int` |
| `puede_prestar(saldo, umbral)` | RN-18 | `bool` |
| `calcular_vencimiento(fecha_prestamo, rol, dias_prestamo)` | RN-19 | `datetime` con zona |
| `dias_atraso(vencimiento, devolucion)` | RN-21 | `int` |
| `multa_diaria(valor_equipo, multa_base)` | RN-21 | `Decimal` |
| `calcular_multa(vencimiento, devolucion, valor_equipo, multa_base, dias_gracia, tope_dias)` | RN-21 | `Decimal` |
| `total_paginas(total, tamanio)` | RN-24 | `int` |
| `tasa_puntualidad(a_tiempo, devueltos)` | RN-26 | `float` |
| `validar_nombre(nombre)`, `validar_email(email)`, `validar_password(password)` | RN-04 | `None` o el código de error |
| `normalizar_email(email)` | RN-01, RN-04 | `str` |

Las fechas se pasan como `datetime` con zona horaria (use `labreserva.reloj.GT`) y los montos como `Decimal`.

## Anexo C. Datos semilla

El sistema se carga con estos datos la primera vez que inicia y cada vez que se invoca `POST /api/soporte/reset`. Las fechas de reservas y préstamos se generan relativas al reloj del sistema en ese momento.

**Usuarios**

| id | Nombre | Correo | Rol | Estado | Contraseña |
|---|---|---|---|---|---|
| 1 | Administración LabReserva | admin@labreserva.test | ADMIN | ACTIVO | Admin2026! |
| 2 | Marta Julieta Pérez | mperez@labreserva.test | DOCENTE | ACTIVO | Docente2026 |
| 3 | Óscar Iván Castañeda | ocastaneda@labreserva.test | DOCENTE | ACTIVO | Docente2026 |
| 4 | Ana Lucía Gómez | agomez@labreserva.test | ESTUDIANTE | ACTIVO | Estudiante2026 |
| 5 | José Andrés Peña | jpena@labreserva.test | ESTUDIANTE | ACTIVO | Estudiante2026 |
| 6 | María Fernanda López | mlopez@labreserva.test | ESTUDIANTE | ACTIVO | Estudiante2026 |
| 7 | Luis Carlos Hernández | lhernandez@labreserva.test | ESTUDIANTE | ACTIVO | Estudiante2026 |
| 8 | Sofía Alejandra Ramírez | sramirez@labreserva.test | ESTUDIANTE | ACTIVO | Estudiante2026 |
| 9 | Carlos Eduardo Toj | ctoj@labreserva.test | ESTUDIANTE | SUSPENDIDO | Estudiante2026 |
| 10 | Diego Armando Xicará | dxicara@labreserva.test | ESTUDIANTE | BAJA | Estudiante2026 |
| 11 | Gabriela Beatriz Sic | gsic@labreserva.test | ESTUDIANTE | ACTIVO | Estudiante2026 |

**Laboratorios:** 1 Laboratorio de Redes (capacidad 20), 2 Laboratorio de Software (30), 3 Laboratorio de Electrónica (15), 4 Sala de Proyectos (8, en MANTENIMIENTO).

**Equipos:** 17 equipos de tipo LAPTOP, PROYECTOR, KIT_ARDUINO y OSCILOSCOPIO, con valores entre Q650.00 y Q8,500.00 y distintos estados. Consúltelos con `GET /api/equipos`.

**Reservas y préstamos:** la semilla incluye reservas en varios estados y un historial de préstamos (devueltos, activos y atrasados) con saldos y observaciones reales de operación. **Explore los datos**: forman parte del objeto de prueba.
