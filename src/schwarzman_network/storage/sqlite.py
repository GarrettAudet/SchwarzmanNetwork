from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import SCHEMA_DIR


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize(conn: sqlite3.Connection) -> None:
    conn.executescript((SCHEMA_DIR / "schema.sql").read_text(encoding="utf-8"))
    conn.executescript((SCHEMA_DIR / "views.sql").read_text(encoding="utf-8"))
    conn.commit()
