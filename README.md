# SKILLS

[![tests](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml/badge.svg)](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml)

Agent skills for research and academic work: citation management and data collection from social media, video platforms and websites. They follow the open [Agent Skills](https://agentskills.io) format, so they work with any compatible agent: OpenCode, Pi, Oh My Pi, Gentle Shell, Claude Code, Codex, Gemini CLI, Cursor and others.

| Skill | What it does |
|---|---|
| [`zotero-citations`](zotero-citations/) | Audits and normalizes manuscript citations with Zotero as the source of truth: APA 7, Chicago 18 (notes and author-date), any Zotero CSL style or a custom format rebuilt from a user example; external validation, retraction checks and quote fidelity against indexed PDFs. |
| [`tweetscraper`](tweetscraper/) | Collects and analyzes X/Twitter data from an agent: account timelines, searches with operators and dates, live capture, replies, tweets by URL, media, Lists, profiles, "About this account", followers, following and retweeters, with an account pool that rotates on rate limits; time series, word clouds, emojis, hashtags, plus optional OpenAI sentiment and image analysis. Node.js port of the TweetScraperR R package. |
| [`wp-api`](wp-api/) | Works with any WordPress site through its REST API: discovers `/wp-json/`, exports posts, pages, taxonomies and plugin collections to verified JSON/NDJSON, and downloads media-library files of every format (PDF, images, audio, video, office documents, archives) with magic-byte validation, SHA-256 manifest, robots checks, polite throttling and volume-consent gates. Public reads only; Python and R CLIs with identical behavior. |
| [`youtube-api`](youtube-api/) | Retrieves public data from a YouTube video without an account or API key: metadata, timestamped transcript (manual or auto-generated captions) and comments with threaded replies, to JSON and CSV; coverage reported against the declared total. Documents the official Data API v3 and fallbacks (`yt-dlp`, `youtube-transcript-api`). |

Skill documentation (`SKILL.md`, `README.md`, references) is written in Spanish.

## Requirements

| Skill | Runtime | Accounts / keys |
|---|---|---|
| `zotero-citations` | Python 3.10+ (standard library only) | Zotero 7+ desktop recommended; Zotero Web API key for writing |
| `tweetscraper` | Node.js 22.13+ with npm (Playwright downloads Chromium on `install`) | An X account of your own; OpenAI key only for `sentiment`/`images` |
| `wp-api` | Python 3.10+ with `requests`, or R 4.4+ with `httr2`, `jsonlite`, `digest` | None: the CLIs read public content only |
| `youtube-api` | Python 3.10+ with `requests` | None; a Data API v3 key only if you choose the official route |

Each skill's `README.md` covers installation, configuration and typical usage in detail.

## Install

Copy or symlink a skill folder into your agent's skills directory. For example, with OpenCode:

```bash
git clone https://github.com/agusnieto77/SKILLS.git
mkdir -p ~/.config/opencode/skills
cp -r SKILLS/zotero-citations SKILLS/tweetscraper SKILLS/wp-api SKILLS/youtube-api ~/.config/opencode/skills/
```

Copy only the skills you need. OpenCode also loads project-level skills from `.opencode/skills/`. Other agents use their own directory (Pi: `~/.pi/agent/skills/`; Claude Code: `~/.claude/skills/`; many agents also read `~/.agents/skills/`). Then follow the per-skill setup:

| Skill | First run |
|---|---|
| `zotero-citations` | Set `ZOTERO_LIBRARY_ID` (and `ZOTERO_API_KEY` to write), then `python scripts/zotero_client.py whoami` |
| `tweetscraper` | `node scripts/tweetscraper.mjs install`, then `doctor` and `login --manual` |
| `wp-api` | `python -m pip install -r assets/requirements.txt`, then `python assets/wp_api.py --help` |
| `youtube-api` | `python -m pip install -r assets/requirements.txt`, then `python assets/yt_datos.py --help` |

## Layout

Every skill is a self-contained folder:

```
<skill>/
├── SKILL.md       # instructions the agent loads (frontmatter: name, description, license, compatibility)
├── README.md      # install, configuration and usage for humans
├── CHANGELOG.md
├── references/    # detail loaded on demand by the agent
└── scripts/ | assets/, tests/ | validation/
```

## Tests

CI runs on Ubuntu and Windows for every push to `main` (see [`tests.yml`](.github/workflows/tests.yml)). Locally, from the repository root:

```bash
# zotero-citations (Python 3.10+)
(cd zotero-citations && python -m unittest discover -s tests -v)

# tweetscraper (Node.js 22.13+)
(cd tweetscraper && npm ci --ignore-scripts && npm test)

# wp-api (Python 3.10+; R suite optional)
(cd wp-api && python -m unittest discover -s assets -p test_wp_api.py -v && python validation/test_scenarios.py)
Rscript wp-api/assets/test_wp_api.R

# youtube-api (Python 3.10+)
python youtube-api/validation/test_yt_datos.py
```

Tests run offline against fixtures and local HTTP servers; they never need credentials.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
