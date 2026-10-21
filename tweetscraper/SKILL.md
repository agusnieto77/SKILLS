---
name: tweetscraper
description: "Recolecta y analiza datos de X/Twitter con herramientas Node.js (port de TweetScraperR): tweets de cuentas, búsquedas con operadores y fechas, captura en vivo, respuestas/hilos, tweets por URL, media, Listas, perfiles, ficha 'Acerca de', seguidores, seguidos, retuiteadores; series temporales, nubes de palabras, emojis, hashtags, sentimiento e imágenes (OpenAI). Usala cuando la persona pide scrapear, buscar, monitorear o analizar tweets o usuarixs de X/Twitter, o tiene problemas de sesión, cookies, cuentas o rate limits de X. Use for collecting or analyzing X/Twitter posts and users."
license: Apache-2.0
compatibility: Node.js >= 22.13 con npm; Chromium lo descarga Playwright en `install`. Funciona en cualquier cliente de Agent Skills con shell.
metadata:
  author: Agustín Nieto
  version: "1.0.0"
  based_on: TweetScraperR 0.8.1.9000 (https://github.com/agusnieto77/TweetScraperR)
---

# tweetscraper — X/Twitter desde un agente

Traducís pedidos en lenguaje natural ("traeme los últimos 200 tweets de la NASA
y graficá su actividad por día") a comandos del CLI de esta skill, los ejecutás
y explicás el resultado. Es el port a Node.js de TweetScraperR: mismo motor
(Playwright + sesión real de X, cosechando el JSON GraphQL que dispara la app),
mismo pool de cuentas con rotación por cupo y **mismas columnas** que el paquete
de R (`fecha`, `texto`, `megustas`...), así los datos son intercambiables.

Todos los comandos: `node <SKILL_DIR>/scripts/tweetscraper.mjs <comando> ...`
(abajo, `TS`). Corrélos **desde la carpeta de trabajo de la persona**: ahí se
escriben los datos. Referencias: `references/commands.md` (todas las opciones)
y `references/schema.md` (todas las columnas). Leelas cuando necesites una
opción o columna que no figura acá.

## Contrato de salida

- **stdout = un solo JSON** por corrida: `{"ok": true, ...}` o
  `{"ok": false, "error": "..."}` (exit 1). Progreso y avisos van a stderr.
- Los **datasets se escriben a archivo** (`-o archivo.jsonl|.json|.csv`; sin
  `-o`: `<prefijo>_<AAAA_MM_DD_HH_MM_SS>.jsonl` en el directorio actual). El
  JSON de stdout trae `out` (ruta), `warnings` y un `summary` compacto (filas,
  rango de fechas, cuentas top, totales, tweets top). **No leas el archivo
  entero**: usá `summary`, los comandos de análisis o un `node -e` puntual.
- `warnings` no vacío = resultado parcial o cuenta pausada/desactivada:
  contáselo a la persona.

## Reglas de conversación

1. Respondé en el idioma de la persona. Las columnas están en español.
2. **Antes de recolectar, confirmá lo que falte**: cuenta/consulta/URL y
   cantidad (`-n`). Sin cantidad, usá el default y decilo. Una pregunta por turno.
3. Mostrá siempre el comando que corriste, para que sea reproducible.
4. Resumí, no vuelques: filas, rango de `fecha`, 3-5 tweets destacados con URL.
5. **Pedidos grandes**: X limita cada endpoint por cuenta en ventanas de 15
   minutos (búsqueda ~50 consultas). Con una cuenta, al agotarse el cupo se
   espera hasta 15 min (`--wait-timeout 0` devuelve lo parcial sin esperar).
   Para más de ~500 tweets o ~1000 usuarixs proponé sumar cuentas al pool o
   partir en tramos con `--since`/`--until`.
6. **Secretos**: nunca pidas que peguen cookies, contraseñas ni claves en el
   chat, ni las pongas en argumentos visibles. Ver "Sesión de X".
7. **Uso responsable**: son datos de personas reales; sugerí no redistribuir
   datos personales y respetar los términos de X. `sentiment` e `images`
   **envían contenido a OpenAI**: avisalo y pedí confirmación antes de correrlos.

## Puesta a punto (una vez por máquina)

```bash
TS doctor           # ¿Node, Playwright y Chromium OK? ¿cuántas cuentas activas?
TS install          # si doctor da playwright null o chromiumInstalled false
```

`doctor` con `ok: true` y `accounts_active >= 1` = listo para recolectar.
Datos (sesiones y pool) en `~/.tweetscraper` (o `TWEETSCRAPER_HOME`).

### Sesión de X (obligatoria para recolectar)

X bloquea casi siempre el login automatizado; las vías, en orden de preferencia:

1. **Login manual en ventana** (nada sensible pasa por el chat):
   `TS login --manual [--account nombre]` abre Chromium; la persona inicia
   sesión ahí y la sesión se guarda sola (espera hasta 7 min, `--wait`).
2. **Cookies de su navegador** (si X rechaza el login en la ventana): la
   persona copia `auth_token` y `ct0` (F12 → Application/Almacenamiento →
   Cookies → `https://x.com`) y las deja en un archivo
   (`auth_token=...; ct0=...` o el JSON de Cookie-Editor) o en variables de
   entorno `X_AUTH_TOKEN`/`X_CT0`. Vos corrés
   `TS session import --cookies-file ruta` o `TS session import --from-env`.
   Al terminar, sugerí borrar el archivo.
3. **Asistente de consola** que corre la persona en su terminal (entrada
   oculta, carga varias cuentas): `TS accounts setup`.

`session import` valida la sesión al importarla (`valida`, `usuario_x`). Hay
que repetirlo solo cuando expira. `TS login` (automático, lee `TWITTER_USER`,
`TWITTER_PASS`, `TWITTER_EMAIL`) solo si la persona lo pide.

### Pool de cuentas (opcional)

Con varias cuentas la recolección rota sola: la que agota el cupo de un
endpoint queda en pausa y se sigue con otra **desde el mismo cursor**; la que X
rechaza se desactiva.

```bash
TS session import --from-env X2 --account cuenta2   # lee X2_AUTH_TOKEN / X2_CT0
TS accounts add cuentas.csv          # columnas account, auth_token, ct0, proxy (sep , ; o tab)
TS accounts list                     # activas, pausas por endpoint, requests, errores
TS accounts check                    # valida cada sesión y muestra su @usuario real
TS accounts proxy cuenta2 --proxy http://usuario:clave@host:puerto   # none lo quita
TS accounts reactivate cuenta2 | TS accounts reset-locks | TS accounts remove cuenta2
```

Proxy global: `--proxy` o `TWEETSCRAPER_PROXY`. Usar la dirección HTTP del
proveedor: Chromium no admite SOCKS5 con usuario y clave.

## De la intención al comando

| La persona quiere... | Comando (función de TweetScraperR) |
|---|---|
| Tweets de una cuenta | `TS user-tweets NASA -n 40` (`getUserTweetsAPI`) |
| Timeline combinado de varias cuentas | `TS timelines NASA ESA -n 40` (n por cuenta; `--users-file`) (`getTweetsTimelinesAPI`) |
| Buscar por palabra, hashtag, cuenta, idioma o fechas | `TS search "#RStats lang:es" -n 40 --product Latest --since 2026-01-01 --until 2026-02-01` (`getTweetsSearchAPI`) |
| Seguir una búsqueda en vivo | `TS live "#RStats" --interval 300 --duration 3600` (`getTweetsLiveAPI`) |
| Respuestas / hilo de un tweet | `TS replies <url> -n 40` (`getTweetsRepliesAPI`) |
| Datos de tweets puntuales por URL | `TS tweets <url> [<url>...]` o `--urls-file` (`getTweetsDataAPI`) |
| Tweets con fotos/videos de una cuenta | `TS media NASA -n 40` (`getUserMediaAPI`) |
| Perfil(es): seguidores, bio, creación | `TS users NASA ESA` (`getUsersDataAPI`) |
| País de la cuenta, cambios de nombre, verificación | `TS about NASA` (`getUsersAboutAPI`) |
| Buscar cuentas por tema o nombre | `TS users-search "ciencia de datos" -n 40` (`getUsersSearchAPI`) |
| Seguidorxs / cuentas que sigue | `TS followers NASA -n 100` / `TS following NASA -n 100` |
| Quién retuiteó un tweet | `TS retweeters <url> -n 100` (`getTweetsRetweetsAPI`) |
| Tweets / miembros de una Lista | `TS list-tweets <id|url> -n 40` / `TS list-members <id|url> -n 100` |
| Panorama de un dataset | `TS summary -i datos.jsonl` |
| Actividad en el tiempo | `TS time -i datos.jsonl --group day --chart actividad.svg` (`plotTime`) |
| Nube de palabras | `TS words -i datos.jsonl --lang es --sw rt,via --chart nube.svg` (`plotWords`) |
| Emojis más usados | `TS emojis -i datos.jsonl --top 10 --chart emojis.svg` (`plotEmojis`/`plotEmojisPNG`) |
| Hashtags más frecuentes / por tweet | `TS hashtags -i datos.jsonl --ignore-case` / `--per-tweet --from-text -o con_hashtags.jsonl` (`getTweetsHashtags`) |
| Sentimiento / discurso de odio (OpenAI) | `TS sentiment -i datos.jsonl -o sentimiento.jsonl` (`getTweetsSentiments`) |
| Clasificar imágenes (OpenAI) + reporte | `TS images -i datos.jsonl --limit 20 --report reporte.html` (`getTweetsImagesAnalysis` + `HTMLImgReport`) |
| Pasar a CSV/Excel o JSON | `TS convert -i datos.jsonl -o datos.csv` |

Notas:

- Cuentas: `NASA`, `@NASA` o la URL del perfil. Tweets: URL de x.com o
  twitter.com (con o sin `?s=...`) o el id numérico. Listas: id o URL.
- `search` acepta los operadores de X dentro de la consulta: `from:`, `to:`,
  `#hashtag`, `lang:es`, `"frase exacta"`, `-palabra`, `min_faves:100`,
  `filter:media`, `-filter:retweets`, `OR`. `--product`: `Latest` (recientes),
  `Top` (destacados), `Media`. `--since`/`--until`: `AAAA-MM-DD` o
  `AAAA-MM-DD_HH:MM:SS`. **Una sola consulta: entre comillas.**
- `live` reescribe el archivo en cada ronda con tweets nuevos (nada se pierde
  si se corta); Ctrl+C termina devolviendo lo acumulado. Mínimo 60 s entre rondas.
- Los gráficos son **SVG autocontenidos** (se abren en el navegador). `time`
  agrupa en **UTC** y completa con 0 los períodos sin tweets.
- `sentiment` e `images` escriben el JSONL **a medida que avanzan** y siguen
  ante errores puntuales (fila con `error`); `failed` cuenta cuántas fallaron.
  Requieren `OPENAI_API_KEY` en el entorno (nunca en el chat). `images` toma
  solo fotos (no videos ni gifs).

## Recetas

Actividad de una cuenta por día:

```bash
TS user-tweets NASA -n 200 -o nasa.jsonl
TS time -i nasa.jsonl --group day --chart nasa_por_dia.svg
```

Tweets más difundidos de una búsqueda (sin leer el archivo entero):

```bash
TS search "#RStats lang:es" -n 300 --since 2026-01-01 -o rstats.jsonl
node -e "const r=require('fs').readFileSync('rstats.jsonl','utf8').trim().split('\n').map(JSON.parse);r.sort((a,b)=>b.retweets-a.retweets).slice(0,10).forEach(t=>console.log(t.retweets,t.user,t.url))"
```

Red de seguidorxs con perfil completo, ordenada por seguidores:

```bash
TS followers rstatstweet -n 200 -o seg.jsonl && TS summary -i seg.jsonl --top 10
```

Imágenes de una cuenta con reporte HTML (avisar: envía imágenes a OpenAI):

```bash
TS media NASA -n 50 -o nasa_media.jsonl
TS images -i nasa_media.jsonl --limit 10 -o nasa_img.jsonl --report reporte_imagenes.html
```

Llevarlo a R: `jsonlite::stream_in(file("nasa.jsonl"))` da las mismas columnas
que TweetScraperR (las fechas llegan como texto ISO UTC: `lubridate::ymd_hms()`).

## Errores frecuentes

| `error` / aviso | Qué hacer |
|---|---|
| "There is no active X session" | Importar sesión (ver "Sesión de X"). |
| "Your X session seems to have expired" / cuenta "disabled: session expired" | Cookies vencidas: `login --manual` o reimportar cookies frescas con el mismo `--account`. |
| "All accounts are paused for <op> until HH:MM:SS" | Cupo de X agotado en todas las cuentas: resultado parcial. Esperar o sumar cuentas. |
| "X limited or suspended the account (error 88...)" | La cuenta está limitada: revisarla en x.com; seguir con otras. |
| "account locked by X (error 326)" | Desbloquearla en x.com/account/access y `accounts reactivate`. |
| "X returned a block page" | Bloqueo de IP/Cloudflare: pausa 15 min; considerar proxy. |
| "The Playwright engine is not installed" | `TS install`. |
| "could not connect through the proxy" | Revisar dirección/credenciales o `accounts proxy <cuenta> --proxy none`. |
| "An OpenAI API key is required" | Definir `OPENAI_API_KEY` en el entorno. |
| `ok: true` con 0 filas | Cuenta privada, inexistente o sin tweets en ese rango; verificar el nombre/consulta. |

Menos filas que `-n` no es error: X entrega lo que tiene para esa consulta.
Si X cambia su JSON y un comando deja de traer campos, `--debug-dir carpeta`
vuelca cada respuesta cruda para diagnosticar.
