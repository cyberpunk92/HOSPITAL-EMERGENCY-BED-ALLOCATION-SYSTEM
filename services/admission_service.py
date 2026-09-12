"""Admission & bed-allocation workflow (Phase 8).

Relies on DB triggers:
  * TRG_Validate_Bed_Assignment - blocks bed assignment without a diagnosis
    or when the bed is not AVAILABLE (ORA-20001 / ORA-20002).
  * TRG_Auto_Occupy_Bed         - flips bed to OCCUPIED on assignment.
  * TRG_Auto_Discharge_Workflow - on discharge: closes assignment, sets bed
    PENDING_CLEANING, dispatches a sanitization log.
  * TRG_Discharge_Notification  - notifies admin on discharge.
"""

import oracledb

from config.db import fetch_all, fetch_one, execute, transaction, get_connection


def list_admissions(status=None, doctor_id=None):
    sql = """
        SELECT a.Admission_ID, p.Full_Name, p.Patient_ID, a.Arrival_Timestamp,
               a.Triage_Priority, a.Chief_Complaint, a.Primary_Diagnosis,
               a.Admission_Status, a.Assigned_Doctor,
               du.FName || ' ' || du.LName AS doctor_name,
               ba.Bed_ID, b.Bed_Number
        FROM Admissions a
        JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
        LEFT JOIN HEBAS_Users du ON du.UserID = a.Assigned_Doctor
        LEFT JOIN Bed_Assignments ba ON ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT'
        LEFT JOIN Beds b ON b.Bed_ID = ba.Bed_ID
    """
    params, where = {}, []
    if status:
        where.append("a.Admission_Status = :st")
        params["st"] = status
    if doctor_id:
        where.append("a.Assigned_Doctor = :doc")
        params["doc"] = doctor_id
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY a.Triage_Priority DESC, a.Arrival_Timestamp ASC"
    return fetch_all(sql, params)


def triage_list():
    return fetch_all(
        """
        SELECT Admission_ID, Full_Name, Gender, Arrival_Timestamp,
               Triage_Priority, Chief_Complaint
        FROM View_Active_Triage_List
        """
    )


def get_admission(admission_id):
    return fetch_one(
        """
        SELECT a.*, p.Full_Name, p.National_ID, p.Gender, p.Date_of_Birth,
               TRUNC(MONTHS_BETWEEN(SYSDATE, p.Date_of_Birth)/12) AS age,
               du.FName || ' ' || du.LName AS doctor_name,
               ba.Bed_ID, b.Bed_Number, b.Current_Status AS bed_status
        FROM Admissions a
        JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
        LEFT JOIN HEBAS_Users du ON du.UserID = a.Assigned_Doctor
        LEFT JOIN Bed_Assignments ba ON ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT'
        LEFT JOIN Beds b ON b.Bed_ID = ba.Bed_ID
        WHERE a.Admission_ID = :id
        """,
        {"id": admission_id},
    )


def doctor_profile(user_id):
    return fetch_one(
        """SELECT d.Doctor_ID, d.Specialization, d.Department, d.Shift_Timing,
                  u.FName || ' ' || u.LName AS name
           FROM Doctor_Profiles d JOIN HEBAS_Users u ON u.UserID = d.Doctor_ID
           WHERE d.Doctor_ID = :id""",
        {"id": user_id},
    )


def doctor_options():
    return fetch_all(
        """
        SELECT d.Doctor_ID, u.FName || ' ' || u.LName AS name,
               d.Specialization, d.Department
        FROM Doctor_Profiles d
        JOIN HEBAS_Users u ON u.UserID = d.Doctor_ID
        ORDER BY name
        """
    )


def has_active_admission(patient_id):
    return (fetch_one(
        "SELECT 1 AS x FROM Admissions WHERE Patient_ID = :p AND Admission_Status = 'ACTIVE' "
        "FETCH FIRST 1 ROWS ONLY", {"p": patient_id}) is not None)


