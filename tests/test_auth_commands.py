from __future__ import annotations

from monarch_api import AuthSession, MfaRequiredError
from typer.testing import CliRunner

from monarch_cli.app import app

runner = CliRunner()


def test_auth_status_reports_missing_session(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = runner.invoke(app, ["auth", "status", "--session-path", str(missing)])

    assert result.exit_code == 1
    assert "No saved session found" in result.output


def test_auth_use_and_export_session(tmp_path) -> None:
    source = tmp_path / "source.json"
    active = tmp_path / "active.json"
    exported = tmp_path / "exported.json"
    source.write_text(
        """
        {
          "token": "token-123",
          "token_expiration": "2030-01-01T00:00:00Z",
          "user_id": "user-123",
          "email": "person@example.com"
        }
        """,
        encoding="utf-8",
    )

    use_result = runner.invoke(
        app,
        ["auth", "use", str(source), "--session-path", str(active)],
    )
    export_result = runner.invoke(
        app,
        ["auth", "export", str(exported), "--session-path", str(active)],
    )

    assert use_result.exit_code == 0
    assert export_result.exit_code == 0
    assert "person@example.com" in export_result.output
    assert exported.exists()


def test_auth_login_prompts_for_mfa_when_required(monkeypatch, tmp_path) -> None:
    calls: list[str | None] = []

    def fake_create_session(
        email: str,
        password: str,
        *,
        mfa_code: str | None = None,
        trusted_device: bool = True,
        session_path=None,
    ) -> AuthSession:
        calls.append(mfa_code)
        if mfa_code is None:
            raise MfaRequiredError(
                "MFA is required. Call create_session again with mfa_code."
            )
        return AuthSession(
            token="token-123",
            token_expiration="2030-01-01T00:00:00Z",
            user_id="user-123",
            email=email,
        )

    monkeypatch.setattr("monarch_cli.auth.create_session", fake_create_session)

    result = runner.invoke(
        app,
        [
            "auth",
            "login",
            "person@example.com",
            "--password",
            "secret",
            "--session-path",
            str(tmp_path / "session.json"),
        ],
        input="123456\n",
    )

    assert result.exit_code == 0
    assert calls == [None, "123456"]
    assert "MFA code" in result.output
    assert "person@example.com" in result.output
    assert "create_session" not in result.output
