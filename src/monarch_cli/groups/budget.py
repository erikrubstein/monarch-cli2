from __future__ import annotations

from enum import Enum
from typing import Annotated

import typer
from monarch_api import (
    Budget,
    BudgetAmount,
    BudgetCategory,
    BudgetCategoryGroup,
    BudgetCategoryRow,
    BudgetFlexRow,
    BudgetGroupRow,
    BudgetMonthTotals,
    BudgetRolloverFrequency,
    BudgetRolloverPeriod,
    BudgetRolloverType,
    BudgetSettings,
    BudgetVariability,
    CategoryType,
    FlexRolloverSettings,
    clear_budget,
    create_budget,
    get_budget,
    get_budget_category,
    get_budget_settings,
    get_flex_rollover_settings,
    list_budget_months,
    reset_budget,
    reset_budget_rollover,
    set_budget_amount,
    set_budget_category_rollover,
    set_budget_category_variability,
    set_budget_group_amount,
    set_budget_group_rollover,
    set_budget_group_variability,
    set_flex_budget_amount,
    set_flex_rollover_settings,
)

from monarch_cli.errors import handle_cli_errors, raise_cli_error
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import format_bool, format_money, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Manage budget months, amounts, and rollover settings.",
    no_args_is_help=True,
)


class EnabledState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


@app.command("get")
@handle_cli_errors
def get_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one budget month."""
    session = require_session(session_path)
    budget = get_budget(session, month)
    if json_output:
        render_json(budget, include_raw=raw_output)
        return
    _print_budget(budget, title="Budget")


@app.command("months")
@handle_cli_errors
def months_command(
    start_month: Annotated[str, typer.Argument(help="Start month, such as 2026-01.")],
    end_month: Annotated[str, typer.Argument(help="End month, such as 2026-12.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List budget months."""
    session = require_session(session_path)
    budgets = list_budget_months(session, start_month, end_month)
    if json_output:
        render_json(budgets, include_raw=raw_output)
        return
    print_table("Budget Months", _MONTH_COLUMNS, (_month_row(budget) for budget in budgets), source_rows=budgets)


@app.command("settings")
@handle_cli_errors
def settings_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show budget settings."""
    session = require_session(session_path)
    settings = get_budget_settings(session)
    if json_output:
        render_json(settings, include_raw=raw_output)
        return
    print_key_values("Budget Settings", _settings_details(settings))


@app.command("category")
@handle_cli_errors
def category_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one budget category."""
    session = require_session(session_path)
    row = get_budget_category(session, month, category_id)
    if row is None:
        raise_cli_error(f"No budget category found for id {category_id}.")
    if json_output:
        render_json(row, include_raw=raw_output)
        return
    print_key_values("Budget Category", _category_details(row.category, row.amount))


@app.command("flex-rollover-settings")
@handle_cli_errors
def flex_rollover_settings_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show flex rollover settings."""
    session = require_session(session_path)
    settings = get_flex_rollover_settings(session)
    if json_output:
        render_json(settings, include_raw=raw_output)
        return
    print_key_values("Flex Rollover Settings", _flex_settings_details(settings))


@app.command("set-amount")
@handle_cli_errors
def set_amount_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    amount: Annotated[float, typer.Argument(help="Budget amount.")],
    session_path: SessionPathOption = None,
    apply_to_future: Annotated[
        bool,
        typer.Option("--apply-to-future", help="Apply the amount to future months."),
    ] = False,
    default_amount: Annotated[float | None, typer.Option("--default-amount", help="Default amount.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set a category budget amount."""
    session = require_session(session_path)
    row = set_budget_amount(
        session,
        month,
        category_id,
        amount,
        apply_to_future=apply_to_future,
        default_amount=default_amount,
    )
    if json_output:
        render_json(row, include_raw=raw_output)
        return
    print_key_values("Budget Amount Updated", _category_details(row.category, row.amount))


