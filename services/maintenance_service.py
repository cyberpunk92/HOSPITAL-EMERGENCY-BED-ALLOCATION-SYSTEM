"""Maintenance module: equipment availability + refills + Medical-Ward extra beds.
(Sanitization moved to its own role/module; complete_sanitization kept for reuse.)"""

import oracledb

from config.db import fetch_all, fetch_one, fetch_scalar, execute, transaction

REFILLABLE = ("Glucose Strips", "BP Machine", "Sugar Machine")
REFILL_BATCH = 2  # units added per "Add Glucose Strip" click


def active_wards():
    """Only the real, named wards that actually hold beds (no placeholders)."""
    return fetch_all(
        """SELECT w.Ward_ID, w.Ward_Name, w.Ward_Type, w.Floor_Number
           FROM Wards w
           WHERE EXISTS (SELECT 1 FROM Ward_Bed_Allocation wba
                         WHERE wba.Ward_ID = w.Ward_ID AND wba.End_Time IS NULL)
           ORDER BY w.Ward_ID"""
    )


def glucose_stock():
    """Glucose-strip stock per active ward (drives the refill section + the
    'needs refill' highlight). Returns ward rows with current quantity."""
    return fetch_all(
        """SELECT w.Ward_ID, w.Ward_Name,
                  NVL((SELECT we.Quantity FROM Ward_Equipment we
                       JOIN Equipment e ON e.Equipment_ID = we.Equipment_ID
                       WHERE we.Ward_ID = w.Ward_ID AND e.Equipment_Name = 'Glucose Strips'), 0) AS quantity
           FROM Wards w
           WHERE EXISTS (SELECT 1 FROM Ward_Bed_Allocation wba
                         WHERE wba.Ward_ID = w.Ward_ID AND wba.End_Time IS NULL)
           ORDER BY w.Ward_ID"""
    )


def wards_capacity():
    """Per-active-ward bed counts so maintenance can see which wards are FULL
    and need an extra bed."""
    return fetch_all(
        """SELECT w.Ward_ID, w.Ward_Name,
                  COUNT(b.Bed_ID) AS total,
                  SUM(CASE WHEN b.Current_Status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied,
                  SUM(CASE WHEN b.Current_Status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available
           FROM Wards w
           JOIN Ward_Bed_Allocation wba ON wba.Ward_ID = w.Ward_ID AND wba.End_Time IS NULL
           JOIN Beds b ON b.Bed_ID = wba.Bed_ID
           GROUP BY w.Ward_ID, w.Ward_Name
           ORDER BY w.Ward_ID"""
    )


def add_bed(ward_id):
    """Create a fresh AVAILABLE bed and allocate it to the given ward.

    Bed numbers are generated automatically (W<ward>-B<n>) so maintenance never
    has to type anything — they just click "Add Bed" for a full ward.
    """
    if not fetch_scalar(
            """SELECT COUNT(*) FROM Ward_Bed_Allocation
               WHERE Ward_ID = :w AND End_Time IS NULL""", {"w": ward_id}):
        raise ValueError("Unknown ward.")
    n = 1
    while fetch_scalar("SELECT COUNT(*) FROM Beds WHERE UPPER(Bed_Number) = UPPER(:b)",
                       {"b": f"W{ward_id}-B{n}"}):
        n += 1
    bed_number = f"W{ward_id}-B{n}"
    with transaction() as cur:
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status)
               VALUES (:b, 'Standard', 'Standard', 'AVAILABLE') RETURNING Bed_ID INTO :id""",
            {"b": bed_number, "id": new_id})
        bid = int(new_id.getvalue()[0])
        cur.execute("INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID) VALUES (:w, :b)",
                    {"w": ward_id, "b": bid})
    return bed_number


def equipment_inventory():
    return fetch_all(
        """SELECT e.Equipment_ID, e.Equipment_Name, e.Equipment_Type, e.Status,
                  NVL(ei.Quantity, 0) AS quantity
           FROM Equipment e
           LEFT JOIN Equipment_Inventory ei ON ei.Equipment_ID = e.Equipment_ID
           ORDER BY e.Equipment_Name"""
    )


def refill(ward_id, equipment_name, qty):
    """Add consumable/device stock to a specific ward (positive integer)."""
    if equipment_name not in REFILLABLE:
        raise ValueError("This item cannot be refilled.")
    if not qty or qty <= 0:
        raise ValueError("Quantity must be a positive whole number.")
    if not ward_id:
        raise ValueError("Select a ward.")
    eid = fetch_scalar("SELECT Equipment_ID FROM Equipment WHERE Equipment_Name = :n",
                       {"n": equipment_name})
    if not eid:
        raise ValueError("Unknown equipment.")
    updated = execute(
        "UPDATE Ward_Equipment SET Quantity = Quantity + :q WHERE Ward_ID = :w AND Equipment_ID = :e",
        {"q": qty, "w": ward_id, "e": eid})
    if not updated:
        execute("INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (:w, :e, :q)",
                {"w": ward_id, "e": eid, "q": qty})
    return qty


def ward_consumables():
    """Per-ward stock of the three consumables (pivot-style for the dashboard)."""
    return fetch_all(
        """SELECT we.Ward_ID, w.Ward_Name, e.Equipment_Name, we.Quantity
           FROM Ward_Equipment we
           JOIN Equipment e ON e.Equipment_ID = we.Equipment_ID
           JOIN Wards w ON w.Ward_ID = we.Ward_ID
           WHERE e.Equipment_Name IN ('Glucose Strips', 'BP Machine', 'Sugar Machine')
           ORDER BY we.Ward_ID, e.Equipment_Name""")


def all_wards():
    return fetch_all("SELECT Ward_ID, Ward_Type, Ward_Name, Floor_Number FROM Wards ORDER BY Ward_ID")


def medical_wards():
    """Only Medical Wards may receive extra beds."""
    return fetch_all(
        """SELECT mw.Ward_ID, w.Ward_Name, w.Floor_Number, w.Total_Capacity
           FROM Medical_Ward mw JOIN Wards w ON w.Ward_ID = mw.Ward_ID
           ORDER BY mw.Ward_ID"""
    )


def add_extra_bed(ward_id, bed_number):
    """Add a bed to a Medical Ward only. Bed number must be unique."""
    if not fetch_scalar("SELECT COUNT(*) FROM Medical_Ward WHERE Ward_ID = :w", {"w": ward_id}):
        raise ValueError("Extra beds are allowed only in Medical Wards.")
    if fetch_scalar("SELECT COUNT(*) FROM Beds WHERE UPPER(Bed_Number) = UPPER(:b)",
                    {"b": bed_number}):
        raise ValueError("This bed number already exists.")
    with transaction() as cur:
        new_id = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status)
               VALUES (:b, 'Medical', 'Standard', 'AVAILABLE') RETURNING Bed_ID INTO :id""",
            {"b": bed_number, "id": new_id})
        bid = int(new_id.getvalue()[0])
        cur.execute("INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID) VALUES (:w, :b)",
                    {"w": ward_id, "b": bid})
    return bid


