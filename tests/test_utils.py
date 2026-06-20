"""Unit tests for skillhub.utils — pure helpers, no Flask."""

from __future__ import annotations

import os

from skillhub import utils
from skillhub.utils import (
    atomic_write,
    claude_skills_path,
    list_openclaw_workspaces,
    list_skills,
    resolve_skill_path,
    safe_join,
)


def test_list_workspaces_finds_patterns(temp_home):
    (temp_home / ".openclaw" / "workspace").mkdir(parents=True)
    (temp_home / ".openclaw" / "workspace-2").mkdir(parents=True)
    (temp_home / ".openclaw" / "random").mkdir(parents=True)  # ignored
    ws = {w.name for w in list_openclaw_workspaces(home=str(temp_home))}
    assert "workspace" in ws
    assert "workspace-2" in ws
    assert "random" not in ws


def test_list_skills_reads_skill_md(temp_home):
    root = temp_home / "skills"
    (root / "a").mkdir(parents=True)
    (root / "a" / "SKILL.md").write_text("# A", encoding="utf-8")
    (root / "b").mkdir(parents=True)  # no SKILL.md
    skills = list_skills(str(root))
    by_name = {s.name: s for s in skills}
    assert by_name["a"].has_skill_md is True
    assert by_name["a"].description.startswith("# A")
    assert by_name["b"].has_skill_md is False


def test_resolve_skill_path_rejects_traversal(temp_home, skills_root):
    """The ``temp_home`` fixture already redirected HOME; the seed tree in
    ``skills_root`` is visible through :func:`resolve_skill_path`."""
    assert resolve_skill_path("claude", "hello-skill") is not None
    assert resolve_skill_path("claude", "../hello-skill") is None
    assert resolve_skill_path("claude", "") is None
    assert resolve_skill_path("claude", "skillhub") is None  # reserved
    assert resolve_skill_path("unknown-source", "x") is None
    # OpenCLAW workspace seeded by fixture
    assert resolve_skill_path("workspace", "demo") is not None
    assert resolve_skill_path("workspace-extra", "extra") is not None


def test_safe_join_blocks_traversal(temp_home):
    root = str(temp_home / "root")
    os.makedirs(root, exist_ok=True)
    assert safe_join(root, "a/b.txt") is not None
    assert safe_join(root, "../etc/passwd") is None
    assert safe_join(root, "") is None


def test_atomic_write_creates_backup(temp_home):
    p = temp_home / "file.md"
    p.write_text("v1", encoding="utf-8")
    atomic_write(str(p), "v2")
    assert p.read_text(encoding="utf-8") == "v2"
    bak = temp_home / "file.md.bak"
    assert bak.exists()
    assert bak.read_text(encoding="utf-8") == "v1"


def test_claude_skills_path_uses_home(temp_home):
    """After redirecting HOME the path resolver should follow."""
    expected = str(temp_home / ".claude" / "skills" / "skills")
    assert claude_skills_path() == expected


def test_skillhub_website_url_default():
    from skillhub.utils import SKILLHUB_WEBSITE_URL

    assert SKILLHUB_WEBSITE_URL.startswith("https://")
    assert "skillhub" in SKILLHUB_WEBSITE_URL


def test_skillhub_website_url_overridable_via_env(monkeypatch):
    monkeypatch.setenv("SKILLHUB_WEBSITE_URL", "https://env-override.test/path")
    # Re-import to pick up env at module load — the function form isn't
    # used here, but we still verify the constant honors the env when set
    # at import time by simulating it.
    import importlib

    import skillhub.utils as utils_mod

    importlib.reload(utils_mod)
    try:
        assert utils_mod.SKILLHUB_WEBSITE_URL == "https://env-override.test/path"
    finally:
        # Restore default by clearing the env var and reloading.
        monkeypatch.delenv("SKILLHUB_WEBSITE_URL", raising=False)
        importlib.reload(utils_mod)
