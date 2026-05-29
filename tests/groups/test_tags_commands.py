from __future__ import annotations

from monarch_api import Tag
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_tags_list_passes_options(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_tags(
        session,
        *,
        search=None,
        limit=None,
        include_transaction_count=False,
    ):
        captured["search"] = search
        captured["limit"] = limit
        captured["include_transaction_count"] = include_transaction_count
        return [Tag(id="tag-123", name="Fun", color="#336699")]

    monkeypatch.setattr("monarch_cli.groups.tags.list_tags", fake_list_tags)

    result = runner.invoke(
        app,
        [
            "tags",
            "list",
            "--session-path",
            str(session_path),
            "--search",
            "fu",
            "--limit",
            "5",
            "--include-transaction-count",
        ],
    )

    assert result.exit_code == 0
    assert "Fun" in result.output
    assert captured == {
        "search": "fu",
        "limit": 5,
        "include_transaction_count": True,
    }


def test_tags_create_passes_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_create_tag(session, *, name, color):
        captured["name"] = name
        captured["color"] = color
        return Tag(id="tag-123", name=name, color=color)

    monkeypatch.setattr("monarch_cli.groups.tags.create_tag", fake_create_tag)

    result = runner.invoke(
        app,
        [
            "tags",
            "create",
            "--session-path",
            str(session_path),
            "--name",
            "Fun",
            "--color",
            "#336699",
        ],
    )

    assert result.exit_code == 0
    assert captured == {"name": "Fun", "color": "#336699"}
    assert "Fun" in result.output


def test_tags_reorder_renders_tags(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_reorder_tag(session, tag_id, *, order):
        captured["tag_id"] = tag_id
        captured["order"] = order
        return [Tag(id=tag_id, name="Fun", order=order)]

    monkeypatch.setattr("monarch_cli.groups.tags.reorder_tag", fake_reorder_tag)

    result = runner.invoke(
        app,
        [
            "tags",
            "reorder",
            "tag-123",
            "--session-path",
            str(session_path),
            "--order",
            "7",
        ],
    )

    assert result.exit_code == 0
    assert captured == {"tag_id": "tag-123", "order": 7}
    assert "Fun" in result.output


def test_tags_delete_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_tag(session, tag_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("monarch_cli.groups.tags.delete_tag", fake_delete_tag)

    result = runner.invoke(
        app,
        ["tags", "delete", "tag-123", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def _write_session(tmp_path):
    session_path = tmp_path / "session.json"
    session_path.write_text(
        """
        {
          "token": "token-123",
          "token_expiration": null,
          "user_id": "user-123",
          "email": "person@example.com"
        }
        """,
        encoding="utf-8",
    )
    return session_path
