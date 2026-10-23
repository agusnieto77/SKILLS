# Changelog

## 1.1.3 — 2026-10-22

- `thread` distingue captura completa, truncamiento confirmado (`truncated`) e incertidumbre (`possibly_truncated`): un cursor focal tras tres desplazamientos estables genera un aviso específico, sin afirmar que falten datos ni que el hilo esté completo.
- El motor y el pool propagan un estado de paginación explícito; los cursores históricos y auxiliares no alteran el estado focal y los cortes confirmados prevalecen sobre la incertidumbre.
- Pruebas offline de los tres estados y del límite total de media con y sin señal del llamador; sincronización del cuerpo por lectura efectiva y limpieza protegida para no ocultar fallos con `TypeError`.

## 1.1.2 — 2026-10-22

- `thread` mantiene el aviso de truncamiento si la última página focal conserva un cursor Bottom o ShowMore, aunque tres desplazamientos consecutivos no produzcan respuestas nuevas.
- Las descargas de media tienen un límite total de cinco minutos, incluido el cuerpo, además del plazo de 30 segundos para las cabeceras; un servidor detenido no bloquea indefinidamente la exportación y la cancelación sigue propagándose.
- Regresiones offline para cursores pendientes tras agotamiento por desplazamiento, cuerpos detenidos y señales `stopped`/`stoppedAt` del recolector.

## 1.1.1 — 2026-10-22

- `thread` distingue una paginación focal interrumpida de cursores históricos, paginaciones completadas y páginas auxiliares de antecedentes o continuación.
- Las reexportaciones Markdown reutilizan media local idéntica a la descarga verificada, sin sobrescribir archivos distintos ni perder los enlaces relativos.
- La cancelación de descargas detiene la exportación y conserva la nota anterior; el plazo de 30 segundos se aplica solo a las cabeceras, no al cuerpo.
- Syndication reconoce `TweetTombstone` como contenido inaccesible; Articles exige marcadores propios y no confunde entidades con título e ID.
- Regresiones offline para estos casos y rutas del CLI convertidas con `fileURLToPath`.

## 1.1.0 — 2026-10-22

- Lectura pública explícita `public-tweet`: FxTwitter y fallback syndication con token calculado, sin cookies ni sesión y con freno ante contenido inaccesible.
- `thread`: reconstrucción acotada de antecedentes y continuación del autor, roles separados, raíz, deduplicación, orden cronológico y advertencias por truncamiento.
- Exportación Markdown/Obsidian (`convert` o recolección a `.md`): front matter, fuentes, citas, formatos compacto/completo y media local opt-in con límites de tipo, host y tamaño.
- `article`: entidad y esquema propios con título, portada, bloques Draft.js, enlaces y media; `entityMap` como objeto o lista y separación explícita entre cuerpo y preview.
- Frontera de confianza explícita: textos, bios, Articles, URLs y errores externos no seleccionan comandos, archivos ni destinos; exportaciones escapadas.
- Pruebas offline de proveedores, contenido inaccesible, hilos parciales, Articles, exportación, descargas y CLI; recetas trasladadas a la referencia para reducir SKILL.md.

## 1.0.0 — 2026-10-21

Primera versión: port a Node.js de TweetScraperR 0.8.1.9000.

- CLI `scripts/tweetscraper.mjs` con un JSON por corrida en stdout y datasets en JSONL/JSON/CSV.
- Recolección: `user-tweets`, `media`, `timelines`, `search`, `live`, `replies`, `tweets`, `list-tweets`, `users`, `about`, `users-search`, `followers`, `following`, `retweeters`, `list-members` (equivalentes a las funciones `*API()` del paquete).
- Motor Playwright + stealth en el mismo proceso (sin puente R ↔ Node) y pool de cuentas en SQLite (`node:sqlite`) con rotación por cupo, reanudación por cursor, desactivación de sesiones vencidas y proxy por cuenta.
- Sesión: `login --manual`, `login`, `session import` (archivo de cookies, variables de entorno), `accounts list|check|add|remove|reactivate|reset-locks|proxy|setup`.
- Análisis local: `summary`, `convert`, `hashtags`, `time`, `words`, `emojis`, con gráficos SVG.
- OpenAI: `sentiment`, `images`, `img-report`, con los prompts de TweetScraperR.
- Tests con los fixtures del paquete de R, rotación del pool incluida.
