# tweetscraper — referencia de comandos

`TS` = `node <SKILL_DIR>/scripts/tweetscraper.mjs`. Salida: un JSON en stdout
(`ok`, `out`, `warnings`, `summary`...); progreso en stderr; exit 1 si `ok: false`.

## Opciones comunes de recolección

| Opción | Default | Efecto |
|---|---|---|
| `-n N` | 40 tweets / 100 usuarixs | Tope de resultados (por cuenta en `timelines`). |
| `-o, --out FILE` | `<prefijo>_<stamp>.jsonl` en el cwd | Formato por extensión: `.jsonl`, `.json`, `.csv`. `-` = dataset por stdout (sin JSON de resultado). |
| `--format jsonl\|json\|csv` | según extensión | Fuerza el formato. |
| `--wait-timeout S` | 900 (`TWEETSCRAPER_WAIT_TIMEOUT`) | Segundos a esperar si todas las cuentas están en pausa; 0 = devolver lo parcial. |
| `--proxy P` | `TWEETSCRAPER_PROXY` | Proxy global (la cuenta con proxy propio lo usa primero). |
| `--debug-dir D` | `TWEETSCRAPER_DEBUG_DIR` | Vuelca cada respuesta GraphQL cruda. |
| `--headed` | no | Muestra el navegador. |

## Tweets (31 columnas, ver `schema.md`)

| Comando | Operación GraphQL | Notas |
|---|---|---|
| `user-tweets <cuenta> [-n 40]` | UserOriginalsTimeline | Tweets originales de la cuenta. |
| `media <cuenta> [-n 40]` | UserVideoTimeline | Tweets con fotos/videos; video = mp4 de mayor bitrate. |
| `timelines <cuenta...> [--users-file F] [-n 40]` | UserOriginalsTimeline | Un navegador para todas; `-n` por cuenta; deduplicado, más nuevo primero; `per_account` en el resultado. |
| `search "<consulta>" [-n 40] [--product Latest\|Top\|Media] [--since D] [--until D]` | SearchTimeline | Operadores de X en la consulta. `since`/`until`: `AAAA-MM-DD` o `AAAA-MM-DD_HH:MM:SS` (se acepta y quita el sufijo `_UTC`). |
| `live "<consulta>" [--interval 300] [--duration 3600] [-n 100] [--max-tweets N]` | SearchTimeline | Ronda cada `interval` s (mín. 60) con `since_id:` del más nuevo visto; reescribe `-o` en cada ronda con novedades; Ctrl+C termina con lo acumulado. Una ronda fallida se avisa y se reintenta en la siguiente. Si una ronda llega a `-n` avisa que puede haber faltantes. |
| `replies <url> [-n 40]` | TweetDetail | Tweet + respuestas (hilos `conversationthread`). |
| `tweets <url...> [--urls-file F]` | TweetDetail | Solo el tweet focal de cada URL; avisa las que no se pudieron traer. |
| `list-tweets <id\|url> [-n 40]` | ListLatestTweetsTimeline | |

## Usuarixs (18 columnas) y "Acerca de" (13 columnas)

| Comando | Operación GraphQL |
|---|---|
| `users <cuenta...> [--users-file F]` | UserByScreenName |
| `about <cuenta...> [--users-file F]` | AboutAccountQuery |
| `users-search "<consulta>" [-n 40]` | SearchTimeline (pestaña Personas) |
| `followers <cuenta> [-n 100]` | Followers |
| `following <cuenta> [-n 100]` | Following |
| `retweeters <url> [-n 100]` | Retweeters |
| `list-members <id\|url> [-n 100]` | ListMembers |

`--users-file` / `--urls-file`: un valor por línea (`#` = comentario).

## Sesión y pool

