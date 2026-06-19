from __future__ import annotations

from enum import Enum
from typing import Annotated

import typer
from monarch_api import (
    Goal,
    GoalBudgetAmount,
    GoalEvent,
    GoalStatus,
    GoalType,
    archive_goal,
    contribute_to_goal,
    create_goal,
    delete_goal,
    delete_goal_event,
    get_goal,
    get_goal_budget_amounts,
    link_goal_account_balance,
    list_goal_events,
    list_goals,
    restore_goal,
    set_goal_budget_amount,
    unlink_goal_account,
    update_goal,
    update_goal_event,
    update_goal_priorities,
    withdraw_from_goal,
)

from monarch_cli.errors import handle_cli_errors, raise_cli_error
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import format_bool, format_money, print_key_values, print_success, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Manage goals, goal events, and goal budget amounts.",
    no_args_is_help=True,
)


class EnabledState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class BudgetState(str, Enum):
    INCLUDED = "included"
    EXCLUDED = "excluded"


@app.command("list")
@handle_cli_errors
def list_command(
    session_path: SessionPathOption = None,
    include_archived: Annotated[
        bool,
        typer.Option("--include-archived", help="Include archived goals."),
    ] = False,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List goals."""
    session = require_session(session_path)
    goals = list_goals(session, include_archived=include_archived)
    if json_output:
        render_json(goals, include_raw=raw_output)
        return
    print_table("Goals", _GOAL_COLUMNS, (_goal_row(goal) for goal in goals), source_rows=goals)


@app.command("get")
@handle_cli_errors
def get_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one goal."""
    session = require_session(session_path)
    goal = get_goal(session, goal_id)
    if goal is None:
        raise_cli_error(f"No goal found for id {goal_id}.")
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal", _goal_details(goal))
    if goal.account_balance_links:
        print_table("Linked Accounts", _LINK_COLUMNS, (_link_row(link) for link in goal.account_balance_links), source_rows=goal.account_balance_links)


@app.command("create")
@handle_cli_errors
def create_command(
    name: Annotated[str, typer.Option("--name", help="Goal name.")],
    session_path: SessionPathOption = None,
    goal_type: Annotated[GoalType, typer.Option("--type", help="Goal type.")] = GoalType.CUSTOM,
    target_amount: Annotated[float | None, typer.Option("--target-amount", help="Target amount.")] = None,
    target_date: Annotated[str | None, typer.Option("--target-date", help="Target date.")] = None,
    planned_monthly_contribution: Annotated[
        float | None,
        typer.Option("--planned-monthly-contribution", help="Planned monthly contribution."),
    ] = None,
    sinking_fund: Annotated[
        bool,
        typer.Option("--sinking-fund", help="Create this as a sinking fund."),
    ] = False,
    priority: Annotated[int | None, typer.Option("--priority", help="Goal priority.")] = None,
    image_storage_provider: Annotated[
        str | None,
        typer.Option("--image-storage-provider", help="Image storage provider."),
    ] = None,
    image_storage_provider_id: Annotated[
        str | None,
        typer.Option("--image-storage-provider-id", help="Image storage provider id."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Create a goal."""
    session = require_session(session_path)
    goal = create_goal(
        session,
        name=name,
        goal_type=goal_type,
        target_amount=target_amount,
        target_date=target_date,
        planned_monthly_contribution=planned_monthly_contribution,
        is_sinking_fund=True if sinking_fund else None,
        priority=priority,
        image_storage_provider=image_storage_provider,
        image_storage_provider_id=image_storage_provider_id,
    )
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal Created", _goal_details(goal))


@app.command("update")
@handle_cli_errors
def update_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    session_path: SessionPathOption = None,
    name: Annotated[str | None, typer.Option("--name", help="Goal name.")] = None,
    goal_type: Annotated[GoalType | None, typer.Option("--type", help="Goal type.")] = None,
    target_amount: Annotated[float | None, typer.Option("--target-amount", help="Target amount.")] = None,
    target_date: Annotated[str | None, typer.Option("--target-date", help="Target date.")] = None,
    planned_monthly_contribution: Annotated[
        float | None,
        typer.Option("--planned-monthly-contribution", help="Planned monthly contribution."),
    ] = None,
    sinking_fund: Annotated[
        EnabledState | None,
        typer.Option("--sinking-fund", help="Set sinking fund state."),
    ] = None,
    priority: Annotated[int | None, typer.Option("--priority", help="Goal priority.")] = None,
    status: Annotated[GoalStatus | None, typer.Option("--status", help="Goal status.")] = None,
    image_storage_provider: Annotated[
        str | None,
        typer.Option("--image-storage-provider", help="Image storage provider."),
    ] = None,
    image_storage_provider_id: Annotated[
        str | None,
        typer.Option("--image-storage-provider-id", help="Image storage provider id."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a goal."""
    session = require_session(session_path)
    goal = update_goal(
        session,
        goal_id,
        name=name,
        goal_type=goal_type,
        target_amount=target_amount,
        target_date=target_date,
        planned_monthly_contribution=planned_monthly_contribution,
        is_sinking_fund=_enabled_value(sinking_fund),
        priority=priority,
        image_storage_provider=image_storage_provider,
        image_storage_provider_id=image_storage_provider_id,
        status=status,
    )
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal Updated", _goal_details(goal))


@app.command("delete")
@handle_cli_errors
def delete_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete a goal."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete goal {goal_id}?"):
        print_warning("Goal left unchanged.")
        return
    deleted = delete_goal(session, goal_id)
    if json_output:
        render_json({"goal_id": goal_id, "deleted": deleted})
        return
    if deleted:
        print_success("Goal deleted.")
    else:
        print_warning("Goal was not deleted.")


@app.command("archive")
@handle_cli_errors
def archive_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Archive a goal."""
    session = require_session(session_path)
    goal = archive_goal(session, goal_id)
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal Archived", _goal_details(goal))


@app.command("restore")
@handle_cli_errors
def restore_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Restore an archived goal."""
    session = require_session(session_path)
    goal = restore_goal(session, goal_id)
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal Restored", _goal_details(goal))


@app.command("priorities")
@handle_cli_errors
def priorities_command(
    goal_ids: Annotated[list[str], typer.Argument(help="Goal ids in priority order.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update goal priorities."""
    session = require_session(session_path)
    goals = update_goal_priorities(session, goal_ids)
    if json_output:
        render_json(goals, include_raw=raw_output)
        return
    print_table("Goal Priorities", _GOAL_COLUMNS, (_goal_row(goal) for goal in goals), source_rows=goals)


@app.command("link-account")
@handle_cli_errors
def link_account_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    session_path: SessionPathOption = None,
    amount: Annotated[
        float | None,
        typer.Option("--amount", help="Specific account balance amount to link."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Link an account balance to a goal."""
    session = require_session(session_path)
    goal = link_goal_account_balance(
        session,
        goal_id,
        account_id,
        use_entire_balance=amount is None,
        amount=amount,
    )
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal Account Linked", _goal_details(goal))


@app.command("unlink-account")
@handle_cli_errors
def unlink_account_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Unlink an account from a goal."""
    session = require_session(session_path)
    goal = unlink_goal_account(session, goal_id, account_id)
    if json_output:
        render_json(goal, include_raw=raw_output)
        return
    print_key_values("Goal Account Unlinked", _goal_details(goal))


@app.command("events")
@handle_cli_errors
def events_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List goal events."""
    session = require_session(session_path)
    events = list_goal_events(session, goal_id)
    if json_output:
        render_json(events, include_raw=raw_output)
        return
    print_table("Goal Events", _EVENT_COLUMNS, (_event_row(event) for event in events), source_rows=events)


@app.command("contribute")
@handle_cli_errors
def contribute_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    amount: Annotated[float, typer.Option("--amount", help="Contribution amount.")],
    session_path: SessionPathOption = None,
    date: Annotated[str | None, typer.Option("--date", help="Contribution date.")] = None,
    budget: Annotated[
        BudgetState | None,
        typer.Option("--budget", help="Set whether the event is included in budget."),
    ] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Event notes.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Add a goal contribution."""
    session = require_session(session_path)
    event = contribute_to_goal(
        session,
        goal_id,
        account_id,
        amount=amount,
        date=date,
        include_in_budget=_budget_value(budget),
        notes=notes,
    )
    if json_output:
        render_json(event, include_raw=raw_output)
        return
    print_key_values("Goal Contribution", _event_details(event))


@app.command("withdraw")
@handle_cli_errors
def withdraw_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    account_id: Annotated[str, typer.Argument(help="Account id.")],
    amount: Annotated[float, typer.Option("--amount", help="Withdrawal amount.")],
    session_path: SessionPathOption = None,
    date: Annotated[str | None, typer.Option("--date", help="Withdrawal date.")] = None,
    budget: Annotated[
        BudgetState | None,
        typer.Option("--budget", help="Set whether the event is included in budget."),
    ] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Event notes.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Add a goal withdrawal."""
    session = require_session(session_path)
    event = withdraw_from_goal(
        session,
        goal_id,
        account_id,
        amount=amount,
        date=date,
        include_in_budget=_budget_value(budget),
        notes=notes,
    )
    if json_output:
        render_json(event, include_raw=raw_output)
        return
    print_key_values("Goal Withdrawal", _event_details(event))


@app.command("update-event")
@handle_cli_errors
def update_event_command(
    event_id: Annotated[str, typer.Argument(help="Goal event id.")],
    session_path: SessionPathOption = None,
    date: Annotated[str | None, typer.Option("--date", help="Event date.")] = None,
    budget: Annotated[
        BudgetState | None,
        typer.Option("--budget", help="Set whether the event is included in budget."),
    ] = None,
    notes: Annotated[str | None, typer.Option("--notes", help="Event notes.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update a goal event."""
    session = require_session(session_path)
    event = update_goal_event(
        session,
        event_id,
        date=date,
        include_in_budget=_budget_value(budget),
        notes=notes,
    )
    if json_output:
        render_json(event, include_raw=raw_output)
        return
    print_key_values("Goal Event Updated", _event_details(event))


@app.command("delete-event")
@handle_cli_errors
def delete_event_command(
    event_id: Annotated[str, typer.Argument(help="Goal event id.")],
    session_path: SessionPathOption = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")] = False,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Delete a goal event."""
    session = require_session(session_path)
    if not yes and not typer.confirm(f"Delete goal event {event_id}?"):
        print_warning("Goal event left unchanged.")
        return
    deleted = delete_goal_event(session, event_id)
    if json_output:
        render_json({"event_id": event_id, "deleted": deleted})
        return
    if deleted:
        print_success("Goal event deleted.")
    else:
        print_warning("Goal event was not deleted.")


@app.command("budget-amounts")
@handle_cli_errors
def budget_amounts_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    start_month: Annotated[str, typer.Argument(help="Start month, such as 2026-01.")],
    end_month: Annotated[str, typer.Argument(help="End month, such as 2026-12.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List goal budget amounts."""
    session = require_session(session_path)
    amounts = get_goal_budget_amounts(session, goal_id, start_month, end_month)
    if json_output:
        render_json(amounts, include_raw=raw_output)
        return
    print_table("Goal Budget Amounts", _BUDGET_COLUMNS, (_budget_row(amount) for amount in amounts), source_rows=amounts)


@app.command("set-budget-amount")
@handle_cli_errors
def set_budget_amount_command(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    month: Annotated[str, typer.Argument(help="Budget month, such as 2026-01.")],
    amount: Annotated[float, typer.Argument(help="Budget amount.")],
    session_path: SessionPathOption = None,
    apply_to_future: Annotated[
        bool,
        typer.Option("--apply-to-future", help="Apply the amount to future months."),
    ] = False,
    account_id: Annotated[str | None, typer.Option("--account-id", help="Account id.")] = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Set a goal budget amount."""
    session = require_session(session_path)
    updated = set_goal_budget_amount(
        session,
        goal_id,
        month,
        amount,
        apply_to_future=apply_to_future,
        account_id=account_id,
    )
    if json_output:
        render_json({"goal_id": goal_id, "month": month, "updated": updated})
        return
    if updated:
        print_success("Goal budget amount updated.")
    else:
        print_warning("Goal budget amount was not updated.")


_GOAL_COLUMNS = [
    ("id", "meta"),
    ("name", ""),
    ("type", "muted"),
    ("status", "muted"),
    ("current", ""),
    ("target", ""),
    ("target_date", "muted"),
    ("priority", "muted"),
]
_LINK_COLUMNS = [
    ("account_id", "meta"),
    ("account", ""),
    ("amount", ""),
    ("current", ""),
    ("entire_balance", "muted"),
]
_EVENT_COLUMNS = [
    ("id", "meta"),
    ("date", "muted"),
    ("type", "muted"),
    ("amount", ""),
    ("account", "muted"),
    ("budget", "muted"),
    ("notes", ""),
]
_BUDGET_COLUMNS = [
    ("id", "meta"),
    ("month", "muted"),
    ("planned", ""),
    ("actual", ""),
    ("remaining", ""),
    ("total_planned", ""),
]


def _goal_row(goal: Goal) -> dict[str, object]:
    return {
        "id": goal.id,
        "name": goal.name,
        "type": _enum_value(goal.type),
        "status": _enum_value(goal.status),
        "current": format_money(goal.current_balance),
        "target": format_money(goal.target_amount),
        "target_date": goal.target_date,
        "priority": goal.priority,
    }


def _goal_details(goal: Goal) -> dict[str, object]:
    return {
        "id": goal.id,
        "name": goal.name,
        "type": _enum_value(goal.type),
        "status": _enum_value(goal.status),
        "progress": _format_percent(goal.progress),
        "current_balance": format_money(goal.current_balance),
        "target_amount": format_money(goal.target_amount),
        "target_date": goal.target_date,
        "planned_monthly_contribution": format_money(goal.planned_monthly_contribution),
        "current_month_planned_contribution": format_money(goal.current_month_planned_contribution_amount),
        "spending_total": format_money(goal.spending_total),
        "net_contribution": format_money(goal.net_contribution),
        "estimated_months_until_completion": goal.estimated_months_until_completion,
        "forecasted_completion_date": goal.forecasted_completion_date,
        "sinking_fund": format_bool(goal.is_sinking_fund),
        "priority": goal.priority,
        "created_at": goal.created_at,
        "archived_at": goal.archived_at,
        "completed_at": goal.completed_at,
    }


def _link_row(link) -> dict[str, object]:
    return {
        "account_id": link.account.id if link.account else link.id,
        "account": link.account.display_name if link.account else "",
        "amount": format_money(link.amount),
        "current": format_money(link.current_amount),
        "entire_balance": format_bool(link.use_entire_balance),
    }


def _event_row(event: GoalEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "date": event.date,
        "type": _enum_value(event.type),
        "amount": format_money(event.amount),
        "account": event.account.display_name if event.account else "",
        "budget": format_bool(event.include_in_budget),
        "notes": event.notes,
    }


def _event_details(event: GoalEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "date": event.date,
        "type": _enum_value(event.type),
        "amount": format_money(event.amount),
        "account": event.account.display_name if event.account else "",
        "account_id": event.account.id if event.account else "",
        "goal": event.goal.name if event.goal else "",
        "goal_id": event.goal.id if event.goal else "",
        "budget": format_bool(event.include_in_budget),
        "can_delete": format_bool(event.can_delete),
        "notes": event.notes,
        "created_at": event.created_at,
    }


def _budget_row(amount: GoalBudgetAmount) -> dict[str, object]:
    return {
        "id": amount.id,
        "month": amount.month,
        "planned": format_money(amount.planned_amount),
        "actual": format_money(amount.actual_amount),
        "remaining": format_money(amount.remaining_amount),
        "total_planned": format_money(amount.total_planned_amount),
    }


def _enabled_value(value: EnabledState | None) -> bool | None:
    if value is None:
        return None
    return value == EnabledState.ENABLED


def _budget_value(value: BudgetState | None) -> bool | None:
    if value is None:
        return None
    return value == BudgetState.INCLUDED


def _enum_value(value: Enum | str | None) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return "" if value is None else str(value)


def _format_percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}%"
