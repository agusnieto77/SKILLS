# Alternativas para obtener datos de YouTube

Las observaciones históricas del 22-10-2026 corresponden al video `j3ZIM9UaXlE` ("La IA debería hacernos trabajar menos (NO MÁS)", canal midudev). Las opciones nuevas del CLI se verifican offline; las recetas de inventario no constituyen nuevas capturas.

## 1. API interna `youtubei` (InnerTube)

Es la API que usa el propio reproductor de YouTube. Se llama sin cuenta: la clave pública (`INNERTUBE_API_KEY`) y la versión de cliente se leen del HTML de la ficha.

| Endpoint | Qué devuelve | Observado |
|---|---|---|
| `POST /youtubei/v1/player` | Metadatos (`videoDetails`, `microformat`) y pistas de subtítulo (`captions`) | Con cliente `ANDROID` (`clientVersion` 20.10.38) responde `playabilityStatus: OK`; con cliente `WEB` responde `UNPLAYABLE` |
| `POST /youtubei/v1/next` | Sección de comentarios y continuaciones | Paginación por token de continuación |
| `POST /youtubei/v1/search` | Resultados de búsqueda | `query` más contexto de cliente |
| `POST /youtubei/v1/browse` | Contenido de canal o lista | `browseId` con el ID de canal |
| `GET /api/timedtext` | XML de subtítulos (`timedtext` formato 1 o 3) | La URL base viene firmada en la pista de subtítulo; no se puede armar a mano |

Claves que hacen funcionar la vía:

- El **cliente `ANDROID`** es el que devuelve `OK` en `player`. Con `WEB` el mismo endpoint responde `UNPLAYABLE` (detección de automatización). Cambiar `clientName` cambia el resultado.
- La transcripción original se pide con la URL firmada de la pista: agregar `fmt=json3` no produjo JSON en la captura histórica. La opción explícita `--tlang` conserva los parámetros firmados y agrega/reemplaza solo el idioma destino: es una solicitud de traducción automática a YouTube, no una garantía de compatibilidad. Los fixtures no validan la aceptación de la firma ni el idioma servido; la salida lo marca con `traduccion_verificada=false`.
- Las respuestas a comentarios viven en `frameworkUpdates.entityBatchUpdate.mutations` con `commentEntityPayload`; el hilo y la respuesta se enlazan por `commentKey`, y la entidad de payload se reconoce porque su `entityKey` es **prefijo** del `commentKey`.

### Orden de comentarios

El token de continuación inicial (sección `comment-item-section`) devuelve la lista en el criterio por defecto. La cabecera (`commentsHeaderRenderer`) publica dos tokens de clasificación:

| Criterio | Token | Cobertura observada (229 comentarios declarados) |
|---|---|---|
| "Destacados" (`sortMenu.subMenuItems[0]`) | `continuationCommand` de la sección de orden | 154 comentarios de primer nivel: es la jerarquía de la interfaz, un subconjunto |
| "Más recientes" (`sortMenu.subMenuItems[1]`) | `continuationCommand` de la sección de orden | 168 comentarios de primer nivel en la captura histórica |

La unión observada dio 168: "Destacados" estaba contenido en "Más recientes". Preferir este último para mayor cobertura, sin prometer totalidad frente a topes, moderación, eliminación, cambios durante captura o fallos por hilo.

### Límites

- Las IP de datacenter y las proxies son las que primero se bloquean. Cuando aparece `LOGIN_REQUIRED` con motivo `Sign in to confirm you're not a bot`, la respuesta es un bloqueo: se informa, no se intenta esquivar.
- La estructura de la respuesta cambia sin aviso (esto pasó varias veces durante 2026: `commentRenderer` pasó a `commentViewModel` más `commentEntityPayload`).
- No hay contrato ni garantía de estabilidad. Es la vía que usa `yt-dlp`, y `yt-dlp` también se rompe.

## 2. `yt-dlp`

