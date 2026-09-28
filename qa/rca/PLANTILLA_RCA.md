# Análisis de causa raíz — DEF-XX

> Copie este archivo como `qa/rca/DEF-XX.md` (un archivo por defecto analizado; mínimo 3).
> El análisis debe llegar al **nivel de código**: archivo, función y línea. No se aceptan causas como "falta de tiempo".

## 1. Defecto

| Campo | Valor |
|---|---|
| ID y título | |
| Regla(s) incumplida(s) | |
| Prueba que lo demuestra | |
| Evidencia en bitácora (n) | |

## 2. Diagrama de Ishikawa (en tabla)

> Para cada categoría anote las causas posibles que consideró y si la confirmó o la descartó, con su evidencia.

| Categoría | Causa posible | ¿Confirmada o descartada? | Evidencia |
|---|---|---|---|
| Requisitos / especificación | | | |
| Diseño | | | |
| Código | | | |
| Datos | | | |
| Pruebas | | | |
| Entorno y herramientas | | | |

## 3. Cinco porqués

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | ¿Por qué ocurre la falla? | |
| 2 | ¿Por qué ...? | |
| 3 | ¿Por qué ...? | |
| 4 | ¿Por qué ...? | |
| 5 | ¿Por qué ...? | |

## 4. Causa raíz

| Campo | Valor |
|---|---|
| Archivo | |
| Función | |
| Línea(s) | |
| Explicación técnica | |

## 5. Corrección y verificación

| Campo | Valor |
|---|---|
| Cambio aplicado (rama `correcciones`) | |
| Commit | |
| Pruebas que ahora pasan | |
| ¿Se ejecutó toda la suite sin regresiones? | |

## 6. Prevención

> ¿Qué prueba, práctica o control evitaría que un defecto de este tipo vuelva a ocurrir?
