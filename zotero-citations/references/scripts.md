# Scripts — comandos, salidas y semántica

Python 3.10+ sin dependencias externas. Salida JSON por stdout; errores como `{"error": ...}` por stderr con código 2. Correlos desde la raíz de la skill.

| Script | Para qué |
|---|---|
| `cite_audit.py` | Leer el manuscrito, detectar la norma, cruzar citas y referencias, reglas de formato. |
| `zotero_client.py` | Biblioteca Zotero: buscar, cotejar, crear, corregir, papelera. |
| `validate_ref.py` | Validación externa (DOI, ISBN, PMID) e integridad (retractaciones). |
| `source_check.py` | Citas textuales, copia sin comillas y pasajes contra el texto completo en Zotero. |
| `cite_format.py` | Referencias, citas y notas: APA, Chicago, cualquier estilo del repositorio o plantilla a medida. |
| `docx_revise.py` | Entregar las correcciones del `.docx` como control de cambios de Word (revisiones y comentarios). |

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
python scripts/docx_revise.py apply manuscrito.docx edits.json --out manuscrito_revisado.docx --author "Nombre"
python scripts/docx_revise.py summary manuscrito_revisado.docx           # conteo de revisiones para el reporte
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
| `ZOTERO_CITATIONS_DSPACE` | Repositorios DSpace extra para `work`: `nombre=d7:https://host,otro=os:https://host` (`d7` = DSpace 7 REST, `os` = OpenSearch). |

En Windows, si la consola se abrió antes de un `setx`, los scripts leen igual las variables del registro de usuario.

## `cite_audit.py`

| Comando | Qué hace |
|---|---|
| `extract MANUSCRITO [--style S] [--bib ARCHIVO ...] [--previous JSON]` | Norma detectada, citas (cuerpo, notas o claves), entradas de la lista/BibTeX, campos vivos Zotero y evidencia de entrada. |
| `audit MANUSCRITO [--style S] [--lang es\|en] [--no-lint] [--bib ARCHIVO ...] [--previous JSON]` | `extract` + cruce cita↔referencia + reglas de la norma. `--no-lint` solo cruza (formatos a medida); no oculta errores de claves ni parseo. |

`--style`: `auto` (default), `apa`, `chicago` (elige la variante; si no hay señales, notas), `chicago-notes`, `chicago-author-date`.

**Lectura**: `.docx` (cuerpo, notas al pie y finales **ancladas** a la oración que las llama, itálicas como `*...*`, campos `ZOTERO_ITEM`, estilos de cita de Word como bloque), `.pdf` con capa de texto (vía `pdftohtml` de Poppler: cuerpo y notas separados por tamaño de fuente, llamadas superíndice ancladas, cursivas, encabezados/pies repetidos descartados, guiones de fin de línea unidos, párrafos íntegramente en cursiva como cita en bloque), `.md` con notas Pandoc (`texto.[^1]` y `[^1]: nota`), `.txt` con sangría francesa. La lista se detecta por encabezado (`Referencias`, `Bibliografía`, `Fuentes`, `References`...); los subtítulos internos (`Fuentes primarias`, `Archivos`) quedan en `section`. En PDF, compará `summary.notes.notes` con `anchored`: si difieren, alguna llamada o nota no se separó bien.

**Notas**: Chicago (`Omar Acha, *Título*, …`) y formato hispano (`Acha, Omar: *Título*, …`, `op. cit.`, `ibídem` con autor, "Citado en:"); ver `chicago.md`.

**Detección** (`style_detection`): cuenta citas con coma `(Acha, 2015)` → APA, sin coma `(Acha 2015)` → Chicago autor-fecha, notas con título de obra o *ibid.* → Chicago notas, y la forma de cada entrada de la lista (vale doble). `confidence` < 0,7: confirmá con el usuario. `style_source`: `requested`, `detected` o `default`.

**Referencias**: `parsed`, `shape` (`apa`, `author-date`, `notes`, `unknown`: en qué sistema está escrita la entrada), `authors` (apellidos), `corporate`, `title`, `year`, `etal`, `doi`, `isbn`, `url`, `kind`, `paragraph` (párrafo del documento: destino de `docx_revise.py`). `references_from_notes: true` cuando no hay bibliografía y las referencias salen de las notas completas (`synthetic`, sin `paragraph`).

