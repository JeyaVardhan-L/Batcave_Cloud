"""Small SQLite data layer with additive, versioned migrations."""

import sqlite3
from pathlib import Path

from flask import current_app, g


def get_connection(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = get_connection(Path(current_app.config["DATABASE_PATH"]))
    return g.db


def close_db(_error=None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def _migration_1(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def _migration_2(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(projects)")}
    if "folder_name" not in columns:
        connection.execute("ALTER TABLE projects ADD COLUMN folder_name TEXT")


MIGRATIONS = (_migration_1, _migration_2)


def init_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection(database_path)
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        for number, migration in enumerate(MIGRATIONS, start=1):
            if version < number:
                migration(connection)
                connection.execute(f"PRAGMA user_version = {number}")
        connection.commit()
    finally:
        connection.close()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    init_database(Path(app.config["DATABASE_PATH"]))
