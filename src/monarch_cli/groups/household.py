from __future__ import annotations

from enum import Enum
from typing import Annotated

import typer
from monarch_api import (
    Household,
    HouseholdMember,
    HouseholdPreferences,
    UserProfile,
    get_current_user,
    get_household,
    get_household_member,
    get_household_preferences,
    list_household_members,
    update_current_user,
    update_household_preferences,
)

from monarch_cli.errors import handle_cli_errors, raise_cli_error
from monarch_cli.options import JsonOption, RawOption, OutputFieldsOption, AppendFieldsOption, SessionPathOption
from monarch_cli.output import format_bool, print_key_values, print_table, print_warning, render_json
from monarch_cli.session import require_session

app = typer.Typer(
    help="Inspect household, members, current user, and preferences.",
    no_args_is_help=True,
)


class PreferenceState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


@app.command("get")
@handle_cli_errors
def get_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show household details."""
    session = require_session(session_path)
    household = get_household(session)
    if json_output:
        render_json(household, include_raw=raw_output)
        return
    print_key_values("Household", _household_details(household))


@app.command("list-members")
@handle_cli_errors
def list_members_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """List household members."""
    session = require_session(session_path)
    members = list_household_members(session)
    if json_output:
        render_json(members, include_raw=raw_output)
        return
    print_table("Household Members", _MEMBER_COLUMNS, (_member_row(member) for member in members), source_rows=members)


@app.command("get-member")
@handle_cli_errors
def get_member_command(
    member_id: Annotated[str, typer.Argument(help="Household member id.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show one household member."""
    session = require_session(session_path)
    member = get_household_member(session, member_id)
    if member is None:
        raise_cli_error(f"No household member found for id {member_id}.")
    if json_output:
        render_json(member, include_raw=raw_output)
        return
    print_key_values("Household Member", _member_details(member))


@app.command("current-user")
@handle_cli_errors
def current_user_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show the current user."""
    session = require_session(session_path)
    user = get_current_user(session)
    if json_output:
        render_json(user, include_raw=raw_output)
        return
    print_key_values("Current User", _user_details(user))


@app.command("update-current-user")
@handle_cli_errors
def update_current_user_command(
    session_path: SessionPathOption = None,
    display_name: Annotated[
        str | None,
        typer.Option("--display-name", help="Display name."),
    ] = None,
    timezone: Annotated[str | None, typer.Option("--timezone", help="Timezone.")] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update the current user."""
    session = require_session(session_path)
    user = update_current_user(
        session,
        display_name=display_name,
        timezone=timezone,
    )
    if json_output:
        render_json(user, include_raw=raw_output)
        return
    print_key_values("Current User Updated", _user_details(user))


@app.command("preferences")
@handle_cli_errors
def preferences_command(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Show household preferences."""
    session = require_session(session_path)
    preferences = get_household_preferences(session)
    if json_output:
        render_json(preferences, include_raw=raw_output)
        return
    print_key_values("Household Preferences", _preferences_details(preferences))


@app.command("update-preferences")
@handle_cli_errors
def update_preferences_command(
    session_path: SessionPathOption = None,
    new_transactions_need_review: Annotated[
        PreferenceState | None,
        typer.Option("--new-transactions-need-review", help="New-transaction review setting."),
    ] = None,
    uncategorized_transactions_need_review: Annotated[
        PreferenceState | None,
        typer.Option(
            "--uncategorized-transactions-need-review",
            help="Uncategorized transaction review setting.",
        ),
    ] = None,
    pending_transactions_can_be_edited: Annotated[
        PreferenceState | None,
        typer.Option("--pending-transactions-can-be-edited", help="Pending edit setting."),
    ] = None,
    hidden_transactions_beta_enabled: Annotated[
        PreferenceState | None,
        typer.Option("--hidden-transactions-beta-enabled", help="Hidden transactions beta setting."),
    ] = None,
    exclude_business_from_budget: Annotated[
        PreferenceState | None,
        typer.Option("--exclude-business-from-budget", help="Business budget exclusion setting."),
    ] = None,
    json_output: JsonOption = False,
    raw_output: RawOption = False,
    output_fields: OutputFieldsOption = None,
    append_output_fields: AppendFieldsOption = None,
) -> None:
    """Update household preferences."""
    session = require_session(session_path)
    preferences = update_household_preferences(
        session,
        new_transactions_need_review=_preference_value(new_transactions_need_review),
        uncategorized_transactions_need_review=_preference_value(
            uncategorized_transactions_need_review
        ),
        pending_transactions_can_be_edited=_preference_value(
            pending_transactions_can_be_edited
        ),
        hidden_transactions_beta_enabled=_preference_value(
            hidden_transactions_beta_enabled
        ),
        exclude_business_from_budget=_preference_value(exclude_business_from_budget),
    )
    if json_output:
        render_json(preferences, include_raw=raw_output)
        return
    print_key_values("Household Preferences Updated", _preferences_details(preferences))


_MEMBER_COLUMNS = [
    ("id", "meta"),
    ("display_name", ""),
    ("email", ""),
    ("role", "muted"),
    ("mfa", "muted"),
]


def _household_details(household: Household) -> dict[str, object]:
    return {
        "id": household.id,
        "name": household.name,
        "address": household.address,
        "city": household.city,
        "state": household.state,
        "zip_code": household.zip_code,
        "country": household.country,
    }


def _member_row(member: HouseholdMember) -> dict[str, object]:
    return {
        "id": member.id,
        "display_name": member.display_name or member.name,
        "email": member.email,
        "role": _enum_value(member.role),
        "mfa": format_bool(member.has_mfa_on),
    }


def _member_details(member: HouseholdMember) -> dict[str, object]:
    return {
        "id": member.id,
        "name": member.name,
        "display_name": member.display_name,
        "email": member.email,
        "role": _enum_value(member.role),
        "mfa": format_bool(member.has_mfa_on),
        "profile_picture_url": member.profile_picture_url,
    }


def _user_details(user: UserProfile) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "display_name": user.display_name,
        "timezone": user.timezone,
        "role": _enum_value(user.household_role),
        "password": format_bool(user.has_password),
        "mfa": format_bool(user.has_mfa_on),
        "created_at": user.created_at,
        "pending_email_update": user.pending_email_update,
    }


def _preferences_details(preferences: HouseholdPreferences) -> dict[str, object]:
    return {
        "new_transactions_need_review": format_bool(
            preferences.new_transactions_need_review
        ),
        "uncategorized_transactions_need_review": format_bool(
            preferences.uncategorized_transactions_need_review
        ),
        "pending_transactions_can_be_edited": format_bool(
            preferences.pending_transactions_can_be_edited
        ),
        "budget_apply_to_future_months_default": format_bool(
            preferences.budget_apply_to_future_months_default
        ),
        "hidden_transactions_beta_enabled": format_bool(
            preferences.hidden_transactions_beta_enabled
        ),
        "exclude_business_from_budget": format_bool(
            preferences.exclude_business_from_budget
        ),
        "budget_system": preferences.budget_system,
    }


def _preference_value(value: PreferenceState | None) -> bool | None:
    if value is None:
        return None
    return value == PreferenceState.ENABLED


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))
