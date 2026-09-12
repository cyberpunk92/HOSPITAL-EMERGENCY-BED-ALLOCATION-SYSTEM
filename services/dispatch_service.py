"""Dispatcher module (Phase 11): ambulance cases + arrival queue."""

import oracledb

from config.db import fetch_all, fetch_one, fetch_scalar, execute, get_connection

CASE_STATUSES = ("DISPATCHED", "EN_ROUTE", "ARRIVED", "COMPLETED", "CANCELLED")


def get_dispatcher(user_id):
    return fetch_one(
        """SELECT ad.AD_ID, ad.Ambulance_Type,
                  sd.Service_Name, sd.Assigned_Region
           FROM Ambulance_Dispatcher ad
           LEFT JOIN Service_Dispatcher sd ON sd.SD_ID = ad.AD_ID
           WHERE ad.AD_ID = :id""",
        {"id": user_id},
    )


def list_cases(dispatcher_id=None):
    sql = """
        SELECT c.Case_ID, c.Patient_Name, c.Pickup_Location, c.Complaint,
               c.Case_Status, c.Dispatcher_ID,
               u.FName || ' ' || u.LName AS dispatcher_name
        FROM Ambulance_Cases c
        LEFT JOIN HEBAS_Users u ON u.UserID = c.Dispatcher_ID
    """
    params = {}
    if dispatcher_id:
        sql += " WHERE c.Dispatcher_ID = :d"
        params["d"] = dispatcher_id
    sql += " ORDER BY c.Case_ID DESC"
    return fetch_all(sql, params)


def create_case(dispatcher_id, patient_name, pickup_location, complaint):
    """Create a case via PR_CREATE_AMBULANCE_CASE; returns the new Case_ID."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            out_id = cur.var(oracledb.NUMBER)
            cur.callproc("PR_CREATE_AMBULANCE_CASE",
                         [dispatcher_id, patient_name, pickup_location, complaint, out_id])
            conn.commit()
            return int(out_id.getvalue())
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def update_case_status(case_id, status, dispatcher_id=None):
    if status not in CASE_STATUSES:
        raise ValueError("Invalid case status.")
    sql = "UPDATE Ambulance_Cases SET Case_Status = :st WHERE Case_ID = :id"
    params = {"st": status, "id": case_id}
    if dispatcher_id:
        sql += " AND Dispatcher_ID = :d"
        params["d"] = dispatcher_id
    return execute(sql, params)


def arrival_queue():
    """All queue entries (admin view) with dispatcher + recommendation."""
    return fetch_all(
        """SELECT q.Queue_ID, q.CNIC, q.Patient_Name, q.Chief_Complaint,
                  q.Assigned_Ward, w.Ward_Type, w.Ward_Name, q.Assigned_Doctor,
                  du.FName || ' ' || du.LName AS doctor_name,
                  q.Arrival_Status, q.Dispatcher_ID,
                  di.FName || ' ' || di.LName AS dispatcher_name
           FROM Arrival_Queue q
           LEFT JOIN Wards w ON w.Ward_ID = q.Assigned_Ward
           LEFT JOIN HEBAS_Users du ON du.UserID = q.Assigned_Doctor
           LEFT JOIN HEBAS_Users di ON di.UserID = q.Dispatcher_ID
           ORDER BY q.Queue_ID DESC"""
    )


def my_queue(dispatcher_id):
    """Only the entries registered by this dispatcher."""
    return fetch_all(
        """SELECT q.Queue_ID, q.CNIC, q.Patient_Name, q.Chief_Complaint,
                  q.Assigned_Ward, w.Ward_Type, w.Ward_Name, q.Assigned_Doctor,
                  du.FName || ' ' || du.LName AS doctor_name, q.Arrival_Status
           FROM Arrival_Queue q
           LEFT JOIN Wards w ON w.Ward_ID = q.Assigned_Ward
           LEFT JOIN HEBAS_Users du ON du.UserID = q.Assigned_Doctor
           WHERE q.Dispatcher_ID = :d
           ORDER BY q.Queue_ID DESC""",
        {"d": dispatcher_id},
    )


def complaint_options():
    """Complaint -> recommended ward + doctor (drives the dispatcher dropdown)."""
    return fetch_all(
        """SELECT cm.Complaint_Name, cm.Recommended_Ward_ID, w.Ward_Type, w.Ward_Name,
                  cm.Recommended_Doctor_ID, u.FName || ' ' || u.LName AS doctor_name
           FROM Complaint_Mapping cm
           LEFT JOIN Wards w ON w.Ward_ID = cm.Recommended_Ward_ID
           LEFT JOIN HEBAS_Users u ON u.UserID = cm.Recommended_Doctor_ID
           ORDER BY cm.Complaint_Name"""
    )


def add_to_queue(dispatcher_id, cnic, patient_name, chief_complaint):
    """Register a pre-arrival. Derives ward/doctor from Complaint_Mapping.
    Blocks a duplicate active CNIC from the same dispatcher."""
    dup = fetch_scalar(
        """SELECT COUNT(*) FROM Arrival_Queue
           WHERE Dispatcher_ID = :d AND CNIC = :c
             AND NVL(Arrival_Status, 'WAITING') <> 'ARRIVED'""",
        {"d": dispatcher_id, "c": cnic},
    )
    if dup:
        raise ValueError("You have already registered this CNIC in the arrival queue.")

    mapping = fetch_one(
        """SELECT Recommended_Ward_ID, Recommended_Doctor_ID
           FROM Complaint_Mapping WHERE UPPER(Complaint_Name) = UPPER(:c)""",
        {"c": chief_complaint},
    )
    ward = mapping["recommended_ward_id"] if mapping else None
    doctor = mapping["recommended_doctor_id"] if mapping else None
    return execute(
        """INSERT INTO Arrival_Queue
             (CNIC, Patient_Name, Chief_Complaint, Assigned_Ward, Assigned_Doctor,
              Arrival_Status, Dispatcher_ID)
           VALUES (:cnic, :name, :cc, :ward, :doc, 'WAITING', :disp)""",
        {"cnic": cnic, "name": patient_name, "cc": chief_complaint,
         "ward": ward, "doc": doctor, "disp": dispatcher_id},
    )


def get_queue_entry(queue_id):
    return fetch_one("SELECT * FROM Arrival_Queue WHERE Queue_ID = :id", {"id": queue_id})


def confirm_arrival(queue_id):
    """Mark a queued arrival as ARRIVED (admin confirms before registration)."""
    return execute(
        "UPDATE Arrival_Queue SET Arrival_Status = 'ARRIVED' WHERE Queue_ID = :id",
        {"id": queue_id},
    )
