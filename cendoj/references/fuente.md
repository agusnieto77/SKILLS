# CENDOJ · mapa del sitio y evidencia verificada

Fuente: Buscador de Jurisprudencia del Consejo General del Poder Judicial
(<https://www.poderjudicial.es/search/indexAN.jsp>, base AN: TS, AN, TSJ,
AP, tribunales militares y unipersonales). Lo documentado aquí fue
observado y verificado contra el sitio el 2026-11-17 (búsqueda `huelga`:
200/200 documentos; 10+1 PDF descargados y validados).

## Endpoints conocidos

| Elemento | URL / patrón | Verificado |
|---|---|---|
| Formulario de búsqueda | `GET indexAN.jsp` (form `frmBusquedajurisprudencia`, campo `TEXT`) | Sí |
| Búsqueda (AJAX) | `POST search.action` con `action=query`, `TEXT`, `databasematch=AN`, `sort`, `recordsPerPage`, `start`, `page`, `maxresults` + cabeceras `Referer`, `Origin`, `X-Requested-With` | Sí |
| Facetas para particionar | `POST search.action` con `action=getQueryAllTagValues`, `field=ANYO\|JURISDICCION\|SUBTIPORESOLUCION\|TIPOORGANOPUB` | Sí |
| Documento (landing) | `https://www.poderjudicial.es/search/AN/openDocument/{hash}/{optimize}` (atributo `data-link` de cada `div.searchresult.doc`) | Sí (200/200 con enlace) |
| PDF real | `object[data]` = `/search/contenidos.action?action=accessToPDF&publicinterface=true&tab=AN&reference={hash}&encode=true&optimize={yyyymmdd}&databasematch=AN` | Sí (11 PDF `%PDF`) |
| Captcha masivas | `Control Descargas masivas` (`input#captcha`, `img stickyImg`, `input#reference`, `#optimize`) | Sí (tras ~2 PDF seguidos) |

`urllib`/`requests` directos devuelven **403**; se requiere TLS tipo
navegador (`curl_cffi` con `impersonate="chrome131"`) más cookies de
sesión de `indexAN.jsp`.

## Estructura del resultado

Cada hit es `div.searchresult.doc` con `data-ref`, `data-db`,
`data-fechares`. Dentro: botón nueva-ventana con `data-link` (el
documento), título en `a#ref-{reference}` (`... - ROJ: ...`), bloque
`.metadatos` con `li` (`ECLI:...`, `Nº de Resolución:`, `Municipio:`,
`Ponente:`, `Nº Recurso:`) y `.summary` con el resumen (término
resaltado en `<font color=red>`).

## Tope de 200 documentos

El visor informa `85186 resultados` pero `máximo documentos a
recuperar 200` (paginación `de 20` con `Ver 10`). `recordsPerPage`
acepta 10/20/30/50: con 50 bastan 4 peticiones (`start=1,51,101,151`)
en vez de 20x10. Conteos `huelga` para planificar particiones:
`ESPECIAL=68` (recuperable 100%), `SOCIAL=20864`, `CIVIL=32122`,
`CONTENCIOSO=20866`; por año 2026=2365, 2021=7054. Todo bucket >200
exige subdividir (jurisdicción+año+órgano) hasta <200.

## PDF y captcha

El PDF se sirve `inline` (`content-disposition: inline;
filename="..."`). Tras ~2 descargas seguidas el mismo endpoint
devuelve HTML de ~3 KB con el captcha en vez del PDF. Política:
`handOff` a la persona, retomar en el mismo TaskSpace con pausas de
2 a 5 s; nunca resolverlo por código ni reintentar en loop.

## Parámetros operativos del script

| Parámetro | Valor |
|---|---|
| Pausa entre peticiones | fija 0,5 s en búsqueda; 2-5 s aleatoria en PDF |
| Timeout | 30 s (60 s en Ego Lite) |
| TLS | `curl_cffi` impersonate Chrome; TLS del sistema verificado |
| HTTP 403 | Solo sin impersonación; con ella no se observó |
| User-Agent | El de la impersonación Chrome (sesión real de navegación) |

## Historial de verificación

- 2026-11-17 (`huelga`): `search.action` 4x50 → 200/200 bloques, 0 sin
  `data-link` (`pj_huelga_200.csv/json`); primer doc `SAP VI 1532/2026`,
  `ECLI:ES:APVI:2026:1532`.
- 2026-11-17 (Ego Lite, espacio 30): 2 PDF directos + stop por captcha;
  tras resolución humana, 8/8 restantes con pausas 2-5 s (79 KB–393 KB,
  todos `%PDF`). Skilltest posterior: 1 doc nuevo (`ATSJ CAT
  1422/2026`, 211 KB, `%PDF`) en espacio nuevo, cerrado con `finish`.
