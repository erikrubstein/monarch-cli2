from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeAlias, cast

JsonValue: TypeAlias = dict[str, Any] | list[Any] | str | int | float | bool | None


def load_json_argument(value: str | None, path: Path | None) -> JsonValue:
    if value is not None and path is not None:
        raise ValueError("Pass either a JSON value or a JSON file, not both.")

    if value is not None:
        source = value
    elif path is not None:
        source = path.expanduser().read_text(encoding="utf-8")
    else:
        raise ValueError("JSON input is required.")

    return cast(JsonValue, json.loads(source))
