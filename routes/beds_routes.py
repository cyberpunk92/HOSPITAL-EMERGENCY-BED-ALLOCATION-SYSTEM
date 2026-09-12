"""Bed management module (Admin, read-only view).

Bed status is driven entirely by the workflow + DB triggers
(assign -> OCCUPIED, discharge -> PENDING_CLEANING, sanitization -> AVAILABLE).
No manual status changes are allowed.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from config.auth import role_required, current_user
from services import bed_service, admission_service
from services.ward_service import ward_options

beds_bp = Blueprint("beds", __name__, url_prefix="/beds")
ADMIN = role_required("Admin Staff")


@beds_bp.route("/")
@ADMIN
def list_beds():
    status = request.args.get("status", "").strip() or None
    ward_id = request.args.get("ward", "").strip() or None
    return render_template(
        "beds/list.html", user=current_user(),
        beds=bed_service.list_beds(status, ward_id),
        counts=bed_service.counts_by_status(),
        wards=ward_options(), statuses=bed_service.VALID_STATUSES,
        waiting=admission_service.patients_awaiting_bed(),
        status_filter=status or "", ward_filter=ward_id or "",
    )


@beds_bp.route("/<int:bed_id>/assign", methods=["POST"])
@ADMIN
def assign(bed_id):
    """Place a waiting (admitted) patient into this AVAILABLE bed."""
    admission_id = request.form.get("admission_id")
    if not admission_id:
        flash("Select a patient to assign to this bed.", "danger")
        return redirect(url_for("beds.list_beds"))
    try:
        admission_service.assign_bed(int(admission_id), bed_id)
        flash("Patient assigned to the bed. It is now occupied.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Could not assign bed: {e}", "danger")
    return redirect(url_for("beds.list_beds"))


@beds_bp.route("/<int:bed_id>")
@ADMIN
def detail(bed_id):
    bed = bed_service.get_bed(bed_id)
    if not bed:
        abort(404)
    return render_template(
        "beds/detail.html", user=current_user(), bed=bed,
        features=bed_service.bed_features(bed_id),
        history=bed_service.status_history(bed_id),
    )