**Citas**: `kind` (`parenthetical`, `narrative`, `note-full`, `note-short`, `note-ibid`, `note-author`), `authors`, `etal`, `years`, `title` (notas), `locator`, `paragraph` (párrafo del cuerpo con la cita o con la llamada de su nota), `note` (id de la nota), `context` (la oración del cuerpo), `ref_indexes`, `quotes` (citas textuales con `text`, `block`, `locator`).

- **Cita textual en línea**: entre `“…”`, `«…»` o `"…"`, de 4 o más palabras; se asigna a la cita o llamada de nota más cercana de la misma oración (primero la de después).
- **Cita en bloque**: párrafo de 40+ palabras sin comillas con marca explícita (`> `, estilo de cita de Word, o párrafo anterior terminado en `:`) y localizador al final o en su nota.


### BibTeX/BibLaTeX y citas por clave

Usar `--bib referencias.bib` para cada bibliografía (opción repetible); una entrada `.bib` como manuscrito permite inventariar la biblioteca. Los archivos originales no se modifican. No se ejecuta LaTeX ni se abren bibliografías o archivos mencionados en metadatos: las rutas deben ser argumentos explícitos.

- `.tex`: `\cite`, `\parencite`, `\textcite`, `\autocite`, `\citep`, `\citet`, con varias claves y notas opcionales `[prenota][posnota]`.
- `.md`/`.markdown`/`.qmd`: citas Pandoc `[@clave]`, grupos como `[@uno; @dos]` y citas narrativas `@clave`. El modo de claves se activa con una cita entre corchetes o `--bib`; un `@handle` aislado no descarta las referencias autor-fecha ni sus reglas de estilo. Los bloques de código, comentarios y direcciones de correo no son citas.
- El parser reconoce llaves anidadas, comillas y escapes; conserva `citekey`, texto original y `location` de la entrada y de cada uso. Las claves se resuelven exactamente, con distinción de mayúsculas; no se inventan citekeys Better BibTeX ni itemKeys.
- Una clave indefinida o duplicada es un error; una entrada sin uso es una advertencia. Los problemas de parseo llevan ubicación y advertencia; revisar `bibliography_complete` (también en `summary`) y `bibliography_warnings` antes de afirmar cobertura completa. Las construcciones no resueltas deben verificarse, no omitirse silenciosamente.
- Los índices `ref_indexes` siguen vinculando cada uso a sus referencias para `match` y `source_check`; `--no-lint` no convierte la entrada BibTeX en una bibliografía formateada.
- `@string` y concatenación `#` se resuelven dentro de cada archivo; `crossref`/`xdata` se vinculan entre las bibliografías explícitas. Las macros desconocidas/cíclicas, las herencias ausentes/cíclicas y las entradas malformadas producen advertencias de cobertura incompleta, conservando el texto para revisión.

### Evidencia y resultados anteriores

`evidence.binding` registra el SHA-256 de los **bytes originales** del manuscrito y de cada `.bib`, además del hash canónico de la auditoría; `checked_at` usa UTC. Cada cita conserva `occurrence.id`, su ubicación exacta y un hash de su contexto/cita/localizador. Los campos Zotero todavía desconocidos en la ingesta son `null`, nunca estimados.

El binding se calcula una sola vez sobre la salida final, sin el propio sobre `evidence` ni marcas de tiempo. `extract()` y la CLI `extract` excluyen `body_text` y comparten el mismo contenido; `audit()` incorpora también los hallazgos y el resumen antes de calcularlo.

