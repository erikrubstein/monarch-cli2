from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from monarch_api import (
    Account,
    AccountBalance,
    AccountFilter,
    AccountHistoryPoint,
    NetWorthBreakdownPoint,
    NetWorthSnapshot,
    create_manual_account,
    delete_account,
    get_account,
    get_account_history,
    get_historical_balances,
    get_net_worth_breakdown,
    get_net_worth_performance,
    list_accounts,
    update_account,
)

from monarch_cli.errors import handle_cli_errors, raise_cli_error
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import (
    format_bool,
    format_money,
    print_key_values,
    print_success,
    print_table,
    print_warning,
    render_json,
)
from monarch_cli.session import require_session

app = typer.Typer(
    help="List, inspect, create, update, and delete accounts.",
    no_args_is_help=True,
)


class NetWorthSetting(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"


class VisibilitySetting(str, Enum):
    VISIBLE = "visible"
    HIDDEN = "hidden"


FilterAccountIdsOption = Annotated[
    list[str] | None,
    typer.Option("--account-id", help="Only include this account. Repeatable."),
]
FilterAccountTypesOption = Annotated[
    list[str] | None,
    typer.Option("--account-type", help="Only include this account type. Repeatable."),
]
FilterAccountSubtypesOption = Annotated[
    list[str] | None,
    typer.Option("--account-subtype", help="Only include this account subtype. Repeatable."),
]
FilterGroupsOption = Annotated[
    list[str] | None,
    typer.Option("--group", help="Only include this account group. Repeatable."),
]
IncludeHiddenOption = Annotated[
    bool,
    typer.Option("--include-hidden", help="Include hidden accounts."),
]
IncludeDeletedOption = Annotated[
    bool,
    typer.Option("--include-deleted", help="Include deleted accounts."),
]


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    account_ids: FilterAccountIdsOption = None,
    account_types: FilterAccountTypesOption = None,
    account_subtypes: FilterAccountSubtypesOption = None,
    groups: FilterGroupsOption = None,
    include_hidden: IncludeHiddenOption = False,
    include_deleted: IncludeDeletedOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List accounts."""
    session = require_session(session_path)
    accounts = list_accounts(
        session,
        filters=_account_filter(
            account_ids=account_ids,
            account_types=account_types,
            account_subtypes=account_subtypes,
            groups=groups,
            include_hidden=include_hidden,
            include_deleted=include_deleted,
        ),
    )
    if json_output:
        render_json(accounts, include_raw=raw_output)
        return
    print_table("Accounts", _ACCOUNT_COLUMNS, (_account_row(account) for account in accounts), source_rows=accounts)


@app.command("get")
@handle_cli_errors
def get_command(
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one account."""
    session = require_session(session_path)
    account = get_account(session, account_id)
    if account is None:
        raise_cli_error(f"No account found for id {account_id}.")
    if json_output:
        render_json(account, include_raw=raw_output)
        return
    print_key_values("Account", _account_details(account))


@app.command("net-worth-performance")
@handle_cli_errors
def net_worth_performance_command(
    session_path: SessionPathOption = None,
    start_date: Annotated[
        str | None,
        typer.Option("--start-date", help="Start date, such as 2026-01-01."),
    ] = None,
    end_date: Annotated[
        str | None,
        typer.Option("--end-date", help="End date, such as 2026-05-28."),
    ] = None,
    adaptive_granularity: Annotated[
        bool,
        typer.Option("--adaptive-granularity", help="Let Monarch choose chart granularity."),
    ] = False,
    account_ids: FilterAccountIdsOption = None,
    account_types: FilterAccountTypesOption = None,
    account_subtypes: FilterAccountSubtypesOption = None,
    groups: FilterGroupsOption = None,
    include_hidden: IncludeHiddenOption = False,
    include_deleted: IncludeDeletedOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show net worth over time."""
    session = require_session(session_path)
    snapshots = get_net_worth_performance(
        session,
        start_date=start_date,
        end_date=end_date,
        filters=_account_filter(
            account_ids=account_ids,
            account_types=account_types,
            account_subtypes=account_subtypes,
            groups=groups,
            include_hidden=include_hidden,
            include_deleted=include_deleted,
        ),
        use_adaptive_granularity=True if adaptive_granularity else None,
    )
    if json_output:
        render_json(snapshots, include_raw=raw_output)
        return
    print_table(
        "Net Worth Performance",
        _NET_WORTH_PERFORMANCE_COLUMNS,
        (_net_worth_snapshot_row(snapshot) for snapshot in snapshots),
        source_rows=snapshots,
    )


@app.command("net-worth-breakdown")
@handle_cli_errors
def net_worth_breakdown_command(
    start_date: Annotated[str, typer.Argument(help="Start date, such as 2026-01-01.")],
    timeframe: Annotated[
        str,
        typer.Argument(help="Timeframe text. Common values: week, month, quarter, year."),
    ],
    session_path: SessionPathOption = None,
    account_ids: FilterAccountIdsOption = None,
    account_types: FilterAccountTypesOption = None,
    account_subtypes: FilterAccountSubtypesOption = None,
    groups: FilterGroupsOption = None,
    include_hidden: IncludeHiddenOption = False,
    include_deleted: IncludeDeletedOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show net worth broken down by account type."""
    session = require_session(session_path)
    points = get_net_worth_breakdown(
        session,
        start_date,
        timeframe,
        filters=_account_filter(
            account_ids=account_ids,
            account_types=account_types,
            account_subtypes=account_subtypes,
            groups=groups,
            include_hidden=include_hidden,
            include_deleted=include_deleted,
        ),
    )
    if json_output:
        render_json(points, include_raw=raw_output)
        return
    print_table(
        "Net Worth Breakdown",
        _NET_WORTH_BREAKDOWN_COLUMNS,
        (_net_worth_breakdown_row(point) for point in points),
        source_rows=points,
    )


@app.command("historical-balances")
@handle_cli_errors
def historical_balances_command(
    balance_date: Annotated[str, typer.Argument(help="Balance date, such as 2026-05-28.")],
    session_path: SessionPathOption = None,
    account_ids: FilterAccountIdsOption = None,
    account_types: FilterAccountTypesOption = None,
    account_subtypes: FilterAccountSubtypesOption = None,
    groups: FilterGroupsOption = None,
    include_hidden: IncludeHiddenOption = False,
    include_deleted: IncludeDeletedOption = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show account balances on a historical date."""
    session = require_session(session_path)
    balances = get_historical_balances(
        session,
        balance_date,
        filters=_account_filter(
            account_ids=account_ids,
            account_types=account_types,
            account_subtypes=account_subtypes,
            groups=groups,
            include_hidden=include_hidden,
            include_deleted=include_deleted,
        ),
    )
    if json_output:
        render_json(balances, include_raw=raw_output)
        return
    print_table(
        "Historical Balances",
        _HISTORICAL_BALANCE_COLUMNS,
        (_account_balance_row(balance) for balance in balances),
        source_rows=balances,
    )


@app.command("history")
@handle_cli_errors
def history_command(
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show balance history for one account."""
    session = require_session(session_path)
    points = get_account_history(session, account_id)
    if json_output:
        render_json(points, include_raw=raw_output)
        return
    print_table(
        "Account History",
        _ACCOUNT_HISTORY_COLUMNS,
        (_account_history_row(point) for point in points),
        source_rows=points,
    )


@app.command("create-manual")
@handle_cli_errors
def create_manual_command(
    name: Annotated[str, typer.Option("--name", help="Account name.")],
    account_type: Annotated[str, typer.Option("--type", help="Account type.")],
    subtype: Annotated[str, typer.Option("--subtype", help="Account subtype.")],
    session_path: SessionPathOption = None,
    balance: Annotated[
        float | None,
        typer.Option("--balance", help="Starting balance."),
    ] = None,
    exclude_from_net_worth: Annotated[
        bool,
        typer.Option("--exclude-from-net-worth", help="Exclude from net worth."),
    ] = False,
    owner_user_id: Annotated[
        str | None,
        typer.Option("--owner-user-id", help="Owner user id."),
    ] = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Create a manual account."""
    session = require_session(session_path)
    account_id = create_manual_account(
        session,
        name=name,
        type=account_type,
        subtype=subtype,
        balance=balance,
        include_in_net_worth=not exclude_from_net_worth,
        owner_user_id=owner_user_id,
    )
    print_key_values(
        "Account Created",
        {"account_id": account_id},
        json_output=json_output,
    )


@app.command("update")
@handle_cli_errors
def update_command(
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    session_path: SessionPathOption = None,
    name: Annotated[str | None, typer.Option("--name", help="Account name.")] = None,
    account_type: Annotated[
        str | None,
        typer.Option("--type", help="Account type."),
    ] = None,
    subtype: Annotated[
        str | None,
        typer.Option("--subtype", help="Account subtype."),
    ] = None,
    balance: Annotated[float | None, typer.Option("--balance", help="Balance.")] = None,
    net_worth: Annotated[
        NetWorthSetting | None,
        typer.Option("--net-worth", help="Whether to include this account in net worth."),
    ] = None,
    list_visibility: Annotated[
        VisibilitySetting | None,
        typer.Option("--list-visibility", help="Whether this account appears in lists."),
    ] = None,
    report_visibility: Annotated[
        VisibilitySetting | None,
        typer.Option(
            "--report-visibility",
            help="Whether this account's transactions appear in reports.",
        ),
    ] = None,
    owner_user_id: Annotated[
        str | None,
        typer.Option("--owner-user-id", help="Owner user id."),
    ] = None,
    deactivated_at: Annotated[
        str | None,
        typer.Option("--deactivated-at", help="Deactivation date."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update an account."""
    session = require_session(session_path)
    account = update_account(
        session,
        account_id,
        name=name,
        type=account_type,
        subtype=subtype,
        balance=balance,
        include_in_net_worth=_net_worth_value(net_worth),
        hide_from_list=_hidden_value(list_visibility),
        hide_transactions_from_reports=_hidden_value(report_visibility),
        owner_user_id=owner_user_id,
        deactivated_at=deactivated_at,
    )
    if json_output:
        render_json(account, include_raw=raw_output)
        return
    print_key_values("Account Updated", _account_details(account))


@app.command("delete")
@handle_cli_errors
def delete_command(
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete an account."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete account {account_id}?"):
        print_warning("Account left unchanged.")
        return
    deleted = delete_account(session, account_id)
    if json_output:
        render_json({"account_id": account_id, "deleted": deleted})
        return
    if deleted:
        print_success("Account deleted.")
    else:
        print_warning("Account was not deleted.")


_ACCOUNT_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("type", "muted"),
    ("subtype", "muted"),
    ("institution", "muted"),
    ("balance", ""),
    ("net_worth", "muted"),
    ("hidden", "muted"),
]
_NET_WORTH_PERFORMANCE_COLUMNS = [
    ("date", "muted"),
    ("net_worth", ""),
    ("assets", ""),
    ("liabilities", ""),
]
_NET_WORTH_BREAKDOWN_COLUMNS = [
    ("date", "muted"),
    ("account_type", ""),
    ("account_group", "muted"),
    ("balance", ""),
]
_HISTORICAL_BALANCE_COLUMNS = [
    ("account_id", "meta"),
    ("account_type", "muted"),
    ("balance", ""),
    ("net_worth", "muted"),
]
_ACCOUNT_HISTORY_COLUMNS = [
    ("date", "muted"),
    ("balance", ""),
]


def _account_filter(
    *,
    account_ids: list[str] | None,
    account_types: list[str] | None,
    account_subtypes: list[str] | None,
    groups: list[str] | None,
    include_hidden: bool,
    include_deleted: bool,
) -> AccountFilter | None:
    if not any(
        [
            account_ids,
            account_types,
            account_subtypes,
            groups,
            include_hidden,
            include_deleted,
        ]
    ):
        return None
    return AccountFilter(
        account_ids=account_ids,
        account_types=account_types,
        account_subtypes=account_subtypes,
        groups=groups,
        include_hidden=True if include_hidden else None,
        include_deleted=True if include_deleted else None,
    )


def _account_row(account: Account) -> dict[str, object]:
    return {
        "id": account.id,
        "name": account.display_name,
        "type": _display_name(account.type),
        "subtype": _display_name(account.subtype),
        "institution": account.institution.name if account.institution else None,
        "balance": format_money(account.balance),
        "net_worth": format_bool(account.include_in_net_worth),
        "hidden": format_bool(account.is_hidden),
    }


def _account_details(account: Account) -> dict[str, object]:
    return {
        "id": account.id,
        "name": account.display_name,
        "balance": format_money(account.balance),
        "current_balance": format_money(account.current_balance),
        "type": _display_name(account.type),
        "subtype": _display_name(account.subtype),
        "institution": account.institution.name if account.institution else None,
        "owner": account.owner.display_name if account.owner else None,
        "asset": format_bool(account.is_asset),
        "manual": format_bool(account.is_manual),
        "hidden": format_bool(account.is_hidden),
        "sync_disabled": format_bool(account.sync_disabled),
        "include_in_net_worth": format_bool(account.include_in_net_worth),
        "last_updated_at": account.last_updated_at,
    }


def _net_worth_snapshot_row(snapshot: NetWorthSnapshot) -> dict[str, object]:
    return {
        "date": snapshot.date,
        "net_worth": format_money(snapshot.net_worth),
        "assets": format_money(snapshot.assets_balance),
        "liabilities": format_money(snapshot.liabilities_balance),
    }


def _net_worth_breakdown_row(point: NetWorthBreakdownPoint) -> dict[str, object]:
    return {
        "date": point.date,
        "account_type": point.account_type,
        "account_group": point.account_group,
        "balance": format_money(point.balance),
    }


def _account_balance_row(balance: AccountBalance) -> dict[str, object]:
    return {
        "account_id": balance.account_id,
        "account_type": balance.account_type,
        "balance": format_money(balance.balance),
        "net_worth": format_bool(balance.include_in_net_worth),
    }


def _account_history_row(point: AccountHistoryPoint) -> dict[str, object]:
    return {
        "date": point.date,
        "balance": format_money(point.balance),
    }


def _display_name(value: object) -> str | None:
    if value is None:
        return None
    display_name = getattr(value, "display_name", None)
    name = getattr(value, "name", None)
    return display_name or name


def _net_worth_value(value: NetWorthSetting | None) -> bool | None:
    if value is None:
        return None
    return value == NetWorthSetting.INCLUDE


def _hidden_value(value: VisibilitySetting | None) -> bool | None:
    if value is None:
        return None
    return value == VisibilitySetting.HIDDEN
