"""Maintenance module — equipment availability, refills, Medical-Ward extra beds."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from config.auth import role_required, current_user
from services import maintenance_service

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")
MAINT = role_required("Maintenance Staff")


@maintenance_bp.route("/")
@MAINT
def dashboard():
    return render_template(
        "maintenance/dashboard.html", user=current_user(),
        profile=maintenance_service.get_staff(current_user()["user_id"]),
        glucose_stock=maintenance_service.glucose_stock(),
        wards_capacity=maintenance_service.wards_capacity(),
        requests=maintenance_service.list_requests(),
        refill_batch=maintenance_service.REFILL_BATCH,
    )


@maintenance_bp.route("/refill", methods=["POST"])
@MAINT
def refill():
    """Add a fixed batch of glucose strips to one ward (one-click refill)."""
    ward_id = request.form.get("ward_id", "")
    try:
        added = maintenance_service.refill(
            int(ward_id) if ward_id.isdigit() else None,
            "Glucose Strips", maintenance_service.REFILL_BATCH)
        flash(f"Added {added} glucose strips. The nurse dashboard now reflects the new stock.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("maintenance.dashboard"))


@maintenance_bp.route("/add-bed", methods=["POST"])
@MAINT
def add_bed():
    """Create + allocate one new AVAILABLE bed to a full ward (one click)."""
    ward_id = request.form.get("ward_id")
    if not ward_id:
        flash("Select a ward.", "danger")
        return redirect(url_for("maintenance.dashboard"))
    try:
        bed_number = maintenance_service.add_bed(int(ward_id))
        flash(f"Bed {bed_number} created and is now AVAILABLE for assignment.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Could not add bed: {e}", "danger")
    return redirect(url_for("maintenance.dashboard"))


@maintenance_bp.route("/requests/<int:request_id>/status", methods=["POST"])
@MAINT
def request_status(request_id):
    maintenance_service.update_request_status(request_id, request.form.get("status", "OPEN"))
    flash("Request updated.", "success")
    return redirect(url_for("maintenance.dashboard"))
