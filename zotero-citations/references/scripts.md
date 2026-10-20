# Scripts — comandos, salidas y semántica

Python 3.10+ sin dependencias externas. Salida JSON por stdout; errores como `{"error": ...}` por stderr con código 2. Correlos desde la raíz de la skill.

| Script | Para qué |
|---|---|
| `cite_audit.py` | Leer el manuscrito, detectar la norma, cruzar citas y referencias, reglas de formato. |
| `zotero_client.py` | Biblioteca Zotero: buscar, cotejar, crear, corregir, papelera. |
| `validate_ref.py` | Validación externa (DOI, ISBN, PMID) e integridad (retractaciones). |
| `source_check.py` | Citas textuales, copia sin comillas y pasajes contra el texto completo en Zotero. |
| `cite_format.py` | Referencias, citas y notas: APA, Chicago, cualquier estilo del repositorio o plantilla a medida. |

Módulos internos: `zotlib.py` (HTTP, normalización), `citecore.py` (lectura y cruce comunes), `style_apa.py` y `style_chicago.py` (reglas por norma).

## Flujo completo

```bash
python scripts/cite_audit.py audit manuscrito.docx --style auto > audit.json   # norma, citas, referencias, findings
python scripts/zotero_client.py whoami                                # credenciales (key enmascarada)
python scripts/zotero_client.py match audit.json > match.json         # estado de cada referencia en Zotero
python scripts/validate_ref.py integrity --from audit.json match.json # retractaciones y avisos
python scripts/source_check.py check audit.json match.json > check.json   # citas textuales, copia, pasajes
python scripts/validate_ref.py doi 10.xxxx/yyy --title "..." --author Apellido --year 2020
python scripts/validate_ref.py payload 10.xxxx/yyy > draft.json       # borrador Zotero; editar → payload.json
python scripts/zotero_client.py check payload.json                    # 0 errores antes de seguir
python scripts/zotero_client.py create payload.json --audit-tags      # dry-run: mostrar al usuario
python scripts/zotero_client.py create payload.json --audit-tags --confirm
python scripts/zotero_client.py update ABCD2345 patch.json --version 812 [--confirm]
python scripts/cite_format.py render --keys ABCD2345,EFGH6789 --style chicago-notes --locators ABCD2345:61 > render.json
```

Si el `.docx` tiene campos vivos de Zotero, `audit` devuelve sus `itemKey` en `summary.zotero_field_item_keys`: pasalos directo a `render`.

## Variables de entorno

| Variable | Uso |
|---|---|
| `ZOTERO_API_KEY` | Obligatoria para escribir y para leer bibliotecas privadas por Web API. |
| `ZOTERO_LIBRARY_ID` | `userID` (biblioteca personal) o `groupID`. `whoami` muestra el `userID` de la key. |
| `ZOTERO_LIBRARY_TYPE` | `user` (default) o `group`. |
| `CROSSREF_MAILTO` | Email para el polite pool de Crossref (más cuota). |
| `OPENALEX_API_KEY` | Sin key OpenAlex da ~US$0,10/día de crédito: ~100 búsquedas; los lookups por DOI son gratis. |
| `GOOGLE_BOOKS_API_KEY` | La cuota anónima de Google Books suele estar agotada; sin key queda como `unavailable`. |
| `ZOTERO_CITATIONS_CACHE` | Carpeta de caché (schema de Zotero e índice de estilos: 7 días; snapshot de la biblioteca por versión). |

En Windows, si la consola se abrió antes de un `setx`, los scripts leen igual las variables del registro de usuario.

## `cite_audit.py`

| Comando | Qué hace |
|---|---|
| `extract MANUSCRITO [--style S]` | Norma detectada, citas (en el cuerpo, en notas al pie y finales) y entradas de la lista, campos vivos de Zotero. |
| `audit MANUSCRITO [--style S] [--lang es\|en] [--no-lint]` | `extract` + cruce cita↔referencia + reglas de la norma. `--no-lint` solo cruza (formatos a medida). |

`--style`: `auto` (default), `apa`, `chicago` (elige la variante; si no hay señales, notas), `chicago-notes`, `chicago-author-date`.

