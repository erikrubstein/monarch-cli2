from __future__ import annotations

from monarch_api import Merchant, MerchantSort
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_merchants_list_passes_options(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_list_merchants(session, *, search=None, limit=None, offset=None, sort=None):
        captured["search"] = search
        captured["limit"] = limit
        captured["offset"] = offset
        captured["sort"] = sort
        return [Merchant(id="merchant-123", name="Store", transaction_count=3)]

    monkeypatch.setattr("monarch_cli.groups.merchants.list_merchants", fake_list_merchants)

    result = runner.invoke(
        app,
        [
            "merchants",
            "list",
            "--session-path",
            str(session_path),
            "--search",
            "sto",
            "--limit",
            "10",
            "--offset",
            "2",
            "--sort",
            "NAME",
        ],
    )

    assert result.exit_code == 0
    assert "Store" in result.output
    assert captured == {
        "search": "sto",
        "limit": 10,
        "offset": 2,
        "sort": MerchantSort.NAME,
    }


def test_merchants_update_passes_name(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_merchant(session, merchant_id, *, name=None):
        captured["merchant_id"] = merchant_id
        captured["name"] = name
        return Merchant(id=merchant_id, name=name or "Store")

    monkeypatch.setattr("monarch_cli.groups.merchants.update_merchant", fake_update_merchant)

    result = runner.invoke(
        app,
        [
            "merchants",
            "update",
            "merchant-123",
            "--session-path",
            str(session_path),
            "--name",
            "New Store",
        ],
    )

    assert result.exit_code == 0
    assert captured == {"merchant_id": "merchant-123", "name": "New Store"}
    assert "New Store" in result.output


def test_merchants_delete_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_merchant(session, merchant_id, *, move_to_merchant_id=None):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("monarch_cli.groups.merchants.delete_merchant", fake_delete_merchant)

    result = runner.invoke(
        app,
        ["merchants", "delete", "merchant-123", "--session-path", str(session_path)],
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
