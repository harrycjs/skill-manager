"""Pytest fixtures — temp skills tree + Flask test client."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from skillhub import create_app


@pytest.fixture
def temp_home(tmp_path, monkeypatch):
    """Redirect HOME so the app reads/writes skills inside tmp_path."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


@pytest.fixture
def skills_root(temp_home):
    """Create a sample skills tree under the temp HOME and return paths."""
    claude = temp_home / ".claude" / "skills" / "skills"
    ws_a = temp_home / ".openclaw" / "workspace"
    ws_b = temp_home / ".openclaw" / "workspace-extra"

    (claude / "hello-skill" / "src").mkdir(parents=True)
    (claude / "hello-skill" / "SKILL.md").write_text(
        "# Hello\n\nA friendly skill.", encoding="utf-8"
    )
    (claude / "hello-skill" / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")

    (ws_a / "skills" / "demo").mkdir(parents=True)
    (ws_a / "skills" / "demo" / "SKILL.md").write_text("# Demo", encoding="utf-8")

    (ws_b / "skills" / "extra").mkdir(parents=True)
    (ws_b / "skills" / "extra" / "SKILL.md").write_text("# Extra", encoding="utf-8")

    return {
        "claude": str(claude),
        "ws_a": str(ws_a),
        "ws_b": str(ws_b),
    }


@pytest.fixture
def client(temp_home, skills_root):
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
