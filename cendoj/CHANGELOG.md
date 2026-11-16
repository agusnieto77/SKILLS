# Changelog

## 1.0.0 — 2026-11-17

Skill inicial, adaptada de la prueba real contra el sitio
(búsqueda `huelga`, 85.186 hits).

- `assets/cendoj_busqueda.py`: CLI con `--texto/--salida/--registros`
  que pagina en óptimo (`recordsPerPage=50`, `start=1,51,101,151`) y
  extrae `reference`, `documento_data_link`, título, ROJ, ECLI,
  municipio, ponente, resolución, recurso y resumen; CSV (`;`,
  `utf-8-sig`), JSON y snapshots por página.
- `assets/cendoj_pdf_ego.mjs`: template Ego Lite (`goto(data-link)` →
  `object[data]` → `page.fetch(saveAs)`) con pausas 2-5 s y `handOff`
  ante captcha; nunca lo resuelve por código.
- `assets/test_cendoj_busqueda.py`: 7 pruebas offline con fixture HTML
  real y sesión falsa (parseo, dedup, parámetros, paginación).
- `references/fuente.md`: endpoints, tope 200, facetas, captcha y
  evidencia (200/200; 10+1 PDF `%PDF`).
- Verificado punta a punta: 200/200 documentos y 1 PDF nuevo (211 KB,
  `%PDF`) con los archivos de la skill.
