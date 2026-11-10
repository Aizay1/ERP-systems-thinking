"""HTTP routes for the procurement application."""

from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from . import repository, workflow

bp = Blueprint("main", __name__)


def _redirect_to_detail(request_id: int):
    return redirect(url_for("main.request_detail", request_id=request_id))


@bp.get("/")
def dashboard():
    """Procurement dashboard: KPIs plus the requests table."""
    return render_template(
        "dashboard.html",
        active_nav="dashboard",
        requests=repository.list_requests(),
        stats=repository.dashboard_stats(),
    )


@bp.get("/requests/<int:request_id>")
def request_detail(request_id: int):
    """Detail view with the workflow timeline and the current action."""
    record = repository.get_request(request_id)
    if record is None:
        abort(404)
    return render_template(
        "detail.html",
        active_nav="requests",
        r=record,
        stages=workflow.STAGES,
        descriptions=workflow.STAGE_DESCRIPTIONS,
        current_index=workflow.index_of(record["stage"]),
    )


@bp.post("/requests")
def create_request():
    """Create a new request (simulates Production input) at the 'Requested' stage."""
    material_name = (request.form.get("material_name") or "").strip()
    quantity_raw = (request.form.get("quantity") or "").strip()

    if not material_name or not quantity_raw.isdigit() or int(quantity_raw) <= 0:
        flash("Please provide a material name and a positive quantity.", "error")
        return redirect(url_for("main.dashboard"))

    request_id = repository.create_request(material_name, int(quantity_raw))
    flash(f"Request #{request_id} created and awaiting procurement review.", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/start-quoting")
def start_quoting(request_id: int):
    """Procurement action: begin sourcing."""
    repository.start_quoting(request_id)
    flash("Quoting started — capture a supplier and price.", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/send-for-approval")
def send_for_approval(request_id: int):
    """Procurement action: submit the quote for management approval."""
    supplier_name = (request.form.get("supplier_name") or "").strip()
    price_raw = (request.form.get("price") or "").strip()

    try:
        price = float(price_raw)
    except ValueError:
        price = -1.0

    if not supplier_name or price <= 0:
        flash("Enter a supplier name and a positive price to send for approval.", "error")
        return _redirect_to_detail(request_id)

    repository.send_for_approval(request_id, supplier_name, price)
    flash(f"Quote from “{supplier_name}” sent to management for approval.", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/simulate-management-approval")
def simulate_management_approval(request_id: int):
    """External trigger: management approval."""
    repository.simulate_management_approval(request_id)
    flash("Management approved the request (simulated).", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/issue-po")
def issue_purchase_order(request_id: int):
    """Procurement action: issue the purchase order."""
    repository.issue_purchase_order(request_id)
    flash("Purchase order issued to the supplier.", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/simulate-warehouse-receipt")
def simulate_warehouse_receipt(request_id: int):
    """External trigger: warehouse receipt with quantity verification."""
    repository.simulate_warehouse_receipt(request_id)
    flash("Warehouse confirmed receipt and verified quantities (simulated).", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/simulate-finance-payment")
def simulate_finance_payment(request_id: int):
    """External trigger: finance payment, closing the loop."""
    repository.simulate_finance_payment(request_id)
    flash("Finance released payment — the request is now closed (simulated).", "success")
    return _redirect_to_detail(request_id)


@bp.post("/requests/<int:request_id>/delete")
def delete_request(request_id: int):
    """Delete a request."""
    repository.delete_request(request_id)
    flash(f"Request #{request_id} deleted.", "success")
    return redirect(url_for("main.dashboard"))
