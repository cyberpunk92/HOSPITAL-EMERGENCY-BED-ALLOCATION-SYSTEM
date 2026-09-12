"""Patient management (Admin module). Business logic + validation;
data access delegated to repositories.patient_repository."""

import math
import re

import oracledb

from config.db import fetch_all, fetch_one, fetch_scalar, transaction
from config.validation import validate, ValidationError
from repositories import patient_repository as repo

_GENDERS = ("M", "F", "OTHER")


def _normalize(data):
    """Strip non-digits from CNIC / emergency contact so 'numeric only' holds
    for dashed input (e.g. 37405-1234567-1 -> 3740512345671)."""
    if data.get("national_id"):
        data["national_id"] = re.sub(r"\D", "", data["national_id"])
    if data.get("emergency_contact"):
        data["emergency_contact"] = re.sub(r"\D", "", data["emergency_contact"]) or None
    return data

# Validation rules shared by create + update.
_PATIENT_RULES = {
    "full_name": [("required",), ("alpha",), ("min_len", 2)],
    "national_id": [("required",), ("cnic",)],            # exactly 13 digits
    "dob": [("required",), ("date_not_future",)],
    "emergency_contact": [("numeric",), ("max_len", 11)],
}


def _validate_patient(data, patient_id=None):
    errors = validate(data, _PATIENT_RULES)
    if (data.get("gender") or "") not in _GENDERS:
        errors.append("Gender is required.")
    if data.get("national_id") and repo.national_id_exists(data["national_id"], exclude_id=patient_id):
        errors.append("A patient with this CNIC already exists.")
    if errors:
        raise ValidationError(errors)


def paginate(search=None, page=1, per_page=10):
    page = max(1, page)
    total = repo.count(search)
    items = repo.page(search, offset=(page - 1) * per_page, limit=per_page)
    return {
        "rows": items, "page": page, "per_page": per_page, "total": total,
        "total_pages": max(1, math.ceil(total / per_page)),
    }


def list_patients(search=None):
    """Unpaginated list (kept for callers that need everything)."""
    return repo.page(search, offset=0, limit=10000)


def get_patient(patient_id):
    return repo.get(patient_id)


def patient_admissions(patient_id):
    return repo.admissions(patient_id)


def national_id_exists(national_id, exclude_id=None):
    return repo.national_id_exists(national_id, exclude_id)


def create_patient(data):
    """Validate + insert a patient. Returns new Patient_ID.
    Raises ValidationError with field messages on bad input."""
    _normalize(data)
    _validate_patient(data)
    return repo.insert(data)


def update_patient(patient_id, data):
    """Validate + update an existing patient."""
    _normalize(data)
    _validate_patient(data, patient_id=patient_id)
    return repo.update(patient_id, data)


def archive_patient(patient_id):
    """Archive (deactivate) a patient instead of permanent delete.
    Blocked while the patient has an active admission."""
    active = fetch_scalar(
        "SELECT COUNT(*) FROM Admissions WHERE Patient_ID = :id AND Admission_Status = 'ACTIVE'",
        {"id": patient_id},
    )
    if active:
        raise ValueError("Cannot archive: this patient has an active admission.")
    return repo.archive(patient_id)


def patient_options():
    return repo.options()


# ---------------------------------------------------------------------------
# Patient self-service portal
# ---------------------------------------------------------------------------
def get_login(patient_id):
    """Return the linked login account for a patient, or None."""
    return repo.get_login(patient_id)


def get_patient_by_user(user_id):
    return fetch_one(
        """SELECT p.*, TRUNC(MONTHS_BETWEEN(SYSDATE, p.Date_of_Birth)/12) AS age
           FROM Patient_Profile p WHERE p.User_ID = :p_user""",
        {"p_user": user_id},
    )


