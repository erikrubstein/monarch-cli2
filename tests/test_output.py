from __future__ import annotations

from dataclasses import dataclass

from monarch_cli.output import to_plain


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
