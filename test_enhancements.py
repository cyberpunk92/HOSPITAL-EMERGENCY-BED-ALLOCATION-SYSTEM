"""Tests for the STEP-4/5 enhancements: procedures, triggers, functions, new routes."""
import random
from app import app
from services import bed_service
from config.db import fetch_scalar, fetch_one, fetch_all, execute

app.config.update(TESTING=True)
PW = "Hebas@123"
ADMIN, DOCTOR, NURSE = "zara.i@hebas.pk", "ali.khan@hebas.pk", "amna.soh@hebas.pk"
results = []
def chk(name, cond, extra=""):
    results.append(cond); print(f"  [{'PASS' if cond else 'FAIL'}] {name} {extra}")
def login(c, e): c.post("/login", data={"email": e, "password": PW})

# ---- 1. New route loads ----
print("== New routes ==")
with app.test_client() as c:
    login(c, ADMIN)
    chk("admin GET /wards/", c.get("/wards/").status_code == 200)
    chk("admin GET /wards/new", c.get("/wards/new").status_code == 200)
    chk("admin GET /wards/1", c.get("/wards/1").status_code == 200)
    chk("admin blocked from /notifications/ (403)", c.get("/notifications/").status_code == 403)
with app.test_client() as c:
    login(c, "ayesha.n@hebas.pk")  # Maintenance Staff
    chk("maintenance GET /notifications/", c.get("/notifications/").status_code == 200)
with app.test_client() as c:
    login(c, NURSE)
    chk("nurse blocked from /notifications/ (403)", c.get("/notifications/").status_code == 403)
    chk("nurse blocked from /wards/ (403)", c.get("/wards/").status_code == 403)

# ---- 2. Functions ----
print("\n== Functions ==")
chk("FN_GET_AVAILABLE_BEDS(NULL) numeric", isinstance(fetch_scalar("SELECT FN_GET_AVAILABLE_BEDS(NULL) FROM dual"), (int, float)))
chk("FN_GET_WARD_OCCUPANCY(1) 0-100", 0 <= fetch_scalar("SELECT FN_GET_WARD_OCCUPANCY(1) FROM dual") <= 100)
chk("FN_GET_DOCTOR_WORKLOAD(1) numeric", isinstance(fetch_scalar("SELECT FN_GET_DOCTOR_WORKLOAD(1) FROM dual"), (int, float)))
chk("FN_GET_NURSE_WORKLOAD(24) numeric", isinstance(fetch_scalar("SELECT FN_GET_NURSE_WORKLOAD(24) FROM dual"), (int, float)))
chk("FN_GET_BED_STATUS(1) valid", fetch_scalar("SELECT FN_GET_BED_STATUS(1) FROM dual") in ('AVAILABLE','OCCUPIED','PENDING_CLEANING'))

# ---- 3. Procedure + trigger workflow ----
print("\n== Procedure/trigger workflow ==")
nid = f"88888-{random.randint(1000000,9999999)}-8"
admin = app.test_client(); login(admin, ADMIN)
doc = app.test_client(); login(doc, "ali.khan@hebas.pk")  # Doctor 1
# free pending beds + pick a complaint whose ward has a free bed
from config.db import execute as _exec
_exec("UPDATE Beds SET Current_Status='AVAILABLE' WHERE Current_Status='PENDING_CLEANING'")
WARD_COMPLAINT = {1: "Chest Pain", 2: "Accident", 3: "Burn Injury", 4: "Child Emergency", 5: "Stroke/Seizure"}
avail0 = bed_service.available_beds()
tgt0 = next((b for b in avail0 if b["ward_id"] in WARD_COMPLAINT), None)
complaint = WARD_COMPLAINT[tgt0["ward_id"]] if tgt0 else "Chest Pain"
r = admin.post("/patients/new", data={"full_name": "Enh Test", "dob": "1980-05-05", "gender": "M", "national_id": nid})
pid = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = admin.post("/admissions/new", data={"patient_id": pid, "triage_priority": "5", "chief_complaint": complaint})
aid = int(r.headers["Location"].rstrip("/").split("/")[-1])

# admin assigns doctor 1 -> TRG_DOCTOR_HISTORY + TRG_NOTIFY_DOCTOR
admin.post(f"/admissions/{aid}/assign-doctor", data={"doctor_id": "1"})
chk("PR_ASSIGN_DOCTOR set doctor", fetch_scalar("SELECT Assigned_Doctor FROM Admissions WHERE Admission_ID=:a", {"a": aid}) == 1)
chk("TRG_DOCTOR_HISTORY logged", fetch_scalar("SELECT COUNT(*) FROM Doctor_Assignment_History WHERE Admission_ID=:a", {"a": aid}) >= 1)
chk("TRG_NOTIFY_DOCTOR notified", fetch_scalar("SELECT COUNT(*) FROM Notifications WHERE User_ID=1 AND Message LIKE :m", {"m": f"%#{aid}%"}) >= 1)

# Priority / measurement are no longer doctor-facing routes (UI removed); the
# underlying service + DB objects remain and are exercised directly here.
from services import admission_service as _adm
_adm.set_priority(aid, 1, "Looks stable", 4)
chk("Patient_Priority recorded (service)", fetch_scalar("SELECT COUNT(*) FROM Patient_Priority WHERE Admission_ID=:a", {"a": aid}) >= 1)
_adm.record_measurement(aid, "120/80", 99)
chk("Medical_Measurements recorded (service)", fetch_scalar("SELECT COUNT(*) FROM Medical_Measurements WHERE Admission_ID=:a", {"a": aid}) >= 1)

