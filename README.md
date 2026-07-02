# Skills Dashboard

A local Skill center for Codex, Claude Code, Hermes, cc-switch, and other Agent Skills-compatible setups.

It launches a browser UI for viewing, searching, categorizing, annotating, and organizing installed skills. The dashboard is local-only and stores your personal metadata separately from the skill source.

## Install

Install the `skills-dashboard/` folder with any Agent Skills-compatible tool, or clone this repository and copy the folder into your skills directory.

Common locations:

```bash
# Codex
mkdir -p ~/.codex/skills
cp -R skills-dashboard ~/.codex/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R skills-dashboard ~/.claude/skills/

# Hermes
mkdir -p ~/.hermes/skills
cp -R skills-dashboard ~/.hermes/skills/
```

Then ask your agent:

```text
Use skills-dashboard to open my Skill center.
```

## Manual Launch

From the installed `skills-dashboard` directory:

```bash
python3 scripts/launch_dashboard.py --browser chrome
```

The default URL is:

```text
http://127.0.0.1:8787/
```

## Scanned Locations

The dashboard scans common skill directories:

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

Add custom roots:

```bash
python3 scripts/launch_dashboard.py --extra-root /path/to/skills
```

Or set:

```bash
export SKILLS_DASHBOARD_EXTRA_ROOTS="/path/a:/path/b"
```

## Privacy

The server binds to `127.0.0.1` only. It does not upload your skill list or modify installed skill source files.

Local metadata is stored at:

```text
~/Library/Application Support/SkillsDashboard/catalog.json
```

on macOS, or the equivalent app data directory on Windows/Linux.
