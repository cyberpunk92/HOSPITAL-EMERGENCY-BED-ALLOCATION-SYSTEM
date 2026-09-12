"""Central application configuration."""

import os


class Settings:
    # --- Flask ---
    SECRET_KEY = os.environ.get("HEBAS_SECRET_KEY", "hebas-dev-secret-change-me")
    DEBUG = os.environ.get("HEBAS_DEBUG", "1") == "1"

    # --- Sessions (server-side via Flask-Session, filesystem store) ---
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "sessions")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # --- Oracle ---
    DB_USER = os.environ.get("HEBAS_DB_USER", "HEBAS")
    DB_PASSWORD = os.environ.get("HEBAS_DB_PASSWORD", "hebas123")
    DB_DSN = os.environ.get("HEBAS_DB_DSN", "localhost:1521/ORCLPDB")
    DB_POOL_MIN = 1
    DB_POOL_MAX = 8
    DB_POOL_INCREMENT = 1

    # --- App ---
    APP_NAME = "HEBAS"
    APP_FULL_NAME = "Hospital Emergency Bed Allocation System"
    HOSPITAL_NAME = "CMH Rawalpindi"


settings = Settings()
