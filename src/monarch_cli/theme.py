from __future__ import annotations

from rich.console import Console
from rich.theme import Theme
import typer.rich_utils


THEME = Theme(
    {
        "accent": "bright_blue",
        "accent.soft": "steel_blue",
        "muted": "grey62",
        "success": "green3",
        "warning": "yellow3",
        "error": "red3",
        "money.positive": "green3",
        "money.negative": "red3",
        "meta": "grey50",
        "json.brace": "grey62",
        "json.key": "bold steel_blue1",
        "json.str": "grey78",
        "json.number": "steel_blue3",
        "json.bool_true": "grey70",
        "json.bool_false": "grey70",
        "json.null": "grey50",
    }
)

console = Console(theme=THEME)


def configure_typer_help_styles() -> None:
    """Keep Typer's generated help close to the CLI's quiet palette."""
    typer.rich_utils.STYLE_OPTION = "bold steel_blue1"
    typer.rich_utils.STYLE_SWITCH = "steel_blue1"
    typer.rich_utils.STYLE_NEGATIVE_OPTION = "steel_blue1"
    typer.rich_utils.STYLE_NEGATIVE_SWITCH = "steel_blue1"
    typer.rich_utils.STYLE_METAVAR = "bold grey70"
    typer.rich_utils.STYLE_REQUIRED_SHORT = "grey62"
    typer.rich_utils.STYLE_REQUIRED_LONG = "grey62"
    typer.rich_utils.STYLE_OPTION_DEFAULT = "grey50"
    typer.rich_utils.STYLE_OPTION_ENVVAR = "grey50"
    typer.rich_utils.STYLE_OPTION_HELP = "grey78"
    typer.rich_utils.STYLE_HELPTEXT = "grey78"
    typer.rich_utils.STYLE_USAGE = "grey62"
    typer.rich_utils.STYLE_USAGE_COMMAND = "bold grey78"
    typer.rich_utils.STYLE_OPTIONS_PANEL_BORDER = "grey35"
    typer.rich_utils.STYLE_COMMANDS_PANEL_BORDER = "grey35"
    typer.rich_utils.STYLE_ERRORS_PANEL_BORDER = "red3"
    typer.rich_utils.STYLE_COMMANDS_TABLE_FIRST_COLUMN = "bold steel_blue1"
