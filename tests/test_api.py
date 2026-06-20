"""Smoke tests for the public API."""

from __future__ import annotations

import json


def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_index_renders(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Skill Manager" in res.data


def test_import_skills_lists_both_sources(client):
    res = client.get("/api/import-skills")
    assert res.status_code == 200
    payload = res.get_json()
    names = [s["name"] for s in payload["claude"]["skills"]]
    assert names == ["hello-skill"]
    ws_names = [w["name"] for w in payload["openclaw"]["workspaces"]]
    assert set(ws_names) == {"workspace", "workspace-extra"}


def test_skill_detail(client):
    res = client.get("/api/skills/claude/hello-skill")
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "hello-skill"
    assert data["has_skill_md"] is True
    assert "Hello" in data["skill_md"]
    assert data["file_count"] >= 2


def test_skill_detail_unknown_returns_404(client):
    res = client.get("/api/skills/claude/does-not-exist")
    assert res.status_code == 404


def test_skill_files_tree(client):
    res = client.get("/api/skills/claude/hello-skill/files")
    assert res.status_code == 200
    entries = res.get_json()["entries"]
    paths = {e["path"] for e in entries}
    assert "SKILL.md" in paths
    assert any(p.startswith("src/") for p in paths)
    # No .bak entries
    assert not any(e["path"].endswith(".bak") for e in entries)


def test_read_and_write_file(client):
    rel = "SKILL.md"
    res = client.get("/api/skills/claude/hello-skill/file", query_string={"path": rel})
    assert res.status_code == 200
    payload = res.get_json()
    assert payload["editable"] is True
    new_content = payload["content"] + "\n\n_edited via test_"
    put = client.put(
        "/api/skills/claude/hello-skill/file",
        data=json.dumps({"path": rel, "content": new_content}),
        content_type="application/json",
    )
    assert put.status_code == 200
    body = put.get_json()
    assert body["success"] is True
    assert body["backup"] is not None
    # Re-read to confirm persistence.
    again = client.get("/api/skills/claude/hello-skill/file", query_string={"path": rel})
    assert "_edited via test_" in again.get_json()["content"]


def test_write_rejects_traversal(client):
    put = client.put(
        "/api/skills/claude/hello-skill/file",
        data=json.dumps({"path": "../../../etc/passwd", "content": "x"}),
        content_type="application/json",
    )
    assert put.status_code == 400


def test_write_rejects_disallowed_extension(client):
    put = client.put(
        "/api/skills/claude/hello-skill/file",
        data=json.dumps({"path": "evil.exe", "content": "x"}),
        content_type="application/json",
    )
    assert put.status_code == 415


def test_write_rejects_oversize(client):
    huge = "x" * (3 * 1024 * 1024)  # 3 MiB
    put = client.put(
        "/api/skills/claude/hello-skill/file",
        data=json.dumps({"path": "big.md", "content": huge}),
        content_type="application/json",
    )
    assert put.status_code == 413


def test_distribute_skills(client, tmp_path):
    target = tmp_path / "project"
    res = client.post(
        "/api/distribute-skills",
        data=json.dumps(
            {
                "skills": [{"name": "hello-skill", "path": None}],  # path filled below
                "targetFolder": str(target),
            }
        ),
        content_type="application/json",
    )
    # Source path missing → graceful skip, still success:True.
    assert res.status_code == 200
    assert "跳过" in res.get_json()["message"]


def test_distribute_skills_requires_target(client):
    res = client.post(
        "/api/distribute-skills",
        data=json.dumps({"skills": [], "targetFolder": ""}),
        content_type="application/json",
    )
    assert res.status_code == 400


def test_index_exposes_skillhub_website_link(client):
    """The install page should advertise the Skillhub marketplace URL."""
    res = client.get("/")
    assert res.status_code == 200
    body = res.data.decode("utf-8")
    from skillhub.utils import SKILLHUB_WEBSITE_URL

    assert SKILLHUB_WEBSITE_URL in body
    assert "target=\"_blank\"" in body  # opens in a new tab
    assert "noopener" in body  # safe rel attribute


def test_skillhub_website_url_overridable_via_config(temp_home, skills_root):
    """Flask config takes precedence over the default URL."""
    from skillhub import create_app

    app = create_app()
    app.config["SKILLHUB_WEBSITE_URL"] = "https://example.test/custom"
    client = app.test_client()
    body = client.get("/").data.decode("utf-8")
    assert "https://example.test/custom" in body
    # The default URL must NOT appear when overridden.
    from skillhub.utils import SKILLHUB_WEBSITE_URL as DEFAULT

    if DEFAULT != "https://example.test/custom":
        assert DEFAULT not in body


def test_open_skill_folder_calls_helper(client, monkeypatch):
    """The endpoint should resolve the path and call the helper."""
    from skillhub import skills_bp

    called = {}

    def fake_open(path):
        called["path"] = path
        return True, "已请求系统文件管理器"

    monkeypatch.setattr(skills_bp, "open_in_file_manager", fake_open)
    res = client.post("/api/skills/claude/hello-skill/open")
    assert res.status_code == 200
    assert res.get_json()["success"] is True
    assert called["path"].endswith("hello-skill")


def test_open_skill_folder_unknown_returns_404(client):
    res = client.post("/api/skills/claude/does-not-exist/open")
    assert res.status_code == 404


def test_open_skill_folder_rejects_bad_source(client):
    res = client.post("/api/skills/evil-source/x/open")
    assert res.status_code == 404


def test_open_in_file_manager_rejects_missing_path():
    from skillhub.open_folder import open_in_file_manager

    ok, msg = open_in_file_manager("/nonexistent/path/should/never/exist")
    assert ok is False
    assert "不存在" in msg or "失败" in msg
