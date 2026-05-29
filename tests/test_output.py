from __future__ import annotations

from dataclasses import dataclass

from monarch_cli.output import project_fields, projected_columns, to_plain, value_at_path


@dataclass
class Example:
    id: str
    raw: dict[str, object] | None = None


def test_to_plain_omits_raw_by_default() -> None:
    assert to_plain(Example(id="abc", raw={"hidden": True})) == {"id": "abc"}


def test_to_plain_can_include_raw() -> None:
    assert to_plain(Example(id="abc", raw={"hidden": True}), include_raw=True) == {
        "id": "abc",
        "raw": {"hidden": True},
    }


def test_project_fields_selects_dotted_paths() -> None:
    value = {
        "id": "abc",
        "merchant": {"name": "Coffee"},
        "tags": [{"name": "work"}, {"name": "travel"}],
    }

    assert project_fields(value, ["id", "merchant.name", "tags.name"]) == {
        "id": "abc",
        "merchant.name": "Coffee",
        "tags.name": ["work", "travel"],
    }


def test_projected_columns_reuses_known_styles_and_mutes_unknown_fields() -> None:
    columns = projected_columns(
        ["id", "merchant", "notes", "category.name", "custom_value"],
        [("id", "meta"), ("merchant", "")],
    )

    assert columns == [
        ("id", "meta"),
        ("merchant", ""),
        ("notes", "muted"),
        ("category.name", "muted"),
        ("custom_value", "muted"),
    ]


def test_value_at_path_returns_none_for_missing_paths() -> None:
    assert value_at_path({"id": "abc"}, "merchant.name") is None
