from __future__ import annotations

from typing import Annotated

import typer

from monarch_cli import __version__
from monarch_cli import accounts
from monarch_cli import auth
from monarch_cli.theme import configure_typer_help_styles, console

configure_typer_help_styles()

app = typer.Typer(
    help="Command line interface for Monarch Money.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.add_typer(auth.app, name="auth")
app.add_typer(accounts.app, name="accounts")


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[accent]monarch[/accent] {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=version_callback,
            help="Show the CLI version.",
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Command line interface for Monarch Money."""


def main() -> None:
    app()
