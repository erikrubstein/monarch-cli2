from __future__ import annotations

from typing import Annotated

import typer
from monarch_api import (
    ReportGroup,
    ReportResult,
    ReportRow,
    ReportSort,
    ReportTimeframe,
    SavedReport,
    TransactionFilter,
    create_saved_report,
    delete_saved_report,
    get_report_data,
    get_saved_report,
    list_saved_reports,
    update_saved_report,
)

from monarch_cli.errors import handle_cli_errors, raise_cli_error
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import format_money, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Run reports and manage saved reports.",
    no_args_is_help=True,
)

GroupByOption = Annotated[
    list[ReportGroup] | None,
    typer.Option("--group-by", help="Group report rows. Repeatable."),
]
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
GoalIdsOption = Annotated[
    list[str] | None,
    typer.Option("--goal-id", help="Only include this goal. Repeatable."),
]


@app.command("data")
@handle_cli_errors
def data_command(
    session_path: SessionPathOption = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="Start date.")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date", help="End date.")] = None,
    search: Annotated[str | None, typer.Option("--search", help="Search text.")] = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    category_group_ids: CategoryGroupIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    tag_ids: TagIdsOption = None,
    goal_ids: GoalIdsOption = None,
    min_amount: Annotated[
        float | None,
        typer.Option("--min-amount", help="Minimum absolute amount."),
    ] = None,
    max_amount: Annotated[
        float | None,
        typer.Option("--max-amount", help="Maximum absolute amount."),
    ] = None,
    group_by: GroupByOption = None,
    timeframe: Annotated[
        ReportTimeframe | None,
        typer.Option("--timeframe", help="Group rows by timeframe."),
    ] = None,
    sort_by: Annotated[
        ReportSort | None,
        typer.Option("--sort-by", help="Sort report rows."),
    ] = None,
    no_fill_empty: Annotated[
        bool,
        typer.Option("--no-fill-empty", help="Do not fill empty timeframe values."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Run report data."""
    session = require_session(session_path)
    result = get_report_data(
        session,
        filters=_transaction_filter(
            start_date=start_date,
            end_date=end_date,
            search=search,
            account_ids=account_ids,
            category_ids=category_ids,
            category_group_ids=category_group_ids,
            merchant_ids=merchant_ids,
            tag_ids=tag_ids,
            goal_ids=goal_ids,
            min_amount=min_amount,
            max_amount=max_amount,
        ),
        group_by=group_by or ReportGroup.CATEGORY,
        timeframe=timeframe,
        sort_by=sort_by,
        fill_empty_values=not no_fill_empty,
    )
    if json_output:
        render_json(result, include_raw=raw_output)
        return
    print_key_values("Report Summary", _summary_details(result))
    print_table("Report Rows", _REPORT_ROW_COLUMNS, (_report_row(row) for row in result.rows), source_rows=result.rows)


@app.command("list-saved")
@handle_cli_errors
def list_saved_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List saved reports."""
    session = require_session(session_path)
    reports = list_saved_reports(session)
    if json_output:
        render_json(reports, include_raw=raw_output)
        return
    print_table("Saved Reports", _SAVED_REPORT_COLUMNS, (_saved_report_row(report) for report in reports), source_rows=reports)


@app.command("get-saved")
@handle_cli_errors
def get_saved_command(
    report_id: Annotated[str, typer.Argument(help="Saved report id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one saved report."""
    session = require_session(session_path)
    report = get_saved_report(session, report_id)
    if report is None:
        raise_cli_error(f"No saved report found for id {report_id}.")
    if json_output:
        render_json(report, include_raw=raw_output)
        return
    print_key_values("Saved Report", _saved_report_details(report))


@app.command("create-saved")
@handle_cli_errors
def create_saved_command(
    name: Annotated[str, typer.Argument(help="Saved report name.")],
    session_path: SessionPathOption = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="Start date.")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date", help="End date.")] = None,
    search: Annotated[str | None, typer.Option("--search", help="Search text.")] = None,
    account_ids: AccountIdsOption = None,
    category_ids: CategoryIdsOption = None,
    category_group_ids: CategoryGroupIdsOption = None,
    merchant_ids: MerchantIdsOption = None,
    tag_ids: TagIdsOption = None,
    goal_ids: GoalIdsOption = None,
    group_by: GroupByOption = None,
    timeframe: Annotated[
        ReportTimeframe | None,
        typer.Option("--timeframe", help="Saved report timeframe."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Create a saved report."""
    session = require_session(session_path)
    report = create_saved_report(
        session,
        name,
        filters=_transaction_filter(
            start_date=start_date,
            end_date=end_date,
            search=search,
            account_ids=account_ids,
            category_ids=category_ids,
            category_group_ids=category_group_ids,
            merchant_ids=merchant_ids,
            tag_ids=tag_ids,
            goal_ids=goal_ids,
        ),
        group_by=group_by or ReportGroup.CATEGORY,
        timeframe=timeframe,
    )
    if json_output:
        render_json(report, include_raw=raw_output)
        return
    print_key_values("Saved Report Created", _saved_report_details(report))


@app.command("update-saved")
@handle_cli_errors
def update_saved_command(
    report_id: Annotated[str, typer.Argument(help="Saved report id.")],
    name: Annotated[str, typer.Option("--name", help="Saved report name.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a saved report."""
    session = require_session(session_path)
    report = update_saved_report(session, report_id, name=name)
    if json_output:
        render_json(report, include_raw=raw_output)
        return
    print_key_values("Saved Report Updated", _saved_report_details(report))


@app.command("delete-saved")
@handle_cli_errors
def delete_saved_command(
    report_id: Annotated[str, typer.Argument(help="Saved report id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete a saved report."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete saved report {report_id}?"):
        print_warning("Saved report left unchanged.")
        return
    deleted = delete_saved_report(session, report_id)
    if json_output:
        render_json({"report_id": report_id, "deleted": deleted})
        return
    if deleted:
        print_success("Saved report deleted.")
    else:
        print_warning("Saved report was not deleted.")


_REPORT_ROW_COLUMNS = [
    ("group", ""),
    ("total", ""),
    ("income", ""),
    ("expenses", ""),
    ("count", "muted"),
    ("average", ""),
]
_SAVED_REPORT_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("group_by", "muted"),
    ("timeframe", "muted"),
]


def _transaction_filter(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    search: str | None = None,
    account_ids: list[str] | None = None,
    category_ids: list[str] | None = None,
    category_group_ids: list[str] | None = None,
    merchant_ids: list[str] | None = None,
    tag_ids: list[str] | None = None,
    goal_ids: list[str] | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> TransactionFilter | None:
    values = {
        "start_date": start_date,
        "end_date": end_date,
        "search": search,
        "account_ids": account_ids,
        "category_ids": category_ids,
        "category_group_ids": category_group_ids,
        "merchant_ids": merchant_ids,
        "tag_ids": tag_ids,
        "goal_ids": goal_ids,
        "min_absolute_amount": min_amount,
        "max_absolute_amount": max_amount,
    }
    if not any(value is not None and value != [] for value in values.values()):
        return None
    return TransactionFilter(**values)


def _summary_details(result: ReportResult) -> dict[str, object]:
    summary = result.summary
    return {
        "total": format_money(summary.total),
        "income": format_money(summary.income),
        "expenses": format_money(summary.expenses),
        "savings": format_money(summary.savings),
        "count": summary.count,
        "average": format_money(summary.average),
        "first_date": summary.first_date,
        "last_date": summary.last_date,
    }


def _report_row(row: ReportRow) -> dict[str, object]:
    summary = row.summary
    return {
        "group": row.group.label,
        "total": format_money(summary.total),
        "income": format_money(summary.income),
        "expenses": format_money(summary.expenses),
        "count": summary.count,
        "average": format_money(summary.average),
    }


def _saved_report_row(report: SavedReport) -> dict[str, object]:
    return {
        "id": report.id,
        "name": report.name,
        "group_by": _group_names(report.group_by),
        "timeframe": _enum_value(report.timeframe),
    }


def _saved_report_details(report: SavedReport) -> dict[str, object]:
    return {
        "id": report.id,
        "name": report.name,
        "group_by": _group_names(report.group_by),
        "timeframe": _enum_value(report.timeframe),
    }


def _group_names(groups: list[ReportGroup] | None) -> str:
    if not groups:
        return ""
    return ", ".join(group.value for group in groups)


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))
