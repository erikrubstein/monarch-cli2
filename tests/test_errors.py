from __future__ import annotations

import typer
from monarch_api import MfaRequiredError
from typer.testing import CliRunner

from monarch_cli.errors import handle_cli_errors

runner = CliRunner()


def test_mfa_error_uses_cli_language() -> None:
    app = typer.Typer()

    @app.command()
    @handle_cli_errors
    def login() -> None:
        raise MfaRequiredError("MFA is required. Call create_session again with mfa_code.")

    result = runner.invoke(app)

    assert result.exit_code == 2
    assert "Run login again with --mfa-code" in result.output
    assert "create_session" not in result.output
    assert "mfa_code" not in result.output
