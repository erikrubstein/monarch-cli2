from __future__ import annotations

from monarch_api import (
    ReportGroup,
    ReportGroupValue,
    ReportResult,
    ReportRow,
    ReportSummary,
    ReportTimeframe,
    SavedReport,
    TransactionFilter,
)
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_reports_data_passes_filters_and_groups(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_get_report_data(
        session,
        *,
        filters=None,
        group_by=ReportGroup.CATEGORY,
        timeframe=None,
        sort_by=None,
        fill_empty_values=True,
    ):
        captured["filters"] = filters
        captured["group_by"] = group_by
        captured["timeframe"] = timeframe
        captured["fill_empty_values"] = fill_empty_values
        return ReportResult(
            summary=ReportSummary(total=42, count=2),
            rows=[
                ReportRow(
                    group=ReportGroupValue(date="2026-01-01"),
                    summary=ReportSummary(total=42, count=2),
                )
            ],
        )

    monkeypatch.setattr("monarch_cli.groups.reports.get_report_data", fake_get_report_data)

    result = runner.invoke(
        app,
        [
            "reports",
            "data",
            "--session-path",
            str(session_path),
            "--start-date",
            "2026-01-01",
            "--account-id",
            "account-123",
            "--group-by",
            "merchant",
            "--timeframe",
            "month",
            "--no-fill-empty",
        ],
    )

    assert result.exit_code == 0
    assert "$42.00" in result.output
    assert captured["filters"] == TransactionFilter(
        start_date="2026-01-01",
        account_ids=["account-123"],
    )
    assert captured["group_by"] == [ReportGroup.MERCHANT]
    assert captured["timeframe"] is ReportTimeframe.MONTH
    assert captured["fill_empty_values"] is False


def test_reports_create_saved_maps_options(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_create_saved_report(session, name, *, filters=None, group_by=None, timeframe=None):
        captured["name"] = name
        captured["filters"] = filters
        captured["group_by"] = group_by
        captured["timeframe"] = timeframe
        return SavedReport(id="report-123", name=name, group_by=group_by, timeframe=timeframe)

    monkeypatch.setattr(
        "monarch_cli.groups.reports.create_saved_report",
        fake_create_saved_report,
    )

    result = runner.invoke(
        app,
        [
            "reports",
            "create-saved",
            "Spending",
            "--session-path",
            str(session_path),
            "--category-id",
            "category-123",
            "--group-by",
            "category",
            "--timeframe",
            "month",
        ],
    )

    assert result.exit_code == 0
    assert captured["name"] == "Spending"
    assert captured["filters"] == TransactionFilter(category_ids=["category-123"])
    assert captured["group_by"] == [ReportGroup.CATEGORY]
    assert captured["timeframe"] is ReportTimeframe.MONTH


def test_reports_delete_saved_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_saved_report(session, report_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(
        "monarch_cli.groups.reports.delete_saved_report",
        fake_delete_saved_report,
    )

    result = runner.invoke(
        app,
        ["reports", "delete-saved", "report-123", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


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