**Lectura**: `.docx` (cuerpo, notas al pie y finales **ancladas** a la oración que las llama, itálicas como `*...*`, campos `ZOTERO_ITEM`, estilos de cita de Word como bloque), `.pdf` con capa de texto (vía `pdftohtml` de Poppler: cuerpo y notas separados por tamaño de fuente, llamadas superíndice ancladas, cursivas, encabezados/pies repetidos descartados, guiones de fin de línea unidos, párrafos íntegramente en cursiva como cita en bloque), `.md` con notas Pandoc (`texto.[^1]` y `[^1]: nota`), `.txt` con sangría francesa. La lista se detecta por encabezado (`Referencias`, `Bibliografía`, `Fuentes`, `References`...); los subtítulos internos (`Fuentes primarias`, `Archivos`) quedan en `section`. En PDF, compará `summary.notes.notes` con `anchored`: si difieren, alguna llamada o nota no se separó bien.

**Notas**: Chicago (`Omar Acha, *Título*, …`) y formato hispano (`Acha, Omar: *Título*, …`, `op. cit.`, `ibídem` con autor, "Citado en:"); ver `chicago.md`.

**Detección** (`style_detection`): cuenta citas con coma `(Acha, 2015)` → APA, sin coma `(Acha 2015)` → Chicago autor-fecha, notas con título de obra o *ibid.* → Chicago notas, y la forma de cada entrada de la lista (vale doble). `confidence` < 0,7: confirmá con el usuario. `style_source`: `requested`, `detected` o `default`.

**Referencias**: `parsed`, `shape` (`apa`, `author-date`, `notes`, `unknown`: en qué sistema está escrita la entrada), `authors` (apellidos), `corporate`, `title`, `year`, `etal`, `doi`, `isbn`, `url`, `kind`. `references_from_notes: true` cuando no hay bibliografía y las referencias salen de las notas completas (`synthetic`).

**Citas**: `kind` (`parenthetical`, `narrative`, `note-full`, `note-short`, `note-ibid`, `note-author`), `authors`, `etal`, `years`, `title` (notas), `locator`, `note` (id de la nota), `context` (la oración del cuerpo), `ref_indexes`, `quotes` (citas textuales con `text`, `block`, `locator`).

- **Cita textual en línea**: entre `“…”`, `«…»` o `"…"`, de 4 o más palabras; se asigna a la cita o llamada de nota más cercana de la misma oración (primero la de después).
- **Cita en bloque**: párrafo de 40+ palabras sin comillas con marca explícita (`> `, estilo de cita de Word, o párrafo anterior terminado en `:`) y localizador al final o en su nota.

### Findings

Comunes y APA (detalle de Chicago en `chicago.md`):

| Regla | Severidad | Significado |
|---|---|---|
| `C-ORPHAN` | error | Cita sin entrada en la lista. |
| `C-UNCITED` | warning (info en Chicago notas) | Entrada sin cita. |
| `C-YEAR-MISMATCH` | error | El autor está en la lista con otro año. |
| `C-AMBIGUOUS` | error | Mismo autor y año sin sufijos a/b, o nota que no distingue entre obras del autor. |
| `C-ETAL-MISUSE` / `C-ETAL-MISSING` / `C-ETAL-REQUIRED` | error | "et al." con <3 autores / faltante con 3+ / autores listados en vez de "et al." (APA 7 y CMOS 18 coinciden). |
| `C-SECOND-AUTHOR` / `C-AUTHOR-COUNT` | error | Obra de 2 autores citada con 1 / cita con más autores que la referencia. |
| `C-SECONDARY` | info | "como se cita en": solo la fuente secundaria va a la lista. |
| `C-COMMA-MISSING` / `C-LOCATOR-FORMAT` | error / warning | APA: falta la coma autor–año / página sin "p.". |
| `R-UNPARSED` | error | La entrada no tiene la estructura de la norma (con pista si parece de otra). |
| `R-DOI-FORMAT`, `R-ORDER`, `R-SAME-AUTHOR-YEAR` | error | Comunes. |
| `R-DASH`, `R-FINAL-PERIOD`, `R-PUNCT` | warning | Comunes. |
| `R-RETRIEVED`, `R-ETAL-IN-LIST`, `R-INITIALS`, `R-ND-LANG`, `R-PP-ARTICLE` | error | APA. |
| `R-PLACE`, `R-SERIAL-COMMA`, `R-EDITION-LANG`, `R-TITLE-CASE`, `R-ITALICS`, `R-CONNECTOR-MIX`, `R-CONNECTOR-LANG` | warning | APA. `R-TITLE-CASE` es heurística: respetá nombres propios. |
| `D-STYLE-MISMATCH` | warning | Se pidió una norma y el manuscrito está en otra: se audita contra lo pedido. |
| `D-LIVE-ZOTERO-FIELDS` | info | `.docx` con campos vivos de Zotero. |
| `D-MIXED-STYLE` / `D-NO-REFERENCES` | error | >30 % de entradas fuera de la norma / sin lista (info en Chicago notas). |
| `D-REFERENCES-FROM-NOTES` | info | Sin bibliografía: referencias armadas desde notas completas. |

