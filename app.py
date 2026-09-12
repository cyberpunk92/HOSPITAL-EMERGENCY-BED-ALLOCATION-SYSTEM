"""HEBAS - Hospital Emergency Bed Allocation System. Flask application factory."""

import os

from flask import Flask, render_template
from flask_session import Session

from config.settings import settings
from config.db import init_pool, close_pool
from config.auth import current_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(settings)

    # Ensure runtime directories exist.
    os.makedirs(settings.SESSION_FILE_DIR, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "reports"), exist_ok=True)

    Session(app)
    init_pool()

    # --- Blueprints ---
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.admin_routes import admin_bp
    from routes.patients_routes import patients_bp
    from routes.beds_routes import beds_bp
    from routes.wards_routes import wards_bp
    from routes.admissions_routes import admissions_bp
    from routes.doctor_routes import doctor_bp
    from routes.nurse_routes import nurse_bp
    from routes.dispatcher_routes import dispatcher_bp
    from routes.maintenance_routes import maintenance_bp
    from routes.sanitization_routes import sanitization_bp
    from routes.reports_routes import reports_bp
    from routes.notifications_routes import notifications_bp
    from routes.patient_routes import patient_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(beds_bp)
    app.register_blueprint(wards_bp)
    app.register_blueprint(admissions_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(nurse_bp)
    app.register_blueprint(dispatcher_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(sanitization_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(patient_bp)

    # --- Template globals ---
    @app.context_processor
    def inject_globals():
        from services.notification_service import unread_count
        user = current_user()
        unread = unread_count(user["user_id"]) if user else 0
        return {
            "app_name": settings.APP_NAME,
            "app_full_name": settings.APP_FULL_NAME,
            "hospital_name": settings.HOSPITAL_NAME,
            "current_user": user,
            "unread_notifications": unread,
        }

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    try:
        app.run(host="127.0.0.1", port=5000, debug=settings.DEBUG)
    finally:
        close_pool()
