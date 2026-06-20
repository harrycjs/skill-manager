# Changelog

All notable changes to Skill Manager are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Clickable link to the Tencent Skillhub marketplace on the install
  panel (configurable via `SKILLHUB_WEBSITE_URL` env var or Flask
  config key).
- Skill detail side panel with full `SKILL.md` Markdown rendering and
  metadata (file count, total size, last modified).
- Recursive file-tree view inside the detail panel.
- In-browser file editor powered by CodeMirror with path-traversal
  protection, size caps, and an editable-extension whitelist.
- Atomic file write helper that preserves `.bak` backups.
- Blueprint-based package layout (`skillhub/{skills,install,editor,distribute}_bp.py`).
- Pytest suite with offline `temp_home` fixture; CI on
  Python 3.10 / 3.11 / 3.12 via GitHub Actions.
- `pyproject.toml`, `requirements-dev.txt`, `.gitignore`, `LICENSE`.

### Changed
- `app.py` is now a thin entry point delegating to `skillhub.create_app()`.
- Hardcoded Skillhub install code deduplicated; duplicate `return`
  fixed.

## [0.1.0] - 2026-03-14

### Added
- Initial single-file Flask app: browse, install via Skillhub, distribute.

[Unreleased]: https://github.com/harrycjs/skill-manager/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/harrycjs/skill-manager/releases/tag/v0.1.0
