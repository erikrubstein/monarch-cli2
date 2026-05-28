from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

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
