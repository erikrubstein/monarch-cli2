from __future__ import annotations

import os
from pathlib import Path

from monarch_api import AuthSession, load_session, save_session


CONFIG_DIR_ENV = "MONARCH_CONFIG_DIR"
SESSION_PATH_ENV = "MONARCH_SESSION_PATH"


def config_dir() -> Path:
    configured = os.environ.get(CONFIG_DIR_ENV)
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config" / "monarch"


def default_session_path() -> Path:
    configured = os.environ.get(SESSION_PATH_ENV)
    if configured:
        return Path(configured).expanduser()
    return config_dir() / "session.json"


def resolve_session_path(session_path: str | Path | None) -> Path:
    if session_path is None:
        return default_session_path()
    return Path(session_path).expanduser()


def has_session(session_path: str | Path | None = None) -> bool:
    return resolve_session_path(session_path).exists()


def read_session(session_path: str | Path | None = None) -> AuthSession:
    return load_session(resolve_session_path(session_path))


def write_session(
    session: AuthSession,
    session_path: str | Path | None = None,
) -> Path:
    path = resolve_session_path(session_path)
    save_session(session, path)
    return path


def delete_session(session_path: str | Path | None = None) -> bool:
    path = resolve_session_path(session_path)
    if not path.exists():
        return False
    path.unlink()
    return True
