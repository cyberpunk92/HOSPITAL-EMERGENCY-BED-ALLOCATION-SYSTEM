"""Reporting module (Phase 13): occupancy, admissions, sanitization, audit.

CSV exports are written to the project-level reports/ directory.
"""

import csv
import os
from datetime import datetime

from config.db import fetch_all, fetch_one

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def occupancy_by_ward():
    return fetch_all(
        """SELECT s.Ward_ID, w.Ward_Name, s.Ward_Type, s.Total_Capacity, s.Beds_Occupied,
                  s.Beds_Available, s.Beds_In_Maintenance
           FROM View_Ward_Capacity_Summary s JOIN Wards w ON w.Ward_ID = s.Ward_ID
           WHERE s.Beds_Occupied + s.Beds_Available + s.Beds_In_Maintenance > 0
           ORDER BY s.Ward_ID"""
    )


def admissions_by_status():
    return fetch_all(
        """SELECT Admission_Status, COUNT(*) AS cnt
           FROM Admissions GROUP BY Admission_Status ORDER BY cnt DESC"""
    )


def admissions_by_priority():
    return fetch_all(
        """SELECT Triage_Priority, COUNT(*) AS cnt
           FROM Admissions GROUP BY Triage_Priority ORDER BY Triage_Priority DESC"""
    )


def recent_admissions(limit=25):
    return fetch_all(
        """SELECT a.Admission_ID, p.Full_Name, a.Triage_Priority, a.Chief_Complaint,
                  a.Admission_Status, a.Arrival_Timestamp
           FROM Admissions a JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
           ORDER BY a.Arrival_Timestamp DESC
           FETCH FIRST :lim ROWS ONLY""",
        {"lim": limit},
    )


def sanitization_summary():
    return fetch_all(
        """SELECT Checking_Status, COUNT(*) AS cnt
           FROM Sanitization_Logs GROUP BY Checking_Status ORDER BY cnt DESC"""
    )


def audit_trail(limit=50):
    return fetch_all(
        """SELECT Audit_ID, Action_Type, Table_Name, Record_ID,
                  Old_Value, New_Value, Action_Timestamp
           FROM Audit_Trails ORDER BY Action_Timestamp DESC
           FETCH FIRST :lim ROWS ONLY""",
        {"lim": limit},
    )


def doctor_workload():
    return fetch_all(
        "SELECT Doctor_Name, Specialization, Department, Active_Patients "
        "FROM VW_DOCTOR_WORKLOAD ORDER BY Active_Patients DESC, Doctor_Name")


def nurse_workload():
    # Resolve the numeric ward id from the view to a readable ward name
    # (the view itself is left untouched).
    return fetch_all(
        """SELECT v.Nurse_Name,
                  NVL(w.Ward_Name, TO_CHAR(v.Assigned_Ward)) AS assigned_ward,
                  v.Ward_Patients, v.Pending_Tasks
           FROM VW_NURSE_WORKLOAD v
           LEFT JOIN Wards w ON w.Ward_ID = v.Assigned_Ward
           ORDER BY v.Ward_Patients DESC, v.Nurse_Name""")


def discharge_report(limit=25):
    return fetch_all(
        """SELECT a.Admission_ID, p.Full_Name, a.Primary_Diagnosis,
                  a.Discharge_Timestamp
           FROM Admissions a JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
           WHERE a.Admission_Status = 'DISCHARGED'
           ORDER BY a.Discharge_Timestamp DESC FETCH FIRST :lim ROWS ONLY""",
        {"lim": limit})


def equipment_report():
    return fetch_all(
        """SELECT e.Equipment_Name, e.Equipment_Type, e.Status, NVL(ei.Quantity, 0) AS quantity
           FROM Equipment e LEFT JOIN Equipment_Inventory ei ON ei.Equipment_ID = e.Equipment_ID
           ORDER BY e.Equipment_Name""")


def kpis():
    return fetch_one(
        """SELECT
              (SELECT COUNT(*) FROM Admissions) AS total_admissions,
              (SELECT COUNT(*) FROM Admissions WHERE Admission_Status='ACTIVE') AS active_admissions,
              (SELECT COUNT(*) FROM Admissions WHERE Admission_Status='DISCHARGED') AS discharged,
              (SELECT COUNT(*) FROM Patient_Profile) AS total_patients,
              (SELECT COUNT(*) FROM Sanitization_Logs WHERE Checking_Status<>'COMPLETED') AS open_sanitizations
           FROM dual"""
    )


# ---- CSV export ----
_EXPORTS = {
    "occupancy": (occupancy_by_ward,
                  ["ward_id", "ward_type", "total_capacity", "beds_occupied", "beds_available", "beds_in_maintenance"]),
    "admissions": (lambda: recent_admissions(1000),
                   ["admission_id", "full_name", "triage_priority", "chief_complaint", "admission_status", "arrival_timestamp"]),
    "sanitization": (lambda: fetch_all(
        """SELECT s.Sanitization_ID, s.Bed_ID, b.Bed_Number, s.Checking_Status,
                  s.Start_Timestamp, s.End_Timestamp, s.Equipment_Type
           FROM Sanitization_Logs s JOIN Beds b ON b.Bed_ID = s.Bed_ID
           ORDER BY s.Sanitization_ID"""),
        ["sanitization_id", "bed_id", "bed_number", "checking_status", "start_timestamp", "end_timestamp", "equipment_type"]),
    "audit": (lambda: audit_trail(1000),
              ["audit_id", "action_type", "table_name", "record_id", "old_value", "new_value", "action_timestamp"]),
}


def export_csv(report_key):
    """Write a report to reports/<key>_<timestamp>.csv. Returns the file path."""
    if report_key not in _EXPORTS:
        raise ValueError("Unknown report.")
    fetcher, columns = _EXPORTS[report_key]
    rows = fetcher()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    fname = f"{report_key}_{datetime.now():%Y%m%d_%H%M%S}.csv"
    path = os.path.join(REPORTS_DIR, fname)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row.get(c) for c in columns])
    return path
