# SKILLS

[![tests](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml/badge.svg)](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml)

Agent skills (Claude Code and compatible agents) for academic work.

| Skill | What it does |
|---|---|
| [`zotero-citations`](zotero-citations/) | Audits and normalizes manuscript citations with Zotero as the source of truth: APA 7, Chicago 18 (notes and author-date), any Zotero CSL style or a custom format rebuilt from a user example; external validation, retraction checks and quote fidelity against indexed PDFs. Docs in Spanish. |
| [`tweetscraper`](tweetscraper/) | Collects and analyzes X/Twitter data from an agent: account timelines, searches with operators and dates, live capture, replies, tweets by URL, media, Lists, profiles, "About this account", followers, following and retweeters, with an account pool that rotates on rate limits; time series, word clouds, emojis, hashtags, plus optional OpenAI sentiment and image analysis. Node.js port of the TweetScraperR R package. Docs in Spanish. |

## Install

Copy or symlink a skill folder into your agent's skills directory (for example `~/.claude/skills/`). Each skill's `README.md` lists its requirements and configuration.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
