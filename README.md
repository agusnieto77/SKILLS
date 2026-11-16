# SKILLS

[![tests](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml/badge.svg)](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml)

**Español** | [English](README.en.md)

Skills para agentes orientadas a la investigación y el trabajo académico. Cubren tres momentos del flujo de investigación:

- **Escribir y citar:** auditar, normalizar y verificar las citas de un manuscrito contra una biblioteca de Zotero.
- **Recolectar datos de la web:** reunir datos públicos de X/Twitter, YouTube, cualquier sitio WordPress, la prensa histórica española (Prensa Histórica) y la jurisprudencia española (CENDOJ) en conjuntos de datos verificados y reproducibles en JSON, CSV y Markdown, con cobertura explícita, límites de solicitudes y controles éticos.
- **Informar la actividad de investigación:** cargar las publicaciones y demás antecedentes propios en el banco de datos de SIGEVA CONICET, verificados registro por registro, con un mapa del sitio que se actualiza solo.

Siguen el formato abierto [Agent Skills](https://agentskills.io), por lo que funcionan con cualquier agente compatible: OpenCode, Pi, Oh My Pi, Gentle Shell, Claude Code, Codex, Gemini CLI, Cursor y otros.

| Área | Skill | Qué hace |
|---|---|---|
| Citas | [`zotero-citations`](zotero-citations/) | Audita y normaliza las citas de un manuscrito con Zotero como fuente de verdad: APA 7, Chicago 18 (notas y autor-fecha), cualquier estilo CSL de Zotero o un formato propio reconstruido a partir de un ejemplo del usuario; citas por clave desde LaTeX y Pandoc/Quarto contra archivos `.bib`/BibLaTeX; validación externa con control de autoría completa, de retractaciones y de fidelidad de las citas textuales contra PDF indexados, con evidencia ligada a hashes que señala conclusiones desactualizadas. |
| Redes sociales | [`tweetscraper`](tweetscraper/) | Recolecta y analiza datos de X/Twitter desde un agente: timelines de cuentas, búsquedas con operadores y fechas, captura en vivo, respuestas, reconstrucción de hilos, X Articles, tuits por URL (también sin sesión mediante proveedores públicos), multimedia, Listas, perfiles, "Acerca de esta cuenta", seguidores, seguidos y retuiteadores, con un grupo de cuentas que rota ante límites de solicitudes; exportación a Markdown/Obsidian con multimedia local opcional, series temporales, nubes de palabras, emojis y hashtags, más análisis opcional de sentimiento y de imágenes con OpenAI. Port a Node.js del paquete de R TweetScraperR. |
| Sitios web | [`wp-api`](wp-api/) | Trabaja con cualquier sitio WordPress a través de su API REST: descubre `/wp-json/`, exporta entradas, páginas, taxonomías y colecciones de plugins a JSON/NDJSON verificados, y descarga archivos de la biblioteca de medios en cualquier formato (PDF, imágenes, audio, video, documentos de oficina, archivos comprimidos) con validación por firma de bytes, manifiesto SHA-256, control de `robots.txt`, pausas corteses y consentimiento explícito de volumen. Las CLI incluidas en Python y R solo leen contenido público y se comportan igual; las lecturas autenticadas y las escrituras confirmadas se documentan aparte. |
| Prensa histórica | [`prensa-ws`](prensa-ws/) | Descarga números en PDF verificados de Prensa Histórica (prensahistorica.mcu.es) sin topes de volumen autoimpuestos: cualquier cantidad de números por publicación, varias publicaciones por ejecución (`--publicacion id1,id2` o `@lista.txt`) y pausa configurable (`--pausa`, 2 s por defecto, admite 0). Lee el listado mes por mes de cada publicación, toma solo los enlaces exactamente `PDF` (que sirven el archivo directamente), valida cada descarga (firma + pypdf + manifiesto SHA-256), reanuda reutilizando lo ya descargado y aísla las fallas para que una publicación bloqueada no detenga a las demás. |
| Jurisprudencia | [`cendoj`](cendoj/) | Busca en la base de jurisprudencia del CENDOJ (poderjudicial.es/search) hasta el tope real del visor (200 documentos), aunque haya miles de resultados: texto libre `TEXT` directo a `search.action` con TLS de navegador, paginado óptimo de 4x50, metadatos verificables (ROJ, ECLI, resumen, `documento` = `data-link`) en CSV/JSON con capturas; los PDF se descargan con Ego Lite (`object[data]` → `accessToPDF`) y el captcha de descarga masiva lo resuelve la persona usuaria. |
| Video | [`youtube-api`](youtube-api/) | Obtiene datos públicos de videos de YouTube (uno solo o lotes acotados de hasta 50) sin cuenta ni clave de API: metadatos, transcripción con marcas de tiempo y preferencia ordenada de idiomas, elección entre subtítulos manuales o automáticos y traducción opcional etiquetada, y comentarios con sus respuestas, en JSON y CSV; la cobertura, los resultados parciales y el presupuesto de solicitudes se informan contra el total declarado. Documenta la Data API v3 oficial y las alternativas (`yt-dlp`, `youtube-transcript-api`). |
| Gestión de la investigación | [`sigeva-bd`](sigeva-bd/) | Pone al día tu *Banco de Datos de Actividades CyT* de SIGEVA CONICET con un navegador real: cruza tu CV con lo que ya está cargado, busca en línea el material que falta antes de pedírtelo, recorta y comprime los textos completos, y carga artículos en revistas, trabajos en eventos, libros y partes de libro (autores, editores, filiaciones del catálogo, rol, referato, área del conocimiento), además de cualquier otra sección mapeada con `inspeccionar`. En seco por defecto; con `--guardar`, cada registro nuevo se confirma en la lista del sitio y se releen sus fechas. `modificar` corrige registros existentes sin dejar duplicados. Un rastreador de solo lectura mapea todo el banco de datos (~120 pantallas) en una línea base sin datos sensibles y documentación generada; cada sesión empieza con `verificar --auto`, que señala cambios en los formularios y se niega a arrancar si cambió uno del que depende el cargador. También carga las secciones de un trámite de convocatoria (PIP), sin apretar nunca ENVIAR PRESENTACIÓN. |

La documentación de cada skill (`SKILL.md`, `README.md`, referencias) está escrita en español.

## Principios compartidos

Todas las skills siguen las mismas reglas, así un agente se comporta igual cualquiera sea la que cargue:

- **Solo lectura y contenido público por defecto.** Las credenciales se piden solo cuando la tarea realmente las necesita, y nunca se pegan en el chat, en los registros ni en archivos.
- **El contenido externo es un dato no confiable.** Páginas web, tuits, comentarios, PDF, entradas BibTeX y respuestas de API nunca se siguen como instrucciones.
- **Recolección acotada y cortés.** Primero muestras chicas, consentimiento explícito de volumen, manejo de límites de solicitudes y control de `robots.txt` y términos de uso donde corresponda.
- **Resultados verificables.** Cada ejecución informa qué se pidió, qué se obtuvo y por qué se detuvo; los archivos llevan hashes o manifiestos, y los resultados parciales se marcan como tales.

## Requisitos

| Skill | Entorno | Cuentas / claves |
|---|---|---|
| `zotero-citations` | Python 3.10+ (solo biblioteca estándar) | Se recomienda Zotero 7+ de escritorio; clave de la API web de Zotero para escribir |
| `tweetscraper` | Node.js 22.13+ con npm (Playwright descarga Chromium en `install`) | Una cuenta propia de X; clave de OpenAI solo para `sentiment`/`images` |
| `wp-api` | Python 3.10+ con `requests`, o R 4.4+ con `httr2`, `jsonlite`, `digest` | Ninguna: las CLI solo leen contenido público |
| `youtube-api` | Python 3.10+ con `requests` | Ninguna; una clave de la Data API v3 solo si se elige la vía oficial |
| `prensa-ws` | Python 3.10+ con `requests`, `beautifulsoup4`, `pypdf` | Ninguna: solo lee contenido público |
| `cendoj` | Python 3.10+ con `curl_cffi`; Ego Lite para los PDF | Ninguna: lee contenido público; el captcha de descarga masiva lo resuelve la persona usuaria |
| `sigeva-bd` | Python 3.10+ con Playwright y Chromium | Una cuenta propia de la intranet del CONICET con el rol del banco de datos |

El `README.md` de cada skill detalla instalación, configuración y uso habitual.

## Instalación

Copiar o enlazar la carpeta de la skill en el directorio de skills del agente. Por ejemplo, con OpenCode:

```bash
git clone https://github.com/agusnieto77/SKILLS.git
mkdir -p ~/.config/opencode/skills
cp -r SKILLS/zotero-citations SKILLS/tweetscraper SKILLS/wp-api SKILLS/youtube-api SKILLS/sigeva-bd SKILLS/prensa-ws SKILLS/cendoj ~/.config/opencode/skills/
```

Copiar solo las skills que se necesiten. OpenCode también carga skills a nivel de proyecto desde `.opencode/skills/`. Otros agentes usan su propio directorio (Pi: `~/.pi/agent/skills/`; Claude Code: `~/.claude/skills/`; muchos agentes también leen `~/.agents/skills/`). Después, seguir la configuración de cada skill:

| Skill | Primera ejecución |
|---|---|
| `zotero-citations` | Definir `ZOTERO_LIBRARY_ID` (y `ZOTERO_API_KEY` para escribir), luego `python scripts/zotero_client.py whoami` |
| `tweetscraper` | `node scripts/tweetscraper.mjs install`, luego `doctor` y `login --manual` |
| `wp-api` | `python -m pip install -r assets/requirements.txt`, luego `python assets/wp_api.py --help` |
| `youtube-api` | `python -m pip install -r assets/requirements.txt`, luego `python assets/yt_datos.py --help` |
| `prensa-ws` | `python -m pip install -r assets/requirements.txt`, luego `python assets/prensa_ws.py --n 1 --salida datos` |
| `cendoj` | `python -m pip install -r assets/requirements.txt`, luego `python assets/cendoj_busqueda.py --texto huelga --salida datos` |
| `sigeva-bd` | `python -m pip install -r assets/requirements.txt`, `python -m playwright install chromium`, luego `python assets/sigeva_bd.py doctor` |

## Estructura

Cada skill es una carpeta autocontenida:

```
<skill>/
├── SKILL.md       # instrucciones que carga el agente (frontmatter: name, description, license, compatibility)
├── README.md      # instalación, configuración y uso para personas
├── CHANGELOG.md
├── references/    # detalle que el agente carga cuando lo necesita
└── scripts/ | assets/, tests/ | validation/
```

## Tests

La integración continua corre en Ubuntu y Windows en cada push a `main` (ver [`tests.yml`](.github/workflows/tests.yml)). En local, desde la raíz del repositorio:

```bash
# zotero-citations (Python 3.10+)
(cd zotero-citations && python -m unittest discover -s tests -v)

# tweetscraper (Node.js 22.13+)
(cd tweetscraper && npm ci --ignore-scripts && npm test)

# wp-api (Python 3.10+; la suite de R es opcional)
(cd wp-api && python -m unittest discover -s assets -p test_wp_api.py -v && python validation/test_scenarios.py)
Rscript wp-api/assets/test_wp_api.R

# prensa-ws (Python 3.10+)
(cd prensa-ws && python -m pip install -r assets/requirements.txt && python -m unittest discover -s assets -p test_prensa_ws.py -v)

# cendoj (Python 3.10+)
(cd cendoj && python -m pip install -r assets/requirements.txt && python -m unittest discover -s assets -p test_cendoj_busqueda.py -v)

# sigeva-bd (Python 3.10+; los tests de punta a punta necesitan Playwright + Chromium y se omiten si faltan)
python sigeva-bd/validation/test_sigeva_bd.py
```

Los tests corren sin conexión, contra fixtures y servidores HTTP locales; nunca necesitan credenciales.

## Licencia

Apache License 2.0 — ver [LICENSE](LICENSE).
