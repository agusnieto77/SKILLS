# Changelog

## 1.2 — 2026-10-22

- Cobertura de comentarios estructurada: `parcial`, `motivo_fin`, presupuesto compartido por orden/padres/respuestas, hilos no expandidos y errores por hilo; sin descarte silencioso de errores.
- Tope de 60 páginas visible y configurable a la baja; hasta 120 intentos HTTP de `/next`, incluidos reintentos 429. El máximo de filas se aplica durante la recolección, antes de descargar respuestas adicionales.
- Lotes secuenciales de hasta 50 IDs/URLs mediante `--url` múltiple/repetible y `--archivo-ids`, con recibo y resultado/error por entrada; fallos de `todo` aislados por operación.
- Comando `pistas`, preferencias `--lang` ordenadas/repetibles, `--tipo-subtitulo` y traducción opcional `--tlang`. Conserva fuente/destino y declara traducción automática de YouTube no verificada en red.
- Referencias para inventario acotado mediante `yt-dlp --flat-playlist` y ruta oficial uploads → `playlistItems.list` → `videos.list` (hasta 50 IDs). Corregidas las notas sobre respuestas, `searchTerms` y `captions.download`.
- Hard Rules y ética: datos externos no confiables, nunca instrucciones; muestra autoseleccionada y moderada, no representativa y sin inferencias de identidad, demografía o veracidad.
- Pruebas offline de presupuestos, truncamiento, errores por hilo/video, preferencias de idioma, solicitud de traducción y CLI; no se realizaron nuevas capturas de YouTube.

## 1.1 — 2026-10-22

- `todo` descarga la ficha `watch` y consulta `youtubei/v1/player` una sola vez por video (antes, tres y dos veces): caché por cliente.
- El JSON embebido (`ytInitialPlayerResponse`, `ytInitialData`) se decodifica con `raw_decode` desde la llave de apertura; el regex anterior cortaba en el primer `};` dentro de un string.
- `Retry-After` con fecha HTTP ya no rompe la espera ante HTTP 429 (se usa la espera por defecto, acotada a 30 s).
- Skill renombrada de `youtube-scraping` a `youtube-api` para coincidir con su carpeta; rutas de la documentación corregidas.
- Mensaje de error de subtítulos: "PO token (proof of origin)".
- `comentarios_declarados` usa el total exacto (`countText`) en lugar del abreviado: en videos con millones de comentarios ("2,4 M") el valor anterior era 24. Las formas abreviadas (`mil`, `M`, `K`) se interpretan cuando no hay total exacto.
- 7 pruebas nuevas (30 en total), incluido un cliente con sesión falsa.

## 1.0 — 2026-10-22

Primera versión: CLI `assets/yt_datos.py` con `metadatos`, `transcripcion`, `comentarios` (orden `newest`/`top`, respuestas por hilo) y `todo`, vía InnerTube y páginas públicas, sin cuenta ni API key. Referencias de la Data API v3, alternativas (`yt-dlp`, `youtube-transcript-api`, Invidious/Piped) y ética.
