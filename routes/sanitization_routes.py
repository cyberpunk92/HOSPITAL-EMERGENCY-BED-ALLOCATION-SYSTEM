"""Sanitization Staff module. Pending beds -> sanitize (3s sim) -> available.
Reuses the existing maintenance_service + sanitization triggers."""

from flask import Blueprint, render_template, redirect, url_for, flash

from config.auth import role_required, current_user
from services import maintenance_service

sanitization_bp = Blueprint("sanitization", __name__, url_prefix="/sanitization")
SAN = role_required("Sanitization Staff")


@sanitization_bp.route("/")
@SAN
def dashboard():
    return render_template(
        "sanitization/dashboard.html", user=current_user(),
        pending=maintenance_service.list_sanitizations(only_open=True),
        history=maintenance_service.list_sanitizations(),
    )


@sanitization_bp.route("/<int:log_id>/complete", methods=["POST"])
@SAN
def complete(log_id):
    # Sanitization staff can clear any pending bed (no per-staff filter).
    n = maintenance_service.complete_sanitization(log_id)
    if n:
        flash("Bed sanitized and returned to AVAILABLE.", "success")
    else:
        flash("Could not complete (already done or not assigned).", "warning")
    return redirect(url_for("sanitization.dashboard"))