def create_admission(patient_id, triage_priority, chief_complaint, auto_assign=True):
    """Register an admission. Optionally auto-assigns a doctor by complaint.
    Rejects a second active admission for the same patient (also enforced by
    the UQ_ACTIVE_ADMISSION unique index)."""
    if has_active_admission(patient_id):
        raise ValueError("This patient already has an active admission.")
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            new_id = cur.var(oracledb.NUMBER)
            cur.execute(
                """INSERT INTO Admissions (Patient_ID, Triage_Priority, Chief_Complaint, Admission_Status)
                   VALUES (:pid, :tp, :cc, 'ACTIVE')
                   RETURNING Admission_ID INTO :new_id""",
                {"pid": patient_id, "tp": triage_priority, "cc": chief_complaint, "new_id": new_id},
            )
            admission_id = int(new_id.getvalue()[0])
            if auto_assign:
                # Best-effort: maps Chief_Complaint -> doctor via Complaint_Mapping.
                cur.callproc("Auto_Assign_Doctor", [admission_id])
            conn.commit()
            return admission_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def _callproc(name, args):
    """Run a stored procedure in its own committed transaction."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.callproc(name, args)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def assign_doctor(admission_id, doctor_id):
    # PR_ASSIGN_DOCTOR updates the admission; TRG_DOCTOR_HISTORY logs the change
    # and TRG_NOTIFY_DOCTOR notifies the doctor.
    _callproc("PR_ASSIGN_DOCTOR", [admission_id, doctor_id])


# Keyword fallbacks so a free-text complaint still maps to the right ward when
# it is not one of the canonical Complaint_Mapping names. Each tuple is
# (keywords, fragment-of-Ward_Name). This is what makes Neurology (and every
# other emergency ward) assign a bed immediately instead of stalling.
WARD_KEYWORDS = [
    (("chest", "cardiac", "heart", "cardio", "angina"), "Cardiac"),
    (("accident", "trauma", "injury", "fracture", "crash", "fall", "wound", "bleed"), "Trauma"),
    (("burn", "scald"), "Burn"),
    (("child", "pediatric", "paediatric", "infant", "baby", "kid"), "Pediatric"),
    (("neuro", "stroke", "seizure", "brain", "epilep", "fit", "convuls"), "Neurology"),
]


def _resolve_ward(cur, complaint):
    """Resolve the destination ward for a complaint: exact Complaint_Mapping
    first, then a tolerant keyword match against active ward names."""
    if not complaint:
        return None
    cur.execute("SELECT Recommended_Ward_ID FROM Complaint_Mapping WHERE UPPER(Complaint_Name) = UPPER(:c)",
                {"c": complaint})
    r = cur.fetchone()
    if r:
        return r[0]
    cl = complaint.lower()
    for keywords, fragment in WARD_KEYWORDS:
        if any(k in cl for k in keywords):
            cur.execute(
                """SELECT w.Ward_ID FROM Wards w
                   WHERE UPPER(w.Ward_Name) LIKE UPPER(:f)
                     AND EXISTS (SELECT 1 FROM Ward_Bed_Allocation wba
                                 WHERE wba.Ward_ID = w.Ward_ID AND wba.End_Time IS NULL)
                   ORDER BY w.Ward_ID FETCH FIRST 1 ROWS ONLY""",
                {"f": f"%{fragment}%"})
            rr = cur.fetchone()
            if rr:
                return rr[0]
    return None


def admit(admission_id):
    """Admit the patient and AUTO-ASSIGN a bed in the recommended ward.

    Returns {"status": ..., "bed": id|None, "ward": ward_name|None} where status
    is one of:
      * "assigned"      - a bed was assigned (bed -> OCCUPIED via trigger)
      * "already"       - patient already had a current bed
      * "no_bed"        - no free bed in an EMERGENCY ward (clean message only,
                          NO maintenance request raised)
      * "no_bed_medical"- no free bed in the MEDICAL ward (maintenance asked to
                          add an extra bed - the only ward allowed to do this)
      * "no_ward"       - complaint could not be matched to any ward
    A patient never gets a second bed (one bed per patient).
    """
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT Primary_Diagnosis, Chief_Complaint FROM Admissions WHERE Admission_ID = :a",
                        {"a": admission_id})
            row = cur.fetchone()
            if not row or not row[0]:
                raise ValueError("Record a diagnosis before admitting the patient.")
            complaint = row[1]

            cur.execute("UPDATE Admissions SET Admit_Status = 'ADMITTED' WHERE Admission_ID = :a",
                        {"a": admission_id})

            # Already has a current bed? (one bed per patient)
            cur.execute("SELECT COUNT(*) FROM Bed_Assignments WHERE Admission_ID = :a AND Assignment_Status = 'CURRENT'",
                        {"a": admission_id})
            if cur.fetchone()[0] > 0:
                conn.commit()
                return {"status": "already", "bed": None, "ward": None}

            ward = _resolve_ward(cur, complaint)
            if not ward:
                conn.commit()
                return {"status": "no_ward", "bed": None, "ward": None}

            cur.execute("SELECT Ward_Name FROM Wards WHERE Ward_ID = :w", {"w": ward})
            wn = cur.fetchone()
            ward_name = wn[0] if wn else None

            cur.execute(
                """SELECT b.Bed_ID FROM Beds b
                   JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
                   WHERE wba.Ward_ID = :w AND b.Current_Status = 'AVAILABLE'
                   FETCH FIRST 1 ROWS ONLY""", {"w": ward})
            br = cur.fetchone()
            bed = br[0] if br else None

            if not bed:
                # Only the Medical Ward may auto-request an extra bed from
                # maintenance. Emergency wards (incl. Neurology) just report a
                # clean "no bed available" with no maintenance involvement.
                cur.execute("SELECT COUNT(*) FROM Medical_Ward WHERE Ward_ID = :w", {"w": ward})
                is_medical = cur.fetchone()[0] > 0
                if is_medical:
                    cur.execute("SELECT MIN(Maintenance_ID) FROM Maintenance_Staff")
                    m = cur.fetchone()[0]
                    if m:
                        cur.callproc("Create_Notification",
                                     [m, f"No available bed for admission #{admission_id} - add extra bed."])
                    conn.commit()
                    return {"status": "no_bed_medical", "bed": None, "ward": ward_name}
                conn.commit()
                return {"status": "no_bed", "bed": None, "ward": ward_name}

            # triggers set bed OCCUPIED + ward capacity
            cur.execute("INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status) VALUES (:a, :b, 'CURRENT')",
                        {"a": admission_id, "b": bed})
            conn.commit()
            return {"status": "assigned", "bed": bed, "ward": ward_name}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def patients_awaiting_bed():
    """Admitted, active patients who still have no current bed (waiting list).
    Lets an admin place them into a free bed from Bed Management."""
    return fetch_all(
        """SELECT a.Admission_ID, p.Full_Name, a.Chief_Complaint
           FROM Admissions a
           JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
           WHERE a.Admission_Status = 'ACTIVE'
             AND a.Primary_Diagnosis IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM Bed_Assignments ba
                             WHERE ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT')
           ORDER BY a.Triage_Priority DESC, a.Arrival_Timestamp ASC"""
    )


def set_diagnosis(admission_id, diagnosis):
    return execute(
        """UPDATE Admissions
           SET Primary_Diagnosis = :dx, Diagnosis_Timestamp = CURRENT_TIMESTAMP
           WHERE Admission_ID = :id""",
        {"dx": diagnosis, "id": admission_id},
    )


def assign_bed(admission_id, bed_id):
    """Insert a bed assignment. Triggers enforce diagnosis + availability.
    Raises ValueError (carrying the trigger's message) on rule violations."""
    try:
        return execute(
            """INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status)
               VALUES (:adm, :bed, 'CURRENT')""",
            {"adm": admission_id, "bed": bed_id},
        )
    except oracledb.DatabaseError as exc:
        (err,) = exc.args
        if getattr(err, "code", None) in (20001, 20002):
            raise ValueError(err.message.split("\n")[0].replace("ORA-20001:", "").replace("ORA-20002:", "").strip())
        raise


def discharge(admission_id):
    """Discharge a patient. Triggers free the bed and dispatch sanitization."""
    return execute(
        """UPDATE Admissions
           SET Discharge_Timestamp = CURRENT_TIMESTAMP, Admission_Status = 'DISCHARGED'
           WHERE Admission_ID = :id AND Admission_Status = 'ACTIVE'""",
        {"id": admission_id},
    )


def record_measurement(admission_id, bp_value, sugar_value):
    return execute(
        """INSERT INTO Medical_Measurements (Admission_ID, BP_Value, Sugar_Value)
           VALUES (:id, :bp, :sugar)""",
        {"id": admission_id, "bp": bp_value, "sugar": sugar_value},
    )


def measurements(admission_id):
    return fetch_all(
        """SELECT BP_Value, Sugar_Value, Measurement_Date
           FROM Medical_Measurements WHERE Admission_ID = :id
           ORDER BY Measurement_Date DESC""",
        {"id": admission_id},
    )


# ----------------------------- Transfers / Nurse / Priority -----------------------------
def transfer(admission_id, to_ward):
    """Transfer a patient to another ward via PKG_HEBAS.Transfer_Patient."""
    try:
        _callproc("PKG_HEBAS.Transfer_Patient", [admission_id, to_ward])
    except oracledb.DatabaseError as exc:
        (err,) = exc.args
        if getattr(err, "code", None) in (20001, 20002):
            raise ValueError(err.message.split("\n")[0].split(":", 1)[-1].strip())
        raise


def assign_nurse(nurse_id, admission_id):
    """Assign a nurse to an admission via PR_ASSIGN_NURSE (notifies the nurse)."""
    _callproc("PR_ASSIGN_NURSE", [nurse_id, admission_id])


def nurse_options(ward_id=None):
    sql = """SELECT DISTINCT n.Nurse_ID, u.FName || ' ' || u.LName AS name, n.Assigned_Ward
             FROM Nurses n JOIN HEBAS_Users u ON u.UserID = n.Nurse_ID"""
    params = {}
    if ward_id:
        sql += " WHERE n.Assigned_Ward = :w"
        params["w"] = ward_id
    sql += " ORDER BY name"
    return fetch_all(sql, params)


def nurse_history(admission_id):
    """Every nurse assignment for this admission (newest first) for the
    optional 'View Previous Nurses' panel — each row is one assignment."""
    return fetch_all(
        """SELECT u.FName || ' ' || u.LName AS nurse_name, na.Assigned_Date
           FROM Nurse_Assignments na
           JOIN HEBAS_Users u ON u.UserID = na.Nurse_ID
           WHERE na.Admission_ID = :id
           ORDER BY na.Assigned_Date DESC""",
        {"id": admission_id},
    )


def set_priority(admission_id, doctor_id, checkup, level):
    return execute(
        """INSERT INTO Patient_Priority (Admission_ID, Doctor_ID, Initial_Checkup, Priority_Level, Priority_Status)
           VALUES (:adm, :doc, :chk, :lvl, 'ACTIVE')""",
        {"adm": admission_id, "doc": doctor_id, "chk": checkup, "lvl": level},
    )


def priorities(admission_id):
    return fetch_all(
        """SELECT pp.Priority_ID, pp.Initial_Checkup, pp.Priority_Level, pp.Priority_Status,
                  pp.Created_At, u.FName || ' ' || u.LName AS doctor_name
           FROM Patient_Priority pp
           LEFT JOIN HEBAS_Users u ON u.UserID = pp.Doctor_ID
           WHERE pp.Admission_ID = :id ORDER BY pp.Created_At DESC""",
        {"id": admission_id},
    )


NURSE_TASK_TYPES = ("Deploy Glucose Strip", "Check BP", "Check Sugar", "Give Medicine")


def assigned_nurses(admission_id):
    """Distinct nurses currently assigned (each nurse shown only once)."""
    return fetch_all(
        """SELECT MIN(u.FName || ' ' || u.LName) AS nurse_name, na.Nurse_ID,
                  LISTAGG(t.Task_Type, ', ') WITHIN GROUP (ORDER BY t.Task_Type) AS tasks
           FROM Nurse_Assignments na
           JOIN HEBAS_Users u ON u.UserID = na.Nurse_ID
           LEFT JOIN Nurse_Tasks t ON t.Admission_ID = na.Admission_ID AND t.Nurse_ID = na.Nurse_ID AND t.Task_Status = 'PENDING'
           WHERE na.Admission_ID = :id
           GROUP BY na.Nurse_ID""",
        {"id": admission_id},
    )


def assign_nurse_with_tasks(nurse_id, admission_id, tasks):
    """Assign a nurse (once) + create the selected task types (no duplicate
    pending task of the same type for the same patient+nurse)."""
    valid = [t for t in (tasks or []) if t in NURSE_TASK_TYPES]
    with transaction() as cur:
        cur.execute("SELECT COUNT(*) FROM Nurse_Assignments WHERE Nurse_ID = :n AND Admission_ID = :a",
                    {"n": nurse_id, "a": admission_id})
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO Nurse_Assignments (Nurse_ID, Admission_ID) VALUES (:n, :a)",
                        {"n": nurse_id, "a": admission_id})
        for t in valid:
            cur.execute("""SELECT COUNT(*) FROM Nurse_Tasks
                           WHERE Admission_ID = :a AND Nurse_ID = :n AND Task_Type = :t AND Task_Status = 'PENDING'""",
                        {"a": admission_id, "n": nurse_id, "t": t})
            if cur.fetchone()[0] == 0:
                cur.execute("""INSERT INTO Nurse_Tasks (Admission_ID, Nurse_ID, Task_Type, Task_Status)
                               VALUES (:a, :n, :t, 'PENDING')""", {"a": admission_id, "n": nurse_id, "t": t})


def nurse_results(admission_id):
    """BP / sugar (Patient_Vitals) + glucose strip status taken by the nurse,
    for the doctor's read-only result view + patient portal."""
    vitals = fetch_all(
        """SELECT Systolic_BP, Diastolic_BP, Glucose_Level, Recorded_At
           FROM Patient_Vitals WHERE Admission_ID = :a
           ORDER BY Recorded_At DESC FETCH FIRST 6 ROWS ONLY""", {"a": admission_id})
    glucose = fetch_one(
        """SELECT Result_Status, End_Time FROM Glucose_Strip_Results
           WHERE Admission_ID = :a ORDER BY NVL(End_Time, Start_Time) DESC FETCH FIRST 1 ROWS ONLY""",
        {"a": admission_id})
    return {"vitals": vitals, "glucose": glucose}