`--previous auditoria_anterior.json` compara los bindings: cualquier cambio de manuscrito, bibliografía o contenido de auditoría marca `evidence.status: stale` y enumera `changed_inputs`. No reutilizar una conclusión por coincidir solamente autor, año, citekey o itemKey.

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
| `C-UNDEFINED-KEY` / `B-DUPLICATE-KEY` | error | Clave usada sin definición / clave bibliográfica repetida y ambigua. |
| `C-UNUSED-KEY` | warning | Entrada `.bib` sin uso en el manuscrito (no se aplica al inventario `.bib` directo). |
| `B-PARSE` / `B-UNRESOLVED-MACRO` / `B-INHERITANCE` | warning | Sintaxis incompleta, macro no resuelta o herencia bibliográfica inválida; `bibliography_complete: false`. |

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
| `doi DOI [--title --author --authors --year] [--etal] [--pmid PMID]` | Agencia por `doi.org/ra` → Crossref, DataCite o negociación CSL + OpenAlex; PubMed si se conoce PMID. DOI inexistente → `not-found`. |
| `isbn ISBN [...]` | Checksum + Open Library + catálogo de bibliotecas vía Citoid (LoC/WorldCat) + Google Books. |
| `pmid PMID [...]` | PubMed (`esummary` + autoría ordenada mediante `efetch`) + Crossref (si PubMed trae DOI). |
| `search --title T [--author A] [--year Y]` | Candidatos de Crossref y OpenAlex con `score`. Solo pistas. |
| `work --title T [--author A] [--year Y] [--url URL] [--sources S1,S2]` | Obras sin DOI/ISBN: Open Library, Library of Congress, BNE, LA Referencia, repositorios DSpace (CONICET, UBA, UNNE, UNC, UNR, UNQ), Crossref, OpenAlex y la ficha de `--url` (Citoid), en paralelo. Mejor candidato por grupo independiente (repositorios + LA Referencia = un grupo) → mismos veredictos. Salida extra: `searched`, `groups`, `leads`. Detalle: `validation-sources.md`. |
| `payload ID` | JSON Zotero vía Citoid (sin `key`/`version`/tags de catálogo) + `check`. Es un borrador: reconciliá fechas y sentence case con los registros validados. |
| `integrity [--dois D1,D2] [--from audit.json match.json]` | Retractaciones y avisos (ver abajo). |

### Veredictos

| Veredicto | Significado | Acción |
|---|---|---|
| `validated` | 2+ fuentes independientes coinciden (título ≥ 0,9, autoría ordenada disponible entre fuentes bibliográficas, primer autor para catálogos, año; se tolera año online vs impreso) y el manuscrito coincide dentro del alcance declarado. | Se puede crear; revisar `authorship.validated` y `authorship.manuscript_scope` antes de afirmar autoría completa. |
| `single-source` | Respondió una sola fuente/grupo independiente, o no hay dos listas completas de autores para validar esa dimensión. | Buscar una segunda fuente completa (`work`, catálogo manual, ficha vía `work --url`) y mostrarla. |
| `mismatch` | Las fuentes coinciden entre sí, el manuscrito difiere. | Mostrar `diffs_vs_manuscript`; corregir el manuscrito o preguntar. |
| `conflict` | Las fuentes no coinciden entre sí. | No crear; revisión manual. |
| `not-found` | DOI o PMID inexistente, ISBN con checksum inválido o sin resultados. | Marcar `[verificar]`. |

`unavailable` lista las fuentes que fallaron (red, cuota o respuesta inutilizable) para que el reporte no las cuente como validación. La ausencia de un PMID solo se confirma si tanto `esummary` como `efetch` devuelven respuestas válidas y ninguna contiene el PMID. Un `esummary` fallido seguido de un `efetch` vacío conserva el fallo en `unavailable`; no confirma que el identificador sea inexistente.

### Autoría completa

`--authors` acepta un JSON ordenado con apellidos o autores estructurados (`{"family":"de la Fuente","given":"Ana"}` / `{"literal":"Consorcio Salud"}`). También se puede repetir `--author Apellido`; un único `--author` conserva la consulta histórica del primer autor. `--etal` declara una lista truncada: solo permite omitir el sufijo de una lista compatible, nunca cambiar autores ni posiciones.

El cotejo compara apellidos, orden, número y tipo persona/consorcio. Los conflictos de coautores son `error`, aunque el primero y la cantidad coincidan; una truncación declarada compatible no es un error. Las listas parciales o de completitud desconocida llevan `authorship_warnings`/advertencias: no equivalen a autoría completa validada. `diff_fields` en `match` aplica el mismo criterio y conserva las diferencias por campo para revisión.