## `zotero_client.py`

Opción global `--source auto|local|web` (default `auto`: API local de Zotero si responde, si no Web API). Las escrituras siempre van a la Web API.

| Comando | Salida / comportamiento |
|---|---|
| `whoami` | Key enmascarada, `userID`, permisos, API local activa. Avisa si `ZOTERO_LIBRARY_ID` no coincide con la key. |
| `search --doi D` / `--isbn I` | Coincidencias **exactas** del identificador (incluye papelera, `inTrash`). |
| `search --title T [--author A] [--year Y]` | Mejor candidato con `score` y `diffs`. |
| `match audit.json` | Por referencia: `status`, `best` (`key`, `version`, `score`, `diffs`), `alternatives`, `duplicates_in_library`. |
| `get KEY...` | JSON editable + `version` (para `update`). |
| `template TIPO` | JSON vacío oficial para ese `itemType`. |
| `check payload.json` | `errors` (bloquean) y `warnings` por ítem contra el schema vivo de Zotero, con la corrección sugerida. |
| `create payload.json [--confirm] [--audit-tags] [--collection KEY] [--allow-duplicate]` | Dry-run: payload, `check`, `duplicates`. Con `--confirm`: lotes de 50, `Zotero-Write-Token` por lote, `created` (índice → `itemKey`), `failed`, `log`. Se niega si hay errores de schema o duplicados. `--audit-tags` agrega `citation-audited` y `validated-AAAA-MM-DD`. |
| `update KEY patch.json --version N [--confirm]` | Dry-run con `diff`. Con `--confirm`: `PATCH` con `If-Unmodified-Since-Version`. |
| `trash KEY --version N [--confirm]` | `PATCH {"deleted": 1}`: va a la papelera, se puede restaurar. |

### Estados de `match`

| Estado | Criterio |
|---|---|
| `exact-doi` / `exact-isbn` | Identificador idéntico (ISBN-10 y -13 equivalen). |
| `strong` | Score ≥ 0,85 (60 % título, 25 % primer autor, 15 % año) sin diferencias. |
| `strong-diff` | Score ≥ 0,85 pero con `diffs` (p. ej. otra edición/año). |
| `weak` | 0,65–0,85: revisar a mano. |
| `trashed` | El mejor candidato está en la papelera. |
| `none` | Sin candidato razonable. |

## `cite_format.py`

| Comando | Qué hace |
|---|---|
| `render --keys K1,K2 [--style S] [--lang es\|en] [--format markdown\|text\|html] [--locators K1:61,K2:12-14] [--ref-connector amp\|y]` | Formatea con el CSL de Zotero. |
| `styles --search TEXTO [--format note\|author-date\|numeric]` | Busca en el repositorio de Zotero (10 800+ estilos: revistas, editoriales, universidades). |
| `match-style --key K --example "..." [--styles a,b] [--search TEXTO]` | Qué estilo reproduce el ejemplo del usuario. |
| `template check --template T.json --key K --expect "..." [--part reference\|citation\|note_full\|note_short]` | Compara la plantilla con el ejemplo. |
| `template render --template T.json --keys K1,K2 [--locators ...]` | Aplica la plantilla a todos los ítems. |

`--style`: `apa`, `chicago-author-date`, `chicago-notes` (alias `chicago`), o cualquier id del repositorio (`iso690-author-date-es`, el de una revista).

### Salida de `render`

