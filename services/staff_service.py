"""Staff / user management (Admin module)."""

from werkzeug.security import generate_password_hash

from config.db import fetch_all, fetch_one, fetch_scalar, execute, transaction
from config.validation import validate, ValidationError
import oracledb

# Role -> subclass table metadata used when provisioning a new staff account.
ROLE_NAMES = [
    "Admin Staff", "Emergency Doctor", "Ward Doctor", "Nurse",
    "Ambulance Dispatcher", "Service Dispatcher", "Maintenance Staff",
]


def list_users(search=None, role=None):
    sql = """
        SELECT u.UserID, u.FName, u.LName, u.Email, u.Phone, u.Is_Active,
               LISTAGG(r.Role_Name, ', ') WITHIN GROUP (ORDER BY r.Role_Name) AS roles
        FROM HEBAS_Users u
        LEFT JOIN User_Role_Assignment ura ON ura.UserID = u.UserID
        LEFT JOIN User_Roles r ON r.Role_ID = ura.Role_ID
    """
    params = {}
    where = []
    if search:
        where.append("(LOWER(u.FName || ' ' || u.LName) LIKE :s OR LOWER(u.Email) LIKE :s)")
        params["s"] = f"%{search.lower()}%"
    if role:
        where.append("""u.UserID IN (
            SELECT ura2.UserID FROM User_Role_Assignment ura2
            JOIN User_Roles r2 ON r2.Role_ID = ura2.Role_ID WHERE r2.Role_Name = :role)""")
        params["role"] = role
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += """ GROUP BY u.UserID, u.FName, u.LName, u.Email, u.Phone, u.Is_Active
               ORDER BY u.UserID"""
    return fetch_all(sql, params)


def get_role_id(role_name):
    return fetch_scalar("SELECT Role_ID FROM User_Roles WHERE Role_Name = :n", {"n": role_name})


# ----------------------------- Staff Management views -----------------------------
def list_doctors():
    return fetch_all(
        """SELECT d.Doctor_ID, u.FName || ' ' || u.LName AS name, u.Email,
                  d.Specialization, d.Department, d.Shift_Timing, d.License_No,
                  FN_GET_DOCTOR_WORKLOAD(d.Doctor_ID) AS workload
           FROM Doctor_Profiles d JOIN HEBAS_Users u ON u.UserID = d.Doctor_ID
           ORDER BY name"""
    )


def list_nurses():
    return fetch_all(
        """SELECT n.Nurse_ID, u.FName || ' ' || u.LName AS name, u.Email,
                  w.Ward_Name AS assigned_ward, n.Shift_Timing,
                  FN_GET_NURSE_WORKLOAD(n.Nurse_ID) AS workload
           FROM Nurses n JOIN HEBAS_Users u ON u.UserID = n.Nurse_ID
           LEFT JOIN Wards w ON w.Ward_ID = n.Assigned_Ward
           ORDER BY name"""
    )


def list_maintenance():
    return fetch_all(
        """SELECT m.Maintenance_ID, u.FName || ' ' || u.LName AS name, u.Email,
                  w.Ward_Name AS assigned_ward, m.Shift_Timing
           FROM Maintenance_Staff m JOIN HEBAS_Users u ON u.UserID = m.Maintenance_ID
           LEFT JOIN Wards w ON w.Ward_ID = m.Assigned_Ward
           ORDER BY name"""
    )


def email_exists(email):
    return fetch_scalar(
        "SELECT COUNT(*) FROM HEBAS_Users WHERE LOWER(Email) = LOWER(:e)", {"e": email}
    ) > 0


def toggle_active(user_id):
    return execute(
        "UPDATE HEBAS_Users SET Is_Active = 1 - Is_Active WHERE UserID = :id",
        {"id": user_id},
    )


def create_staff_user(data):
    """Create a HEBAS_Users row, the role's subclass row, and the role link.

    `data` keys: fname, lname, email, phone, password, role, and role-specific
    optional fields (specialization, license_no, department, shift_timing,
    assigned_ward, ambulance_type, service_name).
    Returns the new UserID. Raises ValueError on validation problems.
    """
    role = data["role"]
    if role not in ROLE_NAMES:
        raise ValueError("Unknown role.")

    errors = validate(data, {
        "fname": [("required",), ("alpha",)],
        "lname": [("required",), ("alpha",)],
        "email": [("required",), ("email",)],
        "phone": [("numeric",)],
        "password": [("required",), ("min_len", 6)],
    })
    if errors:
        raise ValidationError(errors)
    if email_exists(data["email"]):
        raise ValidationError(["Email already in use."])
    if role in ("Emergency Doctor", "Ward Doctor") and data.get("license_no"):
        dup = fetch_scalar("SELECT COUNT(*) FROM Doctor_Profiles WHERE License_No = :l",
                           {"l": data["license_no"]})
        if dup:
            raise ValidationError(["A doctor with this License No already exists."])

    role_id = get_role_id(role)
    pw_hash = generate_password_hash(data["password"])

    with transaction() as cur:
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active)
               VALUES (:f, :l, :e, :p, :ph, 1)
               RETURNING UserID INTO :new_id""",
            {"f": data["fname"], "l": data["lname"], "e": data["email"],
             "p": pw_hash, "ph": data.get("phone"), "new_id": new_id},
        )
        uid = int(new_id.getvalue()[0])

        if role in ("Emergency Doctor", "Ward Doctor"):
            cur.execute(
                """INSERT INTO Doctor_Profiles (Doctor_ID, Specialization, License_No, Department, Shift_Timing)
                   VALUES (:id, :spec, :lic, :dept, :shift)""",
                {"id": uid, "spec": data.get("specialization"),
                 "lic": data.get("license_no") or f"PMDC-{uid:04d}",
                 "dept": "Emergency" if role == "Emergency Doctor" else "Recovery",
                 "shift": data.get("shift_timing")},
            )
        elif role == "Nurse":
            cur.execute(
                "INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (:id, :shift, :ward)",
                {"id": uid, "shift": data.get("shift_timing"), "ward": data.get("assigned_ward") or None},
            )
        elif role == "Maintenance Staff":
            cur.execute(
                "INSERT INTO Maintenance_Staff (Maintenance_ID, Shift_Timing, Assigned_Ward) VALUES (:id, :shift, :ward)",
                {"id": uid, "shift": data.get("shift_timing"), "ward": data.get("assigned_ward") or None},
            )
        elif role == "Admin Staff":
            cur.execute(
                """INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing)
                   VALUES (:id, :dept, 'Mid', 'Level-2', :shift)""",
                {"id": uid, "dept": data.get("department") or "Administration",
                 "shift": data.get("shift_timing")},
            )
        elif role in ("Ambulance Dispatcher", "Service Dispatcher"):
            cur.execute(
                "INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (:id, :g, :t)",
                {"id": uid, "g": data.get("gender") or "M",
                 "t": data.get("ambulance_type") or "Basic Life Support"},
            )
            if role == "Service Dispatcher":
                cur.execute(
                    """INSERT INTO Service_Dispatcher (SD_ID, Service_Name, Shift_Timing, Assigned_Region)
                       VALUES (:id, :svc, :shift, :region)""",
                    {"id": uid, "svc": data.get("service_name") or "Rescue 1122",
                     "shift": data.get("shift_timing"), "region": data.get("assigned_region")},
                )

        cur.execute(
            "INSERT INTO User_Role_Assignment (UserID, Role_ID) VALUES (:u, :r)",
            {"u": uid, "r": role_id},
        )
    return uid
