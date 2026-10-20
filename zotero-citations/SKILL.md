---
name: zotero-citations
description: "Trigger: auditar citas, normalizar a APA o Chicago, revisar bibliografía, citar en formato de una revista, verificar fuentes, Zotero. Gestiona citas con Zotero."
license: Apache-2.0
metadata:
  author: citation-manager
  version: "3.0"
---

## Activation Contract

Usala para **auditar, normalizar o completar** bibliografías en APA, Chicago o el formato que pida el usuario; **verificar citas contra sus fuentes**; **sincronizar con Zotero**; **validar referencias**.

## Hard Rules

- **Norma**: "APA" = APA 7; "Chicago" = CMOS 18.ª (variante del manuscrito; si no se distingue, notas y bibliografía). Edición distinta declarada: respetarla y avisar.
- **Formato a medida**: lo define el ejemplo del usuario; nunca completes por suposición lo que el ejemplo no muestra: preguntá.
- **Validar antes de crear** en Zotero (`validated` o `single-source` + segunda fuente); faltantes: `[verificar: campo]`.
- **Escrituras en dry-run** (`create`/`update`/`trash` sin `--confirm`) y aprobación explícita; `update` exige `--version`. Nunca `DELETE`.
- **Formato desde Zotero** (`cite_format.py`), no a mano; si sale mal, corregí los datos del ítem.
- **Fidelidad**: veredicto con pasaje y página; sin texto completo = `no verificable`.
- **`.docx`**: con `D-LIVE-ZOTERO-FIELDS` corregí en Zotero y refrescá; salida vía skill `docx`, sin Markdown literal.
- **Secretos** nunca impresos; **toda operación Zotero** va al reporte. Archivo/histórico: `references/archival-sources.md`.

## Decision Gates

| Pedido del usuario | Acción |
|---|---|
| Sin norma | `cite_audit --style auto`; confirmá la detectada si `confidence` < 0,7. |
| "APA" / "Chicago" / "Chicago autor-fecha" | `--style apa` / `chicago` / `chicago-author-date`. |
| Norma pedida ≠ manuscrito (`D-STYLE-MISMATCH`) | Convertir a lo pedido; avisá. |
| Revista o editorial nombrada | `cite_format styles --search` → `render --style <csl>`. |
| Ejemplo de cita o referencia | `match-style`: `exact` → ese CSL; `ties` → pedí ejemplo de cita en texto; `close`/`none` → plantilla (`references/custom-formats.md`) hasta `exact_ignoring_italics`; preguntá por `fallback_types` e `incomplete`. |
| Match Zotero `strong-diff`, `weak`, `trashed` | Mostrar diff y preguntar. |
| Validación `mismatch`, `conflict`, `not-found` | No crear; mostrar y preguntar. |
| Integridad `retracted` / `expression-of-concern` | Encabezar el reporte; decide el autor. |
| Cita textual no `exact*`, página `inconsistent`, `verbatim` | Mostrar manuscrito vs fuente; proponer corrección. |

## Execution Steps

1. Ingesta (`.docx`, `.pdf` con texto, `.md`, `.txt`); fijá norma, idioma y si hay formato a medida.
2. `cite_audit.py audit --style ...` (`--no-lint` con formato a medida) → `zotero_client.py whoami` → `match`.
3. `validate_ref.py integrity --from` audit y match; validar lo no encontrado; crear/corregir en Zotero (dry-run → `--confirm`).
4. `source_check.py check`; juicio de respaldo solo si se pide fidelidad.
5. `cite_format.py render --style ... --locators ...` (o `template render`) → reescribir citas, notas y lista; preservar el resto.
6. Reporte (`references/report-template.md`).

## Output Contract

Devolvé: (1) **manuscrito corregido** completo en la norma o formato acordado; (2) **reporte** con norma usada (y cómo se eligió), integridad, fidelidad y log Zotero.

## References

`references/`: `scripts.md` (comandos y salidas), `apa.md`, `chicago.md`, `custom-formats.md`, `zotero-api.md`, `validation-sources.md`, `archival-sources.md`, `report-template.md`.
