---
name: elpais-nota
description: "Trigger: elpais.com URL, nota de El País, comentarios de El País, imágenes/media de una nota, objetos digitales. Descarga una nota de El País con metadatos, objetos digitales y comentarios Disqus."
license: Apache-2.0
metadata:
  author: "agusn"
  version: "1.0"
---

## Activation Contract

Load this skill whenever the user shares an `elpais.com` article URL or asks to download an El País article's content, metadata, media/objects, or comments.

## Hard Rules

- Use the three scripts in `assets/`. Copy them into the working folder first (`descargar_objetos.py` imports `descargar_nota.py`); they are stdlib-only Python 3.
- Comments are publicly readable via Disqus (forum `el-pais-1`); posting requires subscription. Never attempt to bypass site auth or paywalls.
- elpais.com may return 403 to robots (Datadome). Use only the scripts' built-in chain (direct HTTP → Wayback → manual fallback). Do not improvise other bypasses.
- CSV deliverables always use `;` delimiter and `utf-8-sig` (user works in Excel es-ES).
- Never fabricate counts or metadata; report only what the scripts output.

## Decision Gates

| Need | Command |
|------|---------|
| Note content + all metadata + live comment counter | `python descargar_nota.py "URL" --salida DIR` |
| Images/PDF/media with manifest (sha256, bytes, type) | `python descargar_objetos.py DIR\nota.html` |
| All comments (JSON + CSV) | `python descargar_comentarios_elpais.py "URL"` |

## Execution Steps

1. Copy the three scripts from `assets/` to the working folder; create an output folder per note.
2. Run `descargar_nota.py`. If it exits with code 2, ask the user to save the page (Ctrl+S) and rerun with `--html "file.html"`.
3. Read `metadatos.json` → check `comentarios.disqus.contador_actual` and `totales`.
4. Run `descargar_objetos.py` on the generated `nota.html`. Report `resumen_por_tipo`; streams marked `stream-no-descargable` need ffmpeg and are out of scope.
5. For comments: run `descargar_comentarios_elpais.py`. If it asks for the identifier (fresh notes blocked by Datadome), instruct: open note → view-source → Ctrl+F `disqus-identifier` → rerun with `--identificador`.
6. If a script's Disqus API key lookup fails, re-run; the key is re-extracted from the embed bundle each run (it may rotate).

## Output Contract

Final message must report: paths of `nota.html`, `metadatos.json`, `nota.txt`, `links.csv`; `objetos/` summary (downloaded/total, counts by content-type); comments file paths with totals (root vs replies). Flag any files skipped and why.

## References

- `assets/descargar_nota.py` — metadata extractor (meta tags, JSON-LD, disqus counter, links, clean text).
- `assets/descargar_objetos.py` — media downloader with manifest.
- `assets/descargar_comentarios_elpais.py` — Disqus comments paginator.
