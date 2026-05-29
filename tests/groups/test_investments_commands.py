from __future__ import annotations

from monarch_api import Holding, Portfolio, PortfolioSummary, Security
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_investments_portfolio_passes_options(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_get_portfolio(
        session,
        *,
        account_ids=None,
        start_date=None,
        end_date=None,
        include_hidden_holdings=None,
        top_movers_limit=None,
    ):
        captured["account_ids"] = account_ids
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        captured["include_hidden_holdings"] = include_hidden_holdings
        captured["top_movers_limit"] = top_movers_limit
        return Portfolio(summary=PortfolioSummary(total_value=1000, holdings_count=0))

    monkeypatch.setattr("monarch_cli.groups.investments.get_portfolio", fake_get_portfolio)

    result = runner.invoke(
        app,
        [
            "investments",
            "portfolio",
            "--session-path",
            str(session_path),
            "--account-id",
            "account-123",
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-05-28",
            "--include-hidden-holdings",
            "--top-movers-limit",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "$1,000.00" in result.output
    assert captured == {
        "account_ids": ["account-123"],
        "start_date": "2026-01-01",
        "end_date": "2026-05-28",
        "include_hidden_holdings": True,
        "top_movers_limit": 5,
    }


def test_investments_search_securities_can_keep_original_order(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_search_securities(session, query, *, limit=20, order_by_popularity=True):
        captured["query"] = query
        captured["limit"] = limit
        captured["order_by_popularity"] = order_by_popularity
        return [Security(id="security-123", name="Apple", ticker="AAPL")]

    monkeypatch.setattr("monarch_cli.groups.investments.search_securities", fake_search_securities)

    result = runner.invoke(
        app,
        [
            "investments",
            "search-securities",
            "apple",
            "--session-path",
            str(session_path),
            "--limit",
            "3",
            "--original-order",
        ],
    )

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert captured == {"query": "apple", "limit": 3, "order_by_popularity": False}


def test_investments_update_holding_passes_values(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    captured: dict[str, object] = {}

    def fake_update_manual_holding(session, holding_id, *, quantity=None, cost_basis=None, security_type=None):
        captured["holding_id"] = holding_id
        captured["quantity"] = quantity
        captured["cost_basis"] = cost_basis
        captured["security_type"] = security_type
        return Holding(id=holding_id, name="Apple", quantity=quantity, cost_basis=cost_basis)

    monkeypatch.setattr(
        "monarch_cli.groups.investments.update_manual_holding",
        fake_update_manual_holding,
    )

    result = runner.invoke(
        app,
        [
            "investments",
            "update-holding",
            "holding-123",
            "--session-path",
            str(session_path),
            "--quantity",
            "4",
            "--cost-basis",
            "500",
            "--security-type",
            "stock",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "holding_id": "holding-123",
        "quantity": 4.0,
        "cost_basis": 500.0,
        "security_type": "stock",
    }


def test_investments_delete_holding_respects_confirmation(monkeypatch, tmp_path) -> None:
    session_path = _write_session(tmp_path)
    called = False

    def fake_delete_manual_holding(session, holding_id):
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(
        "monarch_cli.groups.investments.delete_manual_holding",
        fake_delete_manual_holding,
    )

    result = runner.invoke(
        app,
        ["investments", "delete-holding", "holding-123", "--session-path", str(session_path)],
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
