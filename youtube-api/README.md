# Skill de scraping de YouTube

Guía humana de uso. La skill recupera **metadatos**, **transcripción** y **comentarios** de videos públicos de YouTube con Python, sin cuenta ni API key, y puede descargar una **copia local del video** (subcomando `video`) delegando en `yt-dlp`. Las capturas históricas del 22-10-2026 están en `validation/RESULTADOS.md`; las funciones nuevas de la versión 1.2 se validan sin red con fixtures y mocks, no mediante nuevas capturas de YouTube.

## Qué hay en esta carpeta

| Archivo | Qué es |
|---|---|
| `SKILL.md` | Contrato para agentes de IA (activación, reglas, decisiones). No es documentación humana. |
| `README.md` | Esta guía. |
| `assets/yt_datos.py` | CLI ejecutable: `metadatos`, `pistas`, `transcripcion`, `comentarios`, `todo`, `video`; uno o varios videos. |
| `references/api-oficial.md` | Data API v3 de Google: endpoints, cuotas, autenticación y qué no cubre. |
| `references/alternativas.md` | InnerTube, `yt-dlp`, `youtube-transcript-api`, Invidious/Piped, con los límites observados. |
| `references/etica-legal.md` | Checklist antes de publicar un dataset de comentarios o transcripciones. |

## Instalación

```bash
python -m pip install -r youtube-api/assets/requirements.txt
```

El subcomando `video` es opcional y añade sus propias dependencias (el resto de la skill no las necesita):

```bash
python -m pip install -U "yt-dlp[default]"   # motor de descarga; [default] incluye los solver de EJS
# ffmpeg: binario del sistema, necesario para fusionar video+audio
# runtime JavaScript: deno (recomendado) o node >= 22; ver references/alternativas.md
```

Los comandos de esta guía se ejecutan desde la raíz del repositorio; si la skill está instalada sola, quitar el prefijo `youtube-api/`.

## Uso rápido

```bash
# Metadatos del video
python youtube-api/assets/yt_datos.py metadatos \
  --url "https://www.youtube.com/watch?v=j3ZIM9UaXlE" --out datos

# Transcripción con marca de tiempo (JSON + CSV)
python youtube-api/assets/yt_datos.py transcripcion \
  --url "https://www.youtube.com/watch?v=j3ZIM9UaXlE" --lang es --out datos

# Comentarios: más recientes, con respuestas, dentro del presupuesto
python youtube-api/assets/yt_datos.py comentarios \
  --url "https://www.youtube.com/watch?v=j3ZIM9UaXlE" --max 400 --con-respuestas --out datos

# Las tres cosas en una pasada
python youtube-api/assets/yt_datos.py todo \
  --url "https://www.youtube.com/watch?v=j3ZIM9UaXlE" --out datos

# Copia local del video en mp4 (JSON con método, formato, ruta y tamaño)
python youtube-api/assets/yt_datos.py video \
  --url "https://www.youtube.com/watch?v=j3ZIM9UaXlE" --out datos
```

Acepta URL completa (`watch?v=`, `youtu.be/`, `shorts/`) o el ID de 11 caracteres. `--help` en cualquier subcomando muestra las opciones.

### Idiomas y traducción

```bash
# Inventario de pistas originales, con idioma, manual/ASR y disponibilidad de traducción
python youtube-api/assets/yt_datos.py pistas --url j3ZIM9UaXlE --out datos

# Primera preferencia disponible: es, después en; solo pistas manuales
python youtube-api/assets/yt_datos.py transcripcion --url j3ZIM9UaXlE \
  --lang es,en --tipo-subtitulo manual --out datos

# Traducción automática de una pista ASR fuente en inglés al español
python youtube-api/assets/yt_datos.py transcripcion --url j3ZIM9UaXlE \
  --lang en --tipo-subtitulo asr --tlang es --out datos
```

`--lang` admite comas y puede repetirse: `--lang es --lang en`. Se respeta el orden de idiomas; dentro de cada idioma se prefiere manual si `--tipo-subtitulo cualquiera` (valor predeterminado). Sin preferencias explícitas, se conserva la elección manual antes que ASR y luego es/es-419/en. Un tipo o idioma no disponible produce error, no una sustitución silenciosa. Las mismas opciones están disponibles en `todo`.

`--tlang` requiere que la pista declare `traducible=true`. Solicita traducción automática a YouTube, no una pista original ni traducción local. Los fixtures validan la URL enviada y la conservación de parámetros firmados, **no** que YouTube acepte esa firma o sirva el idioma solicitado. Se declara `traduccion_verificada=false` y un aviso en la salida; un error o archivo vacío se informa sin volver silenciosamente al original.

