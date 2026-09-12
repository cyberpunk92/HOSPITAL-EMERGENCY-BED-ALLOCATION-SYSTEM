"""Authentication routes: login / logout."""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from services.auth_service import authenticate
from config.auth import home_for, current_user
from config.db import fetch_all

auth_bp = Blueprint("auth", __name__)


def _login_roles():
    """Selectable roles for the 'Login As' dropdown (from the live role table)."""
    return [r["role_name"] for r in
            fetch_all("SELECT Role_Name FROM User_Roles ORDER BY Role_Name")]


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already signed in -> go to role home.
    if current_user():
        return redirect(url_for(home_for(session.get("primary_role"))))

    roles = _login_roles()

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        selected_role = (request.form.get("role") or "").strip()

        def _back(msg):
            flash(msg, "danger")
            return render_template("auth/login.html", email=email, roles=roles, selected_role=selected_role)

        if not email or not password:
            return _back("Email and password are required.")

        user = authenticate(email, password)
        if not user:
            return _back("Invalid email or password.")

        # If a specific role was chosen, the account must actually hold it.
        if selected_role and selected_role not in user["roles"]:
            return _back(f"Your account does not have the '{selected_role}' role. "
                         "Choose the correct role or 'Detect automatically'.")

        session.clear()
        session["user_id"] = user["user_id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["roles"] = user["roles"]
        # Honour the chosen role as primary when valid; otherwise auto-detect.
        session["primary_role"] = selected_role or user["primary_role"]

        flash(f"Welcome, {user['name']}.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        if not session["primary_role"]:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for(home_for(session["primary_role"])))

    return render_template("auth/login.html", email="", roles=roles, selected_role="")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
