---
name: skills-dashboard
description: Local web dashboard for viewing, searching, categorizing, annotating, and launching an installed Agent Skills catalog. Use when the user asks to open or manage a Skill center/dashboard/manager, inspect installed skills, organize skills by category/color/tags/notes, check what skills are available across Codex, Claude Code, Hermes, cc-switch, or ~/.agents, refresh a local skills catalog, or start the bundled Skills Dashboard web UI.
---

# Skills Dashboard

Use this skill to start the bundled local Skills Dashboard web UI and help the user inspect or organize installed Agent Skills.

## Quick Start

Run the launcher from this skill directory:

```bash
python3 scripts/launch_dashboard.py --browser chrome
```

The script prints the local URL after the server is ready. Share that URL with the user. On macOS, `--browser chrome` opens Google Chrome; use `--browser default` for the system browser or `--browser none` when the user only wants the URL.

## What The Dashboard Scans

The bundled server scans common skill locations:

```text
~/.agents/skills
~/.codex/skills
~/.codex/plugins/cache
~/.cc-switch/skills
~/.claude/skills
~/.config/claude/skills
~/.hermes/skills
~/.config/hermes/skills
./.agents/skills
./.codex/skills
./.claude/skills
./.hermes/skills
./.github/skills
```

Add custom locations when needed:

```bash
python3 scripts/launch_dashboard.py --extra-root /path/to/skills
```

Multiple custom roots can also be provided with `SKILLS_DASHBOARD_EXTRA_ROOTS`, separated by the host OS path separator.

## Data And Safety

The dashboard is local-only and binds to `127.0.0.1`. It does not publish data or edit skill source files.

User metadata such as category colors, notes, favorites, hidden state, and custom call hints is stored outside the skill folder:

- macOS: `~/Library/Application Support/SkillsDashboard/catalog.json`
- Windows: `%APPDATA%/SkillsDashboard/catalog.json`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/skills-dashboard/catalog.json`

Override the metadata path with `SKILLS_DASHBOARD_DATA_DIR`.

## Troubleshooting

If port `8787` is already occupied by another process, choose another port:

```bash
python3 scripts/launch_dashboard.py --port 8788
```

If the UI is already running, the launcher reuses the existing dashboard server on the selected port.
