from __future__ import annotations

from monarch_api import Budget, BudgetAmount, BudgetCategory, BudgetCategoryRow, BudgetSettings, BudgetStatus, BudgetVariability
from typer.testing import CliRunner

from monarch_cli.app import app
from monarch_cli.groups.budget import EnabledState, _enabled_value

runner = CliRunner()


def test_budget_settings_renders(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_budget_settings(session):
        return BudgetSettings(status=BudgetStatus(has_budget=True, has_transactions=False, will_create_budget_from_empty_default_categories=False))

    monkeypatch.setattr("monarch_cli.groups.budget.get_budget_settings", fake_get_budget_settings)

    result = runner.invoke(app, ["budget", "settings", "--session-path", str(session_path)])

    assert result.exit_code == 0
    assert "Budget Settings" in result.output
    assert "has_budget" in result.output


def test_budget_set_amount_passes_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_set_budget_amount(session, month, category_id, amount, *, apply_to_future=False, default_amount=None):
        captured["month"] = month
        captured["category_id"] = category_id
        captured["amount"] = amount
        captured["apply_to_future"] = apply_to_future
        captured["default_amount"] = default_amount
        return BudgetCategoryRow(
            category=BudgetCategory(id=category_id, name="Groceries"),
            amounts=[BudgetAmount(month=month, planned_amount=amount)],
        )

    monkeypatch.setattr("monarch_cli.groups.budget.set_budget_amount", fake_set_budget_amount)

    result = runner.invoke(
        app,
        [
            "budget",
            "set-amount",
            "2026-05",
            "cat-123",
            "450",
            "--session-path",
            str(session_path),
            "--apply-to-future",
            "--default-amount",
            "400",
        ],
    )

    assert result.exit_code == 0
    assert "Groceries" in result.output
    assert captured == {
        "month": "2026-05",
        "category_id": "cat-123",
        "amount": 450.0,
        "apply_to_future": True,
        "default_amount": 400.0,
    }


def test_budget_set_category_variability_passes_enum(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_set_budget_category_variability(session, category_id, variability):
        captured["category_id"] = category_id
        captured["variability"] = variability
        return BudgetCategory(id=category_id, name="Rent", budget_variability=variability)

    monkeypatch.setattr(
        "monarch_cli.groups.budget.set_budget_category_variability",
        fake_set_budget_category_variability,
    )

    result = runner.invoke(
        app,
        ["budget", "set-category-variability", "cat-123", "fixed", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert captured == {"category_id": "cat-123", "variability": BudgetVariability.FIXED}


def test_budget_clear_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_clear_budget(session, month, *, confirm=False):
        nonlocal called
        called = True
        return Budget(start_month=month, end_month=month)

    monkeypatch.setattr("monarch_cli.groups.budget.clear_budget", fake_clear_budget)

    result = runner.invoke(
        app,
        ["budget", "clear", "2026-05", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def test_enabled_value_maps_state() -> None:
    assert _enabled_value(EnabledState.ENABLED) is True
    assert _enabled_value(EnabledState.DISABLED) is False


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
