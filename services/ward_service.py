"""Ward queries (shared across modules) + Ward Management (Phase: Ward module)."""

import oracledb

from config.db import fetch_all, fetch_one, fetch_scalar, execute, transaction


def list_wards():
    return fetch_all(
        """
        SELECT w.Ward_ID, w.Floor_Number, w.Ward_Type, w.Total_Capacity,
               NVL(s.Beds_Occupied, 0)      AS beds_occupied,
               NVL(s.Beds_Available, 0)     AS beds_available,
               NVL(s.Beds_In_Maintenance,0) AS beds_in_maintenance
        FROM Wards w
        LEFT JOIN View_Ward_Capacity_Summary s ON s.Ward_ID = w.Ward_ID
        ORDER BY w.Ward_ID
        """
    )


def ward_options():
    """Active wards only (those that actually hold beds) for every dropdown.

    This keeps the UI limited to the real, named wards (Emergency - Cardiac /
    Trauma / Burn / Pediatric / Neurology + Medical Ward) and hides the empty
    placeholder wards so no numeric "Ward 14" style names ever surface.
    """
    return fetch_all(
        """SELECT Ward_ID, Ward_Type, Ward_Name, Floor_Number FROM Wards w
           WHERE EXISTS (SELECT 1 FROM Ward_Bed_Allocation wba
                         WHERE wba.Ward_ID = w.Ward_ID AND wba.End_Time IS NULL)
           ORDER BY Ward_ID"""
    )


def get_ward(ward_id):
    return fetch_one("SELECT * FROM Wards WHERE Ward_ID = :id", {"id": ward_id})


# ----------------------------- Ward Management -----------------------------
def wards_with_stats():
    """Wards plus live availability/occupancy via the DB functions FN_*."""
    return fetch_all(
        """SELECT w.Ward_ID, w.Floor_Number, w.Ward_Type, w.Total_Capacity, w.Current_Capacity,
                  FN_GET_AVAILABLE_BEDS(w.Ward_ID) AS available,
                  FN_GET_WARD_OCCUPANCY(w.Ward_ID) AS occupancy
           FROM Wards w ORDER BY w.Ward_ID"""
    )


def ward_beds(ward_id):
    return fetch_all(
        """SELECT b.Bed_ID, b.Bed_Number, b.Bed_Type, b.Current_Status
           FROM Beds b
           JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
           WHERE wba.Ward_ID = :id ORDER BY b.Bed_Number""",
        {"id": ward_id},
    )


def ward_equipment(ward_id):
    return fetch_all(
        "SELECT * FROM VW_WARD_EQUIPMENT WHERE Ward_ID = :id ORDER BY Equipment_Name",
        {"id": ward_id},
    )


def unallocated_beds():
    """Beds not currently allocated to any ward."""
    return fetch_all(
        """SELECT Bed_ID, Bed_Number, Bed_Type FROM Beds b
           WHERE NOT EXISTS (SELECT 1 FROM Ward_Bed_Allocation wba
                             WHERE wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL)
           ORDER BY Bed_Number"""
    )


def create_ward(floor_number, ward_type, total_capacity):
    if ward_type not in ("EMERGENCY", "RECOVERY"):
        raise ValueError("Ward type must be EMERGENCY or RECOVERY.")
    with transaction() as cur:
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity)
               VALUES (:fl, :wt, :cap, 0) RETURNING Ward_ID INTO :new_id""",
            {"fl": floor_number, "wt": ward_type, "cap": total_capacity, "new_id": new_id},
        )
        return int(new_id.getvalue()[0])


def allocate_bed(ward_id, bed_id):
    """Allocate an unallocated bed to a ward."""
    already = fetch_scalar(
        """SELECT COUNT(*) FROM Ward_Bed_Allocation
           WHERE Bed_ID = :b AND End_Time IS NULL""", {"b": bed_id})
    if already:
        raise ValueError("Bed is already allocated to a ward.")
    return execute(
        "INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID) VALUES (:w, :b)",
        {"w": ward_id, "b": bed_id},
    )

