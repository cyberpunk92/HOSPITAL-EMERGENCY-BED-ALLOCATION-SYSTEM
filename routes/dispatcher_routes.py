"""Dispatcher module — emergency pre-registration into the arrival queue.

Shows only: CNIC, Name, Complaint -> recommended ward/doctor, CMH bed summary,
and this dispatcher's own queue. No address, no other dispatchers' patients.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from config.auth import role_required, current_user
from config.validation import validate, ValidationError
from services import dispatch_service, bed_service

dispatcher_bp = Blueprint("dispatcher", __name__, url_prefix="/dispatcher")
DISPATCH = role_required("Ambulance Dispatcher", "Service Dispatcher")


@dispatcher_bp.route("/")
@DISPATCH
def dashboard():
    me = current_user()
    return render_template(
        "dispatcher/dashboard.html", user=me,
        beds=bed_service.counts_by_status(),
        complaints=dispatch_service.complaint_options(),
        queue=dispatch_service.my_queue(me["user_id"]),
    )


@dispatcher_bp.route("/register", methods=["POST"])
@DISPATCH
def register():
    me = current_user()
    import re
    cnic = re.sub(r"\D", "", request.form.get("cnic", ""))
    name = request.form.get("patient_name", "").strip()
    complaint = request.form.get("chief_complaint", "").strip()

    errors = validate({"cnic": cnic, "patient_name": name, "chief_complaint": complaint}, {
        "cnic": [("required",), ("cnic",)],
        "patient_name": [("required",), ("alpha",), ("min_len", 2)],
        "chief_complaint": [("required",)],
    })
    if errors:
        for m in errors:
            flash(m, "danger")
        return redirect(url_for("dispatcher.dashboard"))
    try:
        dispatch_service.add_to_queue(me["user_id"], cnic, name, complaint)
        flash(f"{name} submitted to the arrival queue.", "success")
    except ValueError as e:
        flash(str(e), "danger")  # duplicate CNIC
    except Exception as e:
        flash(f"Could not register: {e}", "danger")
    return redirect(url_for("dispatcher.dashboard"))
