from __future__ import annotations

from monarch_api import (
    Household,
    HouseholdMember,
    HouseholdPreferences,
    HouseholdRole,
    UserProfile,
)
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_household_get_renders_details(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_household(session):
        return Household(id="household-123", name="Home", city="Chicago")

    monkeypatch.setattr("monarch_cli.groups.household.get_household", fake_get_household)

    result = runner.invoke(
        app,
        ["household", "get", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert "Home" in result.output
    assert "Chicago" in result.output


def test_household_list_members_renders_members(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_list_household_members(session):
        return [
            HouseholdMember(
                id="member-123",
                display_name="Person",
                email="person@example.com",
                role=HouseholdRole.OWNER,
                has_mfa_on=True,
            )
        ]

    monkeypatch.setattr(
        "monarch_cli.groups.household.list_household_members",
        fake_list_household_members,
    )

    result = runner.invoke(
        app,
        ["household", "list-members", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert "Person" in result.output
    assert "owner" in result.output


def test_household_update_current_user_passes_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_current_user(session, *, display_name=None, timezone=None):
        captured["display_name"] = display_name
        captured["timezone"] = timezone
        return UserProfile(id="user-123", display_name=display_name, timezone=timezone)

    monkeypatch.setattr(
        "monarch_cli.groups.household.update_current_user",
        fake_update_current_user,
    )

    result = runner.invoke(
        app,
        [
            "household",
            "update-current-user",
            "--session-path",
            str(session_path),
            "--display-name",
            "Person",
            "--timezone",
            "America/Chicago",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "display_name": "Person",
        "timezone": "America/Chicago",
    }
    assert "Person" in result.output


def test_household_update_preferences_maps_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_household_preferences(
        session,
        *,
        new_transactions_need_review=None,
        uncategorized_transactions_need_review=None,
        pending_transactions_can_be_edited=None,
        hidden_transactions_beta_enabled=None,
        exclude_business_from_budget=None,
    ):
        captured["new_transactions_need_review"] = new_transactions_need_review
        captured["pending_transactions_can_be_edited"] = pending_transactions_can_be_edited
        captured["exclude_business_from_budget"] = exclude_business_from_budget
        return HouseholdPreferences(
            id="prefs-123",
            new_transactions_need_review=new_transactions_need_review,
            pending_transactions_can_be_edited=pending_transactions_can_be_edited,
            exclude_business_from_budget=exclude_business_from_budget,
        )

    monkeypatch.setattr(
        "monarch_cli.groups.household.update_household_preferences",
        fake_update_household_preferences,
    )

    result = runner.invoke(
        app,
        [
            "household",
            "update-preferences",
            "--session-path",
            str(session_path),
            "--new-transactions-need-review",
            "enabled",
            "--pending-transactions-can-be-edited",
            "disabled",
            "--exclude-business-from-budget",
            "enabled",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "new_transactions_need_review": True,
        "pending_transactions_can_be_edited": False,
        "exclude_business_from_budget": True,
    }


def _write_session(tmp_path):
    session_path = tmp_path / "session.json"
    session_path.write_text(
        """
        {
          "token": "token-123",
          "token_expiration": null,
          "user_id": "user-123",
          "email": "person@example.com"
        }
        """,
        encoding="utf-8",
    )
    return session_path