- Siempre: `reference`, `quality` (problemas de datos a corregir en Zotero), `bibliography` ordenada (en estilos numéricos, en el orden dado), `warnings`, `missing`.
- Autor-fecha: `citation`, `narrative`; con localizador, `citation_with_locator` y `narrative_with_locator`.
- Notas: `note_full`, `note_short` (Chicago); con localizador, `note_full_with_locator` (en artículos reemplaza el rango del artículo por la página citada) y `note_short_with_locator`.
- Localizadores solo en perfiles oficiales: APA `p. 61` / `pp. 12–14`; Chicago `61` / `12–14`. En estilos del repositorio, agregalos siguiendo los ejemplos del estilo.

Correcciones sobre Zotero en perfiles oficiales: rayas en rangos fuera de URL/DOI; sufijos `2015a`/`2015b` (renderizando juntos los ítems de mismo autor y año); APA en español, `y` en lugar de `&` en citas (y en la lista con `--ref-connector y`); `n.º` y `2.ª` (Zotero los entrega como superíndice).

`quality` incluye: Title Case o MAYÚSCULAS en títulos, título web con el nombre del sitio, sin fecha, sin autores, artículo sin DOI/URL, tipo sin su contenedor (`bookSection` sin `bookTitle`…), y en estilos de notas, falta de *Short Title* (la nota abreviada repetiría el título entero). `warnings` avisa si un apellido aparece con nombres distintos (agregar iniciales en las citas si son personas distintas, APA 8.20 / CMOS 13.109).

### Salida de `match-style` y `template`

- `match-style`: `verdict` (`exact` ≥ 0,995, `close` ≥ 0,9, `none`), `best` (`style`, `part`, `similarity`, `produced`, `differences` palabra a palabra), `ties` (estilos que empatan: pedir un ejemplo de cita en el texto o nota), `ranking`, `next`.
- `template check`: `produced`, `exact`, `exact_ignoring_italics`, `differences`, `empty_fields`, `pattern_for`.
- `template render`: `entries`, `bibliography`, `fallback_types` (tipos que usaron el patrón `*`), `incomplete` (entradas con campos obligatorios vacíos). Lenguaje de plantillas: `custom-formats.md`.

## `validate_ref.py`

| Comando | Fuentes |
|---|---|
| `doi DOI [--title --author --year]` | Agencia por `doi.org/ra` → Crossref, DataCite o negociación de contenido (mEDRA, etc.) + OpenAlex. DOI inexistente → `not-found`. |
| `isbn ISBN [...]` | Checksum + Open Library + catálogo de bibliotecas vía Citoid (LoC/WorldCat) + Google Books. |
| `pmid PMID [...]` | PubMed + Crossref (si PubMed trae DOI). |
| `search --title T [--author A] [--year Y]` | Candidatos de Crossref y OpenAlex con `score`. Solo pistas. |
| `payload ID` | JSON Zotero vía Citoid (sin `key`/`version`/tags de catálogo) + `check`. Es un borrador: reconciliá fechas y sentence case con los registros validados. |
| `integrity [--dois D1,D2] [--from audit.json match.json]` | Retractaciones y avisos (ver abajo). |

### Veredictos

| Veredicto | Significado | Acción |
|---|---|---|
| `validated` | 2+ fuentes independientes coinciden (título ≥ 0,9, primer autor, año; se tolera año online vs impreso) y el manuscrito coincide. | Se puede crear. |
| `single-source` | Respondió una sola fuente. | Buscar una segunda (sitio del editor, repositorio) y mostrarla. |
| `mismatch` | Las fuentes coinciden entre sí, el manuscrito difiere. | Mostrar `diffs_vs_manuscript`; corregir el manuscrito o preguntar. |
| `conflict` | Las fuentes no coinciden entre sí. | No crear; revisión manual. |
| `not-found` | DOI inexistente, ISBN con checksum inválido o sin resultados. | Marcar `[verificar]`. |

`unavailable` lista las fuentes que fallaron (red, cuota) para que el reporte no las cuente como validación.

### Integridad

Revisa en lote (50 DOIs por consulta) los avisos de Crossref (`updated-by`, que incluye los datos de Retraction Watch) y el `is_retracted` de OpenAlex. Toma los DOIs de la lista del manuscrito y de los ítems de Zotero con los que se emparejaron. `doi` también agrega `integrity` a cada validación.

