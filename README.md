# SKILLS

[![tests](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml/badge.svg)](https://github.com/agusnieto77/SKILLS/actions/workflows/tests.yml)

Agent skills for research and academic work. They follow the open [Agent Skills](https://agentskills.io) format, so they work with any compatible agent: OpenCode, Pi, Oh My Pi, Gentle Shell, Claude Code, Codex, Gemini CLI, Cursor and others.

| Skill | What it does |
|---|---|
| [`zotero-citations`](zotero-citations/) | Audits and normalizes manuscript citations with Zotero as the source of truth: APA 7, Chicago 18 (notes and author-date), any Zotero CSL style or a custom format rebuilt from a user example; external validation, retraction checks and quote fidelity against indexed PDFs. Docs in Spanish. |
| [`tweetscraper`](tweetscraper/) | Collects and analyzes X/Twitter data from an agent: account timelines, searches with operators and dates, live capture, replies, tweets by URL, media, Lists, profiles, "About this account", followers, following and retweeters, with an account pool that rotates on rate limits; time series, word clouds, emojis, hashtags, plus optional OpenAI sentiment and image analysis. Node.js port of the TweetScraperR R package. Docs in Spanish. |

## Install

Copy or symlink a skill folder into your agent's skills directory. For example, with OpenCode:

```bash
git clone https://github.com/agusnieto77/SKILLS.git
mkdir -p ~/.config/opencode/skills
cp -r SKILLS/tweetscraper ~/.config/opencode/skills/
```

OpenCode also loads project-level skills from `.opencode/skills/`. Other agents use their own directory (Pi: `~/.pi/agent/skills/`; Claude Code: `~/.claude/skills/`; many agents also read `~/.agents/skills/`). Each skill's `README.md` lists its requirements and configuration.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
