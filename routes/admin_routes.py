"""Admin Staff module (Phase 5): dashboard + user management."""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from config.auth import role_required, current_user
from config.validation import ValidationError
from services.dashboard_service import hospital_overview, ward_capacity_summary, role_distribution
from services import staff_service, dispatch_service
from services.ward_service import ward_options

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ADMIN_ONLY = role_required("Admin Staff")


@admin_bp.route("/")
@ADMIN_ONLY
def dashboard():
    return render_template(
        "admin/dashboard.html",
        user=current_user(),
        overview=hospital_overview(),
        wards=ward_capacity_summary(),
        roles=role_distribution(),
    )


@admin_bp.route("/users")
@ADMIN_ONLY
def users():
    search = request.args.get("q", "").strip() or None
    role = request.args.get("role", "").strip() or None
    return render_template(
        "admin/users.html",
        user=current_user(),
        users=staff_service.list_users(search, role),
        roles=staff_service.ROLE_NAMES,
        q=search or "", role_filter=role or "",
    )


@admin_bp.route("/users/new", methods=["GET", "POST"])
@ADMIN_ONLY
def user_new():
    if request.method == "POST":
        form = request.form
        required = ["fname", "lname", "email", "password", "role"]
        if not all(form.get(f) for f in required):
            flash("First name, last name, email, password and role are required.", "danger")
            return render_template("admin/user_form.html", user=current_user(),
                                   roles=staff_service.ROLE_NAMES, wards=ward_options(), form=form)
        try:
            uid = staff_service.create_staff_user({
                "fname": form["fname"].strip(), "lname": form["lname"].strip(),
                "email": form["email"].strip(), "phone": form.get("phone", "").strip(),
                "password": form["password"], "role": form["role"],
                "specialization": form.get("specialization"), "license_no": form.get("license_no"),
                "department": form.get("department"), "shift_timing": form.get("shift_timing"),
                "assigned_ward": form.get("assigned_ward") or None,
                "ambulance_type": form.get("ambulance_type"), "service_name": form.get("service_name"),
                "assigned_region": form.get("assigned_region"), "gender": form.get("gender"),
            })
            flash(f"User #{uid} created successfully.", "success")
            return redirect(url_for("admin.users"))
        except ValidationError as e:
            for msg in e.errors:
                flash(msg, "danger")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Could not create user: {e}", "danger")
        return render_template("admin/user_form.html", user=current_user(),
                               roles=staff_service.ROLE_NAMES, wards=ward_options(), form=form)

    return render_template("admin/user_form.html", user=current_user(),
                           roles=staff_service.ROLE_NAMES, wards=ward_options(), form={})


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@ADMIN_ONLY
def user_toggle(user_id):
    staff_service.toggle_active(user_id)
    flash("User status updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/staff")
@ADMIN_ONLY
def staff():
    return render_template(
        "admin/staff.html", user=current_user(),
        doctors=staff_service.list_doctors(),
        nurses=staff_service.list_nurses(),
        maintenance=staff_service.list_maintenance(),
    )


@admin_bp.route("/arrivals")
@ADMIN_ONLY
def arrivals():
    return render_template(
        "admin/arrivals.html", user=current_user(),
        queue=dispatch_service.arrival_queue(),
    )


@admin_bp.route("/arrivals/<int:queue_id>/confirm", methods=["POST"])
@ADMIN_ONLY
def confirm_arrival(queue_id):
    entry = dispatch_service.get_queue_entry(queue_id)
    if not entry:
        flash("Queue entry not found.", "danger")
        return redirect(url_for("admin.arrivals"))
    dispatch_service.confirm_arrival(queue_id)
    flash(f"Arrival confirmed for {entry['patient_name']}. Complete registration below.", "success")
    # Hand off to the registration form, pre-filled.
    return redirect(url_for("patients.new", name=entry["patient_name"], cnic=entry["cnic"] or ""))
