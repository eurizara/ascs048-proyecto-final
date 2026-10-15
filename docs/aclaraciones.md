# Aclaraciones oficiales a la ERS

Este archivo forma parte de la ERS (`docs/ERS_LabReserva.md`) y tiene la misma autoridad como oráculo de prueba. Las consultas se hacen por el grupo de Telegram del curso **hasta el sábado 17 de octubre de 2026**; el docente publica aquí cada respuesta oficial. Solo lo publicado en este archivo es oficial; las respuestas de compañeros en el grupo no lo son.

**Cómo consultar:** pregunte por el requisito (por ejemplo, «¿la regla RN-xx aplica también al rol DOCENTE?»), no por el comportamiento que observó. No publique en el grupo defectos, pruebas, código ni resultados: el proyecto es individual.

**Cómo citarlas:** en sus casos de prueba y reportes, cite la regla y la aclaración, por ejemplo `RN-08 / ACL-01`.

| ID | Fecha | Regla | Consulta | Respuesta oficial |
|---|---|---|---|---|
| — | — | — | (sin aclaraciones publicadas todavía) | — |

1. RN-04 (formato de correo). Primero se quitan los espacios al inicio y al final. Luego el correo es válido si cumple todo lo siguiente:

Tiene exactamente una @.
Tiene al menos un carácter antes de la @.
No tiene espacios internos.
Después de la @ hay un dominio con al menos un punto, y ese punto tiene al menos un carácter antes y después.

El signo «+», los subdominios y los puntos consecutivos no están regulados por la ERS. Por lo tanto no son defecto y no deben probarse como requisito.

2. RN-06 (horario). Dentro de RN-06 se verifica primero el horario de atención: mismo día, lunes a sábado, inicio ≥ 07:00 y fin ≤ 21:00. Después se verifica la regla de minutos 00/30. Un inicio a las 06:45 responde 400 FUERA_DE_HORARIO.

3. RN-08 (anticipación). El límite se mide como 30 × 24 horas (720 h) desde el reloj del sistema, inclusive. Se acepta un inicio hasta exactamente 720 h después del reloj. Un inicio posterior se rechaza con ANTICIPACION_EXCESIVA, siempre que cumpla las validaciones previas del Anexo A.

4. RN-23 (pagos). Las validaciones se aplican en este orden:

Formato del cuerpo (400 VALIDACION).
Rol ADMIN (403 SIN_PERMISO).
Monto mayor que 0 y con máximo 2 decimales (400 MONTO_INVALIDO).
El usuario existe (404 NO_ENCONTRADO).
El monto no excede el saldo (409 MONTO_EXCEDE_SALDO).

Así, un usuario inexistente responde 404 NO_ENCONTRADO. Un monto con más de 2 decimales que además excede el saldo responde 400 MONTO_INVALIDO.

5. RN-24 (paginación). Los valores no se ajustan. Si page es menor que 1 o size está fuera del rango de 1 a 50, se responde 400 VALIDACION (RN-29).

6. RN-26 (estadísticas).

(a) Si desde es posterior a hasta, no es un error. El rango no contiene días, así que se responde 200 como un rango sin devoluciones: devueltos 0, a_tiempo 0, tasa_puntualidad 0.0 y multas_total en cero.
(b) multas_total es la suma de las multas (RN-21) de los préstamos contados en devueltos, es decir, los devueltos dentro del rango. No incluye las penalidades por cancelación (RN-14).
(c) El redondeo «mitad hacia arriba» de RN-21 aplica únicamente a multa_diaria. Para tasa_puntualidad, la ERS no especifica el criterio de desempate. Los valores que caen exactamente a la mitad (por ejemplo, 6.25) no se evalúan y no son defecto. Diseñe sus casos con valores que no generen empate.

En sus casos de prueba y reportes, cite la regla junto con esta aclaración.
