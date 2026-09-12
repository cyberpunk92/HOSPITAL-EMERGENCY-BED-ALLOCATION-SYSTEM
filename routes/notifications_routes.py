"""Notifications module — only Maintenance + Sanitization staff."""

from flask import Blueprint, render_template, redirect, url_for, flash

from config.auth import role_required, current_user
from services import notification_service

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")
NOTIFY_ROLES = role_required("Maintenance Staff", "Sanitization Staff")


@notifications_bp.route("/")
@NOTIFY_ROLES
def index():
    me = current_user()
    items = notification_service.list_for_user(me["user_id"])
    # Decide where each notification routes to (task-style).
    for n in items:
        msg = (n.get("message") or "").lower()
        if "saniti" in msg or "cleaning" in msg:
            n["target"] = url_for("sanitization.dashboard")
            n["icon"] = "bi-droplet-half"
        else:
            n["target"] = url_for("maintenance.dashboard")
            n["icon"] = "bi-tools"
    return render_template("notifications/index.html", user=me, items=items)


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@NOTIFY_ROLES
def read(notification_id):
    notification_service.mark_read(notification_id, current_user()["user_id"])
    return redirect(url_for("notifications.index"))


@notifications_bp.route("/read-all", methods=["POST"])
@NOTIFY_ROLES
def read_all():
    notification_service.mark_all_read(current_user()["user_id"])
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications.index"))
