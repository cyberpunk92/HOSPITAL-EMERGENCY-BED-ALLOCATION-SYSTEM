"""Nurse module: assigned patients, BP/Sugar/Glucose/Medicine tasks, equipment."""

from config.db import fetch_all, fetch_one, fetch_scalar, execute, transaction


def assigned_patients(nurse_id):
    """Patients explicitly assigned to this nurse (Nurse_Assignments)."""
    return fetch_all(
        """SELECT DISTINCT a.Admission_ID, p.Full_Name, p.Patient_ID,
                  a.Chief_Complaint, a.Primary_Diagnosis,
                  b.Bed_Number, w.Ward_ID, w.Ward_Type, w.Ward_Name,
                  du.FName || ' ' || du.LName AS doctor_name
           FROM Nurse_Assignments na
           JOIN Admissions a ON a.Admission_ID = na.Admission_ID AND a.Admission_Status = 'ACTIVE'
           JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
           LEFT JOIN Bed_Assignments ba ON ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT'
           LEFT JOIN Beds b ON b.Bed_ID = ba.Bed_ID
           LEFT JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
           LEFT JOIN Wards w ON w.Ward_ID = wba.Ward_ID
           LEFT JOIN HEBAS_Users du ON du.UserID = a.Assigned_Doctor
           WHERE na.Nurse_ID = :nid
           ORDER BY a.Admission_ID DESC""",
        {"nid": nurse_id},
    )


def equipment_summary(ward_id):
    """Consumable / device availability IN THE NURSE'S WARD."""
    if not ward_id:
        return {}
    rows = fetch_all(
        """SELECT e.Equipment_Name AS nm, we.Quantity AS qty
           FROM Ward_Equipment we JOIN Equipment e ON e.Equipment_ID = we.Equipment_ID
           WHERE we.Ward_ID = :w
             AND e.Equipment_Name IN ('Glucose Strips', 'BP Machine', 'Sugar Machine')""",
        {"w": ward_id},
    )
    return {r["nm"]: r["qty"] for r in rows}


def pending_tasks_map(nurse_id):
    """{admission_id: [task_type, ...]} of this nurse's PENDING tasks."""
    rows = fetch_all(
        "SELECT Admission_ID, Task_Type FROM Nurse_Tasks WHERE Nurse_ID = :n AND Task_Status = 'PENDING'",
        {"n": nurse_id})
    m = {}
    for r in rows:
        m.setdefault(r["admission_id"], []).append(r["task_type"])
    return m


def complete_nurse_task(admission_id, nurse_id, task_type):
    execute(
        """UPDATE Nurse_Tasks SET Task_Status = 'COMPLETED'
           WHERE Admission_ID = :a AND Nurse_ID = :n AND Task_Type = :t AND Task_Status = 'PENDING'""",
        {"a": admission_id, "n": nurse_id, "t": task_type})


def record_bp(admission_id, nurse_id, systolic, diastolic):
    if systolic is None or diastolic is None:
        raise ValueError("Both systolic and diastolic are required.")
    if systolic <= diastolic:
        raise ValueError("Systolic must be greater than diastolic.")
    execute("""INSERT INTO Patient_Vitals (Admission_ID, Nurse_ID, Systolic_BP, Diastolic_BP)
               VALUES (:a, :n, :s, :d)""",
            {"a": admission_id, "n": nurse_id, "s": systolic, "d": diastolic})
    complete_nurse_task(admission_id, nurse_id, "Check BP")


def record_sugar(admission_id, nurse_id, sugar):
    if sugar is None or sugar <= 0:
        raise ValueError("Sugar must be a positive number.")
    execute("""INSERT INTO Patient_Vitals (Admission_ID, Nurse_ID, Glucose_Level)
               VALUES (:a, :n, :g)""",
            {"a": admission_id, "n": nurse_id, "g": sugar})
    complete_nurse_task(admission_id, nurse_id, "Check Sugar")


