from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

import typer
from monarch_api import MonarchAuthError, MonarchError, MfaRequiredError

from monarch_cli.output import print_error, print_warning

F = TypeVar("F", bound=Callable[..., Any])


def handle_cli_errors(function: F) -> F:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return function(*args, **kwargs)
        except MfaRequiredError as error:
            print_warning("MFA is required. Run login again with --mfa-code.")
            raise typer.Exit(2) from error
        except MonarchAuthError as error:
            print_error(f"Authentication failed: {error}")
            raise typer.Exit(1) from error
        except MonarchError as error:
            print_error(str(error))
            raise typer.Exit(1) from error
        except FileNotFoundError as error:
            print_error(str(error))
            raise typer.Exit(1) from error
        except ValueError as error:
            print_error(str(error))
            raise typer.Exit(1) from error

    return cast(F, wrapper)
