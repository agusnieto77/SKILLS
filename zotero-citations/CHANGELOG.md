# Changelog

## 3.2 — 2026-10-21

Cambios surgidos de la revisión de un libro de 11 capítulos y 477 referencias (APA 7). Ese trabajo entregó un `.docx` reescrito sin control de cambios, y 396 entradas sin DOI quedaron sin poder validarse.

- **Control de cambios obligatorio** (`docx_revise.py`, nuevo): las correcciones se aplican a una copia del `.docx` como revisiones de Word (inserción, eliminación, cambio de cursiva, párrafo insertado/eliminado) y comentarios, con autor y fecha, y "Control de cambios" activado. Nunca se acepta nada ni se toca el original. Valida todas las ediciones antes de escribir y comprueba que "Rechazar todo" devuelva el original. Rechaza párrafos con revisiones pendientes, campos vivos de Zotero y llamadas de nota nuevas. Probado con las 183 ediciones del libro: Word abre el archivo y lo verifica (315 revisiones; rechazar todo = original).
- `docx_revise.py summary`: inventario de revisiones y comentarios para el reporte; el reporte suma la sección "Control de cambios".
- `cite_audit`: las referencias traen `paragraph` y los índices de párrafo de las citas ya no se corren después de la bibliografía (apéndices, anexos). La lectura de `.docx` no mueve los espacios en los bordes de las cursivas.
- **Validación sin identificador** (`validate_ref.py work`, nuevo): Open Library, Library of Congress (SRU), Biblioteca Nacional de España (SRU), LA Referencia, repositorios DSpace (CONICET Digital, RIDAA-UNQ, Filo:Digital UBA, UNNE, RDU-UNC, RepHipUNR; ampliable con `ZOTERO_CITATIONS_DSPACE`), Crossref, OpenAlex y la ficha de la obra vía Citoid (`--url`, p. ej. SciELO). Grupos de independencia: repositorios + LA Referencia cuentan como una fuente.
- `validation-sources.md`: catálogo manual ampliado (BNMM con su catálogo Aleph y Z39.50, BCN, BDU-SIU, SNRD, SEDICI, Memoria Académica, CAICYT, AGN, SciELO, Redalyc, Latindex, CLACSO, Biblat, REBIUN, Dialnet, WorldCat, HathiTrust y otros), con modo de acceso y el procedimiento ficha → `work --url`.

## 3.1 — 2026-10-20

Primera prueba con un manuscrito real (artículo en PDF, notas en formato hispano, sin bibliografía).

- Entrada PDF (`citecore.read_pdf`, vía `pdftohtml` de Poppler): cuerpo y notas por tamaño de fuente, llamadas ancladas, cursivas, pies repetidos fuera, guiones de fin de línea, citas en bloque en cursiva.
- Notas en formato hispano: `Apellido, Nombre: Título`, `op. cit.` e `ibídem` con autor (resueltos a la última obra citada del autor), "Citado en:", partes dentro de un libro, títulos sin marcado, `;` en lugar de `:` tras el autor.
- Reglas nuevas: `C-OPCIT`, `C-OPCIT-AMBIGUOUS`, `C-OPCIT-UNRESOLVED`, `C-NOTE-INVERTED`, `C-TITLE-MARKUP`; `--no-lint` ahora también descarta las reglas de formato de citas.
- Las reglas de la lista ya no se aplican a referencias armadas desde notas.
- `match`: solo cuenta autores principales (los editores de un capítulo ya no generan `author_count`); snapshot con versión de formato.
- `render`: `quality` marca capítulos con una sola página en `pages`.
- `integrity --from` sin DOIs informa que no se puede verificar en vez de fallar.
- Localizadores de capítulo (`cap. 2`); un `ibid.` sin página hereda la de la nota anterior (`locator_inherited`).
- `with_locator` no repite la página si la nota ya termina en ella; PDF: espacio entre fragmentos de texto separados.
- Prueba completa con el artículo real: salidas APA 7, Chicago 18 notas y formato de la revista desde la misma auditoría.

## 3.0 — 2026-10-20

Renombrada de `zotero-apa-citation` a `zotero-citations`: deja de estar limitada a APA.

- Chicago 18.ª: perfiles de notas y bibliografía y de autor-fecha (`style_chicago.py`), con reglas de CMOS 18 (autores 6/3 + et al., 1–2 autores en notas, ibid., nota completa y abreviada, raya de 3 em, sistema equivocado).
- Detección automática de la norma del manuscrito (`--style auto`); "Chicago" a secas elige la variante del manuscrito o, si no se distingue, notas.
- Notas al pie y finales ancladas a la oración que las llama (`.docx` y notas Pandoc en Markdown); citas textuales asignadas a la nota.
- Manuscritos en notas sin bibliografía: las notas completas hacen de referencias.
- `cite_format.py` (nuevo): render con cualquier estilo CSL, notas completas y abreviadas, localizadores por norma, sufijos a/b en cualquier estilo autor-fecha, búsqueda en el repositorio de estilos, `match-style` contra un ejemplo y plantillas a medida verificables (`template check` / `render`).
- `zotero_client.py render` eliminado (reemplazado por `cite_format.py render`).
- `cite_audit.py` dividido en `citecore.py` + perfiles por norma; `--no-lint` para formatos a medida.
- `source_check.py` acepta localizadores sin "p." (Chicago) y rangos abreviados.
- Tag de auditoría `apa-audited` → `citation-audited`; caché `~/.cache/zotero-citations` (`ZOTERO_CITATIONS_CACHE`).
- Documentación: `chicago.md`, `custom-formats.md`, `apa.md` (antes `apa-templates.md`), README.

## 2.1 — 2026-10-20

- Integridad: retractaciones, avisos de preocupación y correcciones (Crossref `updated-by` con Retraction Watch, OpenAlex `is_retracted`).
- `source_check.py`: citas textuales, página citada, copia sin comillas y pasajes candidatos contra el texto completo indexado en Zotero.

## 2.0 — 2026-10-19

- Scripts: `cite_audit.py`, `zotero_client.py`, `validate_ref.py`, `zotlib.py`.
- API local de Zotero para lectura, escrituras con dry-run, write tokens y control de versiones, validación contra el schema vivo.
- Validación externa con dos fuentes independientes y veredictos.
- Plantillas corregidas contra el schema de Zotero.

## 1.0

- Versión inicial: instrucciones APA 7 sin scripts.
