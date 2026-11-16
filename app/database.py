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

# Master list of materials. Material requests reference this table by id so the
# material description stored on an operation is never free text.
MATERIALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS Materials_Master (
    material_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name   TEXT    NOT NULL UNIQUE,
    unit_of_measure TEXT    NOT NULL
);
"""

# Operations reference the master table through `material_id`.
OPERATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS Kadisco_Operations (
    request_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id                INTEGER NOT NULL REFERENCES Materials_Master(material_id),
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

SCHEMA = MATERIALS_SCHEMA + OPERATIONS_SCHEMA

# Columns introduced after the first prototype build, applied to older databases.
_MIGRATIONS = {
    "price": "ALTER TABLE Kadisco_Operations ADD COLUMN price REAL",
    "stage": "ALTER TABLE Kadisco_Operations ADD COLUMN stage TEXT NOT NULL DEFAULT 'Requested'",
}

# A short starter list so the searchable dropdown is useful on a fresh install.
_SEED_MATERIALS = [
    ("Cotton Fabric 40s", "Meters"),
    ("Blue Paint", "Liters"),
    ("Red Paint", "Liters"),
    ("Steel Sheet 2mm", "Sheets"),
    ("Aluminium Ingot", "Kilograms"),
    ("Sodium Hydroxide", "Kilograms"),
    ("Packaging Carton (Large)", "Pieces"),
    ("Industrial Adhesive", "Liters"),
]


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_operations(conn: sqlite3.Connection) -> None:
    """Normalise an older Kadisco_Operations table that stored free-text material names.

    Existing names are promoted into Materials_Master, then the operations table is
    rebuilt so it references the master table by ``material_id`` instead.
    """
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(Kadisco_Operations)")}
    if "material_name" not in columns:
        return  # Already normalised.

    conn.execute(
        """
        INSERT OR IGNORE INTO Materials_Master (material_name, unit_of_measure)
        SELECT DISTINCT TRIM(material_name), 'Units'
        FROM Kadisco_Operations
        WHERE TRIM(COALESCE(material_name, '')) <> ''
        """
    )

    conn.execute("ALTER TABLE Kadisco_Operations RENAME TO Kadisco_Operations_legacy")
    conn.executescript(OPERATIONS_SCHEMA)
    conn.execute(
        """
        INSERT INTO Kadisco_Operations (
            request_id, material_id, quantity, supplier_name, price, stage,
            procurement_status, management_approval_status, warehouse_status,
            finance_payment_status, created_at
        )
        SELECT o.request_id, m.material_id, o.quantity, o.supplier_name, o.price,
               o.stage, o.procurement_status, o.management_approval_status,
               o.warehouse_status, o.finance_payment_status, o.created_at
        FROM Kadisco_Operations_legacy o
        JOIN Materials_Master m ON m.material_name = TRIM(o.material_name)
        """
    )
    conn.execute("DROP TABLE Kadisco_Operations_legacy")


def _seed_materials(conn: sqlite3.Connection) -> None:
    """Populate the master table with starter items the first time it is created."""
    if conn.execute("SELECT COUNT(*) FROM Materials_Master").fetchone()[0]:
        return
    conn.executemany(
        "INSERT INTO Materials_Master (material_name, unit_of_measure) VALUES (?, ?)",
        _SEED_MATERIALS,
    )


def init_db() -> None:
    """Create the tables if needed, apply column migrations and normalise old data."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        existing = {
            row["name"] for row in conn.execute("PRAGMA table_info(Kadisco_Operations)")
        }
        for column, statement in _MIGRATIONS.items():
            if column not in existing:
                conn.execute(statement)
        _migrate_operations(conn)
        _seed_materials(conn)
