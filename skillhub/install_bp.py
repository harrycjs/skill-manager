"""Install blueprint — Skillhub CLI bootstrap + per-skill install.

Originally lived in the monolithic ``app.py``; the two download paths
(``ensure_skillhub_installed`` and ``install_skillhub``) were almost
identical and contained a duplicated ``return`` line. This module
extracts them into a single helper :func:`_download_and_install_cli`.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

from flask import Blueprint, jsonify, request

from skillhub.utils import (
    SKILLHUB_DOWNLOAD_URL,
    claude_skills_path,
    home_dir,
    list_openclaw_workspaces,
    skillhub_cli_path,
)

logger = logging.getLogger(__name__)

bp = Blueprint("install", __name__, url_prefix="/api")

SKILLHUB_SKILL_MD = """# Skillhub

## Description
技能商店 - 从这里安装更多 Claude/OpenCLAW 技能

## Usage
使用 skillhub CLI 安装技能：
- skillhub search <关键词> - 搜索技能
- skillhub install <技能名> - 安装技能

## CLI 安装
如需重新安装 CLI，请运行：
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash
"""


def _download_and_install_cli() -> tuple[bool, str]:
    """Download the Skillhub CLI tarball and drop the ``cli/`` folder into place.

    Idempotent: removes any previous ``~/.skill-hub/cli`` before copying.
    Returns ``(success, message)``.
    """
    home = home_dir()
    temp_dir = os.path.join(home, ".skill-temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    tar_path = os.path.join(temp_dir, "latest.tar.gz")
    try:
        dl = subprocess.run(
            ["curl", "-fsSL", SKILLHUB_DOWNLOAD_URL, "-o", tar_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if dl.returncode != 0 or not os.path.exists(tar_path):
            return False, "下载 Skillhub CLI 失败"

        subprocess.run(
            ["tar", "-xzf", tar_path, "-C", temp_dir],
            capture_output=True,
            text=True,
            check=False,
        )

        cli_source = os.path.join(temp_dir, "cli")
        cli_dest = os.path.join(home, ".skill-hub", "cli")
        if not os.path.isdir(cli_source):
            return False, "下载包结构异常,未找到 cli/"

        os.makedirs(os.path.dirname(cli_dest), exist_ok=True)
        if os.path.exists(cli_dest):
            shutil.rmtree(cli_dest)
        shutil.copytree(cli_source, cli_dest)

        skillhub_skill_path = os.path.join(claude_skills_path(), "skillhub")
        os.makedirs(skillhub_skill_path, exist_ok=True)
        with open(
            os.path.join(skillhub_skill_path, "SKILL.md"), "w", encoding="utf-8"
        ) as fh:
            fh.write(SKILLHUB_SKILL_MD)

        return True, "Skillhub CLI 已安装"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as exc:
        logger.warning("Skillhub install failed: %s", exc)
        return False, f"安装失败: {exc}"
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def ensure_skillhub_installed() -> bool:
    """Best-effort bootstrap used on app startup."""
    if os.path.exists(skillhub_cli_path()):
        return True
    ok, msg = _download_and_install_cli()
    if not ok:
        logger.warning("Skillhub auto-install: %s", msg)
    return os.path.exists(skillhub_cli_path())


@bp.post("/install-skillhub")
def install_skillhub():
    """User-facing endpoint to (re)install the Skillhub CLI."""
    if os.path.exists(os.path.join(home_dir(), ".skill-hub", "cli")):
        return jsonify({"success": True, "message": "Skillhub CLI 已安装"})

    ok, message = _download_and_install_cli()
    return jsonify({"success": ok, "message": message}), (200 if ok else 500)


@bp.post("/install-skill")
def install_skill():
    data = request.json or {}
    skill_name = (data.get("skillName") or "").strip()
    targets = data.get("targets") or []

    if not skill_name:
        return jsonify({"success": False, "message": "请输入技能名称"}), 400
    if not targets:
        return jsonify({"success": False, "message": "请选择至少一个安装目标"}), 400
    if not os.path.exists(skillhub_cli_path()):
        return jsonify({"success": False, "message": "请先安装 Skillhub CLI"}), 400

    results: list[str] = []

    if "claude" in targets:
        results.append(_run_cli(skill_name, claude_skills_path(), "Claude Code"))

    for ws in list_openclaw_workspaces():
        if ws.name in targets:
            results.append(_run_cli(skill_name, ws.skills_path, f"OpenCLAW {ws.name}"))

    if not results:
        return jsonify({"success": False, "message": "没有匹配的目标"}), 400

    return jsonify({"success": True, "message": "\n".join(results)})


def _run_cli(skill_name: str, target_dir: str, label: str) -> str:
    """Invoke the Skillhub CLI for ``skill_name`` into ``target_dir``."""
    try:
        result = subprocess.run(
            ["python", skillhub_cli_path(), "--dir", target_dir, "install", skill_name, "--force"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=target_dir,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as exc:
        return f"{label}: 安装失败 - {exc}"

    if result.returncode == 0:
        return f"已安装到 {label}"
    return f"{label}: {result.stderr.strip() or result.stdout.strip() or '未知错误'}"
