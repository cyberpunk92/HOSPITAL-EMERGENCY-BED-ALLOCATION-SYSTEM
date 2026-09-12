"""Reporting module (Phase 13)."""

import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file

from config.auth import role_required, current_user
from services import report_service

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")
REPORT_VIEWERS = role_required("Admin Staff")


@reports_bp.route("/")
@REPORT_VIEWERS
def index():
    return render_template(
        "reports/index.html", user=current_user(),
        kpis=report_service.kpis(),
        occupancy=report_service.occupancy_by_ward(),
        by_status=report_service.admissions_by_status(),
        by_priority=report_service.admissions_by_priority(),
        sanitization=report_service.sanitization_summary(),
        audit=report_service.audit_trail(),
        doctor_workload=report_service.doctor_workload(),
        nurse_workload=report_service.nurse_workload(),
        discharges=report_service.discharge_report(),
        equipment=report_service.equipment_report(),
    )


@reports_bp.route("/export/<report_key>", methods=["POST"])
@REPORT_VIEWERS
def export(report_key):
    try:
        path = report_service.export_csv(report_key)
        flash(f"Exported to reports/{os.path.basename(path)}", "success")
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("reports.index"))
