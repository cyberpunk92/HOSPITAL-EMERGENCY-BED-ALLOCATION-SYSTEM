"""Admission workflow module (Phase 8)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from config.auth import role_required, current_user
from services import admission_service, patient_service, bed_service, ward_service

admissions_bp = Blueprint("admissions", __name__, url_prefix="/admissions")
ADM_STAFF = role_required("Admin Staff", "Emergency Doctor", "Ward Doctor")  # view detail
ADMIN = role_required("Admin Staff")          # registration + assign doctor/bed
DOCTOR = role_required("Emergency Doctor", "Ward Doctor")  # clinical actions


@admissions_bp.route("/")
@ADMIN
def list_admissions():
    status = request.args.get("status", "ACTIVE").strip() or None
    return render_template(
        "admissions/list.html", user=current_user(),
        admissions=admission_service.list_admissions(status),
        triage=admission_service.triage_list(),
        status_filter=status or "",
    )


@admissions_bp.route("/new", methods=["GET", "POST"])
@ADMIN
def new():
    if request.method == "POST":
        form = request.form
        if not form.get("patient_id") or not form.get("triage_priority") or not form.get("chief_complaint"):
            flash("Patient, triage priority and chief complaint are required.", "danger")
            return render_template("admissions/new.html", user=current_user(),
                                   patients=patient_service.patient_options(), form=form)
        try:
            adm_id = admission_service.create_admission(
                int(form["patient_id"]), int(form["triage_priority"]),
                form["chief_complaint"].strip(),
            )
            flash(f"Admission #{adm_id} registered.", "success")
            return redirect(url_for("admissions.detail", admission_id=adm_id))
        except ValueError as e:
            flash(str(e), "danger")  # duplicate active admission
        except Exception as e:
            flash(f"Could not register admission: {e}", "danger")
        return render_template("admissions/new.html", user=current_user(),
                               patients=patient_service.patient_options(), form=form)
    return render_template("admissions/new.html", user=current_user(),
                           patients=patient_service.patient_options(), form={})


@admissions_bp.route("/<int:admission_id>")
@ADM_STAFF
def detail(admission_id):
    adm = admission_service.get_admission(admission_id)
    if not adm:
        abort(404)
    return render_template(
        "admissions/detail.html", user=current_user(), adm=adm,
        doctors=admission_service.doctor_options(),
        results=admission_service.nurse_results(admission_id),
        assigned_nurses=admission_service.assigned_nurses(admission_id),
        nurse_history=admission_service.nurse_history(admission_id),
        nurses=admission_service.nurse_options(),
        task_types=admission_service.NURSE_TASK_TYPES,
        wards=ward_service.ward_options(),
    )


@admissions_bp.route("/<int:admission_id>/transfer", methods=["POST"])
@DOCTOR
def transfer(admission_id):
    to_ward = request.form.get("to_ward")
    if not to_ward:
        flash("Select a target ward.", "danger")
        return redirect(url_for("admissions.detail", admission_id=admission_id))
    try:
        admission_service.transfer(admission_id, int(to_ward))
        flash("Patient transferred. Previous bed flagged for cleaning.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Transfer failed: {e}", "danger")
    return redirect(url_for("admissions.detail", admission_id=admission_id))


@admissions_bp.route("/<int:admission_id>/assign-nurse", methods=["POST"])
@DOCTOR
def assign_nurse(admission_id):
    nurse_id = request.form.get("nurse_id")
    tasks = request.form.getlist("tasks")
    if not nurse_id:
        flash("Select a nurse.", "danger")
    elif not tasks:
        flash("Select at least one task to assign.", "danger")
    else:
        admission_service.assign_nurse_with_tasks(int(nurse_id), admission_id, tasks)
        flash("Nurse task(s) assigned.", "success")
    return redirect(url_for("admissions.detail", admission_id=admission_id))


@admissions_bp.route("/<int:admission_id>/assign-doctor", methods=["POST"])
@ADMIN
def assign_doctor(admission_id):
    doctor_id = request.form.get("doctor_id")
    if doctor_id:
        admission_service.assign_doctor(admission_id, int(doctor_id))
        flash("Doctor assigned.", "success")
    return redirect(url_for("admissions.detail", admission_id=admission_id))


@admissions_bp.route("/<int:admission_id>/diagnose", methods=["POST"])
@DOCTOR
def diagnose(admission_id):
    diagnosis = request.form.get("diagnosis", "").strip()
    if diagnosis:
        admission_service.set_diagnosis(admission_id, diagnosis)
        flash("Diagnosis recorded.", "success")
    else:
        flash("Diagnosis text is required.", "danger")
    return redirect(url_for("admissions.detail", admission_id=admission_id))


# Bed assignment is now automatic on admit (see /admit). No manual admin route.


@admissions_bp.route("/<int:admission_id>/discharge", methods=["POST"])
@DOCTOR
def discharge(admission_id):
    n = admission_service.discharge(admission_id)
    if n:
        flash("Patient discharged. Bed flagged for sanitization.", "success")
    else:
        flash("Admission was not active.", "warning")
    return redirect(url_for("admissions.detail", admission_id=admission_id))


@admissions_bp.route("/<int:admission_id>/admit", methods=["POST"])
@DOCTOR
def admit(admission_id):
    """Doctor admits the patient; the system auto-assigns a bed."""
    try:
        result = admission_service.admit(admission_id)
        status = result["status"]
        ward = result.get("ward")
        if status == "assigned":
            flash(f"Patient admitted. A {ward} bed was assigned automatically.", "success")
        elif status == "already":
            flash("Patient admitted (already has a bed).", "success")
        elif status == "no_bed_medical":
            flash(f"Patient admitted, but no {ward} bed is free. Maintenance has been asked to add a bed.", "warning")
        elif status == "no_bed":
            flash(f"No {ward} bed is currently available.", "danger")
        else:  # no_ward
            flash("Could not match this complaint to a ward. Please record a recognised chief complaint.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admissions.detail", admission_id=admission_id))