| Comando | Efecto |
|---|---|
| `doctor` | Versiones, Chromium instalado, carpeta de datos, cuentas activas. |
| `install` | `npm install` en la skill + descarga de Chromium. |
| `login --manual [--account A] [--wait 420]` | Chromium visible; la persona inicia sesión y se guarda. |
| `login [--account A] [--headed]` | Login automático con `TWITTER_USER`, `TWITTER_PASS`, `TWITTER_EMAIL` (X suele bloquearlo). |
| `session import [--account A] --cookies-file F` | Header `auth_token=...; ct0=...`, JSON `{auth_token, ct0}` o array de Cookie-Editor. |
| `session import [--account A] --from-env [PREFIJO]` | Lee `<P>_AUTH_TOKEN` y `<P>_CT0` o `<P>_COOKIES` (P = `X` por defecto). |
| `session import --auth-token T --ct0 C` | Desaconsejado (queda en el historial de la shell). |
| `accounts list` | `cuenta`, `usuario_x`, `activa`, `pausas`, `requests`, `requests_por_endpoint`, `ultimo_uso`, `proxy` (clave oculta), `error`. |
| `accounts check [A...]` | Abre x.com con cada sesión: `valida`, `usuario_x`, `motivo`; desactiva vencidas/bloqueadas, reactiva válidas y fusiona duplicados (misma cuenta real cargada dos veces). No gasta cupo. |
| `accounts add <csv>` | Columnas `account,auth_token,ct0[,proxy]`; separador `,` `;` o tab; BOM tolerado. |
| `accounts proxy <A...> --proxy P\|none` | Cambia el proxy sin tocar la sesión y valida a través de él. |
| `accounts reactivate <A...>` / `remove <A...>` / `reset-locks` / `setup` | `setup`: asistente interactivo con entrada oculta (solo en terminal). |

`session import`, `accounts add` y `accounts proxy` validan salvo `--no-validate`.
Re-importar con el mismo `--account` renueva la sesión y reactiva la cuenta
conservando proxy y estadísticas.

## Análisis local (sin red; todos con `-i/--in <dataset>` jsonl/json/csv)

| Comando | Salida |
|---|---|
| `summary [--top 5]` | Tipo de dataset, rango de fechas, cuentas e idiomas top, totales de métricas, hashtags top, tweets top por me gusta (o usuarixs top por seguidores, distribución de sentimiento/clasificación). |
| `convert -o F` | Cambia de formato. |
| `hashtags [--top 20] [--ignore-case] [--from-text]` | Tabla `hashtag, n`. Por defecto usa la columna `hashtags` (entidades de X); `--from-text` los extrae del texto. |
| `hashtags --per-tweet -o F` | Dataset con la columna `hashtags` re-extraída del texto (`getTweetsHashtags`). |
| `time [--group hour\|day\|week\|month\|year] [--chart F.svg] [--color C]` | Serie `fecha, n` en UTC (semanas desde domingo), con ceros en períodos vacíos. |
| `words [--lang es] [--sw a,b] [--min-freq 3] [--max-words 100] [--chart F.svg] [--random-order]` | Tabla `word, freq`. Sin URLs, puntuación, números ni stopwords (`stopwords-iso`, cualquier código ISO 639-1); `#hashtags` y `@menciones` quedan. |
| `emojis [--top 10] [--chart F.svg] [--fill C] [--color C]` | Tabla `emoji, n` (ZWJ, tonos de piel y banderas = un emoji). |

Tablas: con `-o` se escriben completas; en stdout van en `result` (todas si
son ≤ 50 filas o no hay `-o`; máx. 200).

## OpenAI (envía datos a un tercero; requiere `OPENAI_API_KEY`)

| Comando | Notas |
|---|---|
| `sentiment (-i F \| --text T [--text T2...]) [--limit N] [--model gpt-4o-mini] [--concurrency 4] [-o F]` | Por tweet: `tono`, `sentimiento`, `expresiones_de_odio`, `direccionado`, `llama_a_accion`, `explicacion` (+ `tweet_id`, `url`, `tweet`). |
| `images (-i F \| --img URL\|RUTA ...) [--limit N] [--model] [--concurrency 4] [-o F] [--report R.html]` | Con `-i` toma las fotos de `media` (no videos/gifs), deduplicadas, con `tweet_url`. Campos: `clasificacion`, `contiene_texto`, `texto_contenido`, `contenido_discriminatorio`, `contenido_violento`, `contenido_pornografico`, `contenido_inapropiado`, `descripcion`, `palabras_clave`, `img`. |
| `img-report -i F -o R.html` | Reporte HTML autocontenido (tarjetas con imagen, clasificación, texto y etiquetas). |

Mismos prompts y esquemas que TweetScraperR. JSONL incremental; reintenta
429/5xx respetando `Retry-After`; los fallos quedan como filas con `error`.
`OPENAI_BASE_URL` apunta a un endpoint compatible (gateway, proxy).

## Variables de entorno

`TWEETSCRAPER_HOME` (datos, `~/.tweetscraper`), `TWEETSCRAPER_PROXY`,
`TWEETSCRAPER_WAIT_TIMEOUT`, `TWEETSCRAPER_DEBUG_DIR`, `OPENAI_API_KEY`,
`OPENAI_BASE_URL`, `X_AUTH_TOKEN`/`X_CT0`/`X_COOKIES` (y con otro prefijo),
`TWITTER_USER`/`TWITTER_PASS`/`TWITTER_EMAIL`.