def record_glucose_strip(admission_id, nurse_id, ward_id):
    """Use one glucose strip: record result, decrement the ward's strip stock,
    and create a maintenance refill task for that ward."""
    with transaction() as cur:
        cur.execute(
            """INSERT INTO Glucose_Strip_Results (Admission_ID, Result_Status, Start_Time, End_Time)
               VALUES (:a, 'COMPLETED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            {"a": admission_id},
        )
        if ward_id:
            cur.execute(
                """UPDATE Ward_Equipment SET Quantity = GREATEST(Quantity - 1, 0)
                   WHERE Ward_ID = :w AND Equipment_ID =
                     (SELECT Equipment_ID FROM Equipment WHERE Equipment_Name = 'Glucose Strips')""",
                {"w": ward_id},
            )
        # Mark the doctor-assigned "Deploy Glucose Strip" task complete.
        cur.execute(
            """UPDATE Nurse_Tasks SET Task_Status = 'COMPLETED'
               WHERE Admission_ID = :a AND Nurse_ID = :n
                 AND Task_Type = 'Deploy Glucose Strip' AND Task_Status = 'PENDING'""",
            {"a": admission_id, "n": nurse_id})
        # Notify maintenance staff to refill the ward (Create_Notification proc).
        maint = fetch_scalar("SELECT MIN(Maintenance_ID) FROM Maintenance_Staff")
        if maint:
            cur.callproc("Create_Notification",
                         [maint, f"Glucose strips used in Ward #{ward_id} - refill needed."])


def log_medicine(admission_id, nurse_id):
    return execute(
        """INSERT INTO Nurse_Tasks (Admission_ID, Nurse_ID, Task_Type, Task_Status)
           VALUES (:a, :n, 'Medicine', 'COMPLETED')""",
        {"a": admission_id, "n": nurse_id},
    )


def recent_vitals(admission_id, limit=4):
    return fetch_all(
        """SELECT Systolic_BP, Diastolic_BP, Glucose_Level, Recorded_At
           FROM Patient_Vitals WHERE Admission_ID = :a
           ORDER BY Recorded_At DESC FETCH FIRST :lim ROWS ONLY""",
        {"a": admission_id, "lim": limit},
    )


def get_nurse(user_id):
    return fetch_one(
        """SELECT n.Nurse_ID, n.Shift_Timing, n.Assigned_Ward, w.Ward_Type, w.Ward_Name
           FROM Nurses n LEFT JOIN Wards w ON w.Ward_ID = n.Assigned_Ward
           WHERE n.Nurse_ID = :id""",
        {"id": user_id},
    )


def ward_patients(ward_id):
    """Active admissions currently occupying a bed in the given ward."""
    if not ward_id:
        return []
    return fetch_all(
        """
        SELECT a.Admission_ID, p.Full_Name, p.Patient_ID, a.Triage_Priority,
               a.Chief_Complaint, a.Primary_Diagnosis, b.Bed_Number, b.Bed_ID
        FROM Admissions a
        JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
        JOIN Bed_Assignments ba ON ba.Admission_ID = a.Admission_ID AND ba.Assignment_Status = 'CURRENT'
        JOIN Beds b ON b.Bed_ID = ba.Bed_ID
        JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
        WHERE wba.Ward_ID = :wid AND a.Admission_Status = 'ACTIVE'
        ORDER BY a.Triage_Priority DESC
        """,
        {"wid": ward_id},
    )


def record_vitals(admission_id, nurse_id, systolic, diastolic, glucose, temperature):
    return execute(
        """INSERT INTO Patient_Vitals
             (Admission_ID, Nurse_ID, Systolic_BP, Diastolic_BP, Glucose_Level, Temperature)
           VALUES (:adm, :nurse, :sys, :dia, :glu, :temp)""",
        {"adm": admission_id, "nurse": nurse_id, "sys": systolic,
         "dia": diastolic, "glu": glucose, "temp": temperature},
    )


def vitals_history(admission_id, limit=10):
    return fetch_all(
        """SELECT v.Systolic_BP, v.Diastolic_BP, v.Glucose_Level, v.Temperature,
                  v.Recorded_At, u.FName || ' ' || u.LName AS nurse_name
           FROM Patient_Vitals v
           LEFT JOIN HEBAS_Users u ON u.UserID = v.Nurse_ID
           WHERE v.Admission_ID = :id
           ORDER BY v.Recorded_At DESC
           FETCH FIRST :lim ROWS ONLY""",
        {"id": admission_id, "lim": limit},
    )


def list_tasks(nurse_id):
    return fetch_all(
        """SELECT t.Task_ID, t.Task_Type, t.Task_Status, t.Assigned_Time,
                  a.Admission_ID, p.Full_Name
           FROM Nurse_Tasks t
           JOIN Admissions a ON a.Admission_ID = t.Admission_ID
           JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
           WHERE t.Nurse_ID = :id
           ORDER BY DECODE(t.Task_Status, 'PENDING', 0, 1), t.Assigned_Time DESC""",
        {"id": nurse_id},
    )


def create_task(admission_id, nurse_id, task_type):
    return execute(
        """INSERT INTO Nurse_Tasks (Admission_ID, Nurse_ID, Task_Type, Task_Status)
           VALUES (:adm, :nurse, :tt, 'PENDING')""",
        {"adm": admission_id, "nurse": nurse_id, "tt": task_type},
    )


def complete_task(task_id, nurse_id):
    return execute(
        "UPDATE Nurse_Tasks SET Task_Status = 'COMPLETED' WHERE Task_ID = :id AND Nurse_ID = :n",
        {"id": task_id, "n": nurse_id},
    )
