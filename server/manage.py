"""Local setup commands. This never creates a default password."""

from __future__ import annotations

import argparse
import getpass
import os
import secrets
from pathlib import Path

from werkzeug.security import generate_password_hash


try:
    from .config import get_default_config_path
except ImportError:  # pragma: no cover
    from config import get_default_config_path


def create_config(output: Path) -> None:
    password = getpass.getpass("Create Batcave password: ")
    confirmation = getpass.getpass("Confirm Batcave password: ")
    if not password:
        raise SystemExit("Password cannot be empty.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing configuration: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "# Keep this file private. Do not commit it.\n"
        f"BATCAVE_SECRET_KEY={secrets.token_urlsafe(48)}\n"
        f"BATCAVE_PASSWORD_HASH={generate_password_hash(password)}\n",
        encoding="utf-8",
    )
    try:
        os.chmod(output, 0o600)
    except OSError:
        pass
    print(f"Created {output}.")
    try:
        is_default = output.resolve() == get_default_config_path().resolve()
    except Exception:
        is_default = False
    if is_default:
        print("Configuration saved to default location. Batcave Cloud will automatically discover it.")
    else:
        print("Set BATCAVE_CONFIG_FILE to this path before starting the app.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batcave Cloud local administration")
    command = parser.add_subparsers(dest="command", required=True)
    create = command.add_parser("create-config", help="create a secret key and password hash")
    create.add_argument(
        "--output",
        type=Path,
        default=None,
        help="path for the private KEY=value config file (defaults to ~/.config/batcave-cloud/batcave.env)",
    )
    args = parser.parse_args()
    if args.command == "create-config":
        output_path = args.output.expanduser() if args.output else get_default_config_path()
        create_config(output_path)


if __name__ == "__main__":
    main()
