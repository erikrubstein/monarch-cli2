from __future__ import annotations

import dataclasses
import json
from enum import Enum
from pathlib import Path
from typing import Any

from rich.table import Table

from monarch_cli.theme import console


def render_json(value: Any, *, include_raw: bool = False) -> None:
    console.print_json(json.dumps(to_plain(value, include_raw=include_raw), indent=2))


def to_plain(value: Any, *, include_raw: bool = False) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_plain(getattr(value, field.name), include_raw=include_raw)
            for field in dataclasses.fields(value)
            if include_raw or field.name != "raw"
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list | tuple):
        return [to_plain(item, include_raw=include_raw) for item in value]
    if isinstance(value, dict):
        return {
            str(key): to_plain(item, include_raw=include_raw)
            for key, item in value.items()
            if include_raw or key != "raw"
        }
    return value


def print_key_values(
    title: str,
    rows: dict[str, object],
    *,
    json_output: bool = False,
) -> None:
    if json_output:
        render_json(rows)
        return

    table = Table(
        title=title,
        title_style="accent",
        show_header=False,
        box=None,
        padding=(0, 1),
    )
    table.add_column("Field", style="muted")
    table.add_column("Value")
    for key, value in rows.items():
        table.add_row(key, "" if value is None else str(value))
    console.print(table)


def print_success(message: str) -> None:
    console.print(f"[success]{message}[/success]")


def print_warning(message: str) -> None:
    console.print(f"[warning]{message}[/warning]")


def print_error(message: str) -> None:
    console.print(f"[error]{message}[/error]")
