from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from monarch_api import MfaRequiredError, create_session, load_session

from monarch_cli.config import delete_session, has_session, resolve_session_path, write_session
from monarch_cli.errors import handle_cli_errors
from monarch_cli.options import JsonOption, SessionPathOption, OutputFieldsOption
from monarch_cli.output import print_key_values, print_success, print_warning

app = typer.Typer(
    help="Sign in, inspect, and manage saved sessions.",
    no_args_is_help=True,
)


@app.command("login")
@handle_cli_errors
def login(
    email: Annotated[str, typer.Argument(help="Monarch account email address.")],
    password: Annotated[
        str,
        typer.Option(
            "--password",
            "-p",
            prompt=True,
            hide_input=True,
            help="Monarch account password.",
        ),
    ],
    mfa_code: Annotated[
        str | None,
        typer.Option("--mfa-code", help="Multi-factor authentication code."),
    ] = None,
    untrusted_device: Annotated[
        bool,
        typer.Option(
            "--untrusted-device",
            help="Do not ask Monarch to remember this device.",
        ),
    ] = False,
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Sign in and save an authenticated session."""
    path = resolve_session_path(session_path)
    try:
        session = create_session(
            email,
            password,
            mfa_code=mfa_code,
            trusted_device=not untrusted_device,
            session_path=path,
        )
    except MfaRequiredError:
        if mfa_code is not None:
            raise
        mfa_code = typer.prompt("MFA code")
        session = create_session(
            email,
            password,
            mfa_code=mfa_code,
            trusted_device=not untrusted_device,
            session_path=path,
        )
    print_key_values(
        "Signed In",
        {
            "email": session.email or email,
            "user_id": session.user_id,
            "token_expiration": session.token_expiration,
            "session_path": path,
        },
        json_output=json_output,
    )


@app.command("status")
@handle_cli_errors
def status(
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Show the currently saved session."""
    path = resolve_session_path(session_path)
    if not path.exists():
        print_warning(f"No saved session found at {path}.")
        raise typer.Exit(1)

    session = load_session(path)
    print_key_values(
        "Session",
        {
            "email": session.email,
            "user_id": session.user_id,
            "token_expiration": session.token_expiration,
            "session_path": path,
        },
        json_output=json_output,
    )


@app.command("use")
@handle_cli_errors
def use_session(
    source: Annotated[Path, typer.Argument(help="Session file to make active.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Use an existing session file as the active session."""
    session = load_session(source.expanduser())
    path = write_session(session, session_path)
    print_key_values(
        "Session Updated",
        {
            "email": session.email,
            "user_id": session.user_id,
            "token_expiration": session.token_expiration,
            "session_path": path,
        },
        json_output=json_output,
    )


@app.command("export")
@handle_cli_errors
def export_session(
    destination: Annotated[Path, typer.Argument(help="Where to write the session file.")],
    session_path: SessionPathOption = None,
    json_output: JsonOption = False,
    output_fields: OutputFieldsOption = None,
) -> None:
    """Copy the active session to another path."""
    source = resolve_session_path(session_path)
    session = load_session(source)
    destination_path = write_session(session, destination)
    print_key_values(
        "Session Exported",
        {
            "email": session.email,
            "user_id": session.user_id,
            "token_expiration": session.token_expiration,
            "destination": destination_path,
        },
        json_output=json_output,
    )


@app.command("logout")
@handle_cli_errors
def logout(
    session_path: SessionPathOption = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
) -> None:
    """Delete the saved session."""
    path = resolve_session_path(session_path)
    if not has_session(path):
        print_warning(f"No saved session found at {path}.")
        return

    if not yes and not typer.confirm(f"Delete saved session at {path}?"):
        print_warning("Session left unchanged.")
        return

    delete_session(path)
    print_success("Signed out.")
