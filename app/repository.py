"""Data-access layer (CRUD + workflow transitions) for Kadisco_Operations."""

from __future__ import annotations

import sqlite3

from .database import get_connection
from .workflow import FINAL_STAGE

# Operations are always read joined to the material master so callers get the
# material description and unit of measure without storing free text.
_OPERATIONS_SELECT = """
SELECT o.*, m.material_name AS material_name, m.unit_of_measure AS unit_of_measure
FROM Kadisco_Operations o
JOIN Materials_Master m ON m.material_id = o.material_id
"""


# ---------- Materials master ----------
def list_materials() -> list[sqlite3.Row]:
    """Return every material from the master table, ordered by name."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT material_id, material_name, unit_of_measure
            FROM Materials_Master
            ORDER BY material_name COLLATE NOCASE
            """
        ).fetchall()


def get_material(material_id: int) -> sqlite3.Row | None:
    """Return a single master material or None."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT material_id, material_name, unit_of_measure
            FROM Materials_Master WHERE material_id = ?
            """,
            (material_id,),
        ).fetchone()


def create_material(material_name: str, unit_of_measure: str) -> tuple[int, bool]:
    """Add a material to the master table, returning ``(material_id, created)``.

    If a material with the same name already exists it is reused (``created=False``).
    """
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT material_id FROM Materials_Master WHERE material_name = ? COLLATE NOCASE",
            (material_name,),
        ).fetchone()
        if existing is not None:
            return int(existing["material_id"]), False
        cursor = conn.execute(
            "INSERT INTO Materials_Master (material_name, unit_of_measure) VALUES (?, ?)",
            (material_name, unit_of_measure),
        )
        return int(cursor.lastrowid), True


# ---------- Material requests ----------
def create_request(material_id: int, quantity: int) -> int:
    """Insert a new material request at the 'Requested' stage."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO Kadisco_Operations (material_id, quantity) VALUES (?, ?)",
            (material_id, quantity),
        )
        return int(cursor.lastrowid)


def list_requests() -> list[sqlite3.Row]:
    """Return all requests, newest first, with their material details."""
    with get_connection() as conn:
        return conn.execute(
            _OPERATIONS_SELECT + " ORDER BY o.request_id DESC"
        ).fetchall()


def get_request(request_id: int) -> sqlite3.Row | None:
    """Return a single request or None."""
    with get_connection() as conn:
        return conn.execute(
            _OPERATIONS_SELECT + " WHERE o.request_id = ?", (request_id,)
        ).fetchone()


def _update(request_id: int, **columns) -> None:
    """Update the given columns for a request. Column names are internal only."""
    assignments = ", ".join(f"{name} = ?" for name in columns)
    with get_connection() as conn:
        conn.execute(
            f"UPDATE Kadisco_Operations SET {assignments} WHERE request_id = ?",
            [*columns.values(), request_id],
        )


def start_quoting(request_id: int) -> None:
    """Procurement begins sourcing: Requested -> Quoting."""
    _update(request_id, stage="Quoting", procurement_status="Quoting")


def send_for_approval(request_id: int, supplier_name: str, price: float) -> None:
    """Capture supplier + price and route to management: Quoting -> Pending Approval."""
    _update(
        request_id,
        stage="Pending Approval",
        procurement_status="Pending Approval",
        supplier_name=supplier_name,
        price=price,
    )


def simulate_management_approval(request_id: int) -> None:
    """External trigger: management approves. Pending Approval -> PO Issued."""
    _update(
        request_id,
        stage="PO Issued",
        management_approval_status="Approved",
    )


def issue_purchase_order(request_id: int) -> None:
    """Procurement raises the PO: PO Issued -> In Transit."""
    _update(request_id, stage="In Transit", procurement_status="PO Issued")


def simulate_warehouse_receipt(request_id: int) -> None:
    """External trigger: goods received & quantity verified. In Transit -> Invoicing."""
    _update(
        request_id,
        stage="Invoicing",
        warehouse_status="Goods Received",
    )


def simulate_finance_payment(request_id: int) -> None:
    """External trigger: finance pays. Invoicing -> Paid (loop closed)."""
    _update(
        request_id,
        stage=FINAL_STAGE,
        finance_payment_status="Paid",
        procurement_status="Completed",
    )


def delete_request(request_id: int) -> None:
    """Permanently remove a request."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM Kadisco_Operations WHERE request_id = ?", (request_id,)
        )


def dashboard_stats() -> dict[str, int]:
    """Aggregate counts for the dashboard KPI cards."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT stage, COUNT(*) AS total FROM Kadisco_Operations GROUP BY stage"
        ).fetchall()
    counts = {row["stage"]: row["total"] for row in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "open": total - counts.get(FINAL_STAGE, 0),
        "awaiting_approval": counts.get("Pending Approval", 0),
        "completed": counts.get(FINAL_STAGE, 0),
    }
