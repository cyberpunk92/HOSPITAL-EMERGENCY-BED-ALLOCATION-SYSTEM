"""Authentication & role-based access control helpers."""

from functools import wraps

from flask import session, redirect, url_for, flash, request, abort

# Where each role lands after login (blueprint.endpoint).
ROLE_HOME = {
    "Admin Staff": "admin.dashboard",
    "Emergency Doctor": "doctor.dashboard",
    "Ward Doctor": "doctor.dashboard",
    "Nurse": "nurse.dashboard",
    "Ambulance Dispatcher": "dispatcher.dashboard",
    "Service Dispatcher": "dispatcher.dashboard",
    "Maintenance Staff": "maintenance.dashboard",
    "Sanitization Staff": "sanitization.dashboard",
    "Patient": "patient.dashboard",
}


def current_user():
    """Return the logged-in user dict from the session, or None."""
    if "user_id" not in session:
        return None
    return {
        "user_id": session.get("user_id"),
        "name": session.get("name"),
        "email": session.get("email"),
        "roles": session.get("roles", []),
        "primary_role": session.get("primary_role"),
    }


def has_role(*roles):
    user_roles = set(session.get("roles", []))
    return bool(user_roles.intersection(roles))


def home_for(role):
    return ROLE_HOME.get(role, "dashboard.index")


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def role_required(*roles):
    """Restrict a view to users holding at least one of the given roles."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            if not has_role(*roles):
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator
