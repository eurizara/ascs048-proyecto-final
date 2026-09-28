# Plan de pruebas — LabReserva UMG

> **Instrucciones:** complete cada sección reemplazando los textos entre corchetes. Basado en ISO/IEC/IEEE 29119-3 (plan de pruebas).
> Este archivo se entrega en el Avance 1 y se resume en la sección 2 de su informe.

## 1. Identificación

| Campo | Valor |
|---|---|
| Estudiante | [nombre] |
| Carné | [carné] |
| Huella | [huella] |
| Versión del plan | [1.0] |
| Fecha | [fecha] |

## 2. Objetivo

[En 3 a 5 líneas: qué se busca con estas pruebas y qué decisión apoyarán sus resultados.]

## 3. Alcance

| Dentro del alcance | Fuera del alcance |
|---|---|
| [reglas, módulos o endpoints que probará] | [lo que no probará y por qué] |

## 4. Matriz de riesgos

> **Probabilidad** de que la regla tenga defectos (1 = baja, 2 = media, 3 = alta), considerando su complejidad: fechas, cálculos, estados, permisos.
> **Impacto** si falla (1 = molestia, 2 = afecta la operación, 3 = afecta dinero, seguridad o datos).
> **Nivel** = probabilidad × impacto. **Prioridad**: Alta (6 a 9), Media (3 a 4), Baja (1 a 2).
> Complete las 31 filas. La prioridad debe explicar el orden en que diseña y ejecuta sus pruebas.

| Regla | Nombre | Probabilidad | Impacto | Nivel | Prioridad | Técnica(s) planificada(s) | Justificación |
|---|---|---|---|---|---|---|---|
| RN-01 | Inicio de sesión | | | | | | |
| RN-02 | Usuarios inactivos | | | | | | |
| RN-03 | Autorización | | | | | | |
| RN-04 | Registro de usuarios | | | | | | |
| RN-05 | Perfiles | | | | | | |
| RN-06 | Horario | | | | | | |
| RN-07 | Duración | | | | | | |
| RN-08 | Anticipación | | | | | | |
| RN-09 | Asistentes | | | | | | |
| RN-10 | Traslape | | | | | | |
| RN-11 | Límite de reservas | | | | | | |
| RN-12 | Creación y estado inicial | | | | | | |
| RN-13 | Ciclo de vida de la reserva | | | | | | |
| RN-14 | Penalidad por cancelación tardía | | | | | | |
| RN-15 | Privacidad de reservas | | | | | | |
| RN-16 | Solicitud de préstamo | | | | | | |
| RN-17 | Límite de préstamos | | | | | | |
| RN-18 | Bloqueo por saldo | | | | | | |
| RN-19 | Vencimiento | | | | | | |
| RN-20 | Equipo restringido | | | | | | |
| RN-21 | Multa por atraso | | | | | | |
| RN-22 | Estados del préstamo y devolución | | | | | | |
| RN-23 | Pagos | | | | | | |
| RN-24 | Listado paginado | | | | | | |
| RN-25 | Exportación CSV | | | | | | |
| RN-26 | Estadísticas | | | | | | |
| RN-27 | Protección de credenciales | | | | | | |
| RN-28 | Desempeño | | | | | | |
| RN-29 | Formato de errores | | | | | | |
| RN-30 | Bitácora de ejecución | | | | | | |
| RN-31 | Soporte de pruebas | | | | | | |

## 5. Enfoque de pruebas

| Elemento | Decisión |
|---|---|
| Niveles | [unitario sobre labreserva/reglas.py, API] |
| Tipos | [funcional, seguridad, desempeño, estático, regresión] |
| Técnicas de diseño | [dónde aplicará EP, VL, tabla de decisión y transición de estados] |
| Herramientas | [pytest, Postman o Bruno, ruff, bandit, GitHub Actions] |

## 6. Entorno y datos de prueba

| Elemento | Detalle |
|---|---|
| Sistema operativo | [Windows / macOS / Linux, versión] |
| Ejecución del sistema | [Docker o Python local] |
| Datos | [datos semilla (ERS, Anexo C), reloj simulado, volumen para RN-28] |
| Mis parámetros | [copie aquí sus 9 parámetros] |

## 7. Criterios

| Criterio | Definición |
|---|---|
| Entrada (cuándo empiezo a ejecutar) | [...] |
| Salida (cuándo doy por terminadas las pruebas) | [...] |
| Suspensión y reanudación | [...] |

## 8. Cronograma

| Semana | Actividad | Producto |
|---|---|---|
| 26 sep – 03 oct | | |
| 03 – 10 oct | | |
| 10 – 17 oct | | |
| 17 – 24 oct | | |
| 24 – 31 oct | | |
| 31 oct – 07 nov | | |

## 9. Ambigüedades y consultas

> Registre cada duda de interpretación de la ERS, si la consultó en el grupo de Telegram y la aclaración oficial que resultó.

| # | Regla | Duda | ¿Consultada? | Aclaración (ACL-xx) |
|---|---|---|---|---|
| 1 | | | | |
