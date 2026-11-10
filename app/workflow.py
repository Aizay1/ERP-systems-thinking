"""Workflow definition for the material-request lifecycle."""

from __future__ import annotations

# Ordered stages a request moves through. The stored `stage` column is always
# one of these values, and it marks the stage currently being worked on.
STAGES = [
    "Requested",
    "Quoting",
    "Pending Approval",
    "PO Issued",
    "In Transit",
    "Invoicing",
    "Paid",
]

FINAL_STAGE = STAGES[-1]

STAGE_DESCRIPTIONS = {
    "Requested": "Production raised the material request (simulated input).",
    "Quoting": "Procurement captures the supplier and quoted price.",
    "Pending Approval": "Awaiting management sign-off (external system).",
    "PO Issued": "Procurement raises the purchase order to the supplier.",
    "In Transit": "Goods in transit; awaiting warehouse receipt (external system).",
    "Invoicing": "Goods received; awaiting finance settlement (external system).",
    "Paid": "Payment settled — the request is closed.",
}


def index_of(stage: str) -> int:
    """Return the position of a stage, defaulting to the first stage."""
    try:
        return STAGES.index(stage)
    except ValueError:
        return 0


def is_final(stage: str) -> bool:
    """True once the request has completed the full workflow."""
    return stage == FINAL_STAGE