Herramienta de línea de comandos que ya resuelve las tres salidas:

```bash
# Metadatos (JSON con todos los campos disponibles)
yt-dlp --skip-download --dump-single-json "https://www.youtube.com/watch?v=ID"

# Subtítulos automáticos en VTT
yt-dlp --skip-download --write-auto-subs --sub-langs es --sub-format vtt -o "v.%(ext)s" "URL"

# Comentarios (hilos + respuestas)
yt-dlp --skip-download --write-comments \
  --extractor-args "youtubecomment:max_comments=all,all,all;max_replies=all" \
  --print "%(comments)j" --no-simulate "URL"
```

Observado: 228 comentarios (168 de primer nivel + 60 respuestas) frente a los 229 declarados por la página; la diferencia es un comentario cuyo hilo no se publica en la interfaz. El orden por defecto de `yt-dlp` es "Más recientes", de ahí que su cobertura coincida con ese criterio.

Advertencia habitual: `WARNING: [youtube] No supported JavaScript runtime could be found`. YouTube va exigiendo un runtime JavaScript (Deno) para resolver formatos. No afecta a metadatos, subtítulos ni comentarios, pero sí a la descarga de video.

## 3. `youtube-transcript-api`

```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
pistas = api.list("j3ZIM9UaXlE")           # ar, en, pt, es (todos ASR)
tr = pistas.find_transcript(["es", "en"]).fetch()
```

- Devuelve los segmentos con `start` y `duration`: mismo contenido que `timedtext`, con la API más cómoda.
- Usa por dentro el mismo `youtubei/v1/player` con cliente `ANDROID`.
- **Falla con `PoTokenRequired`** cuando la URL de subtítulo incluye `exp=xpe`: es el requisito de *proof of origin* token. Ocurre de forma intermitente según la sesión y el video.
- La versión 1.x cambió la API: `YouTubeTranscriptApi()` instancia y `api.list()` / `api.fetch()`; las funciones de módulo de la 0.x están deprecadas.

## 4. Instancias de Invidious y Piped

Proxy web que expone una API JSON propia (`/api/v1/videos/ID`, `/streams/ID`).

Estado observado de las instancias públicas el 22-10-2026:

| Instancia | Respuesta |
|---|---|
| `invidious.f5.si` | HTTP 500 |
| `inv.nadeko.net`, `yewtu.be` | HTTP 403 |
| `invidious.nerdvpn.de` | HTTP 401 |
| `pipedapi.kavin.rocks` | HTTP 526 |
| `pipedapi.adminforge.de` | HTTP 403 |
| `pipedapi.reallyaweso.me` | HTTP 502 |

Es decir: las instancias públicas están degradadas o bloquean por IP. No conviene basar una clase o una recolección en ellas; si se usan, verificar cada vez la instancia concreta y tener la vía directa como plan B.

## 5. `oEmbed`

`GET https://www.youtube.com/oembed?url=URL&format=json` devuelve, sin clave y sin paginación: título, autor, URL del canal, miniatura y el `iframe` de inserción. Sirve para identificar un video o montar un embed, no para analizar contenido.

## Inventario acotado de playlist o canal

Para preparar una muestra de hasta 50 IDs sin descargar videos:

```bash
# Playlist pública; --playlist-end acota el inventario antes de enviarlo al CLI
yt-dlp --flat-playlist --skip-download --playlist-end 50 \
  --print "%(id)s" "https://www.youtube.com/playlist?list=PLAYLIST_ID" > ids.txt

# Pestaña de videos de un canal público
yt-dlp --flat-playlist --skip-download --playlist-end 50 \
  --print "%(id)s" "https://www.youtube.com/@CANAL/videos" > ids.txt

python youtube-api/assets/yt_datos.py metadatos --archivo-ids ids.txt --out datos
```

