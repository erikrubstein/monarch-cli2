from __future__ import annotations

import dataclasses
import json
from contextvars import ContextVar
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence

from rich.table import Table

from monarch_cli.theme import console

Column = tuple[str, str]
Number = int | float
_output_fields: ContextVar[list[str] | None] = ContextVar("output_fields", default=None)
_append_output_fields: ContextVar[list[str] | None] = ContextVar(
    "append_output_fields",
    default=None,
)
DEFAULT_PROJECTED_FIELD_STYLE = "muted"
PROJECTED_FIELD_STYLES = {
    "id": "meta",
    "date": "muted",
    "timeframe": "muted",
    "month": "muted",
    "created_at": "muted",
    "updated_at": "muted",
    "deleted_at": "muted",
    "account": "muted",
    "account.name": "muted",
    "account_name": "muted",
    "category": "muted",
    "category.name": "muted",
    "category_name": "muted",
    "group": "muted",
    "group.name": "muted",
    "tag": "muted",
    "tags": "muted",
    "tags.name": "muted",
    "type": "muted",
    "status": "muted",
    "review": "muted",
    "pending": "muted",
    "hidden": "muted",
    "disabled": "muted",
    "merchant": "",
    "merchant.name": "",
    "merchant_name": "",
    "name": "",
    "display_name": "",
    "filename": "",
    "amount": "",
    "balance": "",
    "value": "",
    "total": "",
    "average": "",
    "current": "",
    "target": "",
    "planned": "",
    "actual": "",
    "remaining": "",
}


def configure_output_fields(fields: str | None, append_fields: str | None) -> None:
    parsed_fields = parse_output_fields(fields, "--fields")
    parsed_append_fields = parse_output_fields(append_fields, "--append-fields")
    if parsed_fields is not None and parsed_append_fields is not None:
        raise ValueError("Use either --fields or --append-fields, not both.")
    _output_fields.set(parsed_fields)
    _append_output_fields.set(parsed_append_fields)


def clear_output_fields() -> None:
    _output_fields.set(None)
    _append_output_fields.set(None)


def parse_output_fields(value: str | None, option_name: str) -> list[str] | None:
    if value is None:
        return None
    fields = [field.strip() for field in value.split(",") if field.strip()]
    if not fields:
        raise ValueError(f"{option_name} must include at least one field.")
    return fields


def get_output_fields() -> list[str] | None:
    return _output_fields.get()


def get_append_output_fields() -> list[str] | None:
    return _append_output_fields.get()


def render_json(
    value: Any,
    *,
    include_raw: bool = False,
    apply_output_fields: bool = True,
) -> None:
    plain = to_plain(value, include_raw=include_raw)
    if apply_output_fields:
        fields = get_output_fields()
        if fields is not None:
            plain = project_fields(plain, fields)
    console.print_json(json.dumps(plain, indent=2))


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
    source: Any | None = None,
    json_output: bool = False,
) -> None:
    fields = get_output_fields()
    if json_output:
        if fields is not None:
            rows = project_row(source if source is not None else rows, fields)
        render_json(rows, apply_output_fields=False)
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


def print_table(
    title: str,
    columns: Sequence[Column],
    rows: Iterable[dict[str, object]],
    *,
    source_rows: Iterable[Any] | None = None,
    json_output: bool = False,
    raw_output: bool = False,
) -> None:
    row_list = list(rows)
    fields = get_output_fields()
    if json_output:
        if fields is not None:
            source_list = list(source_rows) if source_rows is not None else row_list
            row_list = [project_row(row, fields) for row in source_list]
        render_json(row_list, include_raw=raw_output, apply_output_fields=False)
        return

    append_fields = get_append_output_fields()
    if fields is not None:
        source_list = list(source_rows) if source_rows is not None else row_list
        row_list = [project_row(row, fields) for row in source_list]
        columns = projected_columns(fields, columns)
    elif append_fields is not None:
        source_list = list(source_rows) if source_rows is not None else row_list
        row_list = [
            append_projected_row(row, source, append_fields)
            for row, source in zip(row_list, source_list, strict=True)
        ]
        columns = append_projected_columns(append_fields, columns)

    table = Table(title=title, title_style="accent", border_style="grey35")
    for header, style in columns:
        table.add_column(header, style=style)
    for row in row_list:
        table.add_row(*(format_value(row.get(header)) for header, _style in columns))
    console.print(table)


