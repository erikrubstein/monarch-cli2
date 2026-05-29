from __future__ import annotations

from typing import Annotated

import typer
from monarch_api import (
    Holding,
    InvestmentAccount,
    InvestmentPerformance,
    InvestmentPerformancePoint,
    Portfolio,
    PortfolioAllocation,
    Security,
    create_manual_holding,
    delete_manual_holding,
    get_holding,
    get_holding_performance,
    get_portfolio,
    get_security,
    list_holdings,
    list_investment_accounts,
    search_securities,
    update_manual_holding,
)

from monarch_cli.errors import handle_cli_errors
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, SessionPathOption
from monarch_cli.output import format_bool, format_money, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Inspect investment accounts, holdings, and securities.",
    no_args_is_help=True,
)

AccountIdsOption = Annotated[
    list[str] | None,
    typer.Option("--account-id", help="Only include this account. Repeatable."),
]


@app.command("accounts")
@handle_cli_errors
def accounts_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """List investment accounts."""
    session = require_session(session_path)
    accounts = list_investment_accounts(session)
    if json_output:
        render_json(accounts, include_raw=raw_output)
        return
    print_table("Investment Accounts", _ACCOUNT_COLUMNS, (_account_row(account) for account in accounts), source_rows=accounts)


@app.command("portfolio")
@handle_cli_errors
def portfolio_command(
    session_path: SessionPathOption = None,
    account_ids: AccountIdsOption = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="Start date.")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date", help="End date.")] = None,
    include_hidden_holdings: Annotated[
        bool,
        typer.Option("--include-hidden-holdings", help="Include hidden holdings."),
    ] = False,
    top_movers_limit: Annotated[
        int | None,
        typer.Option("--top-movers-limit", help="Number of top movers to include."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show portfolio summary."""
    session = require_session(session_path)
    portfolio = get_portfolio(
        session,
        account_ids=account_ids,
        start_date=start_date,
        end_date=end_date,
        include_hidden_holdings=include_hidden_holdings,
        top_movers_limit=top_movers_limit,
    )
    if json_output:
        render_json(portfolio, include_raw=raw_output)
        return
    print_key_values("Portfolio", _portfolio_details(portfolio))
    print_table("Allocations", _ALLOCATION_COLUMNS, (_allocation_row(row) for row in portfolio.allocations), source_rows=portfolio.allocations)
    print_table("Holdings", _HOLDING_COLUMNS, (_holding_row(holding) for holding in portfolio.holdings), source_rows=portfolio.holdings)


@app.command("holdings")
@handle_cli_errors
def holdings_command(
    session_path: SessionPathOption = None,
    account_ids: AccountIdsOption = None,
    include_hidden_holdings: Annotated[
        bool,
        typer.Option("--include-hidden-holdings", help="Include hidden holdings."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """List holdings."""
    session = require_session(session_path)
    holdings = list_holdings(
        session,
        account_ids=account_ids,
        include_hidden_holdings=include_hidden_holdings,
    )
    if json_output:
        render_json(holdings, include_raw=raw_output)
        return
    print_table("Holdings", _HOLDING_COLUMNS, (_holding_row(holding) for holding in holdings), source_rows=holdings)


@app.command("get-holding")
@handle_cli_errors
def get_holding_command(
    holding_id: Annotated[str, typer.Argument(help="Holding id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show one holding."""
    session = require_session(session_path)
    holding = get_holding(session, holding_id)
    if holding is None:
        print_warning(f"No holding found for id {holding_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(holding, include_raw=raw_output)
        return
    print_key_values("Holding", _holding_details(holding))
    if holding.tax_lots:
        print_table("Tax Lots", _TAX_LOT_COLUMNS, (_tax_lot_row(lot) for lot in holding.tax_lots), source_rows=holding.tax_lots)


@app.command("search-securities")
@handle_cli_errors
def search_securities_command(
    query: Annotated[str, typer.Argument(help="Search text.")],
    session_path: SessionPathOption = None,
    limit: Annotated[int, typer.Option("--limit", help="Number of securities to return.")] = 20,
    original_order: Annotated[
        bool,
        typer.Option("--original-order", help="Keep the original search ordering."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Search securities."""
    session = require_session(session_path)
    securities = search_securities(
        session,
        query,
        limit=limit,
        order_by_popularity=not original_order,
    )
    if json_output:
        render_json(securities, include_raw=raw_output)
        return
    print_table("Securities", _SECURITY_COLUMNS, (_security_row(security) for security in securities), source_rows=securities)


@app.command("get-security")
@handle_cli_errors
def get_security_command(
    security_id: Annotated[str, typer.Argument(help="Security id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show one security."""
    session = require_session(session_path)
    security = get_security(session, security_id)
    if security is None:
        print_warning(f"No security found for id {security_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(security, include_raw=raw_output)
        return
    print_key_values("Security", _security_details(security))


@app.command("holding-performance")
@handle_cli_errors
def holding_performance_command(
    holding_id: Annotated[str, typer.Argument(help="Holding id.")],
    session_path: SessionPathOption = None,
    start_date: Annotated[str | None, typer.Option("--start-date", help="Start date.")] = None,
    end_date: Annotated[str | None, typer.Option("--end-date", help="End date.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show holding performance."""
    session = require_session(session_path)
    performance = get_holding_performance(
        session,
        holding_id,
        start_date=start_date,
        end_date=end_date,
    )
    if performance is None:
        print_warning(f"No performance found for holding id {holding_id}.")
        raise typer.Exit(1)
    if json_output:
        render_json(performance, include_raw=raw_output)
        return
    if performance.security is not None:
        print_key_values("Security", _security_details(performance.security))
    print_table("Performance", _PERFORMANCE_COLUMNS, (_performance_row(point) for point in performance.points), source_rows=performance.points)


@app.command("create-holding")
@handle_cli_errors
def create_holding_command(
    account_id: Annotated[str, typer.Option("--account-id", help="Account id.")],
    security_id: Annotated[str, typer.Option("--security-id", help="Security id.")],
    quantity: Annotated[float, typer.Option("--quantity", help="Holding quantity.")],
    session_path: SessionPathOption = None,
    cost_basis: Annotated[float | None, typer.Option("--cost-basis", help="Cost basis.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Create a manual holding."""
    session = require_session(session_path)
    holding = create_manual_holding(
        session,
        account_id=account_id,
        security_id=security_id,
        quantity=quantity,
        cost_basis=cost_basis,
    )
    if json_output:
        render_json(holding, include_raw=raw_output)
        return
    print_key_values("Holding Created", _holding_details(holding))


@app.command("update-holding")
@handle_cli_errors
def update_holding_command(
    holding_id: Annotated[str, typer.Argument(help="Holding id.")],
    session_path: SessionPathOption = None,
    quantity: Annotated[float | None, typer.Option("--quantity", help="Holding quantity.")] = None,
    cost_basis: Annotated[float | None, typer.Option("--cost-basis", help="Cost basis.")] = None,
    security_type: Annotated[
        str | None,
        typer.Option("--security-type", help="Security type."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Update a manual holding."""
    session = require_session(session_path)
    holding = update_manual_holding(
        session,
        holding_id,
        quantity=quantity,
        cost_basis=cost_basis,
        security_type=security_type,
    )
    if json_output:
        render_json(holding, include_raw=raw_output)
        return
    print_key_values("Holding Updated", _holding_details(holding))


@app.command("delete-holding")
@handle_cli_errors
def delete_holding_command(
    holding_id: Annotated[str, typer.Argument(help="Holding id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Delete a manual holding."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete manual holding {holding_id}?"):
        print_warning("Holding left unchanged.")
        return
    deleted = delete_manual_holding(session, holding_id)
    if json_output:
        render_json({"holding_id": holding_id, "deleted": deleted})
        return
    if deleted:
        print_success("Holding deleted.")
    else:
        print_warning("Holding was not deleted.")


_ACCOUNT_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("subtype", "muted"),
    ("taxable", "muted"),
    ("net_worth", "muted"),
    ("sync_disabled", "muted"),
]
_HOLDING_COLUMNS = [
    ("id", "meta"),
    ("ticker", "muted"),
    ("name", ""),
    ("account", "muted"),
    ("quantity", "muted"),
    ("value", ""),
    ("cost_basis", ""),
    ("manual", "muted"),
]
_SECURITY_COLUMNS = [
    ("id", "meta"),
    ("ticker", "muted"),
    ("name", ""),
    ("type", "muted"),
    ("price", ""),
    ("one_day", ""),
]
_ALLOCATION_COLUMNS = [
    ("label", ""),
    ("value", ""),
    ("percent", "muted"),
]
_PERFORMANCE_COLUMNS = [
    ("date", "muted"),
    ("value", ""),
    ("return", "muted"),
]
_TAX_LOT_COLUMNS = [
    ("id", "meta"),
    ("acquisition_date", "muted"),
    ("quantity", "muted"),
    ("cost_basis_per_unit", ""),
]


def _account_row(account: InvestmentAccount) -> dict[str, object]:
    return {
        "id": account.id,
        "name": account.display_name,
        "subtype": account.subtype_display,
        "taxable": format_bool(account.is_taxable),
        "net_worth": format_bool(account.include_in_net_worth),
        "sync_disabled": format_bool(account.sync_disabled),
    }


def _portfolio_details(portfolio: Portfolio) -> dict[str, object]:
    summary = portfolio.summary
    return {
        "total_value": format_money(summary.total_value),
        "total_change": format_money(summary.total_change_dollars),
        "total_change_percent": _format_percent(summary.total_change_percent),
        "one_day_change": format_money(summary.one_day_change_dollars),
        "one_day_change_percent": _format_percent(summary.one_day_change_percent),
        "holdings": summary.holdings_count,
    }


def _holding_row(holding: Holding) -> dict[str, object]:
    return {
        "id": holding.id,
        "ticker": holding.ticker,
        "name": holding.name,
        "account": holding.account.display_name if holding.account else "",
        "quantity": holding.quantity,
        "value": format_money(holding.value),
        "cost_basis": format_money(holding.cost_basis),
        "manual": format_bool(holding.is_manual),
    }


def _holding_details(holding: Holding) -> dict[str, object]:
    return {
        "id": holding.id,
        "aggregate_id": holding.aggregate_id,
        "ticker": holding.ticker,
        "name": holding.name,
        "type": holding.type_display or holding.type,
        "account": holding.account.display_name if holding.account else "",
        "account_id": holding.account.id if holding.account else "",
        "security": holding.security.name if holding.security else "",
        "security_id": holding.security.id if holding.security else "",
        "quantity": holding.quantity,
        "value": format_money(holding.value),
        "cost_basis": format_money(holding.cost_basis),
        "user_cost_basis": format_money(holding.user_cost_basis),
        "closing_price": format_money(holding.closing_price),
        "manual": format_bool(holding.is_manual),
        "last_synced_at": holding.last_synced_at,
    }


def _security_row(security: Security) -> dict[str, object]:
    return {
        "id": security.id,
        "ticker": security.ticker,
        "name": security.name,
        "type": security.type_display or security.type,
        "price": format_money(security.current_price or security.closing_price),
        "one_day": _format_percent(security.one_day_change_percent),
    }


def _security_details(security: Security) -> dict[str, object]:
    return {
        "id": security.id,
        "ticker": security.ticker,
        "name": security.name,
        "type": security.type_display or security.type,
        "current_price": format_money(security.current_price),
        "current_price_updated_at": security.current_price_updated_at,
        "closing_price": format_money(security.closing_price),
        "closing_price_updated_at": security.closing_price_updated_at,
        "one_day_change": format_money(security.one_day_change_dollars),
        "one_day_change_percent": _format_percent(security.one_day_change_percent),
        "category_group": security.category_group,
        "broad_asset_class": security.broad_asset_class,
        "morningstar_category": security.morningstar_category,
    }


def _allocation_row(allocation: PortfolioAllocation) -> dict[str, object]:
    return {
        "label": allocation.label,
        "value": format_money(allocation.value),
        "percent": _format_percent(allocation.percent_of_portfolio),
    }


def _performance_row(point: InvestmentPerformancePoint) -> dict[str, object]:
    return {
        "date": point.date,
        "value": format_money(point.value),
        "return": _format_percent(point.return_percent),
    }


def _tax_lot_row(lot) -> dict[str, object]:
    return {
        "id": lot.id,
        "acquisition_date": lot.acquisition_date,
        "quantity": lot.acquisition_quantity,
        "cost_basis_per_unit": format_money(lot.cost_basis_per_unit),
    }


def _format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}%"
