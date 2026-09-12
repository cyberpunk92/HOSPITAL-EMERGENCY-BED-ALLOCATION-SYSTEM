"""Patient self-service portal (read-only)."""

from flask import Blueprint, render_template

from config.auth import role_required, current_user
from services import patient_service

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


@patient_bp.route("/")
@role_required("Patient")
def dashboard():
    me = current_user()
    patient = patient_service.get_patient_by_user(me["user_id"])
    if not patient:
        return render_template("patient/no_record.html", user=me)

    adm = patient_service.portal_admission(patient["patient_id"])
    nurse = patient_service.assigned_nurse(adm["admission_id"]) if adm else None
    glucose = patient_service.latest_glucose(adm["admission_id"]) if adm else None

    # Build the patient timeline.
    timeline = []
    if adm:
        timeline = [
            {"label": "Registered", "done": True,
             "detail": adm["arrival_timestamp"].strftime("%Y-%m-%d %H:%M") if adm["arrival_timestamp"] else ""},
            {"label": "Assigned Doctor", "done": bool(adm["doctor_name"]), "detail": adm["doctor_name"] or ""},
            {"label": "Assigned Ward", "done": bool(adm["ward_id"]),
             "detail": adm["ward_name"] or ""},
            {"label": "Bed Assigned", "done": bool(adm["had_bed"]), "detail": adm["bed_number"] or ""},
            {"label": "Nurse Tasks", "done": bool(nurse), "detail": nurse or ""},
            {"label": "Discharged", "done": adm["admission_status"] == "DISCHARGED",
             "detail": adm["discharge_timestamp"].strftime("%Y-%m-%d %H:%M") if adm["discharge_timestamp"] else ""},
        ]

    return render_template(
        "patient/dashboard.html", user=me, patient=patient, adm=adm,
        nurse=nurse, glucose=glucose, timeline=timeline,
        vitals=patient_service.latest_vitals(patient["patient_id"]),
        admissions=patient_service.patient_admissions(patient["patient_id"]),
    )
