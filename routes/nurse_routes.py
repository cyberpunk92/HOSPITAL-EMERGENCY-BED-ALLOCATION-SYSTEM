"""Nurse module — assigned patients + BP / Sugar / Glucose / Medicine tasks."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from config.auth import role_required, current_user
from services import nurse_service

nurse_bp = Blueprint("nurse", __name__, url_prefix="/nurse")
NURSE = role_required("Nurse")


def _int(v):
    try:
        return int(v) if v not in (None, "") else None
    except (ValueError, TypeError):
        return None


@nurse_bp.route("/")
@NURSE
def dashboard():
    me = current_user()
    profile = nurse_service.get_nurse(me["user_id"])
    ward_id = profile["assigned_ward"] if profile else None
    patients = nurse_service.assigned_patients(me["user_id"])
    return render_template(
        "nurse/dashboard.html", user=me, profile=profile,
        patients=patients, equipment=nurse_service.equipment_summary(ward_id),
        tasks=nurse_service.pending_tasks_map(me["user_id"]),
        vitals={p["admission_id"]: nurse_service.recent_vitals(p["admission_id"]) for p in patients},
    )


@nurse_bp.route("/bp", methods=["POST"])
@NURSE
def bp():
    me = current_user()
    f = request.form
    try:
        nurse_service.record_bp(int(f["admission_id"]), me["user_id"],
                                _int(f.get("systolic")), _int(f.get("diastolic")))
        flash("BP recorded.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Could not record BP: {e}", "danger")
    return redirect(url_for("nurse.dashboard"))


@nurse_bp.route("/sugar", methods=["POST"])
@NURSE
def sugar():
    me = current_user()
    f = request.form
    try:
        nurse_service.record_sugar(int(f["admission_id"]), me["user_id"], _int(f.get("sugar")))
        flash("Sugar recorded.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Could not record sugar: {e}", "danger")
    return redirect(url_for("nurse.dashboard"))


@nurse_bp.route("/glucose", methods=["POST"])
@NURSE
def glucose():
    me = current_user()
    profile = nurse_service.get_nurse(me["user_id"])
    ward_id = profile["assigned_ward"] if profile else None
    nurse_service.record_glucose_strip(int(request.form["admission_id"]), me["user_id"], ward_id)
    flash("Glucose strip completed. Ward stock updated; maintenance notified.", "success")
    return redirect(url_for("nurse.dashboard"))


@nurse_bp.route("/medicine", methods=["POST"])
@NURSE
def medicine():
    me = current_user()
    nurse_service.log_medicine(int(request.form["admission_id"]), me["user_id"])
    flash("Medicine task marked completed.", "success")
    return redirect(url_for("nurse.dashboard"))
