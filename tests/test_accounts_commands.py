from __future__ import annotations

from monarch_api import Account, AccountFilter
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_accounts_list_passes_filters(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, AccountFilter | None] = {}

    def fake_list_accounts(session, *, filters=None):
        captured["filters"] = filters
        return [
            Account(
                id="account-123",
                display_name="Checking",
                balance=123.45,
                include_in_net_worth=True,
                is_hidden=False,
            )
        ]

    monkeypatch.setattr("monarch_cli.accounts.list_accounts", fake_list_accounts)

    result = runner.invoke(
        app,
        [
            "accounts",
            "list",
            "--session-path",
            str(session_path),
            "--account-id",
            "account-123",
            "--account-type",
            "depository",
            "--include-hidden",
        ],
    )

    assert result.exit_code == 0
    assert "Checking" in result.output
    assert captured["filters"] == AccountFilter(
        account_ids=["account-123"],
        account_types=["depository"],
        include_hidden=True,
    )


def test_accounts_update_maps_value_options(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_account(session, account_id, **kwargs):
        captured["account_id"] = account_id
        captured.update(kwargs)
        return Account(id=account_id, display_name="Updated")

    monkeypatch.setattr("monarch_cli.accounts.update_account", fake_update_account)

    result = runner.invoke(
        app,
        [
            "accounts",
            "update",
            "account-123",
            "--session-path",
            str(session_path),
            "--net-worth",
            "exclude",
            "--list-visibility",
            "hidden",
            "--report-visibility",
            "visible",
        ],
    )

    assert result.exit_code == 0
    assert captured["account_id"] == "account-123"
    assert captured["include_in_net_worth"] is False
    assert captured["hide_from_list"] is True
    assert captured["hide_transactions_from_reports"] is False


def test_accounts_delete_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_account(session, account_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("monarch_cli.accounts.delete_account", fake_delete_account)

    result = runner.invoke(
        app,
        ["accounts", "delete", "account-123", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def test_accounts_missing_session_uses_cli_message(tmp_path) -> None:
    result = runner.invoke(
        app,
        ["accounts", "list", "--session-path", str(tmp_path / "missing.json")],
    )

    assert result.exit_code == 1
    assert "No saved session found" in result.output
    assert "monarch auth login" in result.output


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
