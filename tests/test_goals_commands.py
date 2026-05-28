from __future__ import annotations

from monarch_api import Goal, GoalBudgetAmount, GoalType
from typer.testing import CliRunner

from monarch_cli.app import app
from monarch_cli.groups.goals import BudgetState, EnabledState, _budget_value, _enabled_value

runner = CliRunner()


def test_goals_list_passes_include_archived(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_goals(session, *, include_archived=False):
        captured["include_archived"] = include_archived
        return [Goal(id="goal-123", name="Vacation", type=GoalType.VACATION, target_amount=1000)]

    monkeypatch.setattr("monarch_cli.groups.goals.list_goals", fake_list_goals)

    result = runner.invoke(
        app,
        ["goals", "list", "--session-path", str(session_path), "--include-archived"],
    )

    assert result.exit_code == 0
    assert "Goals" in result.output
    assert captured == {"include_archived": True}


def test_goals_link_account_uses_amount(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_link_goal_account_balance(session, goal_id, account_id, *, use_entire_balance=True, amount=None):
        captured["goal_id"] = goal_id
        captured["account_id"] = account_id
        captured["use_entire_balance"] = use_entire_balance
        captured["amount"] = amount
        return Goal(id=goal_id, name="Vacation")

    monkeypatch.setattr(
        "monarch_cli.groups.goals.link_goal_account_balance",
        fake_link_goal_account_balance,
    )

    result = runner.invoke(
        app,
        [
            "goals",
            "link-account",
            "goal-123",
            "account-123",
            "--session-path",
            str(session_path),
            "--amount",
            "250",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "goal_id": "goal-123",
        "account_id": "account-123",
        "use_entire_balance": False,
        "amount": 250.0,
    }


def test_goals_budget_amounts_render(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_goal_budget_amounts(session, goal_id, start_month, end_month):
        return [GoalBudgetAmount(id="budget-123", month=start_month, planned_amount=100)]

    monkeypatch.setattr(
        "monarch_cli.groups.goals.get_goal_budget_amounts",
        fake_get_goal_budget_amounts,
    )

    result = runner.invoke(
        app,
        ["goals", "budget-amounts", "goal-123", "2026-01", "2026-02", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert "$100.00" in result.output


def test_goals_delete_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_goal(session, goal_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("monarch_cli.groups.goals.delete_goal", fake_delete_goal)

    result = runner.invoke(
        app,
        ["goals", "delete", "goal-123", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def test_state_helpers() -> None:
    assert _enabled_value(EnabledState.ENABLED) is True
    assert _enabled_value(EnabledState.DISABLED) is False
    assert _enabled_value(None) is None
    assert _budget_value(BudgetState.INCLUDED) is True
    assert _budget_value(BudgetState.EXCLUDED) is False
    assert _budget_value(None) is None


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
