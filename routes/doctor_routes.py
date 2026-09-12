"""Doctor module (Emergency + Ward) — sees only their own patients."""

from flask import Blueprint, render_template

from config.auth import role_required, current_user
from services import admission_service

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")
DOCTOR = role_required("Emergency Doctor", "Ward Doctor")


@doctor_bp.route("/")
@DOCTOR
def dashboard():
    me = current_user()
    profile = admission_service.doctor_profile(me["user_id"])
    is_emergency = "Emergency Doctor" in me["roles"]
    my_patients = admission_service.list_admissions(status="ACTIVE", doctor_id=me["user_id"])
    # Emergency doctors also see the unassigned triage queue.
    triage = admission_service.triage_list() if is_emergency else []
    return render_template(
        "doctor/dashboard.html", user=me, profile=profile,
        is_emergency=is_emergency, my_patients=my_patients, triage=triage,
    )
