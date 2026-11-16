# cendoj

Búsqueda en el Buscador de Jurisprudencia del CENDOJ
([poderjudicial.es/search](https://www.poderjudicial.es/search/indexAN.jsp))
**hasta el tope real del visor (200 documentos)** con metadatos
verificables (ROJ, ECLI, resumen, `documento` = `data-link`), y descarga
de los PDF con Ego Lite con captcha resuelto por la persona.

Adaptada de la prueba real del 2026-11-17 con la búsqueda `huelga`
(85.186 hits → 200/200 recuperados; 10+1 PDF validados).

## Qué hace

- Lanza la búsqueda del formulario `frmBusquedajurisprudencia` (`TEXT`,
  base `AN`) directo contra `POST search.action`, con TLS tipo Chrome
  (`curl_cffi`; `urllib` da 403).
- Pagina en óptimo: `recordsPerPage=50` y `start=1,51,101,151`
  (4 peticiones en vez de 20x10), orden fecha de resolución descendente.
- Extrae por bloque `div.searchresult.doc`: `reference`, `documento`
  (`data-link` → `.../AN/openDocument/{hash}/{optimize}`), título, ROJ,
  ECLI, municipio, ponente, resolución, recurso y resumen limpio.
- Guarda en `--salida`: `cendoj_resultados.csv` (`;`, `utf-8-sig`),
  `cendoj_resultados.json` y un snapshot HTML por página.
- Para el contenido: con Ego Lite abre cada `data-link`, lee el
  `object[data]` (`contenidos.action?action=accessToPDF...`) y lo
  descarga con pausas aleatorias de 2 a 5 s, validando `%PDF`.
- Ante el captcha `Control Descargas masivas` (HTML de ~3 KB en vez
  del PDF) frena y lo resuelve la persona (`handoff`); nunca por código.

## Instalación

Python 3.10+:

```bash
python -m pip install -r assets/requirements.txt
```

Para los PDF: Ego Lite instalado (skill `ego-browser`) y resolver el
captcha a mano cuando aparezca.

## Uso

```bash
# Búsqueda de ejemplo (tope 200 en 4 peticiones) en ./datos
python assets/cendoj_busqueda.py --texto huelga --salida datos

# Solo los primeros 40 (páginas de 10)
python assets/cendoj_busqueda.py --texto "huelga" --registros 10 --salida datos10
```

| Opción | Valores | Comportamiento |
|---|---|---|
| `--texto` | texto (requerido) | Texto libre del formulario (`frmBusquedajurisprudencia_TEXT`) |
| `--salida` | directorio (default `./datos`) | Estructura abajo |
| `--registros` | 10/20/30/50 (default 50) | Resultados por página; con 50 se llega al tope 200 en 4 peticiones |

Estructura de salida:

```
datos/
├── cendoj_resultados.csv   # una fila por documento (;, utf-8-sig)
├── cendoj_resultados.json  # {texto, recuperados, tope_visor, docs}
├── snapshot_pag_1.html     # snapshot de cada página consultada
├── snapshot_pag_2.html
├── snapshot_pag_3.html
└── snapshot_pag_4.html
```

PDF con Ego Lite (ver `assets/cendoj_pdf_ego.mjs`): pegar los pares
`[nombre, data-link]`, correr en el espacio, pausas 2-5 s, validar
`%PDF` en cada archivo y cerrar con `finish`.

## Cobertura y límites técnicos

- **Tope del visor: 200 documentos** aunque haya decenas de miles de
  hits. Más allá, particionar por facetas (`action=getQueryAllTagValues`
  por `ANYO`, `JURISDICCION`, `TIPOORGANOPUB`) hasta buckets < 200.
- Verificado con `huelga`: 200/200 bloques, 0 sin `data-link`; 10 PDF
  (79–393 KB) + 1 skilltest (211 KB), todos con cabecera `%PDF`.
- El captcha aparece tras ~2 descargas seguidas; lo resuelve la
  persona y se retoma en el mismo TaskSpace.
- Condiciones del sitio (información para el operador): el aviso legal
  del CENDOJ no permite la descarga masiva ni el uso comercial; uso
  previsto: muestras acotadas con fines educativos/de investigación.

## Detalles del sitio y re-diagnóstico

Endpoints, selectores y evidencia: [`references/fuente.md`](references/fuente.md).
Si el HTML no encaja (bloques, `data-link`, `object[data]`), abortar y
re-diagnosticar con esa guía antes de insistir.

## Tests

```bash
(cd cendoj && python -m pip install -r assets/requirements.txt && python -m unittest discover -s assets -p test_cendoj_busqueda.py -v)
```

7 pruebas offline (fixture HTML real de 10 bloques, sesión HTTP falsa):
parseo, primer documento, 0 sin enlace, resumen sin tags, dedup,
parámetros y paginación óptima (`start=1,51,101,151`). Sin red ni
credenciales.