Entre catálogos, repositorios o fichas Citoid, el cotejo conserva la semántica de primer autor: las listas pueden incluir editores o colaboradores y no se comparan como autorías ordenadas equivalentes. `agreement[].authorship.scope` es `first-author-only` en ese caso y `ordered` entre Crossref, DataCite, OpenAlex, PubMed y negociación DOI. Las diferencias de estas últimas usan `source_a`/`source_b` y sus campos `_kind`, en el orden de `agreement[].sources`, nunca `manuscript`. Un acuerdo limitado al primer autor no establece `authorship.validated: true`; el cotejo de una lista explícita del manuscrito contra la fuente elegida sigue siendo completo.

`authorship` informa `validated`, `complete_sources`, `incomplete_sources` y `manuscript_scope` (`complete`, `truncated`, `first-author-only`, `not-provided`). Los registros conservan `authors`, `author_details`, `authors_complete` y `authorship_warnings`. PubMed `esummary` + `efetch` cuenta como una fuente; el PMID de `OpenAlex.ids.pmid` también permite recuperar autoría cuando está disponible.


### Integridad

Revisa en lote (50 DOIs por consulta) los avisos de Crossref (`updated-by`, que incluye los datos de Retraction Watch) y el `is_retracted` de OpenAlex. Toma los DOIs de la lista del manuscrito y de los ítems de Zotero con los que se emparejaron. `doi` también agrega `integrity` a cada validación.

| Estado | Avisos de Crossref | Acción |
|---|---|---|
| `retracted` | `retraction`, `partial_retraction`, `withdrawal`, `removal`, o `is_retracted` de OpenAlex | Primera sección del reporte; el autor decide si la cita (p. ej. para discutir el caso) o la quita. |
| `expression-of-concern` | `expression_of_concern` | Avisar; citar con cautela. |
| `corrected` | `correction`, `erratum`, `corrigendum`, `addendum`, `clarification` | Informar; revisar si la corrección afecta lo citado. |
| `new-version` | `new_version`, `new_edition` | Sugerir citar la versión vigente. |
| `clean` / `unknown` | sin avisos / ninguna fuente respondió | `unknown` no es "limpio". Las obras sin DOI no se pueden revisar. |

## `docx_revise.py`

Aplica las correcciones a una **copia** del `.docx` como control de cambios: inserciones y eliminaciones (`w:ins`/`w:del`), cambios de cursiva (`w:rPrChange`) y comentarios, todo con el autor de `--author` y la fecha. No acepta nada ni toca el original; activa "Control de cambios" en la copia para que lo que edite el autor después también quede registrado. Si una sola edición falla, no escribe nada y devuelve `errors` (código 1).

| Comando | Qué hace |
|---|---|
| `apply MANUSCRITO.docx EDITS.json --out SALIDA.docx [--author NOMBRE]` | Aplica `EDITS.json`. `--out` tiene que ser un archivo nuevo. Salida: `revisions` (`insertions`, `deletions`, `italic_changes`, `paragraphs_inserted`, `paragraphs_deleted`, `comments`), `paragraphs_revised`, `track_revisions_on`. |
| `summary ARCHIVO.docx` | Revisiones y comentarios presentes, por tipo y autor: verificación y cifra para el reporte. |

`EDITS.json` es una lista. Destino: `paragraph` = el índice que da `audit.json` (citas del cuerpo y entradas de la lista: párrafos no vacíos del documento, desde 0) o `note` = id de la nota (`"3"` al pie, `"e3"` final). Una cita con `note` se corrige en la nota, no en el párrafo que la llama.

| `op` | Campos | Uso |
|---|---|---|
| `replace` | `old`, `new`, [`occurrence`] | Cita en el cuerpo o en una nota. `old` se copia del texto de la auditoría; si aparece más de una vez, `occurrence` (desde 1). |
| `rewrite` | `new` | Párrafo completo (una entrada de la lista): diff palabra por palabra, se conservan los blancos de los bordes. |
| `insert` | `after`, `new` | Párrafo nuevo después del índice `after` (entrada faltante); copia el formato del párrafo de referencia. |
| `delete` | `paragraph` | Eliminar un párrafo (entrada duplicada). |
| `comment` | `comment` | Comentario de Word sobre el párrafo: dudas, `[verificar: campo]`, fuente que respalda un cambio de datos. Cualquier otra operación acepta también `comment`. |

