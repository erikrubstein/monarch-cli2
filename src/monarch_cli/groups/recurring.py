from __future__ import annotations

from enum import Enum
from typing import Annotated

import typer
from monarch_api import (
    RecurringFilter,
    RecurringFrequency,
    RecurringOccurrence,
    RecurringStatus,
    RecurringStream,
    RecurringSummary,
    RecurringSummaryBucket,
    RecurringType,
    create_recurring_stream,
    get_recurring_stream,
    get_recurring_summary,
    list_recurring_occurrences,
    list_recurring_streams,
    remove_recurring_stream,
    update_recurring_stream,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, SessionPathOption, TrueFalseFilter
from monarch_cli.output import format_bool, format_money, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Manage recurring transactions.",
    no_args_is_help=True,
)


class ActiveState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


AccountIdsOption = Annotated[
    list[str] | None,
    typer.Option("--account-id", help="Only include this account. Repeatable."),
]
CategoryIdsOption = Annotated[
    list[str] | None,
    typer.Option("--category-id", help="Only include this category. Repeatable."),
]
MerchantIdsOption = Annotated[
    list[str] | None,
    typer.Option("--merchant-id", help="Only include this merchant. Repeatable."),
]
RecurringIdsOption = Annotated[
    list[str] | None,
    typer.Option("--recurring-id", help="Only include this recurring item. Repeatable."),
]
FrequencyOption = Annotated[
    list[RecurringFrequency] | None,
    typer.Option("--frequency", help="Only include this frequency. Repeatable."),
]
TypeOption = Annotated[
    list[RecurringType] | None,
    typer.Option("--type", help="Only include this type. Repeatable."),
]


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    recurring_ids: RecurringIdsOption = None,
    frequencies: FrequencyOption = None,
    recurring_types: TypeOption = None,
    completed: Annotated[
        TrueFalseFilter | None,
        typer.Option("--completed", help="Filter by completed status."),
    ] = None,
    exclude_pending: Annotated[
        bool,
        typer.Option("--exclude-pending", help="Exclude pending recurring items."),
    ] = False,
    exclude_liabilities: Annotated[
        bool,
        typer.Option("--exclude-liabilities", help="Exclude liability items."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """List recurring items."""
    session = require_session(session_path)
    streams = list_recurring_streams(
        session,
        filters=_recurring_filter(
            account_ids=account_ids,
            category_ids=category_ids,
            merchant_ids=merchant_ids,
            recurring_ids=recurring_ids,
            frequencies=frequencies,
            recurring_types=recurring_types,
            completed=completed,
        ),
        include_pending=not exclude_pending,
        include_liabilities=not exclude_liabilities,
    )
    if json_output:
        render_json(streams, include_raw=raw_output)
        return
    print_table("Recurring Items", _STREAM_COLUMNS, (_stream_row(stream) for stream in streams), source_rows=streams)


@app.command("get")
@handle_cli_errors
def get_command(
    recurring_id: Annotated[str, typer.Argument(help="Recurring item id.")],
    session_path: SessionPathOption = None,
    exclude_liabilities: Annotated[
        bool,
        typer.Option("--exclude-liabilities", help="Exclude liability items."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show one recurring item."""
    session = require_session(session_path)
    stream = get_recurring_stream(
        session,
        recurring_id,
        include_liabilities=not exclude_liabilities,
    )
    if stream is None:
        print_warning(f"No recurring item found for id {recurring_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(stream, include_raw=raw_output)
        return
    print_key_values("Recurring Item", _stream_details(stream))


@app.command("occurrences")
@handle_cli_errors
def occurrences_command(
    start_date: Annotated[str, typer.Argument(help="Start date, such as 2026-01-01.")],
    end_date: Annotated[str, typer.Argument(help="End date, such as 2026-05-28.")],
    session_path: SessionPathOption = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    recurring_ids: RecurringIdsOption = None,
    frequencies: FrequencyOption = None,
    recurring_types: TypeOption = None,
    completed: Annotated[
        TrueFalseFilter | None,
        typer.Option("--completed", help="Filter by completed status."),
    ] = None,
    exclude_liabilities: Annotated[
        bool,
        typer.Option("--exclude-liabilities", help="Exclude liability items."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """List recurring occurrences."""
    session = require_session(session_path)
    occurrences = list_recurring_occurrences(
        session,
        start_date,
        end_date,
        filters=_recurring_filter(
            account_ids=account_ids,
            category_ids=category_ids,
            merchant_ids=merchant_ids,
            recurring_ids=recurring_ids,
            frequencies=frequencies,
            recurring_types=recurring_types,
            completed=completed,
        ),
        include_liabilities=not exclude_liabilities,
    )
    if json_output:
        render_json(occurrences, include_raw=raw_output)
        return
    print_table("Recurring Occurrences", _OCCURRENCE_COLUMNS, (_occurrence_row(item) for item in occurrences), source_rows=occurrences)


@app.command("summary")
@handle_cli_errors
def summary_command(
    start_date: Annotated[str, typer.Argument(help="Start date, such as 2026-01-01.")],
    end_date: Annotated[str, typer.Argument(help="End date, such as 2026-05-28.")],
    session_path: SessionPathOption = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    recurring_ids: RecurringIdsOption = None,
    frequencies: FrequencyOption = None,
    recurring_types: TypeOption = None,
    completed: Annotated[
        TrueFalseFilter | None,
        typer.Option("--completed", help="Filter by completed status."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Summarize recurring items."""
    session = require_session(session_path)
    summary = get_recurring_summary(
        session,
        start_date,
        end_date,
        filters=_recurring_filter(
            account_ids=account_ids,
            category_ids=category_ids,
            merchant_ids=merchant_ids,
            recurring_ids=recurring_ids,
            frequencies=frequencies,
            recurring_types=recurring_types,
            completed=completed,
        ),
    )
    if json_output:
        render_json(summary, include_raw=raw_output)
        return
    print_table("Recurring Summary", _SUMMARY_COLUMNS, _summary_rows(summary))


@app.command("create")
@handle_cli_errors
def create_command(
    merchant_id: Annotated[str, typer.Argument(help="Merchant id.")],
    frequency: Annotated[RecurringFrequency, typer.Option("--frequency", help="Recurring frequency.")],
    amount: Annotated[float, typer.Option("--amount", help="Recurring amount.")],
    base_date: Annotated[str, typer.Option("--base-date", help="Base date, such as 2026-01-01.")],
    session_path: SessionPathOption = None,
    inactive: Annotated[
        bool,
        typer.Option("--inactive", help="Create the recurring item as inactive."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Create a recurring item for a merchant."""
    session = require_session(session_path)
    stream = create_recurring_stream(
        session,
        merchant_id,
        frequency=frequency,
        amount=amount,
        base_date=base_date,
        is_active=not inactive,
    )
    if json_output:
        render_json(stream, include_raw=raw_output)
        return
    print_key_values("Recurring Item Created", _stream_details(stream))


@app.command("update")
@handle_cli_errors
def update_command(
    recurring_id: Annotated[str, typer.Argument(help="Recurring item id.")],
    session_path: SessionPathOption = None,
    frequency: Annotated[
        RecurringFrequency | None,
        typer.Option("--frequency", help="Recurring frequency."),
    ] = None,
    amount: Annotated[float | None, typer.Option("--amount", help="Recurring amount.")] = None,
    base_date: Annotated[
        str | None,
        typer.Option("--base-date", help="Base date, such as 2026-01-01."),
    ] = None,
    active: Annotated[
        ActiveState | None,
        typer.Option("--active", help="Set whether this recurring item is active."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Update a recurring item."""
    session = require_session(session_path)
    stream = update_recurring_stream(
        session,
        recurring_id,
        frequency=frequency.value if frequency is not None else None,
        amount=amount,
        base_date=base_date,
        is_active=_active_value(active),
    )
    if json_output:
        render_json(stream, include_raw=raw_output)
        return
    print_key_values("Recurring Item Updated", _stream_details(stream))


@app.command("remove")
@handle_cli_errors
def remove_command(
    recurring_id: Annotated[str, typer.Argument(help="Recurring item id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Remove a recurring item."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Remove recurring item {recurring_id}?"):
        print_warning("Recurring item left unchanged.")
        return
    removed = remove_recurring_stream(session, recurring_id)
    if json_output:
        render_json({"recurring_id": recurring_id, "removed": removed})
        return
    if removed:
        print_success("Recurring item removed.")
    else:
        print_warning("Recurring item was not removed.")


_STREAM_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("amount", ""),
    ("next_date", "muted"),
    ("next_amount", ""),
    ("frequency", "muted"),
    ("type", "muted"),
    ("status", "muted"),
    ("account", "muted"),
    ("category", "muted"),
]
_OCCURRENCE_COLUMNS = [
    ("recurring_id", "meta"),
    ("date", "muted"),
    ("name", ""),
    ("amount", ""),
    ("completed", "muted"),
    ("late", "muted"),
    ("account", "muted"),
    ("category", "muted"),
    ("transaction_id", "meta"),
]
_SUMMARY_COLUMNS = [
    ("type", "muted"),
    ("completed", ""),
    ("remaining", ""),
    ("total", ""),
    ("count", "muted"),
    ("pending_amounts", "muted"),
]


def _recurring_filter(
    *,
    account_ids: list[str] | None,
    category_ids: list[str] | None,
    merchant_ids: list[str] | None,
    recurring_ids: list[str] | None,
    frequencies: list[RecurringFrequency] | None,
    recurring_types: list[RecurringType] | None,
    completed: TrueFalseFilter | None,
) -> RecurringFilter | None:
    if not any(
        [
            account_ids,
            category_ids,
            merchant_ids,
            recurring_ids,
            frequencies,
            recurring_types,
            completed,
        ]
    ):
        return None
    return RecurringFilter(
        account_ids=account_ids,
        category_ids=category_ids,
        merchant_ids=merchant_ids,
        recurring_ids=recurring_ids,
        frequencies=frequencies,
        recurring_types=recurring_types,
        is_completed=_true_false_value(completed),
    )


def _stream_row(stream: RecurringStream) -> dict[str, object]:
    return {
        "id": stream.id,
        "name": stream.name,
        "amount": format_money(stream.amount),
        "next_date": stream.next_date,
        "next_amount": format_money(stream.next_amount),
        "frequency": stream.frequency,
        "type": _enum_value(stream.recurring_type),
        "status": _enum_value(stream.status),
        "account": stream.account.display_name if stream.account else "",
        "category": stream.category.name if stream.category else "",
    }


def _stream_details(stream: RecurringStream) -> dict[str, object]:
    return {
        "id": stream.id,
        "name": stream.name,
        "amount": format_money(stream.amount),
        "next_date": stream.next_date,
        "next_amount": format_money(stream.next_amount),
        "base_date": stream.base_date,
        "day_of_month": stream.day_of_month,
        "frequency": stream.frequency,
        "type": _enum_value(stream.recurring_type),
        "status": _enum_value(stream.status),
        "active": format_bool(stream.is_active),
        "approximate": format_bool(stream.is_approximate),
        "merchant": stream.merchant.name if stream.merchant else "",
        "merchant_id": stream.merchant.id if stream.merchant else "",
        "account": stream.account.display_name if stream.account else "",
        "account_id": stream.account.id if stream.account else "",
        "category": stream.category.name if stream.category else "",
        "category_id": stream.category.id if stream.category else "",
        "liability_account_id": stream.liability_account_id,
    }


def _occurrence_row(item: RecurringOccurrence) -> dict[str, object]:
    return {
        "recurring_id": item.recurring_id,
        "date": item.date,
        "name": item.name,
        "amount": format_money(item.amount),
        "completed": format_bool(item.is_completed),
        "late": format_bool(item.is_late),
        "account": item.account.display_name if item.account else "",
        "category": item.category.name if item.category else "",
        "transaction_id": item.transaction_id,
    }


def _summary_rows(summary: RecurringSummary) -> list[dict[str, object]]:
    return [
        _summary_row("expense", summary.expense),
        _summary_row("income", summary.income),
        _summary_row("credit_card", summary.credit_card),
    ]


def _summary_row(name: str, bucket: RecurringSummaryBucket) -> dict[str, object]:
    return {
        "type": name,
        "completed": format_money(bucket.completed),
        "remaining": format_money(bucket.remaining),
        "total": format_money(bucket.total),
        "count": bucket.count,
        "pending_amounts": bucket.pending_amount_count,
    }


def _active_value(value: ActiveState | None) -> bool | None:
    if value is None:
        return None
    return value == ActiveState.ENABLED


def _true_false_value(value: TrueFalseFilter | None) -> bool | None:
    if value is None:
        return None
    return value == TrueFalseFilter.TRUE


def _enum_value(value: Enum | str | None) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return "" if value is None else str(value)
