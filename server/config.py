"""Configuration loaded from environment variables, never committed secrets."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_DATA_ROOT = Path("/storage/emulated/0/BatCave")


def _boolean(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _integer(value: str | None, default: int, variable_name: str) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as error:
        raise RuntimeError(f"{variable_name} must be a whole number.") from error
    if parsed <= 0:
        raise RuntimeError(f"{variable_name} must be greater than zero.")
    return parsed


def load_environment_file(path: str | None) -> None:
    """Load a deliberately simple KEY=value file when explicitly requested."""
    if not path:
        return

    config_path = Path(path).expanduser()
    if not config_path.is_file():
        raise RuntimeError(f"BATCAVE_CONFIG_FILE does not exist: {config_path}")

    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            raise RuntimeError(f"Invalid configuration line in {config_path}")
        os.environ.setdefault(key.strip(), value.strip())


def build_config(overrides: dict | None = None) -> dict:
    """Build Flask configuration. Test overrides are applied last."""
    load_environment_file(os.environ.get("BATCAVE_CONFIG_FILE"))

    data_root = Path(os.environ.get("BATCAVE_DATA_ROOT", DEFAULT_DATA_ROOT)).expanduser()
    config = {
        "DATA_ROOT": data_root,
        "DATABASE_PATH": data_root / "batcave.db",
        "SECRET_KEY": os.environ.get("BATCAVE_SECRET_KEY"),
        "PASSWORD_HASH": os.environ.get("BATCAVE_PASSWORD_HASH"),
        "MAX_CONTENT_LENGTH": _integer(os.environ.get("BATCAVE_MAX_UPLOAD_MB"), 25, "BATCAVE_MAX_UPLOAD_MB")
        * 1024
        * 1024,
        "HOST": os.environ.get("BATCAVE_HOST", "0.0.0.0"),
        "PORT": _integer(os.environ.get("BATCAVE_PORT"), 8080, "BATCAVE_PORT"),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": _boolean(os.environ.get("BATCAVE_SECURE_COOKIES")),
        "SESSION_REFRESH_EACH_REQUEST": False,
    }
    if overrides:
        config.update(overrides)
    return config


def validate_security_config(config: dict) -> None:
    missing = [key for key in ("SECRET_KEY", "PASSWORD_HASH") if not config.get(key)]
    if missing:
        names = ", ".join(f"BATCAVE_{key}" for key in missing)
        raise RuntimeError(
            f"Missing required configuration: {names}. "
            "Run 'python -m server.manage create-config --output <path>' first."
        )
