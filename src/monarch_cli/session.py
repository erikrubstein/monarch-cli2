from __future__ import annotations

from monarch_api import AuthSession

from monarch_cli.config import read_session


def require_session(session_path: str | None = None) -> AuthSession:
    return read_session(session_path)
