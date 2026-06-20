"""Cross-cutting helpers: workspace discovery, path safety, file limits."""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Captured at import time for reference only; call :func:`home_dir` for
# any path lookup so tests can redirect ``HOME`` / ``USERPROFILE``.
HOME = str(Path.home())

SKILLHUB_DOWNLOAD_URL = (
    "https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/latest.tar.gz"
)
# Public Tencent Skillhub marketplace where users can browse available skills
# before installing. Overridable via the ``SKILLHUB_WEBSITE_URL`` environment
# variable or the Flask ``SKILLHUB_WEBSITE_URL`` config key.
SKILLHUB_WEBSITE_URL = os.environ.get(
    "SKILLHUB_WEBSITE_URL",
    "https://www.skillhub.cn/skills?sortBy=score",
)


def home_dir() -> str:
    """Return the active user home directory.

    Re-reads the environment on every call so test fixtures can redirect
    ``HOME`` / ``USERPROFILE`` after the module is imported.
    """
    return (
        os.environ.get("HOME")
        or os.environ.get("USERPROFILE")
        or str(Path.home())
    )


def claude_skills_path() -> str:
    return os.path.join(home_dir(), ".claude", "skills", "skills")


def skillhub_cli_path() -> str:
    return os.path.join(home_dir(), ".skill-hub", "cli", "skills_store_cli.py")


# File size limits for the in-browser editor (bytes).
MAX_READ_BYTES = 2 * 1024 * 1024  # 2 MiB
MAX_WRITE_BYTES = 2 * 1024 * 1024

# Allowed extensions for write operations in the editor.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".md",
        ".markdown",
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".sh",
        ".bash",
        ".txt",
        ".css",
        ".html",
    }
)

# Skillhub reserved names — never treat as workspace names.
_SKILLHUB_RESERVED = {"skillhub"}


@dataclass(frozen=True)
class Workspace:
    """An OpenCLAW workspace (a directory with a ``skills`` subdirectory)."""

    name: str
    path: str
    skills_path: str
    exists: bool


def list_openclaw_workspaces(home: str | None = None) -> list[Workspace]:
    """Return all OpenCLAW workspaces under ``~/.openclaw``."""
    root = os.path.join(home or home_dir(), ".openclaw")
    workspaces: list[Workspace] = []
    if not os.path.exists(root):
        return workspaces

    for item in sorted(os.listdir(root)):
        if not (item == "workspace" or item.startswith("workspace")):
            continue
        item_path = os.path.join(root, item)
        if not os.path.isdir(item_path):
            continue
        skills_path = os.path.join(item_path, "skills")
        workspaces.append(
            Workspace(
                name=item,
                path=item_path,
                skills_path=skills_path,
                exists=os.path.exists(skills_path),
            )
        )
    return workspaces


@dataclass
class SkillInfo:
    """A single skill directory on disk."""

    name: str
    path: str
    description: str
    has_skill_md: bool


def list_skills(skills_path: str) -> list[SkillInfo]:
    """List skills directly under ``skills_path`` (non-recursive)."""
    skills: list[SkillInfo] = []
    if not os.path.exists(skills_path):
        return skills

    for item in sorted(os.listdir(skills_path)):
        item_path = os.path.join(skills_path, item)
        if not os.path.isdir(item_path):
            continue
        skill = SkillInfo(
            name=item,
            path=item_path,
            description="",
            has_skill_md=False,
        )
        skill_md = os.path.join(item_path, "SKILL.md")
        if os.path.exists(skill_md):
            skill.has_skill_md = True
            try:
                with open(skill_md, "r", encoding="utf-8") as fh:
                    skill.description = fh.read(4096)
            except OSError as exc:
                logger.warning("Failed to read %s: %s", skill_md, exc)
        skills.append(skill)
    return skills


def resolve_skill_path(source: str, skill_name: str) -> str | None:
    """Resolve a ``(source, skill_name)`` pair to an absolute skill directory.

    Returns ``None`` if the source is unknown or the skill does not exist.
    Used by detail/editor endpoints to centralise path safety.
    """
    if not skill_name or skill_name in _SKILLHUB_RESERVED:
        return None

    if source == "claude":
        base = claude_skills_path()
    else:
        workspace_names = {ws.name for ws in list_openclaw_workspaces()}
        if source not in workspace_names:
            return None
        base = os.path.join(home_dir(), ".openclaw", source, "skills")

    candidate = os.path.realpath(os.path.join(base, skill_name))
    base_real = os.path.realpath(base)
    if not candidate.startswith(base_real + os.sep) and candidate != base_real:
        return None
    if not os.path.isdir(candidate):
        return None
    return candidate


def safe_join(root: str, rel_path: str) -> str | None:
    """Join ``rel_path`` to ``root`` defensively; reject path traversal."""
    if not rel_path:
        return None
    root_real = os.path.realpath(root)
    candidate = os.path.realpath(os.path.join(root_real, rel_path))
    if not candidate.startswith(root_real + os.sep):
        return None
    return candidate


def atomic_write(path: str, content: str) -> None:
    """Write ``content`` to ``path`` via a sibling temp file + rename.

    A ``.bak`` of the previous contents is preserved when one exists.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)

    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, target)


__all__ = [
    "HOME",
    "home_dir",
    "claude_skills_path",
    "skillhub_cli_path",
    "SKILLHUB_DOWNLOAD_URL",
    "SKILLHUB_WEBSITE_URL",
    "MAX_READ_BYTES",
    "MAX_WRITE_BYTES",
    "ALLOWED_EXTENSIONS",
    "Workspace",
    "SkillInfo",
    "list_openclaw_workspaces",
    "list_skills",
    "resolve_skill_path",
    "safe_join",
    "atomic_write",
]
