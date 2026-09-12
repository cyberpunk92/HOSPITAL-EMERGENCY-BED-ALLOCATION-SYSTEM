"""Repository layer for Patient_Profile (data access only — no business logic)."""

import oracledb

from config.db import fetch_all, fetch_one, fetch_scalar, execute, transaction


def count(search=None):
    sql = "SELECT COUNT(*) FROM Patient_Profile p WHERE p.Is_Active = 1"
    params = {}
    if search:
        sql += " AND (LOWER(p.Full_Name) LIKE :s OR p.National_ID LIKE :s2)"
        params = {"s": f"%{search.lower()}%", "s2": f"%{search}%"}
    return fetch_scalar(sql, params) or 0


def page(search=None, offset=0, limit=10):
    sql = """
        SELECT p.Patient_ID, p.Full_Name, p.Gender, p.National_ID,
               p.Date_of_Birth, p.Insurance_ID, p.Emergency_Contact, p.User_ID,
               TRUNC(MONTHS_BETWEEN(SYSDATE, p.Date_of_Birth) / 12) AS age
        FROM Patient_Profile p
        WHERE p.Is_Active = 1
    """
    params = {}
    if search:
        sql += " AND (LOWER(p.Full_Name) LIKE :s OR p.National_ID LIKE :s2)"
        params.update({"s": f"%{search.lower()}%", "s2": f"%{search}%"})
    sql += " ORDER BY p.Patient_ID DESC OFFSET :off ROWS FETCH NEXT :lim ROWS ONLY"
    params.update({"off": offset, "lim": limit})
    return fetch_all(sql, params)


def get(patient_id):
    return fetch_one(
        """SELECT p.*, TRUNC(MONTHS_BETWEEN(SYSDATE, p.Date_of_Birth) / 12) AS age
           FROM Patient_Profile p WHERE p.Patient_ID = :id""",
        {"id": patient_id},
    )


def national_id_exists(national_id, exclude_id=None):
    sql = "SELECT COUNT(*) FROM Patient_Profile WHERE National_ID = :n"
    params = {"n": national_id}
    if exclude_id:
        sql += " AND Patient_ID <> :ex"
        params["ex"] = exclude_id
    return (fetch_scalar(sql, params) or 0) > 0


def admission_count(patient_id):
    return fetch_scalar(
        "SELECT COUNT(*) FROM Admissions WHERE Patient_ID = :id", {"id": patient_id}
    ) or 0


def admissions(patient_id):
    return fetch_all(
        """SELECT a.Admission_ID, a.Arrival_Timestamp, a.Triage_Priority,
                  a.Chief_Complaint, a.Primary_Diagnosis, a.Admission_Status,
                  a.Discharge_Timestamp
           FROM Admissions a WHERE a.Patient_ID = :id
           ORDER BY a.Arrival_Timestamp DESC""",
        {"id": patient_id},
    )


def options():
    return fetch_all(
        "SELECT Patient_ID, Full_Name, National_ID FROM Patient_Profile ORDER BY Full_Name"
    )


def insert(data):
    with transaction() as cur:
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO Patient_Profile
                 (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact)
               VALUES (:name, TO_DATE(:dob,'YYYY-MM-DD'), :gender, :nid, :ins, :ec)
               RETURNING Patient_ID INTO :new_id""",
            {"name": data["full_name"], "dob": data["dob"], "gender": data["gender"],
             "nid": data["national_id"], "ins": data.get("insurance_id"),
             "ec": data.get("emergency_contact"), "new_id": new_id},
        )
        return int(new_id.getvalue()[0])


def update(patient_id, data):
    return execute(
        """UPDATE Patient_Profile
           SET Full_Name = :name, Date_of_Birth = TO_DATE(:dob,'YYYY-MM-DD'),
               Gender = :gender, National_ID = :nid,
               Insurance_ID = :ins, Emergency_Contact = :ec
           WHERE Patient_ID = :id""",
        {"name": data["full_name"], "dob": data["dob"], "gender": data["gender"],
         "nid": data["national_id"], "ins": data.get("insurance_id"),
         "ec": data.get("emergency_contact"), "id": patient_id},
    )


def archive(patient_id):
    return execute(
        "UPDATE Patient_Profile SET Is_Active = 0 WHERE Patient_ID = :id", {"id": patient_id}
    )


def get_login(patient_id):
    return fetch_one(
        """SELECT u.UserID, u.Email, u.Is_Active
           FROM Patient_Profile p JOIN HEBAS_Users u ON u.UserID = p.User_ID
           WHERE p.Patient_ID = :id""",
        {"id": patient_id},
    )
