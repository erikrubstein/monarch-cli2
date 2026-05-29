from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer


class TrueFalseFilter(str, Enum):
    TRUE = "true"
    FALSE = "false"


SessionPathOption = Annotated[
    Path | None,
    typer.Option(
        "--session-path",
        "-s",
        help="Path to the saved session file.",
    ),
]

JsonOption = Annotated[
    bool,
    typer.Option("--json", help="Print machine-readable JSON."),
]

RawOption = Annotated[
    bool,
    typer.Option("--raw", help="Include raw Monarch response data in JSON output."),
]

OutputFieldsOption = Annotated[
    str | None,
    typer.Option(
        "--fields",
        help="Comma-separated output fields to show. Supports dotted paths.",
    ),
]
