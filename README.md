# Skill Manager

> A web UI to **browse, install, distribute, view, and edit** Claude Code / OpenCLAW skills locally.

![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![Flask](https://img.shields.io/badge/flask-%3E=3.0-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Status](https://img.shields.io/badge/status-MVP-orange)

Skill Manager is a lightweight Flask application that turns your local
Claude Code / OpenCLAW skills folder into a discoverable, browsable,
editable workspace — no database, no cloud dependency, no setup beyond
`pip install`.

---

## ✨ Features

- 📂 **Browse** — see every skill installed under Claude Code and across
  every OpenCLAW workspace in one place
- 📑 **View detail** — click a skill to see its full `SKILL.md` rendered,
  file tree, total size, last-modified time, and file count
- ✏️ **Edit in-browser** — open any editable file in a CodeMirror
  editor, save back to disk with a `.bak` backup; path-traversal-safe
- 📦 **Install from Skillhub** — pull new skills from the Skillhub CLI
  into Claude Code and/or any OpenCLAW workspace; click the
  "浏览 Skillhub ↗" link in the install panel to browse the marketplace
  first
- 🚚 **Distribute** — copy selected skills into a target project folder
  to ship them with your app
- 🛡️ **Safe by default** — every read/write goes through path validation,
  size caps, and an extension whitelist

---

## 📸 Screenshots

> _Coming soon — `docs/screenshots/` reserved for the upcoming release._

---

## 🚀 Quick start

```bash
# 1. Clone
git clone https://github.com/harrycjs/skill-manager.git
cd skill-manager

# 2. Install (runtime only)
pip install -r requirements.txt
# or, for contributors:
pip install -r requirements-dev.txt

# 3. Run
python app.py
# open http://127.0.0.1:5000
```

On first launch Skill Manager will try to fetch the Skillhub CLI from
the official mirror. If you're offline or don't need it, the rest of the
UI (browse / view / edit / distribute) still works.

### Production

```bash
flask --app skillhub run --host 0.0.0.0 --port 5000
# or
gunicorn 'skillhub:create_app()'
```

---

## 🧩 How it works

```
┌─────────── Browser ───────────┐
│  Tabs:  Import | Install |   │
│         Distribute            │
│                              │
│  Side panel:                 │
│   [SKILL.md]  [Files]   ◄────── click a card to open
│   • rendered markdown        │
│   • file tree → CodeMirror   │
└──────────┬───────────────────┘
           │  /api/...
┌──────────▼───────────────────┐
│  Flask app (skillhub pkg)    │
│   skills_bp   install_bp     │
│   editor_bp   distribute_bp  │
│           utils.py           │
└──────────┬───────────────────┘
           │
   ~/.claude/skills/skills/*
   ~/.openclaw/workspace*/skills/*
   ~/.skill-hub/cli/...
```

All skill directories are sandboxed: every API call resolves the path
through `utils.resolve_skill_path` + `utils.safe_join`, so a malicious
request cannot escape a skill's root.

---

## 🧪 Development

```bash
# run tests
pytest --cov=skillhub

# lint
ruff check .

# format (optional)
ruff format .
```

The test suite ships a `temp_home` fixture that redirects `HOME` to a
`tmp_path` and seeds a small skills tree, so tests are fully offline
and reproducible.

### Project layout

```
skill-manager/
├── app.py                      # entry point
├── skillhub/                   # application package
│   ├── __init__.py             #   create_app() factory
│   ├── utils.py                #   path helpers, workspace discovery
│   ├── skills_bp.py            #   list / detail / file-tree API
│   ├── editor_bp.py            #   file read / write API
│   ├── install_bp.py           #   Skillhub CLI bootstrap
│   ├── distribute_bp.py        #   copy skills to projects
│   └── cli.py                  #   reserved for future CLI
├── templates/
│   ├── base.html
│   ├── index.html
│   └── _skill_detail.html
├── static/
│   ├── css/app.css
│   └── js/
│       ├── app.js
│       └── editor.js
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_utils.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── .github/workflows/ci.yml
```

---

## 🗺️ Roadmap

The MVP focuses on browse + view + edit. The following are intentionally
**not** in this release and are listed to help contributors find a slot:

- [ ] **CLI / TUI** — `skill-manager` subcommand (Click / Textual)
- [ ] **Skill market** — browse trending skills from Skillhub
- [ ] **Versioning** — pinned `skill@1.2.0`, upgrade-all, dependency graph
- [ ] **Project-level `skill.json`** — like `package.json`; auto-load on `cd`
- [ ] **Diff view** — see changes before saving
- [ ] **Real-time install logs** — Server-Sent Events for live output
- [ ] **Bulk operations** — multi-select → install / upgrade / export
- [ ] **i18n** — English UI alongside Chinese
- [ ] **Skill templates / scaffolding** — `skill create my-skill`
- [ ] **Backup vault** — central `.bak` browser / restore UI
- [ ] **Auth + sharing** — multi-user, role-based (team mode)

PRs welcome — please open an issue first to discuss scope.

---

## 📄 License

[MIT](LICENSE) — see the file for full text.

---

## 🙏 Acknowledgements

- The **CodeMirror** team for the in-browser editor (loaded from jsDelivr).
- **marked.js** for client-side Markdown rendering.
- Inspired by **Homebrew**, **Oh My Zsh**, **lazygit**, and the
  VSCode Remote Explorer — all examples of "a tiny CLI/web tool that
  becomes indispensable once you use it".
