from __future__ import annotations

from monarch_api import (
    CashflowBreakdown,
    CashflowBreakdownDirection,
    CashflowBreakdownGroup,
    CashflowBreakdownRow,
    CashflowFilter,
    CashflowInterval,
    CashflowSummary,
    CashflowTrendPoint,
)
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_cashflow_summary_passes_filters(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_get_cashflow_summary(session, start_date, end_date, *, filters=None):
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        captured["filters"] = filters
        return CashflowSummary(
            start_date=start_date,
            end_date=end_date,
            income=1000,
            expenses=400,
            savings=600,
            savings_rate=60,
        )

    monkeypatch.setattr(
        "monarch_cli.groups.cashflow.get_cashflow_summary",
        fake_get_cashflow_summary,
    )

    result = runner.invoke(
        app,
        [
            "cashflow",
            "summary",
            "2026-01-01",
            "2026-05-28",
            "--session-path",
            str(session_path),
            "--account-id",
            "account-123",
            "--include-hidden",
        ],
    )

    assert result.exit_code == 0
    assert "$1,000.00" in result.output
    assert captured["filters"] == CashflowFilter(
        account_ids=["account-123"],
        include_hidden=True,
    )


def test_cashflow_trends_passes_interval(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_get_cashflow_trends(
        session,
        start_date,
        end_date,
        *,
        interval=CashflowInterval.MONTH,
        filters=None,
    ):
        captured["interval"] = interval
        return [
            CashflowTrendPoint(
                start_date="2026-01-01",
                end_date="2026-03-31",
                label="2026-01-01",
                income=100,
                expenses=50,
                savings=50,
            )
        ]

    monkeypatch.setattr(
        "monarch_cli.groups.cashflow.get_cashflow_trends",
        fake_get_cashflow_trends,
    )

    result = runner.invoke(
        app,
        [
            "cashflow",
            "trends",
            "2026-01-01",
            "2026-05-28",
            "--session-path",
            str(session_path),
            "--interval",
            "quarter",
        ],
    )

    assert result.exit_code == 0
    assert captured["interval"] is CashflowInterval.QUARTER
    assert "$100.00" in result.output


def test_cashflow_breakdown_passes_direction_and_group(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_get_cashflow_breakdown(
        session,
        start_date,
        end_date,
        direction,
        *,
        group_by=CashflowBreakdownGroup.CATEGORY,
        filters=None,
    ):
        captured["direction"] = direction
        captured["group_by"] = group_by
        return CashflowBreakdown(
            direction=direction,
            group_by=group_by,
            rows=[
                CashflowBreakdownRow(
                    id="merchant-123",
                    name="Store",
                    amount=42,
                    percent=100,
                    transaction_count=2,
                )
            ],
        )

    monkeypatch.setattr(
        "monarch_cli.groups.cashflow.get_cashflow_breakdown",
        fake_get_cashflow_breakdown,
    )

    result = runner.invoke(
        app,
        [
            "cashflow",
            "breakdown",
            "2026-01-01",
            "2026-05-28",
            "expenses",
            "--session-path",
            str(session_path),
            "--group-by",
            "merchant",
        ],
    )

    assert result.exit_code == 0
    assert captured["direction"] is CashflowBreakdownDirection.EXPENSES
    assert captured["group_by"] is CashflowBreakdownGroup.MERCHANT
    assert "Store" in result.output
    assert "100.00%" in result.output


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