def get_staff(user_id):
    return fetch_one(
        """SELECT m.Maintenance_ID, m.Shift_Timing, m.Assigned_Ward, w.Ward_Type
           FROM Maintenance_Staff m LEFT JOIN Wards w ON w.Ward_ID = m.Assigned_Ward
           WHERE m.Maintenance_ID = :id""",
        {"id": user_id},
    )


def list_sanitizations(maintenance_id=None, only_open=False):
    sql = """
        SELECT s.Sanitization_ID, s.Bed_ID, b.Bed_Number, s.Maintenance_ID,
               s.Start_Timestamp, s.End_Timestamp, s.Checking_Status, s.Equipment_Type,
               u.FName || ' ' || u.LName AS staff_name
        FROM Sanitization_Logs s
        JOIN Beds b ON b.Bed_ID = s.Bed_ID
        LEFT JOIN HEBAS_Users u ON u.UserID = s.Maintenance_ID
    """
    params, where = {}, []
    if maintenance_id:
        where.append("s.Maintenance_ID = :m")
        params["m"] = maintenance_id
    if only_open:
        where.append("s.Checking_Status <> 'COMPLETED'")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY DECODE(s.Checking_Status,'COMPLETED',1,0), s.Start_Timestamp DESC"
    return fetch_all(sql, params)


def complete_sanitization(sanitization_id, maintenance_id=None):
    """Mark a sanitization complete and return the bed to AVAILABLE."""
    with transaction() as cur:
        sql = """UPDATE Sanitization_Logs
                 SET Checking_Status = 'COMPLETED', End_Timestamp = CURRENT_TIMESTAMP
                 WHERE Sanitization_ID = :id AND Checking_Status <> 'COMPLETED'"""
        params = {"id": sanitization_id}
        if maintenance_id:
            sql += " AND Maintenance_ID = :m"
            params["m"] = maintenance_id
        cur.execute(sql, params)
        if cur.rowcount == 0:
            return 0
        # Free the bed (TRG_Audit_Bed_Status records the change).
        cur.execute(
            """UPDATE Beds SET Current_Status = 'AVAILABLE'
               WHERE Bed_ID = (SELECT Bed_ID FROM Sanitization_Logs WHERE Sanitization_ID = :id)
               AND Current_Status = 'PENDING_CLEANING'""",
            {"id": sanitization_id},
        )
        return 1


def list_requests():
    return fetch_all(
        """SELECT r.Request_ID, r.Equipment_ID, e.Equipment_Name, r.Reported_By,
                  u.FName || ' ' || u.LName AS reporter, r.Request_Status
           FROM Maintenance_Requests r
           JOIN Equipment e ON e.Equipment_ID = r.Equipment_ID
           LEFT JOIN HEBAS_Users u ON u.UserID = r.Reported_By
           ORDER BY r.Request_ID DESC"""
    )


def equipment_options():
    return fetch_all(
        "SELECT Equipment_ID, Equipment_Name, Status FROM Equipment ORDER BY Equipment_Name"
    )


def create_request(equipment_id, reported_by):
    return execute(
        """INSERT INTO Maintenance_Requests (Equipment_ID, Reported_By, Request_Status)
           VALUES (:e, :u, 'OPEN')""",
        {"e": equipment_id, "u": reported_by},
    )


def update_request_status(request_id, status):
    return execute(
        "UPDATE Maintenance_Requests SET Request_Status = :s WHERE Request_ID = :id",
        {"s": status, "id": request_id},
    )
