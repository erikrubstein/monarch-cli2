from __future__ import annotations

from functools import wraps
from typing import Any, Callable, NoReturn, TypeVar, cast

from monarch_api import MonarchAuthError, MonarchError, MfaRequiredError
from typer import _click

from monarch_cli.output import clear_output_fields, configure_output_fields

F = TypeVar("F", bound=Callable[..., Any])


def raise_cli_error(
    message: str,
    *,
    exit_code: int = 1,
    cause: BaseException | None = None,
) -> NoReturn:
    error = _click.ClickException(message)
    error.exit_code = exit_code
    if cause is not None:
        raise error from cause
    raise error


def handle_cli_errors(function: F) -> F:
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            configure_output_fields(
                kwargs.get("output_fields"),
                kwargs.get("append_output_fields"),
            )
            return function(*args, **kwargs)
        except MfaRequiredError as error:
            raise_cli_error(
                "MFA is required. Run login again with --mfa-code.",
                exit_code=2,
                cause=error,
            )
        except MonarchAuthError as error:
            raise_cli_error(f"Authentication failed: {error}", cause=error)
        except MonarchError as error:
            raise_cli_error(str(error), cause=error)
        except FileNotFoundError as error:
            raise_cli_error(str(error), cause=error)
        except ValueError as error:
            raise_cli_error(str(error), cause=error)
        finally:
            clear_output_fields()

    return cast(F, wrapper)