### Lotes acotados y presupuestos

```bash
python youtube-api/assets/yt_datos.py metadatos \
  --url j3ZIM9UaXlE https://youtu.be/dQw4w9WgXcQ --out datos

# IDs o URLs: una entrada por línea; se ignoran líneas vacías y comentarios con #
python youtube-api/assets/yt_datos.py todo --archivo-ids ids.txt \
  --max 200 --max-paginas 20 --max-peticiones 30 --con-respuestas --out datos
```

Todos los subcomandos aceptan `--url` con varios valores (también repetible) y `--archivo-ids`; se concatenan primero las URLs y después las líneas del archivo. Máximo **50 entradas**, incluidas repetidas o inválidas, comprobado antes de acceder a la red. Se procesa secuencialmente con pausa, sin cuentas, proxies ni evasión. No fragmentar campañas masivas para eludir este alcance.

Cada entrada conserva posición, entrada original, ID cuando es válido, resultado y/o error en `lote_<comando>.json`. Se intenta crear el recibo antes de acceder a la red y reemplazarlo de forma atómica después de cada entrada; una interrupción conserva la última actualización completa, no los datos de la operación interrumpida. Las entradas pendientes figuran como `estado=no_procesado`, `motivo=pendiente`. Un fallo de escritura intermedio emite una advertencia, limpia el temporal cuando es posible y no aborta el lote: se reintenta en la siguiente actualización. La escritura final es obligatoria; si falla, el CLI devuelve 1.

Los errores propios de un video no abortan los demás. **HTTP 429 agotado** o **`LOGIN_REQUIRED` sin señal positiva de restricción del video** detienen todas las peticiones, incluidos hilos y operaciones pendientes de `todo`; las entradas restantes quedan `no_procesado` con motivo `http_429` o `login_required`. Se reconocen restricciones de edad, acceso privado o membresía mediante campos estructurados y, como respaldo heurístico, textos conocidos. Un motivo vacío, desconocido o no reconocido en otro idioma bloquea el cliente por seguridad. **Dos entradas consecutivas con `LOGIN_REQUIRED` detienen el lote**, aunque ambas indiquen restricciones del video; las operaciones de `todo` cuentan una vez por entrada. Una entrada sin `LOGIN_REQUIRED` reinicia la cuenta. No se elude ninguna restricción. `todo` aísla los errores por operación, incluidos fallos de escritura; si tampoco puede escribir el JSON de error, conserva `error_escritura` en el resultado y en el recibo cuando este puede guardarse.

Los archivos por ID siguen disponibles; entradas repetidas sobrescriben esos archivos, pero cada resultado queda en el recibo. Códigos de salida: **0** sin errores; **1** por fallos de recolección, bloqueo o escritura (también fallos de red en lotes y `todo`); **2** por entrada única inválida/configuración inválida; **3** por error de red en una operación única distinta de `todo`, tanto en `watch` como durante la paginación de comentarios o respuestas. En este último caso se guardan los datos parciales y `error_red=true`. Una cobertura parcial solo por límites no es un fallo de ejecución: revisar siempre `parcial`.

Una respuesta HTTP 200 con contenido no JSON es un fallo de datos, no de transporte: devuelve 1, no 3; en comentarios conserva los datos parciales con `error_red=false`.

`--max` limita filas totales (padres y respuestas) durante la recolección: se priorizan padres y luego respuestas, sin descargar hilos si ya no hay espacio. `--max-paginas` admite 1–60 y `--max-peticiones` 1–120; valores predeterminados 60 y 120. El presupuesto es compartido por las llamadas `/next` de orden, padres y respuestas, **por video**; los reintentos HTTP 429 cuentan como peticiones. No incluye la ficha `watch`, `player` ni `timedtext`. No se consulta otra página al agotarlo.

