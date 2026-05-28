from __future__ import annotations

from monarch_api import (
    Receipt,
    ReceiptLineItem,
    ReceiptLineItemUpdate,
    ReceiptOrder,
    ReceiptPage,
    ReceiptSettings,
)
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_receipts_list_renders_receipts(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_receipts(session, *, filters=None, limit=100, offset=0):
        captured["filters"] = filters
        captured["limit"] = limit
        captured["offset"] = offset
        return ReceiptPage(
            receipts=[
                Receipt(
                    id="receipt-123",
                    order=ReceiptOrder(
                        id="order-123",
                        merchant_name="Store",
                        date="2026-05-28",
                        grand_total=12.34,
                    ),
                )
            ],
            total_count=1,
            limit=limit,
            offset=offset,
        )

    monkeypatch.setattr("monarch_cli.groups.receipts.list_receipts", fake_list_receipts)

    result = runner.invoke(
        app,
        ["receipts", "list", "--session-path", str(session_path), "--limit", "25"],
    )

    assert result.exit_code == 0
    assert captured["limit"] == 25
    assert "Store" in result.output


def test_receipts_update_parses_line_items(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_receipt(session, receipt_id, **kwargs):
        captured["receipt_id"] = receipt_id
        captured.update(kwargs)
        return Receipt(id=receipt_id)

    monkeypatch.setattr("monarch_cli.groups.receipts.update_receipt", fake_update_receipt)

    result = runner.invoke(
        app,
        [
            "receipts",
            "update",
            "receipt-123",
            "--session-path",
            str(session_path),
            "--line-items-json",
            '[{"line_item_id": "line-1", "title": "Coffee", "price": 4.5}]',
        ],
    )

    assert result.exit_code == 0
    assert captured["receipt_id"] == "receipt-123"
    assert captured["line_items"] == [
        ReceiptLineItemUpdate(line_item_id="line-1", title="Coffee", price=4.5)
    ]


def test_receipts_update_settings_maps_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_receipt_settings(
        session,
        *,
        auto_categorize=None,
        update_transaction_notes=None,
    ):
        captured["auto_categorize"] = auto_categorize
        captured["update_transaction_notes"] = update_transaction_notes
        return ReceiptSettings(
            auto_categorize=auto_categorize,
            update_transaction_notes=update_transaction_notes,
        )

    monkeypatch.setattr(
        "monarch_cli.groups.receipts.update_receipt_settings",
        fake_update_receipt_settings,
    )

    result = runner.invoke(
        app,
        [
            "receipts",
            "update-settings",
            "--session-path",
            str(session_path),
            "--auto-categorize",
            "enabled",
            "--update-transaction-notes",
            "disabled",
        ],
    )

    assert result.exit_code == 0
    assert captured["auto_categorize"] is True
    assert captured["update_transaction_notes"] is False


def test_receipts_delete_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_receipt(session, receipt_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("monarch_cli.groups.receipts.delete_receipt", fake_delete_receipt)

    result = runner.invoke(
        app,
        ["receipts", "delete", "receipt-123", "--session-path", str(session_path)],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "left unchanged" in result.output
    assert called is False


def test_receipts_get_renders_line_items(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)

    def fake_get_receipt(session, receipt_id):
        return Receipt(
            id=receipt_id,
            order=ReceiptOrder(
                id="order-123",
                merchant_name="Store",
                line_items=[ReceiptLineItem(id="line-1", title="Coffee", total=4.5)],
            ),
        )

    monkeypatch.setattr("monarch_cli.groups.receipts.get_receipt", fake_get_receipt)

    result = runner.invoke(
        app,
        ["receipts", "get", "receipt-123", "--session-path", str(session_path)],
    )

    assert result.exit_code == 0
    assert "Store" in result.output
    assert "Coffee" in result.output


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
