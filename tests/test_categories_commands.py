from __future__ import annotations

from monarch_api import Category, CategoryFilter, CategoryGroup, CategoryGroupReference, CategoryType
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_categories_list_passes_filters(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_categories(session, *, filters=None, include_disabled=False):
        captured["filters"] = filters
        captured["include_disabled"] = include_disabled
        return [
            Category(
                id="cat-123",
                name="Groceries",
                group=CategoryGroupReference(id="group-123", name="Food", type=CategoryType.EXPENSE),
            )
        ]

    monkeypatch.setattr("monarch_cli.groups.categories.list_categories", fake_list_categories)

    result = runner.invoke(
        app,
        [
            "categories",
            "list",
            "--session-path",
            str(session_path),
            "--group-id",
            "group-123",
            "--type",
            "expense",
            "--include-disabled",
        ],
    )

    assert result.exit_code == 0
    assert "Groceries" in result.output
    assert captured["filters"] == CategoryFilter(
        group_ids=["group-123"],
        types=[CategoryType.EXPENSE],
    )
    assert captured["include_disabled"] is True


def test_categories_create_group_passes_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_create_category_group(session, *, name, type):
        captured["name"] = name
        captured["type"] = type
        return CategoryGroup(id="group-123", name=name, type=type)

    monkeypatch.setattr(
        "monarch_cli.groups.categories.create_category_group",
        fake_create_category_group,
    )

    result = runner.invoke(
        app,
        [
            "categories",
            "create-group",
            "--session-path",
            str(session_path),
            "--name",
            "Food",
            "--type",
            "expense",
        ],
    )

    assert result.exit_code == 0
    assert captured == {"name": "Food", "type": CategoryType.EXPENSE}
    assert "Food" in result.output


def test_categories_remove_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_remove_category(session, category_id, *, move_to_category_id=None):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("monarch_cli.groups.categories.remove_category", fake_remove_category)

    result = runner.invoke(
        app,
        ["categories", "remove", "cat-123", "--session-path", str(session_path)],
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
