"""Shared dashboard / occupancy metrics."""

from config.db import fetch_one, fetch_all, fetch_scalar


def hospital_overview():
    """Top-level counters for the admin dashboard."""
    beds = fetch_one(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN Current_Status = 'OCCUPIED' THEN 1 ELSE 0 END) AS occupied,
            SUM(CASE WHEN Current_Status = 'AVAILABLE' THEN 1 ELSE 0 END) AS available,
            SUM(CASE WHEN Current_Status = 'PENDING_CLEANING' THEN 1 ELSE 0 END) AS cleaning
        FROM Beds
        """
    )
    total = beds["total"] or 0
    occupied = beds["occupied"] or 0
    occupancy_rate = round((occupied / total) * 100, 1) if total else 0.0

    return {
        "total_beds": total,
        "occupied_beds": occupied,
        "available_beds": beds["available"] or 0,
        "cleaning_beds": beds["cleaning"] or 0,
        "occupancy_rate": occupancy_rate,
        "total_wards": fetch_scalar("SELECT COUNT(*) FROM Wards") or 0,
        "total_users": fetch_scalar("SELECT COUNT(*) FROM HEBAS_Users") or 0,
        "total_patients": fetch_scalar("SELECT COUNT(*) FROM Patient_Profile") or 0,
        "doctors_count": fetch_scalar("SELECT COUNT(*) FROM Doctor_Profiles") or 0,
        "nurses_count": fetch_scalar("SELECT COUNT(*) FROM Nurses") or 0,
        "active_admissions": fetch_scalar(
            "SELECT COUNT(*) FROM Admissions WHERE Admission_Status = 'ACTIVE'"
        ) or 0,
        "today_patients": fetch_scalar(
            "SELECT COUNT(*) FROM Admissions WHERE TRUNC(Arrival_Timestamp) = TRUNC(SYSDATE)"
        ) or 0,
        "completed_cases": fetch_scalar(
            "SELECT COUNT(*) FROM Admissions WHERE Admission_Status = 'DISCHARGED'"
        ) or 0,
        "waiting_triage": fetch_scalar(
            "SELECT COUNT(*) FROM Admissions WHERE Admission_Status = 'ACTIVE' AND Assigned_Doctor IS NULL"
        ) or 0,
        "pending_sanitization": fetch_scalar(
            "SELECT COUNT(*) FROM Sanitization_Logs WHERE Checking_Status <> 'COMPLETED'"
        ) or 0,
        "pending_arrivals": fetch_scalar(
            "SELECT COUNT(*) FROM Arrival_Queue WHERE NVL(Arrival_Status,'WAITING') <> 'ARRIVED'"
        ) or 0,
    }


def ward_capacity_summary():
    """Per-ward capacity rows (only wards that have allocated beds)."""
    return fetch_all(
        """
        SELECT Ward_ID, Ward_Type, Total_Capacity,
               Beds_Occupied, Beds_Available, Beds_In_Maintenance
        FROM View_Ward_Capacity_Summary
        WHERE Beds_Occupied + Beds_Available + Beds_In_Maintenance > 0
        ORDER BY Ward_ID
        """
    )


def role_distribution():
    return fetch_all(
        """
        SELECT r.Role_Name, COUNT(ura.UserID) AS user_count
        FROM User_Roles r
        LEFT JOIN User_Role_Assignment ura ON ura.Role_ID = r.Role_ID
        GROUP BY r.Role_Name
        ORDER BY user_count DESC
        """
    )
