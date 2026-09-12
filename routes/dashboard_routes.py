"""Generic dashboard entry point — routes a user to their role home."""

from flask import Blueprint, redirect, url_for, session, render_template

from config.auth import login_required, current_user, home_for

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    role = session.get("primary_role")
    if role:
        return redirect(url_for(home_for(role)))
    # User with no assigned role: show a neutral landing page.
    return render_template("dashboard/no_role.html", user=current_user())
