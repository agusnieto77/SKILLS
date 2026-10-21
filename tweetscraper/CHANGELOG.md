# Changelog

## 1.0.0 — 2026-10-21

Primera versión: port a Node.js de TweetScraperR 0.8.1.9000.

- CLI `scripts/tweetscraper.mjs` con un JSON por corrida en stdout y datasets en JSONL/JSON/CSV.
- Recolección: `user-tweets`, `media`, `timelines`, `search`, `live`, `replies`, `tweets`, `list-tweets`, `users`, `about`, `users-search`, `followers`, `following`, `retweeters`, `list-members` (equivalentes a las funciones `*API()` del paquete).
- Motor Playwright + stealth en el mismo proceso (sin puente R ↔ Node) y pool de cuentas en SQLite (`node:sqlite`) con rotación por cupo, reanudación por cursor, desactivación de sesiones vencidas y proxy por cuenta.
- Sesión: `login --manual`, `login`, `session import` (archivo de cookies, variables de entorno), `accounts list|check|add|remove|reactivate|reset-locks|proxy|setup`.
- Análisis local: `summary`, `convert`, `hashtags`, `time`, `words`, `emojis`, con gráficos SVG.
- OpenAI: `sentiment`, `images`, `img-report`, con los prompts de TweetScraperR.
- Tests con los fixtures del paquete de R, rotación del pool incluida.
