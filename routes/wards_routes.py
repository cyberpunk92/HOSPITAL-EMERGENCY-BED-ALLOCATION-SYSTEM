"""Ward Management module (Admin)."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from config.auth import role_required, current_user
from services import ward_service

wards_bp = Blueprint("wards", __name__, url_prefix="/wards")
ADMIN_ONLY = role_required("Admin Staff")


@wards_bp.route("/")
@ADMIN_ONLY
def list_wards():
    return render_template(
        "wards/list.html", user=current_user(),
        wards=ward_service.wards_with_stats(),
    )


@wards_bp.route("/new", methods=["GET", "POST"])
@ADMIN_ONLY
def new():
    if request.method == "POST":
        f = request.form
        if not f.get("floor_number") or not f.get("ward_type") or not f.get("total_capacity"):
            flash("Floor, type and capacity are required.", "danger")
            return render_template("wards/form.html", user=current_user(), form=f)
        try:
            wid = ward_service.create_ward(int(f["floor_number"]), f["ward_type"], int(f["total_capacity"]))
            flash(f"Ward #{wid} created.", "success")
            return redirect(url_for("wards.detail", ward_id=wid))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Could not create ward: {e}", "danger")
        return render_template("wards/form.html", user=current_user(), form=f)
    return render_template("wards/form.html", user=current_user(), form={})


@wards_bp.route("/<int:ward_id>")
@ADMIN_ONLY
def detail(ward_id):
    ward = ward_service.get_ward(ward_id)
    if not ward:
        abort(404)
    return render_template(
        "wards/detail.html", user=current_user(), ward=ward,
        beds=ward_service.ward_beds(ward_id),
        equipment=ward_service.ward_equipment(ward_id),
        unallocated=ward_service.unallocated_beds(),
    )


@wards_bp.route("/<int:ward_id>/allocate", methods=["POST"])
@ADMIN_ONLY
def allocate(ward_id):
    bed_id = request.form.get("bed_id")
    if not bed_id:
        flash("Select a bed to allocate.", "danger")
        return redirect(url_for("wards.detail", ward_id=ward_id))
    try:
        ward_service.allocate_bed(ward_id, int(bed_id))
        flash("Bed allocated to ward.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("wards.detail", ward_id=ward_id))
