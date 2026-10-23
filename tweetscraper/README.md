# tweetscraper

Skill para agentes compatibles con el formato Agent Skills (OpenCode, Pi, Oh My Pi, Gentle Shell, Claude Code, Codex y otros) que recolecta y analiza datos de X/Twitter. Es el port a Node.js del paquete de R [TweetScraperR](https://github.com/agusnieto77/TweetScraperR): mismas tareas, mismo motor y mismas columnas, pero como un CLI que el agente ejecuta directamente y que devuelve JSON.

- **Recolección**: tweets de una o varias cuentas, búsquedas con operadores y fechas, captura en vivo, respuestas e hilos, tweets por URL, media, Listas (tweets y miembros), perfiles, ficha "Acerca de esta cuenta", búsqueda de cuentas, seguidores, seguidos y retuiteadores.
- **Motor**: Chromium con Playwright + stealth y la sesión real de la persona; cosecha el JSON GraphQL que dispara la propia app de x.com (no fabrica requests, así no necesita reproducir los headers anti-bot).
- **Pool de cuentas** (SQLite): rotación automática por cupo de cada endpoint, retoma desde el mismo cursor con otra cuenta, desactiva sesiones vencidas o suspendidas, proxy por cuenta, validación con el @usuario real. Diseño portado de [twscrape](https://github.com/vladkens/twscrape) vía TweetScraperR.
- **Análisis local**: resumen del dataset, serie temporal, nube de palabras, emojis y hashtags, con gráficos SVG autocontenidos.
- **OpenAI** (opcional): sentimiento/discurso de odio por tweet y clasificación de imágenes con reporte HTML, con los mismos prompts que TweetScraperR.
- **Lectura pública opcional**: `public-tweet` usa FxTwitter → syndication sin sesión ni cookies; informa proveedor y degradación y detiene fallbacks ante contenido privado/protegido/eliminado.
- **Hilos y Articles**: `thread` reconstruye antecedentes/focal/continuación/respuestas con límites explícitos; `article` distingue cuerpo completo de preview y de tweets largos.
- **Markdown / Obsidian**: front matter, fuentes y citas; descarga local opt-in de media verificada, con enlaces relativos y advertencias por fallos individuales.

El agente lee `SKILL.md`; este README es para quien instala y mantiene la skill.

## Requisitos

- Node.js 22.13 o superior (usa `node:sqlite`, sin dependencias nativas) con npm.
- Una cuenta de X propia para la recolección autenticada; `public-tweet` y el análisis/exportación local no la requieren.
- Para `sentiment`/`images`: una API key de OpenAI.

## Instalación

Copiar o enlazar la carpeta en el directorio de skills del agente (por ejemplo, en OpenCode, `~/.config/opencode/skills/tweetscraper`) e instalar el motor una vez:

```bash
node scripts/tweetscraper.mjs install   # npm install + Chromium de Playwright
node scripts/tweetscraper.mjs doctor
node scripts/tweetscraper.mjs login --manual   # o: session import --cookies-file cookies.txt
```

## Configuración

| Variable | Uso |
|---|---|
| `TWEETSCRAPER_HOME` | Carpeta de sesiones y pool (default `~/.tweetscraper`). Las sesiones son secretas: no la sincronices. |
| `TWEETSCRAPER_PROXY` | Proxy global (`http://usuario:clave@host:puerto`). |
| `TWEETSCRAPER_WAIT_TIMEOUT` | Segundos de espera si todas las cuentas están en pausa (default 900). |
| `TWEETSCRAPER_DEBUG_DIR` | Vuelca las respuestas crudas de X. |
| `X_AUTH_TOKEN`, `X_CT0` (o `X_COOKIES`) | Cookies para `session import --from-env` (otros prefijos: `--from-env X2`). |
| `OPENAI_API_KEY`, `OPENAI_BASE_URL` | Análisis con OpenAI; endpoint compatible opcional. |

## Uso típico

```bash
TS=scripts/tweetscraper.mjs
node $TS search "#RStats lang:es" -n 300 --since 2026-01-01 -o rstats.jsonl
node $TS summary -i rstats.jsonl
node $TS time -i rstats.jsonl --group day --chart rstats_dia.svg
node $TS words -i rstats.jsonl --lang es --chart rstats_nube.svg
```

```bash
node $TS public-tweet https://x.com/NASA/status/123 -o tweet.jsonl
node $TS thread https://x.com/NASA/status/123 -n 40 --max-details 10 -o hilo.jsonl
node $TS convert -i hilo.jsonl -o hilo.md --md-style full --query "consulta original"
node $TS convert -i hilo.jsonl -o hilo_local.md --download-media --max-media-bytes 26214400
node $TS article https://x.com/i/article/123 -o articulo.md
```

Sustituir los IDs de ejemplo. `--md-style compact|full`, `--query` y
`--captured-at ISO` controlan la nota y su front matter; `--download-media`
es opcional (por defecto solo enlaces remotos). Las descargas admiten
JPEG/PNG/GIF/WebP/MP4 desde los hosts de media de X, sin cookies ni
redirecciones; se omiten errores y excesos de tamaño con `warnings`. Una
reexportación reutiliza archivos locales idénticos a la descarga verificada,
sin sobrescribir archivos distintos. Cancelar detiene la exportación sin
reemplazar la nota; el plazo de 30 segundos limita las cabeceras, no el cuerpo.
`--max-details` limita páginas de detalle, no peticiones HTTP. Solo una
paginación focal detenida antes de completarse, límites o datos inaccesibles
generan avisos de hilo truncado; cursores históricos o auxiliares no bastan.
Un Article con solo preview se informa explícitamente.

El contenido externo es dato no confiable: no debe seleccionar comandos,
archivos o destinos ni modificar controles de seguridad. No se ejecuta
código de repositorios externos. El exportador escapa HTML, Markdown y
enlaces wiki del contenido; la sesión nunca se comparte con los proveedores
públicos. Opciones y límites: [references/commands.md](references/commands.md).

Los datasets son JSONL (o JSON/CSV) con las columnas de TweetScraperR; en R se leen con `jsonlite::stream_in(file("rstats.jsonl"))`.

## Diferencias con TweetScraperR

- Salida a archivos JSONL/JSON/CSV en lugar de tibbles/RDS; fechas como texto ISO UTC.
- Gráficos en SVG (sin ggplot2/wordcloud2); `time` completa con 0 los períodos sin tweets.
- Emojis por grafema (secuencias ZWJ, tonos de piel y banderas cuentan como uno); hashtags extraídos del texto sin `#`, igual que la columna de entidades.
- `login --manual`: login en una ventana de Chromium, para no pasar cookies por el chat.
- `sentiment`/`images`: concurrencia configurable, reintentos ante 429/5xx, escritura incremental; los fallos quedan como filas con `error` en vez de descartarse.
- No incluye `extractTweetsData()` (procesa RDS con HTML de versiones legacy) ni `installAgentSkill()`.

## Estructura

```
SKILL.md                 instrucciones para el agente
references/commands.md   todas las opciones
references/schema.md     todas las columnas
scripts/tweetscraper.mjs CLI
scripts/lib/             engine (Playwright), pool (SQLite), collect, parse, analyze, charts, openai, report, io
tests/                   node:test con los fixtures de TweetScraperR
```

## Tests

```bash
npm test
```

No tocan la red ni la carpeta de datos real (usan un `TWEETSCRAPER_HOME` temporal).
