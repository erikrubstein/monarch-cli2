from __future__ import annotations

from typing import Annotated

import typer
from monarch_api import (
    Merchant,
    MerchantSort,
    delete_merchant,
    get_merchant,
    list_merchants,
    update_merchant,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import format_bool, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="List, inspect, update, and delete merchants.",
    no_args_is_help=True,
)


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    search: Annotated[str | None, typer.Option("--search", help="Search text.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", help="Number of merchants to return.")] = None,
    offset: Annotated[int | None, typer.Option("--offset", help="Number of merchants to skip.")] = None,
    sort: Annotated[
        MerchantSort,
        typer.Option("--sort", help="Sort order."),
    ] = MerchantSort.TRANSACTION_COUNT,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List merchants."""
    session = require_session(session_path)
    merchants = list_merchants(
        session,
        search=search,
        limit=limit,
        offset=offset,
        sort=sort,
    )
    if json_output:
        render_json(merchants, include_raw=raw_output)
        return
    print_table("Merchants", _MERCHANT_COLUMNS, (_merchant_row(merchant) for merchant in merchants), source_rows=merchants)


@app.command("get")
@handle_cli_errors
def get_command(
    merchant_id: Annotated[str, typer.Argument(help="Merchant id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one merchant."""
    session = require_session(session_path)
    merchant = get_merchant(session, merchant_id)
    if merchant is None:
        print_warning(f"No merchant found for id {merchant_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(merchant, include_raw=raw_output)
        return
    print_key_values("Merchant", _merchant_details(merchant))


@app.command("update")
@handle_cli_errors
def update_command(
    merchant_id: Annotated[str, typer.Argument(help="Merchant id.")],
    session_path: SessionPathOption = None,
    name: Annotated[str | None, typer.Option("--name", help="Merchant name.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a merchant."""
    session = require_session(session_path)
    merchant = update_merchant(session, merchant_id, name=name)
    if json_output:
        render_json(merchant, include_raw=raw_output)
        return
    print_key_values("Merchant Updated", _merchant_details(merchant))


@app.command("delete")
@handle_cli_errors
def delete_command(
    merchant_id: Annotated[str, typer.Argument(help="Merchant id.")],
    session_path: SessionPathOption = None,
    move_to_merchant_id: Annotated[
        str | None,
        typer.Option("--move-to-merchant-id", help="Move related data to this merchant."),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete a merchant."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete merchant {merchant_id}?"):
        print_warning("Merchant left unchanged.")
        return
    deleted = delete_merchant(
        session,
        merchant_id,
        move_to_merchant_id=move_to_merchant_id,
    )
    if json_output:
        render_json({"merchant_id": merchant_id, "deleted": deleted})
        return
    if deleted:
        print_success("Merchant deleted.")
    else:
        print_warning("Merchant was not deleted.")


_MERCHANT_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("transactions", "muted"),
    ("rules", "muted"),
    ("deletable", "muted"),
    ("recurring_id", "meta"),
]


def _merchant_row(merchant: Merchant) -> dict[str, object]:
    return {
        "id": merchant.id,
        "name": merchant.name,
        "transactions": merchant.transaction_count,
        "rules": merchant.rule_count,
        "deletable": format_bool(merchant.can_be_deleted),
        "recurring_id": merchant.recurring_id,
    }


def _merchant_details(merchant: Merchant) -> dict[str, object]:
    return {
        "id": merchant.id,
        "name": merchant.name,
        "transactions": merchant.transaction_count,
        "rules": merchant.rule_count,
        "deletable": format_bool(merchant.can_be_deleted),
        "recurring_id": merchant.recurring_id,
        "created_at": merchant.created_at,
        "logo_url": merchant.logo_url,
    }