| Estado | Avisos de Crossref | Acción |
|---|---|---|
| `retracted` | `retraction`, `partial_retraction`, `withdrawal`, `removal`, o `is_retracted` de OpenAlex | Primera sección del reporte; el autor decide si la cita (p. ej. para discutir el caso) o la quita. |
| `expression-of-concern` | `expression_of_concern` | Avisar; citar con cautela. |
| `corrected` | `correction`, `erratum`, `corrigendum`, `addendum`, `clarification` | Informar; revisar si la corrección afecta lo citado. |
| `new-version` | `new_version`, `new_edition` | Sugerir citar la versión vigente. |
| `clean` / `unknown` | sin avisos / ninguna fuente respondió | `unknown` no es "limpio". Las obras sin DOI no se pueden revisar. |

## `source_check.py`

Coteja cada cita con el texto completo que Zotero indexó del PDF, EPUB o HTML adjunto (`/items/{key}/fulltext`). Solo considera las referencias con match `exact-doi`, `exact-isbn`, `strong` o `strong-diff`. Funciona igual con citas autor-fecha y con notas (el contexto es la oración que llama la nota).

| Comando | Qué hace |
|---|---|
| `check audit.json match.json [-k 3] [--no-passages]` | Todas las citas resueltas: citas textuales, copia sin comillas y pasajes candidatos. |
| `quote KEY --text "..." [--locator "p. 61"]` | Verifica una cita textual. |
| `passages KEY --query "..." [-k 5]` | Pasajes más relevantes (BM25) para una afirmación; útil para reformular la consulta en el idioma de la fuente. |

Estado por cita: `checked`, `no-fulltext` (sin adjunto o sin indexar: en Zotero, *Reindexar ítem*), `no-zotero-item` (match débil o ausente) o `unresolved-citation` (cita huérfana o ambigua).

### Citas textuales

La comparación ignora mayúsculas, ligaduras (`ﬁ`), guiones de corte de línea y tipo de comillas. `[...]`, `(...)`, `…` y las inserciones entre corchetes cortan la cita en tramos que tienen que aparecer en orden.

| Estado | Significado |
|---|---|
| `exact` / `exact-with-edits` | Literal; con omisiones o inserciones editoriales marcadas. |
| `near` | ≥ 85 % de las palabras en tramos de 3 o más; `differences` muestra cada cambio (p. ej. ortografía modernizada). |
| `weak` | 60–85 %: la cita fue alterada; mostrar `differences`. |
| `partial` | Un tramo largo coincide y el resto no (`diverges_after`): cita empalmada, completada de memoria o en parte inventada. |
| `not-found` | No está en el texto indexado. Antes de concluir, verificar que el índice esté completo (`indexedPages` < `totalPages` → `partial_index`) y que no sea una traducción del autor. |

Página (`page_status`), con localizadores APA (`p. 61`) o Chicago (`61`, `112–14`): `consistent` / `inconsistent` cuando se conoce la página impresa (anotaciones de Zotero con número de página, o el rango `pages` del artículo frente a las páginas del PDF); `matches-pdf-page` si solo coincide la página del PDF; `unverifiable` si el texto indexado no conserva saltos de página.

### Copia sin comillas (`verbatim`)

Tramos de 6 o más palabras idénticas a la fuente en la oración citante, sin contar lo que ya está entre comillas. Se descartan los tramos de palabras funcionales (`de la que en el…`).

### Respaldo de la afirmación (juicio del agente)

`passages` trae los 3 fragmentos más relevantes con su página. El agente decide y siempre cita el pasaje:

| Veredicto | Cuándo |
|---|---|
| `fiel` | El pasaje dice lo que el manuscrito le atribuye. |
| `exagerada` | El manuscrito generaliza o refuerza (p. ej. "todos" donde la fuente dice "68 %"). |
| `parcial` | La fuente respalda solo una parte. |
| `sin respaldo` | Ningún pasaje lo dice, revisando también `passages` con otra consulta. |
| `no verificable` | Sin texto completo, índice parcial o fuente en otro idioma sin revisar. |

Si `cross_language` es `true`, repetí `passages` con la afirmación traducida al idioma de la fuente. Si la oración solo enmarca una cita textual (`claim_note`), alcanza con la verificación de la cita.

## Tests

`python -m unittest discover -s tests` (sin red: servidor Zotero simulado, schema fijo y manuscritos de prueba APA, Chicago notas, Chicago autor-fecha y notas sin bibliografía en `tests/fixtures`).