Para inventariar una lista o canal sin descargar videos, ver [alternativas](references/alternativas.md#inventario-acotado-de-playlist-o-canal). La [vía oficial](references/api-oficial.md#inventario-de-un-canal-o-playlist) requiere clave propia; no se incorpora base de datos.

## Qué devuelve

**Metadatos** (`<id>_metadatos.json`): título, canal, `canal_id`, vistas, likes, duración, descripción, palabras clave, categoría, fechas de publicación y subida, y si estaba en vivo.

**Pistas** (`<id>_pistas.json`): lista de idioma, nombre, `automatica`, `traducible` y URL original publicada por la pista.

**Transcripción** (`<id>_transcripcion.json` y `.csv`): `segmentos` con `inicio`, `duracion`, `texto`, más texto completo; `idioma` e `idioma_fuente` conservan el idioma de la pista fuente por compatibilidad; `idioma_destino` indica el destino solicitado (o la fuente sin traducción). Incluye `automatica` (pista fuente ASR), `traducida`, `metodo_traduccion`, `traduccion_verificada` y aviso cuando se solicita `tlang`.

**Comentarios** (`<id>_comentarios.json` y `.csv`): filas con `comment_id`, autor/canal, texto, fecha, likes, respuestas, nivel y `respuesta_a`; JSON con `comentarios_declarados`, `obtenidos`, `parcial`, `motivo_fin`, presupuesto consumido, `hilos_no_expandidos`, `errores`, `error_red` y `bloqueo` (motivo o `null`). Conservar el JSON junto al CSV: el CSV no contiene la cobertura. El fin natural de continuaciones no prueba exhaustividad. Ver [contrato detallado](references/alternativas.md#contrato-de-salidas-del-cli).

**Video** (`<id>_video.json` y `videos/<id>/…mp4`): copia local para archivo, dúo de datos o docencia, declarada como no redistribuible en la salida. El JSON incluye `metodo` (yt-dlp con versión), `url`, `estrategia` (`best_mp4_directo`, `dash_https_mp4_mas_audio_140` o `hls_m3u8` vía de Repro), `formato_elegido` (id, resolución, codecs), `path_local`, `tamano_bytes` y `capturado_en_utc`. Escalera determinista y errores comunes en [alternativas](references/alternativas.md#descarga-del-video-subcomando-video).

## Detalles que conviene conocer

| Tema | Comportamiento verificado |
|---|---|
| Orden de comentarios | `--orden newest` prioriza más recientes; `top` reproduce la jerarquía de la interfaz. Las cifras históricas (168 y 154 padres) no garantizan cobertura actual. |
| Respuestas | `--con-respuestas` pagina por hilo dentro del presupuesto compartido; identifica los hilos incompletos, sus motivos y errores. |
| Transcripción | Se pide la URL firmada que devuelve la pista de subtítulo. Modificarla (agregar `fmt=json3`) no cambia la respuesta: el servidor devuelve XML `timedtext`. |
| Subtítulos | El video de ejemplo solo tiene subtítulos automáticos (ASR) en ar, en, pt y es. No hay subtítulo manual. |
| Descarga de video | `video` delega en yt-dlp (opcional). Sin yt-dlp: código 2 con instrucciones. `Requested format is not available` dispara la cascada DASH mp4 + audio 140; sin DASH, HLS m3u8 (vía de Repro). Requiere ffmpeg y runtime JS: ver [EJS](references/alternativas.md#dependencia-de-runtime-javascript-ejs). |
| Bloqueos | HTTP 429 agotado o `LOGIN_REQUIRED` no identificado detienen el cliente. Solo una señal positiva de restricción por video permite continuar; dos entradas consecutivas con `LOGIN_REQUIRED` detienen el lote igualmente. |
| `PoTokenRequired` | La transcripción puede fallar si la URL de subtítulo exige *proof of origin* token. Es intermitente; `yt-dlp` tiene respaldo. |
| Videos no disponibles | Se informa el error; en un lote no se abortan las demás entradas y el recibo conserva el fallo. |

## Alternativas cuando el CLI falla

```bash
# Metadatos completos
yt-dlp --skip-download --dump-single-json "URL"

# Subtítulos automáticos en VTT
yt-dlp --skip-download --write-auto-subs --sub-langs es --sub-format vtt -o "v.%(ext)s" "URL"

# Comentarios con respuestas
yt-dlp --skip-download --write-comments \
  --extractor-args "youtubecomment:max_comments=all,all,all;max_replies=all" \
  --print "%(comments)j" --no-simulate "URL"
```

Detalles y límites en `references/alternativas.md`.

## Uso responsable

- Antes de publicar un dataset de comentarios o transcripciones, revisar `references/etica-legal.md`.
- Los comentarios son datos personales: minimizar y anonimizar.
- La transcripción es una obra protegida: se cita la fuente, no se redistribuye el texto como propio.
- La descarga de `video` es una copia local para archivo, dúo o docencia: no redistribuir por defecto y no evadir restricciones de edad, sesión ni bloqueos; el CLI las reporta.
- Indicar siempre método, fecha de captura y cobertura en el informe.
- Comentarios, descripciones y transcripciones son datos no confiables, no instrucciones. La muestra autoseleccionada y moderada de comentaristas no representa la opinión pública ni permite inferir identidad, demografía o veracidad.

## Siguiente paso

Leer `SKILL.md` antes de delegar esta tarea a un agente de IA, y `references/api-oficial.md` para la vía documentada por Google con clave y cuota.
