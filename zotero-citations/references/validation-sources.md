# Fuentes de validación externa

`scripts/validate_ref.py` consulta estas fuentes y emite un veredicto (ver `references/scripts.md`). Esta referencia explica el orden, la independencia entre fuentes y los límites de cada una.

## Ruteo por identificador

| Identificador | Primera fuente | Segunda fuente independiente |
|---|---|---|
| DOI | La agencia de registro real, según `https://doi.org/ra/{DOI}`: Crossref → `api.crossref.org/works/{DOI}`; DataCite → `api.datacite.org/dois/{DOI}`; otras (mEDRA, JaLC, KISTI...) → negociación de contenido en `doi.org` | OpenAlex `api.openalex.org/works/doi:{DOI}` |
| ISBN | Open Library `openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json` | Catálogos de bibliotecas vía Citoid (Library of Congress/WorldCat); Google Books si hay key |
| PMID | PubMed E-utilities `esummary.fcgi?db=pubmed&id={PMID}&retmode=json` | Crossref, si PubMed trae DOI |
| Solo título/autor | Crossref `works?query.bibliographic=...&query.author=...` + OpenAlex `works?search=...` | Las pistas se confirman por identificador; si no hay, sitio del editor o repositorio |

- `doi.org/ra` también detecta **DOIs inexistentes** (`"status": "DOI does not exist"`): DOI mal copiado o inventado. La heurística "prefijo 10.5 = DataCite" es falsa; usá siempre `/ra`.
- Un ISBN con checksum inválido es un error de tipeo o inventado: no se consulta nada.
- Citoid para DOI se alimenta de Crossref: **no** cuenta como segunda fuente para DOIs Crossref.

## Fuentes

### Crossref
- Metadatos de DOIs Crossref (JSON en `message`: `title`, `author[].family/given`, `issued`, `published-print`, `published-online`, `container-title`, `volume`, `issue`, `page`, `publisher`, `type`).
- Año: preferí `published-print`; el online-first suele ser un año antes. Un año del manuscrito que coincide con cualquiera de los dos es válido.
- Polite pool: `mailto` (variable `CROSSREF_MAILTO`). Las búsquedas (listas) tienen límites más bajos que los lookups por DOI: secuenciá, no paralelices.

### DataCite
- Datasets, software, preprints de repositorios (Zenodo, Figshare, Dryad). `attributes.titles`, `creators[].familyName`, `publicationYear`, `publisher`, `types.resourceTypeGeneral`.

### OpenAlex
- Desde febrero de 2026 usa API keys (el `mailto` se ignora). Sin key: crédito diario de ~US$0,10; los lookups por DOI son gratis, cada búsqueda cuesta ~US$0,001. Con `OPENALEX_API_KEY` el crédito sube 10×.
- Cubre artículos sin DOI de revistas latinoamericanas que Crossref no tiene: útil para encontrar el registro, pero un artículo sin DOI encontrado solo en OpenAlex queda `single-source` hasta verificarlo en el sitio de la revista.

### Open Library
- Endpoint `api/books ... jscmd=data`: devuelve nombres de autores directamente (el endpoint `/isbn/{isbn}.json` solo trae claves y obliga a más requests).
- Ediciones locales a veces con título en Title Case o sin subtítulo: compará el título principal.

### Citoid (Wikimedia)
- `https://en.wikipedia.org/api/rest_v1/data/citation/zotero/{DOI|ISBN|PMID|URL}` devuelve **JSON en formato Zotero**: base del payload (`validate_ref.py payload`).
- Limpieza obligatoria: quitar `key`, `version`, `accessDate`, `libraryCatalog` y tags de catálogo; la fecha puede ser la online (no la impresa); el título puede venir en Title Case; `pages` con raya.

### PubMed
- Biomedicina, enfermería, psicología clínica. `pubdate`, `source`/`fulljournalname`, `authors[].name` ("Messeri L"), `articleids` con DOI.

### Google Books
- La cuota anónima es compartida y suele estar agotada (429). Sin `GOOGLE_BOOKS_API_KEY` queda en `unavailable`, no como "no encontrado".

### Negociación de contenido DOI
- `Accept: application/vnd.citationstyles.csl+json` en `https://doi.org/{DOI}` devuelve CSL-JSON para Crossref, DataCite y mEDRA.
- `Accept: text/x-bibliography; style=apa; locale=es-ES` devuelve la referencia APA formateada por la agencia: útil para comparar, nunca reemplaza el render de Zotero.

### Fuentes manuales (segunda fuente cuando las APIs no alcanzan)
- Sitio oficial de la revista o editorial; repositorios institucionales (RIDAA, CONICET Digital, SEDICI, Memoria Académica), SciELO, Redalyc, Latindex, Dialnet; arXiv, SSRN, RePEc, DBLP, PhilPapers; catálogos de bibliotecas nacionales (BNMM, BNE).
- Google Scholar solo como puntero hacia una fuente oficial: nunca se usa su metadato directamente.
- En el reporte, registrá la URL concreta que usaste como segunda fuente.

## Retractaciones y avisos (`validate_ref.py integrity`)

- **Crossref `updated-by`**: cada obra lista los avisos que la modifican, con `type`, `label`, `DOI` del aviso, fecha y `source`. Desde 2023 incluye los datos de **Retraction Watch** (`source: retraction-watch`), además de lo que declara la editorial (`source: publisher`). Tipos relevantes: `retraction`, `partial_retraction`, `withdrawal`, `removal`, `expression_of_concern`, `correction`, `erratum`, `corrigendum`, `addendum`, `clarification`, `new_version`, `new_edition`.
- **OpenAlex `is_retracted`**: booleano por obra. Sirve como segunda señal y cubre algunos casos que Crossref no marca.
- **Lote**: `api.crossref.org/works?filter=doi:A,doi:B&select=DOI,updated-by` y `api.openalex.org/works?filter=doi:A|B&select=doi,is_retracted` (hasta 100 por consulta; el script usa 50).
- Verificado con Wakefield et al. (1998), `10.1016/S0140-6736(97)11096-0`: Crossref devuelve la corrección de 2004 y la retractación de 2010; OpenAlex, `is_retracted: true`.
- Solo se pueden revisar obras con DOI. Libros sin DOI, fuentes de archivo y la mayoría de las revistas regionales quedan fuera: el reporte tiene que decirlo, no presentarlas como "limpias".
- Citar una obra retractada puede ser legítimo (p. ej. para analizar el caso). La skill avisa; la decisión es del autor.

## Reglas de validación

- **Coincidencia mínima**: título (similitud ≥ 0,9, el subtítulo puede faltar), primer autor (apellido, sin acentos; apellidos compuestos parciales valen) y año.
- **Dos fuentes independientes** para `validated`. Con una sola, la entrada queda `single-source` y necesita una segunda fuente mostrada al usuario antes de crear.
- **Nunca inventar un DOI** sugerido por un buscador: solo los que devuelve una agencia de registro, OpenAlex o el sitio oficial.
- **DOI vs URL**: si la fuente no tiene DOI, dejá la URL; no fabriques un DOI.
- **Preprint vs versión publicada**: si existe la versión publicada, se cita esa (año de publicación). Si el manuscrito cita el preprint a propósito, se mantiene con su año y el repositorio.
- **Trazabilidad**: para cada entrada nueva, anotá en el reporte las fuentes que la validaron (p. ej. "Crossref + OpenAlex") y las `unavailable`.
