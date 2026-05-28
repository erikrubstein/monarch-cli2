from __future__ import annotations

from monarch_api import AuthSession

from monarch_cli.config import read_session, resolve_session_path


def require_session(session_path: str | None = None) -> AuthSession:
    path = resolve_session_path(session_path)
    if not path.exists():
        raise FileNotFoundError(
            f"No saved session found at {path}. Run `monarch auth login` first."
        )
    return read_session(path)
