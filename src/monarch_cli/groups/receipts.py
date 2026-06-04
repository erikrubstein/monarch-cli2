from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import typer
from monarch_api import (
    Receipt,
    ReceiptFilter,
    ReceiptLineItemUpdate,
    ReceiptPage,
    ReceiptSettings,
    ReceiptStatus,
    delete_receipt,
    get_receipt,
    get_receipt_settings,
    list_receipts,
    match_receipt,
    unmatch_receipt,
    update_receipt,
    update_receipt_settings,
    upload_receipt,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.input import load_json_argument
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import (
    format_bool,
    format_bytes,
    format_money,
    print_key_values,
    print_success,
    print_table,
    print_warning,
    render_json,
)
from monarch_cli.session import require_session

app = typer.Typer(
    help="Upload, inspect, edit, match, and manage receipts.",
    no_args_is_help=True,
)


class SettingState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    status: Annotated[
        ReceiptStatus | None,
        typer.Option("--status", help="Only include this receipt status."),
    ] = None,
    limit: Annotated[int, typer.Option("--limit", help="Number of receipts to return.")] = 100,
    offset: Annotated[int, typer.Option("--offset", help="Number of receipts to skip.")] = 0,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List receipts."""
    session = require_session(session_path)
    page = list_receipts(
        session,
        filters=ReceiptFilter(status=status) if status is not None else None,
        limit=limit,
        offset=offset,
    )
    if json_output:
        render_json(page, include_raw=raw_output)
        return
    print_table(
        f"Receipts ({page.total_count} total)",
        _RECEIPT_COLUMNS,
        (_receipt_row(receipt) for receipt in page.receipts),
        source_rows=page.receipts,
    )


@app.command("get")
@handle_cli_errors
def get_command(
    receipt_id: Annotated[str, typer.Argument(help="Receipt id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one receipt."""
    session = require_session(session_path)
    receipt = get_receipt(session, receipt_id)
    if receipt is None:
        print_warning(f"No receipt found for id {receipt_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(receipt, include_raw=raw_output)
        return
    print_key_values("Receipt", _receipt_details(receipt))
    if receipt.order is not None and receipt.order.line_items:
        print_table(
            "Receipt Line Items",
            _LINE_ITEM_COLUMNS,
            (_line_item_row(item) for item in receipt.order.line_items),
            source_rows=receipt.order.line_items,
        )


@app.command("upload")
@handle_cli_errors
def upload_command(
    file_path: Annotated[Path, typer.Argument(help="Receipt file to upload.")],
    session_path: SessionPathOption = None,
    filename: Annotated[
        str | None,
        typer.Option("--filename", help="Filename to store in Monarch."),
    ] = None,
    content_type: Annotated[
        str | None,
        typer.Option("--content-type", help="File content type."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Upload a receipt."""
    session = require_session(session_path)
    receipt = upload_receipt(
        session,
        file_path,
        filename=filename,
        content_type=content_type,
    )
    if json_output:
        render_json(receipt, include_raw=raw_output)
        return
    print_key_values("Receipt Uploaded", _receipt_details(receipt))


@app.command("delete")
@handle_cli_errors
def delete_command(
    receipt_id: Annotated[str, typer.Argument(help="Receipt id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete a receipt."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete receipt {receipt_id}?"):
        print_warning("Receipt left unchanged.")
        return
    deleted = delete_receipt(session, receipt_id)
    if json_output:
        render_json({"receipt_id": receipt_id, "deleted": deleted})
        return
    if deleted:
        print_success("Receipt deleted.")
    else:
        print_warning("Receipt was not deleted.")


@app.command("match")
@handle_cli_errors
def match_command(
    receipt_id: Annotated[str, typer.Argument(help="Receipt id.")],
    transaction_id: Annotated[str, typer.Argument(help="Transaction id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Match a receipt to a transaction."""
    session = require_session(session_path)
    receipt = match_receipt(session, receipt_id, transaction_id)
    if json_output:
        render_json(receipt, include_raw=raw_output)
        return
    print_key_values("Receipt Matched", _receipt_details(receipt))


@app.command("unmatch")
@handle_cli_errors
def unmatch_command(
    receipt_id: Annotated[str, typer.Argument(help="Receipt id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Remove a receipt transaction match."""
    session = require_session(session_path)
    receipt = unmatch_receipt(session, receipt_id)
    if json_output:
        render_json(receipt, include_raw=raw_output)
        return
    print_key_values("Receipt Unmatched", _receipt_details(receipt))


@app.command("update")
@handle_cli_errors
def update_command(
    receipt_id: Annotated[str, typer.Argument(help="Receipt id.")],
    session_path: SessionPathOption = None,
    merchant_name: Annotated[
        str | None,
        typer.Option("--merchant-name", help="Merchant name."),
    ] = None,
    date: Annotated[str | None, typer.Option("--date", help="Receipt date.")] = None,
    total_before_tax: Annotated[
        float | None,
        typer.Option("--total-before-tax", help="Total before tax."),
    ] = None,
    tax: Annotated[float | None, typer.Option("--tax", help="Tax amount.")] = None,
    tip: Annotated[float | None, typer.Option("--tip", help="Tip amount.")] = None,
    grand_total: Annotated[
        float | None,
        typer.Option("--grand-total", help="Grand total."),
    ] = None,
    line_items_json: Annotated[
        str | None,
        typer.Option("--line-items-json", help="JSON array of line item updates."),
    ] = None,
    line_items_file: Annotated[
        Path | None,
        typer.Option("--line-items-file", help="Path to a JSON file of line item updates."),
    ] = None,
    transaction_date: Annotated[
        str | None,
        typer.Option("--transaction-date", help="Linked transaction date."),
    ] = None,
    transaction_total: Annotated[
        float | None,
        typer.Option("--transaction-total", help="Linked transaction total."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a receipt."""
    session = require_session(session_path)
    receipt = update_receipt(
        session,
        receipt_id,
        merchant_name=merchant_name,
        date=date,
        total_before_tax=total_before_tax,
        tax=tax,
        tip=tip,
        grand_total=grand_total,
        line_items=(
            _line_item_updates(load_json_argument(line_items_json, line_items_file))
            if line_items_json is not None or line_items_file is not None
            else None
        ),
        transaction_date=transaction_date,
        transaction_total=transaction_total,
    )
    if json_output:
        render_json(receipt, include_raw=raw_output)
        return
    print_key_values("Receipt Updated", _receipt_details(receipt))


@app.command("settings")
@handle_cli_errors
def settings_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show receipt settings."""
    session = require_session(session_path)
    settings = get_receipt_settings(session)
    if json_output:
        render_json(settings, include_raw=raw_output)
        return
    print_key_values("Receipt Settings", _settings_details(settings))


@app.command("update-settings")
@handle_cli_errors
def update_settings_command(
    session_path: SessionPathOption = None,
    auto_categorize: Annotated[
        SettingState | None,
        typer.Option("--auto-categorize", help="Receipt auto-categorization setting."),
    ] = None,
    update_transaction_notes: Annotated[
        SettingState | None,
        typer.Option(
            "--update-transaction-notes",
            help="Transaction note update setting.",
        ),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update receipt settings."""
    session = require_session(session_path)
    settings = update_receipt_settings(
        session,
        auto_categorize=_setting_value(auto_categorize),
        update_transaction_notes=_setting_value(update_transaction_notes),
    )
    if json_output:
        render_json(settings, include_raw=raw_output)
        return
    print_key_values("Receipt Settings Updated", _settings_details(settings))


_RECEIPT_COLUMNS = [
    ("id", "meta"),
    ("status", "muted"),
    ("merchant", ""),
    ("date", "muted"),
    ("total", ""),
    ("matched", "muted"),
    ("transaction_id", "meta"),
    ("attachment", "muted"),
]
_LINE_ITEM_COLUMNS = [
    ("id", "meta"),
    ("title", ""),
    ("quantity", "muted"),
    ("price", ""),
    ("total", ""),
    ("category", "muted"),
]


def _receipt_row(receipt: Receipt) -> dict[str, object]:
    order = receipt.order
    return {
        "id": receipt.id,
        "status": _enum_value(receipt.status),
        "merchant": order.merchant_name if order else None,
        "date": order.date if order else None,
        "total": format_money(order.grand_total if order else None),
        "matched": format_bool(receipt.is_matched),
        "transaction_id": receipt.transaction_id,
        "attachment": receipt.attachment.filename if receipt.attachment else None,
    }


def _receipt_details(receipt: Receipt) -> dict[str, object]:
    order = receipt.order
    attachment = receipt.attachment
    return {
        "id": receipt.id,
        "status": _enum_value(receipt.status),
        "merchant": order.merchant_name if order else None,
        "date": order.date if order else None,
        "total_before_tax": format_money(order.total_before_tax if order else None),
        "tax": format_money(order.tax if order else None),
        "tip": format_money(order.tip if order else None),
        "grand_total": format_money(order.grand_total if order else None),
        "matched": format_bool(receipt.is_matched),
        "transaction_id": receipt.transaction_id,
        "attachment": attachment.filename if attachment else None,
        "attachment_size": format_bytes(attachment.size_bytes if attachment else None),
        "created_at": receipt.created_at,
        "updated_at": receipt.updated_at,
    }


def _line_item_row(item) -> dict[str, object]:
    return {
        "id": item.id,
        "title": item.title,
        "quantity": item.quantity,
        "price": format_money(item.price),
        "total": format_money(item.total),
        "category": item.category.name if item.category else None,
    }


def _settings_details(settings: ReceiptSettings) -> dict[str, object]:
    return {
        "auto_categorize": format_bool(settings.auto_categorize),
        "update_transaction_notes": format_bool(settings.update_transaction_notes),
    }


def _line_item_updates(data: Any) -> list[ReceiptLineItemUpdate]:
    if not isinstance(data, list):
        raise ValueError("Line item input must be a JSON array.")
    updates = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Line item {index} must be a JSON object.")
        line_item_id = item.get("line_item_id")
        if not isinstance(line_item_id, str) or not line_item_id:
            raise ValueError(f"Line item {index} must include line_item_id.")
        updates.append(ReceiptLineItemUpdate(**item))
    return updates


def _setting_value(value: SettingState | None) -> bool | None:
    if value is None:
        return None
    return value == SettingState.ENABLED


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))