@app.command("set-group-amount")
@handle_cli_errors
def set_group_amount_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    category_group_id: Annotated[str, typer.Argument(help="Category group id.")],
    amount: Annotated[float, typer.Argument(help="Budget amount.")],
    session_path: SessionPathOption = None,
    apply_to_future: Annotated[
        bool,
        typer.Option("--apply-to-future", help="Apply the amount to future months."),
    ] = False,
    default_amount: Annotated[float | None, typer.Option("--default-amount", help="Default amount.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set a category group budget amount."""
    session = require_session(session_path)
    row = set_budget_group_amount(
        session,
        month,
        category_group_id,
        amount,
        apply_to_future=apply_to_future,
        default_amount=default_amount,
    )
    if json_output:
        render_json(row, include_raw=raw_output)
        return
    print_key_values("Budget Group Amount Updated", _group_details(row.group, row.amount))


@app.command("set-flex-amount")
@handle_cli_errors
def set_flex_amount_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    amount: Annotated[float, typer.Argument(help="Flex budget amount.")],
    session_path: SessionPathOption = None,
    apply_to_future: Annotated[
        bool,
        typer.Option("--apply-to-future", help="Apply the amount to future months."),
    ] = False,
    default_amount: Annotated[float | None, typer.Option("--default-amount", help="Default amount.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set a flex budget amount."""
    session = require_session(session_path)
    row = set_flex_budget_amount(
        session,
        month,
        amount,
        apply_to_future=apply_to_future,
        default_amount=default_amount,
    )
    if json_output:
        render_json(row, include_raw=raw_output)
        return
    print_key_values("Flex Budget Amount Updated", _flex_details(row))


@app.command("set-category-variability")
@handle_cli_errors
def set_category_variability_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    variability: Annotated[BudgetVariability, typer.Argument(help="Budget variability.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set category budget variability."""
    session = require_session(session_path)
    category = set_budget_category_variability(session, category_id, variability)
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category Variability Updated", _category_details(category, None))


@app.command("set-group-variability")
@handle_cli_errors
def set_group_variability_command(
    category_group_id: Annotated[str, typer.Argument(help="Category group id.")],
    variability: Annotated[BudgetVariability, typer.Argument(help="Budget variability.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set category group budget variability."""
    session = require_session(session_path)
    group = set_budget_group_variability(session, category_group_id, variability)
    if json_output:
        render_json(group, include_raw=raw_output)
        return
    print_key_values("Group Variability Updated", _group_details(group, None))


@app.command("set-category-rollover")
@handle_cli_errors
def set_category_rollover_command(
    category_id: Annotated[str, typer.Argument(help="Category id.")],
    state: Annotated[EnabledState, typer.Option("--state", help="Set rollover state.")],
    session_path: SessionPathOption = None,
    start_month: Annotated[str | None, typer.Option("--start-month", help="Rollover start month.")] = None,
    starting_balance: Annotated[float | None, typer.Option("--starting-balance", help="Starting balance.")] = None,
    frequency: Annotated[
        BudgetRolloverFrequency | None,
        typer.Option("--frequency", help="Rollover frequency."),
    ] = None,
    target_amount: Annotated[float | None, typer.Option("--target-amount", help="Target amount.")] = None,
    rollover_type: Annotated[
        BudgetRolloverType | None,
        typer.Option("--type", help="Rollover type."),
    ] = None,
    apply_to_future: Annotated[
        bool,
        typer.Option("--apply-to-future", help="Apply rollover settings to future months."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set category rollover settings."""
    session = require_session(session_path)
    category = set_budget_category_rollover(
        session,
        category_id,
        enabled=_enabled_value(state),
        start_month=start_month,
        starting_balance=starting_balance,
        frequency=frequency,
        target_amount=target_amount,
        rollover_type=rollover_type,
        apply_to_future=True if apply_to_future else None,
    )
    if json_output:
        render_json(category, include_raw=raw_output)
        return
    print_key_values("Category Rollover Updated", _category_details(category, None))


@app.command("set-group-rollover")
@handle_cli_errors
def set_group_rollover_command(
    category_group_id: Annotated[str, typer.Argument(help="Category group id.")],
    state: Annotated[EnabledState, typer.Option("--state", help="Set rollover state.")],
    session_path: SessionPathOption = None,
    start_month: Annotated[str | None, typer.Option("--start-month", help="Rollover start month.")] = None,
    starting_balance: Annotated[float | None, typer.Option("--starting-balance", help="Starting balance.")] = None,
    rollover_type: Annotated[
        BudgetRolloverType | None,
        typer.Option("--type", help="Rollover type."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set category group rollover settings."""
    session = require_session(session_path)
    group = set_budget_group_rollover(
        session,
        category_group_id,
        enabled=_enabled_value(state),
        start_month=start_month,
        starting_balance=starting_balance,
        rollover_type=rollover_type,
    )
    if json_output:
        render_json(group, include_raw=raw_output)
        return
    print_key_values("Group Rollover Updated", _group_details(group, None))


@app.command("set-flex-rollover")
@handle_cli_errors
def set_flex_rollover_command(
    state: Annotated[EnabledState, typer.Option("--state", help="Set rollover state.")],
    session_path: SessionPathOption = None,
    start_month: Annotated[str | None, typer.Option("--start-month", help="Rollover start month.")] = None,
    starting_balance: Annotated[float | None, typer.Option("--starting-balance", help="Starting balance.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set flex rollover settings."""
    session = require_session(session_path)
    settings = set_flex_rollover_settings(
        session,
        enabled=_enabled_value(state),
        start_month=start_month,
        starting_balance=starting_balance,
    )
    if json_output:
        render_json(settings, include_raw=raw_output)
        return
    print_key_values("Flex Rollover Updated", _flex_settings_details(settings))


@app.command("reset-rollover")
@handle_cli_errors
def reset_rollover_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    session_path: SessionPathOption = None,
    category_id: Annotated[str | None, typer.Option("--category-id", help="Category id.")] = None,
    category_group_id: Annotated[str | None, typer.Option("--category-group-id", help="Category group id.")] = None,
    starting_balance: Annotated[float | None, typer.Option("--starting-balance", help="Starting balance.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Reset rollover for a category or group."""
    session = require_session(session_path)
    budget = reset_budget_rollover(
        session,
        month,
        category_id=category_id,
        category_group_id=category_group_id,
        starting_balance=starting_balance,
    )
    if json_output:
        render_json(budget, include_raw=raw_output)
        return
    _print_budget(budget, title="Budget Rollover Reset")


@app.command("create")
@handle_cli_errors
def create_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Create a budget month."""
    session = require_session(session_path)
    budget = create_budget(session, month)
    if json_output:
        render_json(budget, include_raw=raw_output)
        return
    _print_budget(budget, title="Budget Created")


@app.command("reset")
@handle_cli_errors
def reset_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    session_path: SessionPathOption = None,
    category_ids: Annotated[
        list[str] | None,
        typer.Option("--category-id", help="Only reset this category. Repeatable."),
    ] = None,
    category_type: Annotated[CategoryType | None, typer.Option("--category-type", help="Category type.")] = None,
    budget_variability: Annotated[
        BudgetVariability | None,
        typer.Option("--variability", help="Budget variability."),
    ] = None,
    overwrite_existing: Annotated[
        bool,
        typer.Option("--overwrite-existing", help="Overwrite existing budget amounts."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Reset budget amounts."""
    session = require_session(session_path)
    budget = reset_budget(
        session,
        month,
        category_ids=category_ids,
        category_type=category_type,
        budget_variability=budget_variability,
        overwrite_existing=overwrite_existing,
    )
    if json_output:
        render_json(budget, include_raw=raw_output)
        return
    _print_budget(budget, title="Budget Reset")


@app.command("clear")
@handle_cli_errors
def clear_command(
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    session_path: SessionPathOption = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Clear budget amounts for a month."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Clear budget amounts for {month}?"):
        print_warning("Budget left unchanged.")
        return
    budget = clear_budget(session, month, confirm=True)
    if json_output:
        render_json(budget, include_raw=raw_output)
        return
    _print_budget(budget, title="Budget Cleared")


_MONTH_COLUMNS = [
    ("month", "muted"),
    ("income_planned", ""),
    ("income_actual", ""),
    ("expenses_planned", ""),
    ("expenses_actual", ""),
    ("expenses_remaining", ""),
]
_TOTAL_COLUMNS = [
    ("month", "muted"),
    ("income_planned", ""),
    ("income_actual", ""),
    ("expenses_planned", ""),
    ("expenses_actual", ""),
    ("expenses_remaining", ""),
]
_GROUP_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("planned", ""),
    ("actual", ""),
    ("remaining", ""),
    ("variability", "muted"),
    ("rollover", "muted"),
]
_CATEGORY_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("group_id", "meta"),
    ("planned", ""),
    ("actual", ""),
    ("remaining", ""),
    ("variability", "muted"),
    ("rollover", "muted"),
]


def _print_budget(budget: Budget, *, title: str) -> None:
    print_key_values(title, _budget_details(budget))
    print_table("Totals", _TOTAL_COLUMNS, (_totals_row(total) for total in budget.totals_by_month), source_rows=budget.totals_by_month)
    print_table("Groups", _GROUP_COLUMNS, (_group_row(row) for row in budget.groups), source_rows=budget.groups)
    print_table("Categories", _CATEGORY_COLUMNS, (_category_row(row) for row in budget.categories), source_rows=budget.categories)
    if budget.flex is not None:
        print_key_values("Flex Budget", _flex_details(budget.flex))


def _budget_details(budget: Budget) -> dict[str, object]:
    return {
        "start_month": budget.start_month,
        "end_month": budget.end_month,
        "budget_system": _enum_value(budget.budget_system),
        "has_budget": format_bool(budget.status.has_budget if budget.status else None),
        "has_transactions": format_bool(budget.status.has_transactions if budget.status else None),
        "groups": len(budget.groups),
        "categories": len(budget.categories),
    }


def _settings_details(settings: BudgetSettings) -> dict[str, object]:
    return {
        "budget_system": _enum_value(settings.budget_system),
        "apply_to_future_months_default": format_bool(settings.apply_to_future_months_default),
        "has_budget": format_bool(settings.status.has_budget if settings.status else None),
        "has_transactions": format_bool(settings.status.has_transactions if settings.status else None),
        **_rollover_details(settings.flex_rollover),
    }


def _flex_settings_details(settings: FlexRolloverSettings) -> dict[str, object]:
    return {
        "budget_system": _enum_value(settings.budget_system),
        **_rollover_details(settings.rollover_period),
    }


def _month_row(budget: Budget) -> dict[str, object]:
    totals = budget.totals_by_month[0] if budget.totals_by_month else None
    return _totals_row(totals) if totals is not None else {"month": budget.start_month}


def _totals_row(total: BudgetMonthTotals) -> dict[str, object]:
    return {
        "month": total.month,
        "income_planned": format_money(total.income.planned_amount if total.income else None),
        "income_actual": format_money(total.income.actual_amount if total.income else None),
        "expenses_planned": format_money(total.expenses.planned_amount if total.expenses else None),
        "expenses_actual": format_money(total.expenses.actual_amount if total.expenses else None),
        "expenses_remaining": format_money(total.expenses.remaining_amount if total.expenses else None),
    }


def _group_row(row: BudgetGroupRow) -> dict[str, object]:
    amount = row.amount
    return {
        "id": row.group.id,
        "name": row.group.name,
        "planned": format_money(amount.planned_amount if amount else None),
        "actual": format_money(amount.actual_amount if amount else None),
        "remaining": format_money(amount.remaining_amount if amount else None),
        "variability": _enum_value(row.group.budget_variability),
        "rollover": format_bool(row.group.rollover_period is not None),
    }


def _category_row(row: BudgetCategoryRow) -> dict[str, object]:
    amount = row.amount
    return {
        "id": row.category.id,
        "name": row.category.name,
        "group_id": row.category.group_id,
        "planned": format_money(amount.planned_amount if amount else None),
        "actual": format_money(amount.actual_amount if amount else None),
        "remaining": format_money(amount.remaining_amount if amount else None),
        "variability": _enum_value(row.category.budget_variability),
        "rollover": format_bool(row.category.rollover_period is not None),
    }


def _category_details(category: BudgetCategory, amount: BudgetAmount | None) -> dict[str, object]:
    return {
        "id": category.id,
        "name": category.name,
        "group_id": category.group_id,
        "type": _enum_value(category.type),
        "budget_variability": _enum_value(category.budget_variability),
        "exclude_from_budget": format_bool(category.exclude_from_budget),
        "planned": format_money(amount.planned_amount if amount else None),
        "actual": format_money(amount.actual_amount if amount else None),
        "remaining": format_money(amount.remaining_amount if amount else None),
        **_rollover_details(category.rollover_period),
    }


def _group_details(group: BudgetCategoryGroup, amount: BudgetAmount | None) -> dict[str, object]:
    return {
        "id": group.id,
        "name": group.name,
        "type": _enum_value(group.type),
        "budget_variability": _enum_value(group.budget_variability),
        "group_level_budgeting": format_bool(group.group_level_budgeting_enabled),
        "planned": format_money(amount.planned_amount if amount else None),
        "actual": format_money(amount.actual_amount if amount else None),
        "remaining": format_money(amount.remaining_amount if amount else None),
        **_rollover_details(group.rollover_period),
    }


def _flex_details(row: BudgetFlexRow) -> dict[str, object]:
    amount = row.amount
    return {
        "budget_variability": _enum_value(row.budget_variability),
        "planned": format_money(amount.planned_amount if amount else None),
        "actual": format_money(amount.actual_amount if amount else None),
        "remaining": format_money(amount.remaining_amount if amount else None),
        "rollover_type": amount.rollover_type if amount else None,
        "rollover_target": format_money(amount.rollover_target_amount if amount else None),
    }


def _rollover_details(period: BudgetRolloverPeriod | None) -> dict[str, object]:
    return {
        "rollover_id": period.id if period else None,
        "rollover_start_month": period.start_month if period else None,
        "rollover_end_month": period.end_month if period else None,
        "rollover_starting_balance": format_money(period.starting_balance if period else None),
        "rollover_target_amount": format_money(period.target_amount if period else None),
        "rollover_frequency": period.frequency if period else None,
        "rollover_type": period.type if period else None,
    }


def _enabled_value(value: EnabledState) -> bool:
    return value == EnabledState.ENABLED


def _enum_value(value: Enum | str | None) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return "" if value is None else str(value)
