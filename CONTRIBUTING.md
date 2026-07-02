# Contributing

Thanks for your interest in Skills Dashboard.

This project is still early. The most valuable contributions right now are practical feedback from real Agent Skills users.

## Good Issues To Open

Please open an issue if you have:

- A Skill directory path that the dashboard does not detect yet
- A Codex / Claude Code / Hermes / agent setup that behaves differently
- A confusing Skill category or description
- A UI detail that feels awkward or slow
- A better installation flow
- A product idea for Skill discovery, updates, sharing, or sync

Screenshots, short screen recordings, and exact local paths are very helpful.

## Good Pull Requests

Pull requests are welcome for:

- Better Skill scanning rules
- More accurate category inference
- UI polish and responsive layout improvements
- Dark mode and theme work
- Better bilingual copy
- Installation and launch improvements
- Documentation improvements
- Cross-platform fixes for macOS, Windows, or Linux

## Local Development

Run the dashboard directly:

```bash
cd skills-dashboard/assets/dashboard
python3 app.py
```

Then open:

```text
http://127.0.0.1:8787/
```

Or use the launcher:

```bash
cd skills-dashboard
python3 scripts/launch_dashboard.py --browser default
```

## Validation

Before opening a PR, please run:

```bash
python3 -m py_compile skills-dashboard/assets/dashboard/app.py skills-dashboard/scripts/launch_dashboard.py
node --check skills-dashboard/assets/dashboard/static/app.js
```

If you do not have Node installed, mention that in the PR.

## Product Direction

The project should stay:

- Local-first
- Agent Skills-compatible
- Easy to install
- Useful before it becomes complex
- Friendly to both Chinese and English users

Please avoid adding cloud sync, login, analytics, or write operations without discussion first.
