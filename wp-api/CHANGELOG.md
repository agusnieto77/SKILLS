# Changelog

## 3.1 — 2026-10-22

- Distinción entre `content.raw` y `content.rendered`, preservación de bloques Gutenberg y límite explícito del CLI público para obtener fuente editable.
- Guía de `_embed` selectivo y `_fields` anidados con `--filtro`/`--campos` existentes, sin ampliar la superficie CLI; pruebas offline de transporte en Python y R.
- Diagnóstico de campos/meta invisibles: exposición REST, registro, soporte `custom-fields` y esquemas de arrays/objetos, sin modificar PHP ni configuración.
- Precisión de la acción `wp_rest` para nonces de autenticación por cookies y enlaces al Handbook oficial.

## 3.0 — 2026-10-22

Generalización de PDF a todos los formatos de la API REST de WordPress.

- Comandos `media` (reemplaza `pdfs`), `download --mime/--url/--id` y `export` en Python y R, con paridad de flags, salidas y códigos de salida.
- Registro MIME con los tipos de la biblioteca de medios de WordPress: familias de destino (`documentos`, `datos`, `imagenes`, `audio`, `video`, `comprimidos`, `otros`), alias de extensión y firma de bytes por formato.
- Validación en tres capas: Content-Type, firma mágica (JSON parseado, SVG, tar, OLE, ftyp, EBML, etc.) y SHA-256. El HTML disfrazado se descarta como `tipo_inesperado` o `invalido`.
- `export`: colecciones REST a JSON con envoltura o NDJSON, filtros, `_fields`, objeto por ID, colecciones objeto (`types`, `statuses`, `taxonomies`) y rutas de plugins.
- Freno de volumen de `export` por solicitudes estimadas, calculado antes de consultar.
- Reintentos acotados de lecturas transitorias respetando `Retry-After`.
- Huella de exportación canónica compartida entre Python y R.
- Estados de manifiesto `descargado`, `reutilizado`, `exportado`, `tipo_inesperado`; los históricos `descargado_pdf`/`reutilizado_pdf` siguen verificándose.
- Skill renombrada de `wordpress-api-pdf` a `wp-api`; referencia `descarga-pdf.md` reemplazada por `descarga.md`.

## 2.0

Descubrimiento REST robusto (subdirectorios, `rest_route`, anuncio `Link`), autenticación y operaciones documentadas para el agente, descarga verificada de PDF con manifiesto, freno de volumen y clientes Python/R.