Guardar el archivo como UTF-8 (en Windows PowerShell antiguo la redirección puede generar UTF-16: usar una salida UTF-8). Una línea por ID o URL; líneas vacías y `#` se ignoran. Revisar el inventario: una lista puede contener videos privados, eliminados o duplicados; el recibo conserva error/posición por entrada. Los errores propios de un video no detienen el resto, salvo el corte por dos `LOGIN_REQUIRED` consecutivos; un 429 agotado o un `LOGIN_REQUIRED` sin restricción del video identificada detienen el cliente. No sustituir IDs ausentes ni afirmar que el inventario representa todos los videos del canal. Procesamiento secuencial, máximo 50 entradas, con pausas y presupuesto por video; no dividir campañas para eludir límites, cuotas o bloqueos. No se utiliza SQLite.

Para un canal con clave de proyecto propia, usar uploads → `playlistItems.list` → `videos.list`, según [API oficial](api-oficial.md#inventario-de-un-canal-o-playlist).

## Contrato de salidas del CLI

Todas las salidas JSON de operación llevan método/fuente y fecha `capturado_en_utc` cuando la operación se completa. En `todo`, cada error se intenta guardar en su propio JSON con ID y fecha; un fallo de escritura queda en el resultado sin descartar otras operaciones. Si también falla el JSON de error, se añade `error_escritura`; el recibo de lote preserva esos resultados si puede escribirse. Ante bloqueo, las operaciones restantes quedan `{estado: "no_procesado", motivo, error}` sin nuevas peticiones.

### Comentarios y cobertura

- `parcial`: verdadero ante truncamiento, error, ciclo de token, hilos conocidos no expandidos, orden `top` o menos filas que el total declarado. Falso significa que no se detectó una de esas condiciones, **no** certifica totalidad.
- `motivo_fin`: `sin_continuacion`, `max_filas`, `max_paginas`, `max_peticiones`, `token_repetido`, `error_pagina` o el primer motivo de hilo cuando el recorrido principal terminó naturalmente.
- `presupuesto`: `max_filas`, `max_paginas` (máximo 60), `max_peticiones` (máximo 120), `paginas_consumidas` y `peticiones_consumidas`. Páginas = respuestas HTTP 200 de `/next` con objeto JSON válido, sin error ni bloqueo; peticiones = intentos HTTP de `/next`, incluidos errores y el único reintento ante 429. Un reintento exitoso consume dos peticiones y una página; una respuesta fallida no consume página. Orden, comentarios y respuestas comparten presupuesto; `watch`, `player` y `timedtext` quedan fuera.
- `hilos_no_expandidos`: lista de `{comment_id, respuestas_declaradas, respuestas_obtenidas, motivo, error?}`. Motivos: `no_solicitadas`, `max_filas`, `max_paginas`, `max_peticiones`, `sin_token_respuestas`, `token_repetido`, `error_hilo`, `bloqueo` o `menos_respuestas_declaradas`. Un error de hilo conserva respuestas previas y permite intentar otros hilos dentro del presupuesto, salvo bloqueo: los siguientes quedan con motivo `bloqueo`, sin peticiones.
- `errores`: mensajes de fallos del recorrido principal. Los errores de hilo permanecen asociados a su ID; no se silencian.
- `error_red`: verdadero solo si falló el transporte durante páginas o respuestas; conserva las filas anteriores y permite al CLI devolver 3 en una operación única distinta de `todo`. HTTP de error, bloqueo o JSON inválido devuelve 1; una respuesta HTTP 200 no JSON conserva `error_red=false`. Lotes y `todo` devuelven 1 ante cualquier fallo de red.
- `bloqueo`: `http_429`, `login_required` o `null`. Un bloqueo detiene todas las peticiones pendientes del cliente, incluso si aparece durante comentarios. Un 429 que no puede reintentarse por presupuesto entra en el mismo estado que un 429 persistente: `motivo_fin=error_pagina` en padres o `error_hilo` en respuestas, con el mensaje de bloqueo; no es una parada ordinaria `max_peticiones`.
- Se priorizan padres antes de respuestas. El límite de filas se aplica al incorporar cada fila y antes de solicitar otra página/hilo; una página ya recibida puede contener filas descartadas. Se informan hilos conocidos de esa página, incluidos padres descartados. No se conocen los hilos de páginas no solicitadas.
- Comparar `obtenidos` con `comentarios_declarados`, sin asumir que el total declarado (posiblemente abreviado o cambiante) coincide con lo accesible.

### Idiomas y traducción

`pistas` expone las pistas originales publicadas, sin descargar texto. `--lang es,en` selecciona en orden y `--tipo-subtitulo manual|asr|cualquiera` filtra pistas fuente; no sustituye una preferencia explícita por un idioma arbitrario. En el JSON de transcripción, `automatica` describe ASR en la fuente, no si la traducción fue automática. `idioma` e `idioma_fuente` conservan el idioma de la pista fuente por compatibilidad; solo `idioma_destino` indica el destino solicitado (o la fuente sin traducción). `traducida=true` y `metodo_traduccion=traduccion_automatica_youtube_tlang` declaran la solicitud a YouTube; `traduccion_verificada=false` y `aviso_traduccion` impiden confundirla con una pista original o con idioma efectivamente comprobado. Los errores HTTP, XML inválido y archivos vacíos se informan sin volver al original. La calidad/idioma de una traducción exige revisión independiente.

### Lotes

`lote_<comando>.json`: `max_videos=50`, `total` (todas las entradas), `exitosos`, método y fecha; `resultados` conserva `{posicion, entrada, video_id?, ok, estado, motivo?, bloqueo?, resultado?, error?}` por entrada. `estado` es `procesado` o `no_procesado`; este último lleva `ok=false` y `motivo=pendiente` hasta ser procesado. Se intenta crear el recibo antes de la red y reemplazarlo atómicamente después de cada entrada: una interrupción conserva la última actualización completa, no el trabajo en curso. Si falla una escritura intermedia, se informa una advertencia y se reintenta en la siguiente sin detener la recolección; se intenta limpiar el temporal. La escritura final es obligatoria y su fallo produce salida 1, aunque todas las entradas hayan podido procesarse.

La validación de reproducibilidad usa un criterio de cierre seguro: `LOGIN_REQUIRED` es un error propio del video solo con señal positiva de restricción. Se priorizan `AGE_CHECK_REQUIRED`/`CONTENT_CHECK_REQUIRED`, `desktopLegacyAgeGateReason`, los renderizadores de edad `playerAgeGateRenderer`/`playerAgeGateContentRenderer` y el icono `PRIVACY_PRIVATE` de `errorScreen.playerErrorMessageRenderer`. Como respaldo, `MARCAS_RESTRICCION_VIDEO` reúne textos conocidos de edad, acceso privado o membresía en `reason` y en `playerErrorMessageRenderer.reason/subreason`; es una heurística incompleta y dependiente del idioma, no una lista exhaustiva de bloqueos.

Un `LOGIN_REQUIRED` sin señal positiva —incluidos motivo vacío, desconocido o idioma no reconocido— detiene el cliente con motivo `login_required`; HTTP 429 agotado lo detiene con `http_429`. Además, dos entradas consecutivas con `LOGIN_REQUIRED` detienen inmediatamente el lote aunque ambas parezcan restricciones por video. Las operaciones de `todo` cuentan una sola vez por entrada; una entrada sin `LOGIN_REQUIRED` reinicia la cuenta. Al alcanzar el corte durante `todo`, no se solicitan sus operaciones restantes. La entrada que detectó el bloqueo conserva `bloqueo`; las restantes quedan `no_procesado` con el motivo. `resultado` conserva datos parciales; `ok=false` indica errores o entradas no procesadas, no meramente alcanzar un límite de cobertura. Las entradas inválidas cuentan para el máximo y quedan registradas.
