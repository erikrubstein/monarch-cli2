from __future__ import annotations

from monarch_api import RecurringFilter, RecurringFrequency, RecurringStream, RecurringSummary, RecurringSummaryBucket, RecurringType
from typer.testing import CliRunner

from monarch_cli.app import app
from monarch_cli.groups.recurring import ActiveState, _active_value

runner = CliRunner()


def test_recurring_list_passes_filters(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_recurring_streams(session, *, filters=None, include_pending=True, include_liabilities=True):
        captured["filters"] = filters
        captured["include_pending"] = include_pending
        captured["include_liabilities"] = include_liabilities
        return [RecurringStream(id="recurring-123", name="Gym", amount=50.0)]

    monkeypatch.setattr(
        "monarch_cli.groups.recurring.list_recurring_streams",
        fake_list_recurring_streams,
    )

    result = runner.invoke(
        app,
        [
            "recurring",
            "list",
            "--session-path",
            str(session_path),
            "--account-id",
            "account-123",
            "--frequency",
            "monthly",
            "--type",
            "expense",
            "--completed",
            "false",
            "--exclude-pending",
            "--exclude-liabilities",
        ],
    )

    assert result.exit_code == 0
    assert "Gym" in result.output
    assert captured["filters"] == RecurringFilter(
        account_ids=["account-123"],
        frequencies=[RecurringFrequency.MONTHLY],
        recurring_types=[RecurringType.EXPENSE],
        is_completed=False,
    )
    assert captured["include_pending"] is False
    assert captured["include_liabilities"] is False


def test_recurring_summary_renders_buckets(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_recurring_summary(session, start_date, end_date, *, filters=None):
        return RecurringSummary(
            expense=RecurringSummaryBucket(completed=10, remaining=20, total=30, count=2),
            income=RecurringSummaryBucket(completed=100, remaining=0, total=100, count=1),
            credit_card=RecurringSummaryBucket(),
        )

    monkeypatch.setattr(
        "monarch_cli.groups.recurring.get_recurring_summary",
        fake_get_recurring_summary,
    )

    result = runner.invoke(
        app,
        ["recurring", "summary", "2026-01-01", "2026-01-31", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert "expense" in result.output
    assert "$30.00" in result.output


def test_recurring_remove_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_remove_recurring_stream(session, recurring_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(
        "monarch_cli.groups.recurring.remove_recurring_stream",
        fake_remove_recurring_stream,
    )

    result = runner.invoke(
        app,
        ["recurring", "remove", "recurring-123", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def test_active_value_maps_state() -> None:
    assert _active_value(ActiveState.ENABLED) is True
    assert _active_value(ActiveState.DISABLED) is False
    assert _active_value(None) is None


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
