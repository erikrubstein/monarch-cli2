from __future__ import annotations

from monarch_api import (
    AccountReference,
    CategoryReference,
    Transaction,
    TransactionFilter,
    TransactionPage,
    TransactionSplit,
    TransactionSplitDetails,
    TransactionSplitDraft,
)
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_transactions_list_passes_filters(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_transactions(session, *, filters=None, limit=100, offset=0, sort=None):
        captured["filters"] = filters
        captured["limit"] = limit
        captured["offset"] = offset
        captured["sort"] = sort
        return TransactionPage(
            transactions=[
                    Transaction(
                        id="transaction-123",
                        date="2026-05-28",
                        amount=-12.34,
                        merchant_name="Coffee",
                        notes="memo",
                )
            ],
            total_count=1,
            limit=limit,
            offset=offset,
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.list_transactions",
        fake_list_transactions,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "list",
            "--session-path",
            str(session_path),
            "--start-date",
            "2026-05-01",
            "--account-id",
            "account-123",
            "--needs-review",
            "true",
            "--pending",
            "false",
            "--limit",
            "25",
            "--offset",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "Coffee" in result.output
    assert captured["limit"] == 25
    assert captured["offset"] == 5
    assert captured["filters"] == TransactionFilter(
        start_date="2026-05-01",
        account_ids=["account-123"],
        is_pending=False,
        needs_review=True,
    )


def test_transactions_list_can_override_output_fields(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_list_transactions(session, *, filters=None, limit=100, offset=0, sort=None):
        return TransactionPage(
            transactions=[
                Transaction(
                    id="transaction-123",
                    date="2026-05-28",
                    amount=-12.34,
                    merchant_name="Coffee",
                    notes="memo",
                )
            ],
            total_count=1,
            limit=limit,
            offset=offset,
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.list_transactions",
        fake_list_transactions,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "list",
            "--session-path",
            str(session_path),
            "--fields",
            "id,notes",
        ],
    )

    assert result.exit_code == 0
    assert "transaction-123" in result.output
    assert "memo" in result.output


def test_transactions_list_can_append_output_fields(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_list_transactions(session, *, filters=None, limit=100, offset=0, sort=None):
        return TransactionPage(
            transactions=[
                Transaction(
                    id="transaction-123",
                    date="2026-05-28",
                    amount=-12.34,
                    merchant_name="Coffee",
                    notes="memo",
                )
            ],
            total_count=1,
            limit=limit,
            offset=offset,
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.list_transactions",
        fake_list_transactions,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "list",
            "--session-path",
            str(session_path),
            "--append-fields",
            "notes",
        ],
    )

    assert result.exit_code == 0
    assert "Coffee" in result.output
    assert "memo" in result.output


def test_transactions_list_rejects_fields_and_append_fields(tmp_path) -> None:
    session_path = _write_session(tmp_path)

    result = runner.invoke(
        app,
        [
            "transactions",
            "list",
            "--session-path",
            str(session_path),
            "--fields",
            "id",
            "--append-fields",
            "notes",
        ],
    )

    assert result.exit_code == 1
    assert "Use either --fields or --append-fields, not both." in result.output


def test_transactions_list_help_shows_output_fields_option() -> None:
    result = runner.invoke(app, ["transactions", "list", "--help"])

    assert result.exit_code == 0
    assert "--fields" in result.output
    assert "--append-fields" in result.output
    assert "--columns" not in result.output


def test_transactions_update_maps_value_options(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_transaction(session, transaction_id, **kwargs):
        captured["transaction_id"] = transaction_id
        captured.update(kwargs)
        return Transaction(id=transaction_id, date="2026-05-28", amount=-12.34)

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.update_transaction",
        fake_update_transaction,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "update",
            "transaction-123",
            "--session-path",
            str(session_path),
            "--report-visibility",
            "hidden",
            "--tag-id",
            "tag-1",
            "--tag-id",
            "tag-2",
            "--clear-goal",
        ],
    )

    assert result.exit_code == 0
    assert captured["transaction_id"] == "transaction-123"
    assert captured["hide_from_reports"] is True
    assert captured["tag_ids"] == ["tag-1", "tag-2"]
    assert captured["clear_goal"] is True


def test_transactions_update_splits_parses_json(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_transaction_splits(session, transaction_id, splits):
        captured["transaction_id"] = transaction_id
        captured["splits"] = splits
        return TransactionSplitDetails(
            transaction=Transaction(id=transaction_id, date="2026-05-28", amount=-100),
            splits=[TransactionSplit(id="split-1", amount=-40)],
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.update_transaction_splits",
        fake_update_transaction_splits,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "update-splits",
            "transaction-123",
            "--session-path",
            str(session_path),
            "--splits-json",
            '[{"amount": -40, "category_id": "category-1"}, {"amount": -60}]',
        ],
    )

    assert result.exit_code == 0
    assert captured["transaction_id"] == "transaction-123"
    assert captured["splits"] == [
        TransactionSplitDraft(amount=-40, category_id="category-1"),
        TransactionSplitDraft(amount=-60),
    ]


def test_transactions_delete_attachment_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_transaction_attachment(session, attachment_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.delete_transaction_attachment",
        fake_delete_transaction_attachment,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "delete-attachment",
            "attachment-123",
            "--session-path",
            str(session_path),
        ],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def test_transactions_get_renders_friendly_details(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_transaction(session, transaction_id, *, redirect_posted=True):
        return Transaction(
            id=transaction_id,
            date="2026-05-28",
            amount=-12.34,
            account=AccountReference(id="account-1", display_name="Checking"),
            category=CategoryReference(id="category-1", name="Coffee"),
            merchant_name="Cafe",
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.get_transaction",
        fake_get_transaction,
    )

    result = runner.invoke(
        app,
        ["transactions", "get", "transaction-123", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert "Cafe" in result.output
    assert "Checking" in result.output
    assert "Coffee" in result.output


def test_transactions_get_fields_do_not_shape_friendly_details(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_transaction(session, transaction_id, *, redirect_posted=True):
        return Transaction(
            id=transaction_id,
            date="2026-05-28",
            amount=-12.34,
            account=AccountReference(id="account-1", display_name="Checking"),
            category=CategoryReference(id="category-1", name="Coffee"),
            merchant_name="Cafe",
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.get_transaction",
        fake_get_transaction,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "get",
            "transaction-123",
            "--session-path",
            str(session_path),
            "--fields",
            "id",
        ],
    )

    assert result.exit_code == 0
    assert "transaction-123" in result.output
    assert "Cafe" in result.output
    assert "Checking" in result.output


def test_transactions_get_append_fields_do_not_shape_friendly_details(
    monkeypatch,
    tmp_path,
) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_transaction(session, transaction_id, *, redirect_posted=True):
        return Transaction(
            id=transaction_id,
            date="2026-05-28",
            amount=-12.34,
            account=AccountReference(id="account-1", display_name="Checking"),
            category=CategoryReference(id="category-1", name="Coffee"),
            merchant_name="Cafe",
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.get_transaction",
        fake_get_transaction,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "get",
            "transaction-123",
            "--session-path",
            str(session_path),
            "--append-fields",
            "account.id",
        ],
    )

    assert result.exit_code == 0
    assert "Cafe" in result.output
    assert "Checking" in result.output
    assert "account.id" not in result.output
    assert "account-1" not in result.output


def test_transactions_get_fields_shape_json(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_transaction(session, transaction_id, *, redirect_posted=True):
        return Transaction(
            id=transaction_id,
            date="2026-05-28",
            amount=-12.34,
            account=AccountReference(id="account-1", display_name="Checking"),
            category=CategoryReference(id="category-1", name="Coffee"),
            merchant_name="Cafe",
        )

    monkeypatch.setattr(
        "monarch_cli.groups.transactions.get_transaction",
        fake_get_transaction,
    )

    result = runner.invoke(
        app,
        [
            "transactions",
            "get",
            "transaction-123",
            "--session-path",
            str(session_path),
            "--json",
            "--fields",
            "id,account.display_name,category.name",
        ],
    )

    assert result.exit_code == 0
    assert '"id": "transaction-123"' in result.output
    assert '"account.display_name": "Checking"' in result.output
    assert '"category.name": "Coffee"' in result.output
    assert '"merchant_name"' not in result.output


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
