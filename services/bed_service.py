"""Bed management (Phase 7)."""

from config.db import fetch_all, fetch_one, fetch_scalar, execute

VALID_STATUSES = ("AVAILABLE", "OCCUPIED", "PENDING_CLEANING")


def list_beds(status=None, ward_id=None):
    sql = """
        SELECT b.Bed_ID, b.Bed_Number, b.Bed_Type, b.Bed_Size, b.Current_Status,
               wba.Ward_ID, w.Ward_Type, w.Ward_Name,
               p.Full_Name AS patient_name
        FROM Beds b
        LEFT JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
        LEFT JOIN Wards w ON w.Ward_ID = wba.Ward_ID
        LEFT JOIN Bed_Assignments ba ON ba.Bed_ID = b.Bed_ID AND ba.Assignment_Status = 'CURRENT'
        LEFT JOIN Admissions a ON a.Admission_ID = ba.Admission_ID
        LEFT JOIN Patient_Profile p ON p.Patient_ID = a.Patient_ID
    """
    params, where = {}, []
    if status:
        where.append("b.Current_Status = :st")
        params["st"] = status
    if ward_id:
        where.append("wba.Ward_ID = :wid")
        params["wid"] = ward_id
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY b.Bed_ID"
    return fetch_all(sql, params)


def available_beds():
    """Beds that can currently be assigned (AVAILABLE + allocated to a ward)."""
    return fetch_all(
        """
        SELECT b.Bed_ID, b.Bed_Number, b.Bed_Type, w.Ward_ID, w.Ward_Type
        FROM Beds b
        JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
        JOIN Wards w ON w.Ward_ID = wba.Ward_ID
        WHERE b.Current_Status = 'AVAILABLE'
        ORDER BY w.Ward_ID, b.Bed_Number
        """
    )


def get_bed(bed_id):
    return fetch_one(
        """
        SELECT b.*, wba.Ward_ID, w.Ward_Type, w.Ward_Name
        FROM Beds b
        LEFT JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
        LEFT JOIN Wards w ON w.Ward_ID = wba.Ward_ID
        WHERE b.Bed_ID = :id
        """,
        {"id": bed_id},
    )


def bed_features(bed_id):
    return fetch_all(
        "SELECT Feature_Name FROM Bed_Feature_Assignment WHERE Bed_ID = :id ORDER BY Feature_Name",
        {"id": bed_id},
    )


def status_history(bed_id, limit=20):
    return fetch_all(
        """
        SELECT Old_Value, New_Value, Action_Timestamp
        FROM Audit_Trails
        WHERE Table_Name = 'Beds' AND Record_ID = :id
        ORDER BY Action_Timestamp DESC
        FETCH FIRST :lim ROWS ONLY
        """,
        {"id": bed_id, "lim": limit},
    )


def set_status(bed_id, new_status):
    """Manually change a bed's status (TRG_Audit_Bed_Status records the change)."""
    if new_status not in VALID_STATUSES:
        raise ValueError("Invalid bed status.")
    return execute(
        "UPDATE Beds SET Current_Status = :st WHERE Bed_ID = :id",
        {"st": new_status, "id": bed_id},
    )


def counts_by_status():
    return fetch_one(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN Current_Status='AVAILABLE' THEN 1 ELSE 0 END) AS available,
            SUM(CASE WHEN Current_Status='OCCUPIED' THEN 1 ELSE 0 END) AS occupied,
            SUM(CASE WHEN Current_Status='PENDING_CLEANING' THEN 1 ELSE 0 END) AS cleaning
        FROM Beds
        """
    )
