"""SQLite connection management and schema definition for Kadisco_Operations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Database file lives next to the project root.
DB_PATH = Path(__file__).resolve().parent.parent / "kadisco.db"

# Department status values.
STATUS_PENDING = "Pending"
STATUS_QUOTING = "Quoting"
STATUS_PENDING_APPROVAL = "Pending Approval"
STATUS_APPROVED = "Approved"
STATUS_PO_ISSUED = "PO Issued"
STATUS_GOODS_RECEIVED = "Goods Received"
STATUS_PAID = "Paid"
STATUS_COMPLETED = "Completed"

SCHEMA = """
CREATE TABLE IF NOT EXISTS Kadisco_Operations (
    request_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name              TEXT    NOT NULL,
    quantity                   INTEGER NOT NULL,
    supplier_name              TEXT,
    price                      REAL,
    stage                      TEXT    NOT NULL DEFAULT 'Requested',
    procurement_status         TEXT    NOT NULL DEFAULT 'Pending',
    management_approval_status TEXT    NOT NULL DEFAULT 'Pending',
    warehouse_status           TEXT    NOT NULL DEFAULT 'Pending',
    finance_payment_status     TEXT    NOT NULL DEFAULT 'Pending',
    created_at                 TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# Columns introduced after the first prototype build, applied to older databases.
_MIGRATIONS = {
    "price": "ALTER TABLE Kadisco_Operations ADD COLUMN price REAL",
    "stage": "ALTER TABLE Kadisco_Operations ADD COLUMN stage TEXT NOT NULL DEFAULT 'Requested'",
}


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the table if needed and apply lightweight column migrations."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        existing = {
            row["name"] for row in conn.execute("PRAGMA table_info(Kadisco_Operations)")
        }
        for column, statement in _MIGRATIONS.items():
            if column not in existing:
                conn.execute(statement)
