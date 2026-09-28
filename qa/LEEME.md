# Carpeta qa/ — Documentación de su trabajo de calidad

Complete estos archivos. Todos tienen formato fijo: **no cambie columnas ni campos**; solo llénelos.
El detalle de cada uno está en el enunciado (secciones 6 y 7).

**Regla de los números:** diseñe 30 casos → automatice **cada caso** en una prueba pytest con el mismo ID (30 pruebas: al menos 8 unitarias y 15 de API) → repita **15 de sus casos de API** como peticiones en su colección. Un caso se cuenta una sola vez aunque esté en pytest y en la colección.

| Archivo | Qué contiene | Mínimo | Paso |
|---|---|---|---|
| `estudiante.yaml` | Nombre, carné, huella, herramienta de API, usuario y URL del repositorio | Completo | 1 |
| `plan_pruebas.md` | Plan de pruebas y matriz de riesgos de las 31 reglas | Completo | 2 |
| `casos_prueba.csv` | Casos de prueba diseñados y dónde se automatizó cada uno | 30 casos sobre 20 reglas; 4 por técnica (EP, VL, TD, TE) | 3 |
| `trazabilidad.csv` | Qué casos, pruebas y defectos cubren cada regla | 31 filas llenas | 3 a 6 |
| `defectos.yaml` | Reportes de defectos | 8 reportes | 5 |
| `rca/DEF-XX.md` | Análisis de causa raíz (copie `rca/PLANTILLA_RCA.md`) | 3 análisis | 6 |
| `metricas.csv` | Métricas M01 a M05: línea base (main) y valor final (correcciones) | 5 métricas | 3 y 6 |
| `bitacora_ia.md` | Registro de uso de IA | Todo uso relevante | Todos |
| `guion_video.md` | Guion de los 8 segmentos del video | Completo | 5 |
| `Informe_Plantilla.docx` | Plantilla del informe final | — | 6 |
| `informe.pdf` | Su informe final (exporte la plantilla llena a PDF) | Máx. 20 páginas sin anexos | 6 |

Archivos CSV: si los edita en Excel, guárdelos como **"CSV UTF-8 (delimitado por comas)"** para conservar tildes y comas.