def format_money(value: Number | str | None) -> str:
    if value is None:
        return ""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"${amount:,.2f}"


def format_bool(value: object) -> str:
    if value is None:
        return ""
    return "yes" if bool(value) else "no"


def format_bytes(value: Number | str | None) -> str:
    if value is None:
        return ""
    try:
        size = int(value)
    except (TypeError, ValueError):
        return str(value)
    units = ["B", "KB", "MB", "GB"]
    amount = float(size)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(amount)} {unit}"
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return str(size)


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list | tuple):
        return ", ".join(format_value(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def projected_columns(fields: Sequence[str], base_columns: Sequence[Column]) -> list[Column]:
    base_styles = {header: style for header, style in base_columns}
    return [(field, projected_field_style(field, base_styles)) for field in fields]


def append_projected_columns(
    fields: Sequence[str],
    base_columns: Sequence[Column],
) -> list[Column]:
    base_headers = {header for header, _style in base_columns}
    appended_fields = [field for field in fields if field not in base_headers]
    return [*base_columns, *projected_columns(appended_fields, base_columns)]


def projected_field_style(field: str, base_styles: dict[str, str]) -> str:
    if field in base_styles:
        return base_styles[field]
    if field in PROJECTED_FIELD_STYLES:
        return PROJECTED_FIELD_STYLES[field]

    leaf = field.rsplit(".", maxsplit=1)[-1]
    if leaf in PROJECTED_FIELD_STYLES:
        return PROJECTED_FIELD_STYLES[leaf]
    if leaf == "id" or leaf.endswith("_id"):
        return "meta"
    if leaf.endswith("_date") or leaf.endswith("_at"):
        return "muted"
    if leaf.startswith(("has_", "is_")):
        return "muted"
    return DEFAULT_PROJECTED_FIELD_STYLE


def project_fields(value: Any, fields: Sequence[str]) -> Any:
    if isinstance(value, list):
        return [project_row(item, fields) for item in value]
    if isinstance(value, tuple):
        return [project_row(item, fields) for item in value]
    return project_row(value, fields)


def project_row(value: Any, fields: Sequence[str]) -> dict[str, Any]:
    plain = to_plain(value)
    return {field: value_at_path(plain, field) for field in fields}


def append_projected_row(
    row: dict[str, object],
    source: Any,
    fields: Sequence[str],
) -> dict[str, object]:
    appended = project_row(source, fields)
    return {**row, **{key: value for key, value in appended.items() if key not in row}}


def value_at_path(value: Any, path: str) -> Any:
    parts = [part for part in path.split(".") if part]
    return _value_at_parts(value, parts)


def _value_at_parts(value: Any, parts: Sequence[str]) -> Any:
    if not parts:
        return value
    if value is None:
        return None

    part = parts[0]
    rest = parts[1:]
    if isinstance(value, dict):
        return _value_at_parts(value.get(part), rest)
    if isinstance(value, list):
        if part.isdigit():
            index = int(part)
            if index >= len(value):
                return None
            return _value_at_parts(value[index], rest)
        return [_value_at_parts(item, parts) for item in value]
    return None


def print_success(message: str) -> None:
    console.print(f"[success]{message}[/success]")


def print_warning(message: str) -> None:
    console.print(f"[warning]{message}[/warning]")


def print_error(message: str) -> None:
    console.print(f"[error]{message}[/error]")
