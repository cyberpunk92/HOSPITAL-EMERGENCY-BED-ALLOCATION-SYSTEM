"""Patient management module (Admin: register/update/delete; staff: view)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from config.auth import role_required, current_user
from config.validation import ValidationError
from services import patient_service

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")
STAFF = role_required("Admin Staff", "Emergency Doctor", "Ward Doctor", "Nurse")
ADMIN = role_required("Admin Staff")


def _form_payload(form):
    return {
        "full_name": form.get("full_name", "").strip(),
        "dob": form.get("dob", "").strip(),
        "gender": form.get("gender", ""),
        "national_id": form.get("national_id", "").strip(),
        "insurance_id": form.get("insurance_id", "").strip() or None,
        "emergency_contact": form.get("emergency_contact", "").strip() or None,
    }


@patients_bp.route("/")
@ADMIN
def list_patients():
    search = request.args.get("q", "").strip() or None
    page = request.args.get("page", 1, type=int)
    result = patient_service.paginate(search, page)
    return render_template(
        "patients/list.html", user=current_user(), result=result, q=search or "",
    )


@patients_bp.route("/<int:patient_id>")
@ADMIN
def detail(patient_id):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        abort(404)
    return render_template(
        "patients/detail.html", user=current_user(),
        patient=patient, admissions=patient_service.patient_admissions(patient_id),
        login=patient_service.get_login(patient_id),
    )


@patients_bp.route("/new", methods=["GET", "POST"])
@ADMIN
def new():
    if request.method == "POST":
        data = _form_payload(request.form)
        try:
            pid = patient_service.create_patient(data)
            flash(f"Patient '{data['full_name']}' registered successfully.", "success")
            return redirect(url_for("patients.detail", patient_id=pid))
        except ValidationError as e:
            for msg in e.errors:
                flash(msg, "danger")
        except Exception as e:
            flash(f"Could not register patient: {e}", "danger")
        return render_template("patients/form.html", user=current_user(), form=request.form, mode="new")
    # GET: optionally pre-fill from an arrival-queue handoff (?name=&cnic=)
    prefill = {"full_name": request.args.get("name", ""), "national_id": request.args.get("cnic", "")}
    return render_template("patients/form.html", user=current_user(), form=prefill, mode="new")


@patients_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@ADMIN
def edit(patient_id):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        abort(404)
    if request.method == "POST":
        data = _form_payload(request.form)
        try:
            patient_service.update_patient(patient_id, data)
            flash("Patient updated successfully.", "success")
            return redirect(url_for("patients.detail", patient_id=patient_id))
        except ValidationError as e:
            for msg in e.errors:
                flash(msg, "danger")
        except Exception as e:
            flash(f"Could not update patient: {e}", "danger")
        return render_template("patients/form.html", user=current_user(), form=request.form, mode="edit", patient_id=patient_id)
    # Pre-fill from the existing record.
    form = {
        "full_name": patient["full_name"],
        "dob": patient["date_of_birth"].strftime("%Y-%m-%d") if patient["date_of_birth"] else "",
        "gender": patient["gender"], "national_id": patient["national_id"],
        "insurance_id": patient["insurance_id"], "emergency_contact": patient["emergency_contact"],
    }
    return render_template("patients/form.html", user=current_user(), form=form, mode="edit", patient_id=patient_id)


@patients_bp.route("/<int:patient_id>/archive", methods=["POST"])
@ADMIN
def archive(patient_id):
    try:
        patient_service.archive_patient(patient_id)
        flash("Patient archived.", "success")
        return redirect(url_for("patients.list_patients"))
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Could not archive patient: {e}", "danger")
    return redirect(url_for("patients.detail", patient_id=patient_id))


@patients_bp.route("/<int:patient_id>/create-login", methods=["POST"])
@ADMIN
def create_login(patient_id):
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or "Hebas@123"
    if not email:
        flash("An email is required to create a portal login.", "danger")
        return redirect(url_for("patients.detail", patient_id=patient_id))
    try:
        patient_service.create_patient_login(patient_id, email, password)
        flash(f"Portal login created for {email} (password: {password}).", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Could not create login: {e}", "danger")
    return redirect(url_for("patients.detail", patient_id=patient_id))