doc.post(f"/admissions/{aid}/diagnose", data={"diagnosis": "Enh diagnosis"})
doc.post(f"/admissions/{aid}/admit")  # system auto-assigns a bed
bed_a_id = fetch_scalar("SELECT Bed_ID FROM Bed_Assignments WHERE Admission_ID=:a AND Assignment_Status='CURRENT'", {"a": aid})
chk("bed AUTO-assigned (OCCUPIED)", bed_a_id is not None and fetch_scalar("SELECT FN_GET_BED_STATUS(:b) FROM dual", {"b": bed_a_id}) == "OCCUPIED")
cur_ward = fetch_scalar("""SELECT wba.Ward_ID FROM Ward_Bed_Allocation wba WHERE wba.Bed_ID=:b AND wba.End_Time IS NULL""", {"b": bed_a_id}) if bed_a_id else None
target_ward = next((b["ward_id"] for b in bed_service.available_beds() if b["ward_id"] != cur_ward), None)

# doctor assigns nurse 24 with a task -> PR_ASSIGN_NURSE + TRG_NOTIFY_NURSE
doc.post(f"/admissions/{aid}/assign-nurse", data={"nurse_id": "24", "tasks": ["Check BP"]})
chk("PR_ASSIGN_NURSE -> Nurse_Assignments", fetch_scalar("SELECT COUNT(*) FROM Nurse_Assignments WHERE Admission_ID=:a AND Nurse_ID=24", {"a": aid}) >= 1)
chk("TRG_NOTIFY_NURSE notified", fetch_scalar("SELECT COUNT(*) FROM Notifications WHERE User_ID=24 AND Message LIKE :m", {"m": f"%#{aid}%"}) >= 1)

# doctor transfer -> PR_TRANSFER_PATIENT + TRG_TRANSFER_HISTORY
if target_ward:
    doc.post(f"/admissions/{aid}/transfer", data={"to_ward": str(target_ward)})
    chk("PR_TRANSFER_PATIENT -> Patient_Transfers", fetch_scalar("SELECT COUNT(*) FROM Patient_Transfers WHERE Admission_ID=:a", {"a": aid}) >= 1)
    chk("TRG_TRANSFER_HISTORY audited", fetch_scalar("SELECT COUNT(*) FROM Audit_Trails WHERE Action_Type='TRANSFER' AND Record_ID=:a", {"a": aid}) >= 1)
else:
    chk("transfer skipped (no 2nd ward bed)", True, "(skipped)")

# ---- 4. TRG_AUTO_TRIAGE (direct insert, NULL triage) ----
# Use a FRESH patient (UQ_ACTIVE_ADMISSION allows only one active admission per patient).
print("\n== Auto-triage trigger ==")
import oracledb
from config.db import get_connection
with get_connection() as conn:
    cur = conn.cursor()
    pp = cur.var(oracledb.NUMBER)
    cur.execute(
        """INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID)
           VALUES ('Auto Triage', TO_DATE('2000-01-01','YYYY-MM-DD'), 'M', :nid)
           RETURNING Patient_ID INTO :pp""",
        {"nid": str(random.randint(1000000000000, 9999999999999)), "pp": pp})
    pid2 = int(pp.getvalue()[0])
    out = cur.var(oracledb.NUMBER)
    cur.execute(
        """INSERT INTO Admissions (Patient_ID, Chief_Complaint, Admission_Status)
           VALUES (:p, 'Severe chest pain auto', 'ACTIVE') RETURNING Admission_ID INTO :o""",
        {"p": pid2, "o": out})
    conn.commit()
    at_aid = int(out.getvalue()[0])
chk("TRG_AUTO_TRIAGE set P5 for chest", fetch_scalar("SELECT Triage_Priority FROM Admissions WHERE Admission_ID=:a", {"a": at_aid}) == 5)

# ---- 5. Equipment proc + audit + auto maintenance request ----
print("\n== Equipment status proc/triggers ==")
before_reqs = fetch_scalar("SELECT COUNT(*) FROM Maintenance_Requests")
with get_connection() as conn:
    cur = conn.cursor(); cur.callproc("PR_UPDATE_EQUIPMENT_STATUS", [3, "BROKEN"]); conn.commit()
chk("PR_UPDATE_EQUIPMENT_STATUS set BROKEN", fetch_scalar("SELECT Status FROM Equipment WHERE Equipment_ID=3") == "BROKEN")
chk("TRG_EQUIPMENT_AUDIT logged", fetch_scalar("SELECT COUNT(*) FROM Audit_Trails WHERE Table_Name='Equipment' AND Record_ID=3") >= 1)
chk("TRG_MAINTENANCE_REQUEST opened request", fetch_scalar("SELECT COUNT(*) FROM Maintenance_Requests") > before_reqs)
with get_connection() as conn:  # reset
    cur = conn.cursor(); cur.callproc("PR_UPDATE_EQUIPMENT_STATUS", [3, "FUNCTIONAL"]); conn.commit()

# ---- 6. Daily report proc ----
print("\n== Daily report proc ==")
with get_connection() as conn:
    cur = conn.cursor(); cur.callproc("PR_GENERATE_DAILY_REPORT"); conn.commit()
chk("PR_GENERATE_DAILY_REPORT updated Hospitals",
    fetch_scalar("SELECT Total_Beds FROM Hospitals WHERE ROWNUM=1") == fetch_scalar("SELECT COUNT(*) FROM Beds"))

print(f"\nRESULT: {sum(results)}/{len(results)} passed",
      "-- ALL PASS" if all(results) else "-- SOME FAILED")