- **Texto**: convención de la auditoría: `*cursiva*`, `[^3]` para una llamada de nota, `\*` para un asterisco literal. Si `old` y `new` no tienen `*`, el formato existente se respeta (el texto nuevo hereda el de al lado); con `*`, la cursiva de `new` manda y cada cambio queda como revisión de formato.
- Varias ediciones sobre el mismo párrafo se aplican en orden, cada una sobre el resultado de la anterior.
- **Rechaza** (y no escribe nada): `old` ausente o ambiguo, párrafos con revisiones pendientes de otra persona (que se acepten o rechacen antes), párrafos con campos vivos de Zotero (corregir en Zotero y refrescar), cuadros de texto, y llamadas de nota nuevas (solo se conservan o eliminan las existentes).
- **Autocontrol**: antes de escribir comprueba, párrafo por párrafo, que "Rechazar todo" devuelve exactamente el original y "Aceptar todo" el texto pedido (con sus cursivas).
- Comentarios: anclados al párrafo completo. Comentá los cambios de datos (autor, año, DOI, título) con la fuente que los respalda; los ajustes mecánicos de formato no necesitan comentario.

## `source_check.py`

Coteja cada cita con el texto completo que Zotero indexó del PDF, EPUB o HTML adjunto (`/items/{key}/fulltext`). Solo considera las referencias con match `exact-doi`, `exact-isbn`, `strong` o `strong-diff`. Funciona igual con citas autor-fecha y con notas (el contexto es la oración que llama la nota).

| Comando | Qué hace |
|---|---|
| `check audit.json match.json [-k 3] [--no-passages] [--previous check_anterior.json]` | Citas resueltas: citas textuales, copia y pasajes. Reutiliza únicamente juicios ligados a inputs idénticos. |
| `quote KEY --text "..." [--locator "p. 61"]` | Verifica una cita textual. |
| `passages KEY --query "..." [-k 5]` | Pasajes más relevantes (BM25) para una afirmación; útil para reformular la consulta en el idioma de la fuente. |

Estado por cita: `checked`, `no-fulltext` (sin adjunto o sin indexar: en Zotero, *Reindexar ítem*), `no-zotero-item` (match débil o ausente) o `unresolved-citation` (cita huérfana o ambigua).

Cada resultado incluye `evidence.binding`: hashes SHA-256 de manuscrito, auditoría, match y texto fuente indexado (UTF-8 exacto), `itemKey`, `attachmentKey`, versiones de ítem/adjunto, opciones de comprobación y ubicación/hash de la ocurrencia. La CLI registra los hashes de los bytes de `audit.json` y `match.json`; la API Python, hashes de JSON canónico. También se vinculan los metadatos de páginas/anotaciones que afectan la comprobación. `quote` y `passages` registran identidad, versiones y hash de texto fuente y consulta.

Para conservar un juicio humano/del agente, guardarlo como `results[].judgement` con veredicto, pasaje y página, manteniendo `evidence`. En una nueva comprobación, `--previous` solo copia `judgement` si corresponde a la misma ocurrencia, todos los inputs son idénticos y las identidades/versiones están disponibles. Cualquier cambio marca `stale` y expone el juicio como `previous_judgement`, nunca como juicio vigente. Un informe antiguo sin binding no se puede reutilizar; una cita movida no hereda la conclusión de otra oración. Los controles deterministas se calculan de nuevo, incluso cuando se proporciona `--previous`.

Si el manuscrito sigue accesible en la ruta registrada, se compara su hash actual con el auditado: un cambio posterior a `audit` invalida la vigencia. Si solo se dispone de los JSON, el hash del manuscrito es el declarado por la auditoría; debe preservarse el archivo original para comprobar su vigencia externamente. Para aprobar de nuevo un juicio obsoleto, ejecutar una comprobación nueva sin `--previous` y revisar su pasaje antes de añadir `judgement`.


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