def create_patient_login(patient_id, email, password):
    """Provision a portal login for an existing patient: create the user,
    link Patient_Profile.User_ID and grant the 'Patient' role."""
    from werkzeug.security import generate_password_hash

    if get_login(patient_id):
        raise ValueError("This patient already has a portal login.")
    if fetch_scalar("SELECT COUNT(*) FROM HEBAS_Users WHERE LOWER(Email)=LOWER(:e)", {"e": email}):
        raise ValueError("That email is already in use.")

    patient = get_patient(patient_id)
    if not patient:
        raise ValueError("Patient not found.")
    first, _, last = patient["full_name"].partition(" ")
    pw_hash = generate_password_hash(password)

    with transaction() as cur:
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active)
               VALUES (:f, :l, :e, :p, :ph, 1) RETURNING UserID INTO :new_id""",
            {"f": first or patient["full_name"], "l": last or "-", "e": email,
             "p": pw_hash, "ph": patient.get("emergency_contact"), "new_id": new_id},
        )
        uid = int(new_id.getvalue()[0])
        cur.execute("UPDATE Patient_Profile SET User_ID = :u WHERE Patient_ID = :id",
                    {"u": uid, "id": patient_id})
        cur.execute(
            """INSERT INTO User_Role_Assignment (UserID, Role_ID)
               SELECT :u, Role_ID FROM User_Roles WHERE Role_Name = 'Patient'""",
            {"u": uid},
        )
    return uid


def current_admission(patient_id):
    """The patient's active admission with bed / ward / doctor, if any."""
    return fetch_one(
        """SELECT a.Admission_ID, a.Triage_Priority, a.Chief_Complaint,
                  a.Primary_Diagnosis, a.Arrival_Timestamp, a.Admission_Status,
                  du.FName || ' ' || du.LName AS doctor_name,
                  b.Bed_Number, w.Ward_ID, w.Ward_Type
           FROM Admissions a
           LEFT JOIN HEBAS_Users du ON du.UserID = a.Assigned_Doctor
           LEFT JOIN Bed_Assignments ba ON ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT'
           LEFT JOIN Beds b ON b.Bed_ID = ba.Bed_ID
           LEFT JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
           LEFT JOIN Wards w ON w.Ward_ID = wba.Ward_ID
           WHERE a.Patient_ID = :id AND a.Admission_Status = 'ACTIVE'
           ORDER BY a.Arrival_Timestamp DESC FETCH FIRST 1 ROWS ONLY""",
        {"id": patient_id},
    )


def portal_admission(patient_id):
    """Latest admission (any status) with doctor / bed / ward / discharge info."""
    return fetch_one(
        """SELECT a.Admission_ID, a.Triage_Priority, a.Chief_Complaint, a.Primary_Diagnosis,
                  a.Arrival_Timestamp, a.Admission_Status, a.Discharge_Timestamp,
                  du.FName || ' ' || du.LName AS doctor_name, a.Assigned_Doctor,
                  b.Bed_Number, w.Ward_ID, w.Ward_Type, w.Ward_Name,
                  (SELECT COUNT(*) FROM Bed_Assignments x WHERE x.Admission_ID = a.Admission_ID) AS had_bed
           FROM Admissions a
           LEFT JOIN HEBAS_Users du ON du.UserID = a.Assigned_Doctor
           LEFT JOIN Bed_Assignments ba ON ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT'
           LEFT JOIN Beds b ON b.Bed_ID = ba.Bed_ID
           LEFT JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
           LEFT JOIN Wards w ON w.Ward_ID = wba.Ward_ID
           WHERE a.Patient_ID = :id
           ORDER BY a.Arrival_Timestamp DESC FETCH FIRST 1 ROWS ONLY""",
        {"id": patient_id},
    )


def assigned_nurse(admission_id):
    if not admission_id:
        return None
    return fetch_scalar(
        """SELECT u.FName || ' ' || u.LName FROM Nurse_Assignments na
           JOIN HEBAS_Users u ON u.UserID = na.Nurse_ID
           WHERE na.Admission_ID = :a ORDER BY na.Assigned_Date DESC FETCH FIRST 1 ROWS ONLY""",
        {"a": admission_id},
    )


def latest_glucose(admission_id):
    if not admission_id:
        return None
    return fetch_one(
        """SELECT Result_Status, End_Time FROM Glucose_Strip_Results
           WHERE Admission_ID = :a ORDER BY NVL(End_Time, Start_Time) DESC FETCH FIRST 1 ROWS ONLY""",
        {"a": admission_id},
    )


def latest_vitals(patient_id, limit=5):
    return fetch_all(
        """SELECT v.Systolic_BP, v.Diastolic_BP, v.Glucose_Level, v.Temperature, v.Recorded_At
           FROM Patient_Vitals v
           JOIN Admissions a ON a.Admission_ID = v.Admission_ID
           WHERE a.Patient_ID = :id
           ORDER BY v.Recorded_At DESC FETCH FIRST :lim ROWS ONLY""",
        {"id": patient_id, "lim": limit},
    )
