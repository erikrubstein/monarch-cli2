from __future__ import annotations

from typing import Annotated

import typer
from monarch_api import (
    CashflowBreakdown,
    CashflowBreakdownDirection,
    CashflowBreakdownGroup,
    CashflowBreakdownRow,
    CashflowFilter,
    CashflowInterval,
    CashflowSummary,
    CashflowTrendPoint,
    get_cashflow_breakdown,
    get_cashflow_summary,
    get_cashflow_trends,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.options import JsonOption, RawOption, SessionPathOption
from monarch_cli.output import format_money, print_key_values, print_table, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Summarize cashflow trends and breakdowns.",
    no_args_is_help=True,
)

AccountIdsOption = Annotated[
    list[str] | None,
    typer.Option("--account-id", help="Only include this account. Repeatable."),
]
CategoryIdsOption = Annotated[
    list[str] | None,
    typer.Option("--category-id", help="Only include this category. Repeatable."),
]
CategoryGroupIdsOption = Annotated[
    list[str] | None,
    typer.Option("--category-group-id", help="Only include this category group. Repeatable."),
]
MerchantIdsOption = Annotated[
    list[str] | None,
    typer.Option("--merchant-id", help="Only include this merchant. Repeatable."),
]
TagIdsOption = Annotated[
    list[str] | None,
    typer.Option("--tag-id", help="Only include this tag. Repeatable."),
]
IncludeHiddenOption = Annotated[
    bool,
    typer.Option("--include-hidden", help="Include hidden transactions."),
]


@app.command("summary")
@handle_cli_errors
def summary_command(
    start_date: Annotated[str, typer.Argument(help="Start date, such as 2026-01-01.")],
    end_date: Annotated[str, typer.Argument(help="End date, such as 2026-05-28.")],
    session_path: SessionPathOption = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    category_group_ids: CategoryGroupIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    tag_ids: TagIdsOption = None,
    include_hidden: IncludeHiddenOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Show cashflow summary."""
    session = require_session(session_path)
    summary = get_cashflow_summary(
        session,
        start_date,
        end_date,
        filters=_cashflow_filter(
            account_ids=account_ids,
            category_ids=category_ids,
            category_group_ids=category_group_ids,
            merchant_ids=merchant_ids,
            tag_ids=tag_ids,
            include_hidden=include_hidden,
        ),
    )
    if json_output:
        render_json(summary, include_raw=raw_output)
        return
    print_key_values("Cashflow Summary", _summary_details(summary))


@app.command("trends")
@handle_cli_errors
def trends_command(
    start_date: Annotated[str, typer.Argument(help="Start date, such as 2026-01-01.")],
    end_date: Annotated[str, typer.Argument(help="End date, such as 2026-05-28.")],
    session_path: SessionPathOption = None,
    interval: Annotated[
        CashflowInterval,
        typer.Option("--interval", help="Trend interval."),
    ] = CashflowInterval.MONTH,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    category_group_ids: CategoryGroupIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    tag_ids: TagIdsOption = None,
    include_hidden: IncludeHiddenOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Show cashflow trends over time."""
    session = require_session(session_path)
    points = get_cashflow_trends(
        session,
        start_date,
        end_date,
        interval=interval,
        filters=_cashflow_filter(
            account_ids=account_ids,
            category_ids=category_ids,
            category_group_ids=category_group_ids,
            merchant_ids=merchant_ids,
            tag_ids=tag_ids,
            include_hidden=include_hidden,
        ),
    )
    if json_output:
        render_json(points, include_raw=raw_output)
        return
    print_table(
        "Cashflow Trends",
        _TREND_COLUMNS,
        (_trend_row(point) for point in points),
    )


@app.command("breakdown")
@handle_cli_errors
def breakdown_command(
    start_date: Annotated[str, typer.Argument(help="Start date, such as 2026-01-01.")],
    end_date: Annotated[str, typer.Argument(help="End date, such as 2026-05-28.")],
    direction: Annotated[
        CashflowBreakdownDirection,
        typer.Argument(help="Cashflow direction."),
    ],
    session_path: SessionPathOption = None,
    group_by: Annotated[
        CashflowBreakdownGroup,
        typer.Option("--group-by", help="Breakdown grouping."),
    ] = CashflowBreakdownGroup.CATEGORY,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    category_group_ids: CategoryGroupIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    tag_ids: TagIdsOption = None,
    include_hidden: IncludeHiddenOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
) -> None:
    """Show cashflow breakdown rows."""
    session = require_session(session_path)
    breakdown = get_cashflow_breakdown(
        session,
        start_date,
        end_date,
        direction,
        group_by=group_by,
        filters=_cashflow_filter(
            account_ids=account_ids,
            category_ids=category_ids,
            category_group_ids=category_group_ids,
            merchant_ids=merchant_ids,
            tag_ids=tag_ids,
            include_hidden=include_hidden,
        ),
    )
    if json_output:
        render_json(breakdown, include_raw=raw_output)
        return
    print_table(
        f"Cashflow Breakdown ({breakdown.direction.value})",
        _BREAKDOWN_COLUMNS,
        (_breakdown_row(row) for row in breakdown.rows),
    )


_TREND_COLUMNS = [
    ("label", "muted"),
    ("start_date", "muted"),
    ("end_date", "muted"),
    ("income", ""),
    ("expenses", ""),
    ("savings", ""),
    ("savings_rate", "muted"),
]
_BREAKDOWN_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("amount", ""),
    ("percent", "muted"),
    ("transactions", "muted"),
]


def _cashflow_filter(
    *,
    account_ids: list[str] | None,
    category_ids: list[str] | None,
    category_group_ids: list[str] | None,
    merchant_ids: list[str] | None,
    tag_ids: list[str] | None,
    include_hidden: bool,
) -> CashflowFilter | None:
    if not any(
        [
            account_ids,
            category_ids,
            category_group_ids,
            merchant_ids,
            tag_ids,
            include_hidden,
        ]
    ):
        return None
    return CashflowFilter(
        account_ids=account_ids,
        category_ids=category_ids,
        category_group_ids=category_group_ids,
        merchant_ids=merchant_ids,
        tag_ids=tag_ids,
        include_hidden=include_hidden,
    )


def _summary_details(summary: CashflowSummary) -> dict[str, object]:
    return {
        "start_date": summary.start_date,
        "end_date": summary.end_date,
        "income": format_money(summary.income),
        "expenses": format_money(summary.expenses),
        "savings": format_money(summary.savings),
        "savings_rate": _format_percent(summary.savings_rate),
    }


def _trend_row(point: CashflowTrendPoint) -> dict[str, object]:
    return {
        "label": point.label,
        "start_date": point.start_date,
        "end_date": point.end_date,
        "income": format_money(point.income),
        "expenses": format_money(point.expenses),
        "savings": format_money(point.savings),
        "savings_rate": _format_percent(point.savings_rate),
    }


def _breakdown_row(row: CashflowBreakdownRow) -> dict[str, object]:
    return {
        "id": row.id,
        "name": row.name,
        "amount": format_money(row.amount),
        "percent": _format_percent(row.percent),
        "transactions": row.transaction_count,
    }


def _format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}%"
