# Changelog

## 1.3.0 — 2026-10-26

- Subcomando `video`: copia local del video en mp4 delegando en `yt-dlp`, dependencia opcional exclusiva (si falta, código 2 con instrucciones de instalación, sin tocar la red). Escalera de formato determinista: `best[ext=mp4]/best` → ante `Requested format is not available`, inventario `-J` y cascada DASH https mp4 + audio 140 (ejemplo verificado `137+140/136+140/231+140`) → HLS m3u8 registrada como vía de Repro, no DASH puro. ffmpeg ausente: aviso y solo formatos progresivos.
- Runtime JavaScript (EJS): detección de deno/node; `--js-runtimes node` y `--remote-components ejs:github` se añaden cuando la versión de yt-dlp los admite. Sin runtime se registra `aviso_js_runtime` con la wiki EJS. Documentada la cadena completa en `references/alternativas.md` con los errores reales vistos (formato no disponible, 403 por yt-dlp desactualizado, warnings de EJS) y sus mitigaciones.
- Ética de la descarga: declaración de copia local para archivo/duo/docencia sin redistribución por defecto; sin cookies, tokens ni evasión. Restricciones de edad/privado/membresía se reportan por entrada (`clasificacion_error`); el bloqueo de cliente ("Sign in to confirm you're not a bot") detiene el lote con `motivo=bloqueo_cliente_yt_dlp`.
- Salida `<id>_video.json`: `metodo` (yt-dlp con versión), `url`, `estrategia`, `formato_solicitado`, `formato_elegido` (id, resolución, codecs), `path_local`, `tamano_bytes` (medido sobre el archivo final), `runtime_js`, `solver_ejs`, `capturado_en_utc` y `declaracion`. Lotes con recibo `lote_video.json` y método propio.
- 12 pruebas offline nuevas (99 en total): cascada DASH por altura/tasa con audio 140, fallback m4a, ausencia de DASH con presencia de m3u8, clasificación de fallos, CLI sin yt-dlp, contrato del JSON, fallback DASH y HLS tras formato no disponible, restricción de edad reportada sin evasión, corte de lote por bloqueo de cliente y escalón DASH inhabilitado sin ffmpeg.
- Verificación en red del 26-10-2026 (Windows, yt-dlp 2026.10.21, node 24, ffmpeg 6.0.1): reproducción del error `Requested format is not available` con EJS incompleto y su resolución; descargas reales de `jNQXAC9IVRw` (escalones 1 y 2) y `rajbNWCjpmo` (transcripción, comentarios y video mp4 de 12 492 272 B); registradas en `validation/RESULTADOS.md`.

## 1.2.4 — 2026-10-23

- La ficha watch vuelve a tolerar `AGE_CHECK_REQUIRED`/`CONTENT_CHECK_REQUIRED`: `metadatos` y `comentarios` leen el HTML público de videos con verificación de edad, como antes de 1.2.3. Solo el reproductor rechaza esos estados.

## 1.2.3 — 2026-10-22

- Cierre seguro ante `LOGIN_REQUIRED`: solo señales positivas de restricción por video permiten continuar; motivos vacíos, desconocidos o de idioma no reconocido detienen el cliente.
- Señales estructurales de edad/privacidad prioritarias y constantes con nombre para las heurísticas textuales de edad, acceso privado y membresía.
- Corte inmediato ante dos entradas consecutivas con `LOGIN_REQUIRED`, incluso por restricciones del video; `todo` cuenta una sola vez por entrada y no solicita operaciones posteriores al corte.
- Validador renombrado a `_validar_reproducibilidad`, con excepciones explícitas y una sola entrada al estado de bloqueo.
- Clasificación de transporte compatible con requests anterior a 2.27 mediante detección opcional de `JSONDecodeError`, sin añadir dependencias.
- Guardado de recibos devuelve el estado de persistencia; comentarios explican la limpieza del temporal y la escritura final obligatoria. Fixture del segundo video aclarada.
- Regresiones offline de motivos desconocidos/localizados, señales estructurales, corte consecutivo y reinicio, compatibilidad de requests y persistencia del recibo.

## 1.2.2 — 2026-10-22

- `LOGIN_REQUIRED` distingue restricciones propias del video de un bloqueo explícito de bots mediante `reason` y la estructura de error del reproductor; edad, acceso privado o motivo desconocido no detienen otros videos.
- Los fallos de escritura de recibos intermedios emiten advertencia y no interrumpen el lote; se reintenta en la siguiente actualización y se exige una escritura final. Se intenta limpiar el temporal incluso ante fallos.
- JSON inválido en respuestas HTTP 200 no se clasifica como fallo de transporte: salida 1 y `error_red=false`, también en hilos y en `player`.
- Entrada única al estado de bloqueo y mensaje compartido. Un 429 sin presupuesto para reintentar se informa como `error_pagina` o `error_hilo`, no como agotamiento ordinario de presupuesto.
- Índice explícito para marcar entradas pendientes; pruebas de escritura con simulaciones selectivas y conteo documentado. Regresiones offline de restricciones por video, recibos transitorios/finales y JSON inválido.

## 1.2.1 — 2026-10-22

- Interrupción del lote y de las operaciones/hilos pendientes ante HTTP 429 agotado o `LOGIN_REQUIRED`; recibo con entradas no procesadas y motivo explícito.
- Recibo inicial e incremental con reemplazo atómico después de cada entrada: una interrupción conserva la última actualización completa.
- Código de salida 3 uniforme para errores de transporte en operaciones únicas, incluidas páginas y respuestas de comentarios; conserva la salida parcial con `error_red`.
- `todo` aísla también `OSError` de JSON/CSV y fallos al guardar el propio JSON de error, sin perder otros resultados.
- Validación de límites compartida entre CLI y cliente, mensajes derivados de las constantes y contabilidad de páginas localizada en el presupuesto.
- Compatibilidad de transcripción: `idioma` vuelve a conservar la pista fuente; `idioma_destino` identifica la traducción solicitada.
- Regresiones offline para bloqueos, recibos interrumpidos, errores de red/escritura y semántica del idioma; sin nuevas capturas de YouTube.

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
