"""Skills blueprint — list, detail, and file-tree endpoints."""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify

from skillhub.utils import (
    claude_skills_path,
    list_openclaw_workspaces,
    list_skills,
    resolve_skill_path,
)
from skillhub.open_folder import open_in_file_manager

logger = logging.getLogger(__name__)

bp = Blueprint("skills", __name__, url_prefix="/api")


def _skill_to_dict(skill) -> dict:
    return {
        "name": skill.name,
        "path": skill.path,
        "description": skill.description[:200] if skill.description else "",
        "has_skill_md": skill.has_skill_md,
    }


@bp.get("/import-skills")
def import_skills():
    """List Claude Code + OpenCLAW workspaces and their skills (legacy route)."""
    claude_skills = list_skills(claude_skills_path())
    workspaces = list_openclaw_workspaces()
    payload = {
        "claude": {
            "name": "Claude Code",
            "path": claude_skills_path(),
            "skills": [_skill_to_dict(s) for s in claude_skills],
        },
        "openclaw": {
            "workspaces": [
                {
                    "name": ws.name,
                    "path": ws.path,
                    "skills_path": ws.skills_path,
                    "exists": ws.exists,
                    "skills": [_skill_to_dict(s) for s in list_skills(ws.skills_path)],
                }
                for ws in workspaces
            ]
        },
    }
    return jsonify(payload)


@bp.get("/skills/<source>/<skill_name>")
def skill_detail(source: str, skill_name: str):
    """Skill metadata + raw SKILL.md content (full, not truncated)."""
    skill_path = resolve_skill_path(source, skill_name)
    if skill_path is None:
        return jsonify({"error": "Skill not found"}), 404

    skill_md = os.path.join(skill_path, "SKILL.md")
    skill_md_text = ""
    has_md = os.path.exists(skill_md)
    if has_md:
        try:
            with open(skill_md, "r", encoding="utf-8") as fh:
                skill_md_text = fh.read(64 * 1024)  # cap at 64KB for the renderer
        except OSError as exc:
            logger.warning("Failed to read %s: %s", skill_md, exc)

    total_size = 0
    file_count = 0
    last_mtime = 0.0
    for dirpath, _dirnames, filenames in os.walk(skill_path):
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            total_size += st.st_size
            file_count += 1
            if st.st_mtime > last_mtime:
                last_mtime = st.st_mtime

    return jsonify(
        {
            "name": skill_name,
            "source": source,
            "path": skill_path,
            "has_skill_md": has_md,
            "skill_md": skill_md_text,
            "file_count": file_count,
            "total_size": total_size,
            "last_mtime": last_mtime,
        }
    )


@bp.get("/skills/<source>/<skill_name>/files")
def skill_files(source: str, skill_name: str):
    """Recursive file listing for a skill (used by the editor's tree view)."""
    from skillhub.utils import MAX_READ_BYTES

    skill_path = resolve_skill_path(source, skill_name)
    if skill_path is None:
        return jsonify({"error": "Skill not found"}), 404

    entries: list[dict] = []
    skill_root = skill_path
    for dirpath, dirnames, filenames in os.walk(skill_path):
        # Hide our own backups and dotfiles from the tree.
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
        filenames = [f for f in filenames if not f.endswith(".bak") and not f.startswith(".")]

        rel_dir = os.path.relpath(dirpath, skill_root)
        for d in dirnames:
            entries.append(
                {
                    "type": "dir",
                    "path": os.path.join(rel_dir, d).replace("\\", "/"),
                    "name": d,
                    "size": 0,
                    "mtime": 0,
                    "too_large": False,
                }
            )
        for f in filenames:
            full = os.path.join(dirpath, f)
            try:
                st = os.stat(full)
            except OSError:
                continue
            rel = os.path.join(rel_dir, f).replace("\\", "/") if rel_dir != "." else f
            entries.append(
                {
                    "type": "file",
                    "path": rel,
                    "name": f,
                    "size": st.st_size,
                    "mtime": st.st_mtime,
                    "too_large": st.st_size > MAX_READ_BYTES,
                }
            )

    entries.sort(key=lambda e: (e["type"] != "dir", e["path"].lower()))
    return jsonify({"entries": entries})


@bp.post("/skills/<source>/<skill_name>/open")
def open_skill_folder(source: str, skill_name: str):
    """Open a skill directory in the host OS file explorer.

    Validates the ``(source, skill_name)`` pair against
    :func:`skillhub.utils.resolve_skill_path` so a request can never
    escape the user's skill roots.
    """
    skill_path = resolve_skill_path(source, skill_name)
    if skill_path is None:
        return jsonify({"success": False, "message": "Skill not found"}), 404

    ok, message = open_in_file_manager(skill_path)
    return jsonify({"success": ok, "message": message}), (200 if ok else 500)
