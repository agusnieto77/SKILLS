# zotero-citations

Skill para agentes compatibles con el formato Agent Skills (OpenCode, Pi, Oh My Pi, Gentle Shell, Claude Code, Codex y otros) que audita y normaliza las citas de un manuscrito académico usando Zotero como fuente de verdad.

- **Normas**: APA 7 y Chicago 18.ª (notas y bibliografía, o autor-fecha) por defecto; cualquier estilo del repositorio de Zotero (10 800+); o un formato a medida reconstruido a partir de un ejemplo del usuario.
- **Auditoría**: citas huérfanas y no citadas, "et al.", años, sufijos a/b, ibid., notas completas y abreviadas, reglas de formato de cada norma.
- **Zotero**: coteja la lista con la biblioteca, crea y corrige ítems con dry-run y control de versiones.
- **Validación**: Crossref, DataCite, OpenAlex, Open Library, Library of Congress, Biblioteca Nacional de España, LA Referencia y repositorios institucionales (CONICET, UBA, UNNE, UNC, UNR, UNQ), fichas de SciELO u otros sitios vía Citoid, PubMed; catálogo manual para BNMM, BCN, Redalyc y otros; retractaciones (Retraction Watch vía Crossref, OpenAlex).
- **Fidelidad**: verifica citas textuales, páginas y copia sin comillas contra el texto completo que Zotero indexó de los PDF.
- **Control de cambios**: el manuscrito corregido se entrega como copia del `.docx` con cada corrección como revisión de Word y las dudas como comentarios; el autor acepta o rechaza.

El agente lee `SKILL.md`; este README es para quien instala y mantiene la skill.

## Requisitos

- Python 3.10 o superior (solo biblioteca estándar).
- Zotero 7+ de escritorio, recomendado: habilitar *Configuración → Avanzado → Permitir que otras aplicaciones de esta computadora se comuniquen con Zotero* (API local: rápida, sin cuota).
- Una API key de Zotero con permiso de escritura (https://www.zotero.org/settings/keys).

## Configuración

| Variable | Obligatoria | Uso |
|---|---|---|
| `ZOTERO_API_KEY` | para escribir | Key de la Web API. Nunca se imprime completa. |
| `ZOTERO_LIBRARY_ID` | sí | `userID` (lo muestra `zotero_client.py whoami`) o `groupID`. |
| `ZOTERO_LIBRARY_TYPE` | no | `user` (default) o `group`. |
| `CROSSREF_MAILTO` | no | Email para el polite pool de Crossref. |
| `OPENALEX_API_KEY` | no | Más cuota de búsquedas en OpenAlex. |
| `GOOGLE_BOOKS_API_KEY` | no | Tercera fuente para ISBN. |
| `ZOTERO_CITATIONS_CACHE` | no | Carpeta de caché (default `~/.cache/zotero-citations`). |

Comprobación:

```bash
python scripts/zotero_client.py whoami
```

## Uso típico

```bash
python scripts/cite_audit.py audit manuscrito.docx --style auto > audit.json
python scripts/zotero_client.py match audit.json > match.json
python scripts/validate_ref.py integrity --from audit.json match.json
python scripts/source_check.py check audit.json match.json > check.json
python scripts/cite_format.py render --keys KEY1,KEY2 --style chicago-notes --locators KEY1:61
python scripts/docx_revise.py apply manuscrito.docx edits.json --out manuscrito_revisado.docx --author "Nombre"
```

Formato de una revista o de un ejemplo:

```bash
python scripts/cite_format.py styles --search "nombre de la revista"
python scripts/cite_format.py match-style --key KEY1 --example "referencia como la quiere el usuario"
python scripts/cite_format.py template check --template plantilla.json --key KEY1 --expect "..."
```

Referencia completa de comandos y salidas: `references/scripts.md`.

## Estructura

```
SKILL.md                 contrato para el agente
scripts/                 cite_audit, zotero_client, validate_ref, source_check, cite_format, docx_revise (+ módulos internos)
references/              scripts, apa, chicago, custom-formats, zotero-api, validation-sources, archival-sources, report-template
tests/                   unittest sin red (servidor Zotero simulado, manuscritos de prueba)
```

## Tests

```bash
python -m unittest discover -s tests
```

## Límites conocidos

- PDF: se leen con `pdftohtml` de Poppler (incluido en MiKTeX, TeX Live o Git for Windows); sin él, o con PDF escaneados sin OCR, hay que convertir antes. La separación cuerpo/notas usa tamaños de fuente: revisá `summary.notes` (notas vs llamadas ancladas).
- La extracción de citas usa patrones: revisá los casos marcados antes de reportarlos (p. ej. un paréntesis de prosa con lugar y año en autor-fecha).
- Las retractaciones solo se pueden revisar en obras con DOI.
- La fidelidad depende de que el PDF esté adjunto, indexado y con OCR.
- Control de cambios (`docx_revise.py`): no edita párrafos con revisiones pendientes de otra persona, campos vivos de Zotero ni cuadros de texto; no crea llamadas de nota nuevas; los comentarios se anclan al párrafo entero.
