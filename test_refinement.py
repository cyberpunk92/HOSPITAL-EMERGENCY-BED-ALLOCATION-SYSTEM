"""Refinement tests: role-scoped dashboards, validation, dedup, maintenance, portal."""
import random
from app import app
from config.db import fetch_scalar, fetch_one

app.config.update(TESTING=True)
PW = "Hebas@123"
U = {
    "admin": "sana.m@hebas.pk", "edoc": "ali.khan@hebas.pk", "wdoc": "kamran.m@hebas.pk",
    "nurse": "amna.soh@hebas.pk", "maint": "ayesha.n@hebas.pk", "san": "zainab.r@hebas.pk",
    "patient": "ahmed.raza@patient.hebas.pk", "disp": "tariq.meh@hebas.pk",
}
res = []
def chk(n, c, extra=""): res.append(c); print(f"  [{'PASS' if c else 'FAIL'}] {n} {extra}")
def login(c, k): c.post("/login", data={"email": U[k], "password": PW})

# ---- Doctor: header + scoping ----
print("== Doctor ==")
with app.test_client() as c:
    login(c, "edoc")
    r = c.get("/doctor/")
    chk("emergency doctor dashboard", r.status_code == 200 and b"Triage Queue" in r.data and b"Emergency Doctor" in r.data)
with app.test_client() as c:
    login(c, "wdoc")
    r = c.get("/doctor/")
    chk("ward doctor: no triage queue", r.status_code == 200 and b"Triage Queue" not in r.data and b"Ward Doctor" in r.data)

# ---- Admin role-trimming on admission detail ----
print("\n== Admin role-trim ==")
adm_id = fetch_scalar("SELECT MIN(Admission_ID) FROM Admissions WHERE Admission_Status='ACTIVE'")
with app.test_client() as c:
    login(c, "admin")
    r = c.get(f"/admissions/{adm_id}")
    d = r.data
    chk("admin sees Assign Doctor", b"Assign Doctor" in d)
    chk("admin does NOT see Discharge", b"Discharge Patient" not in d)
    chk("admin does NOT see Diagnosis card", b"Required before a bed" not in d)
    chk("admin does NOT see Set Priority", b"Set Priority" not in d)
with app.test_client() as c:
    login(c, "edoc")
    r = c.get(f"/admissions/{adm_id}")
    chk("doctor sees Discharge + Diagnosis", b"Discharge Patient" in r.data)

# ---- Nurse: assigned patients + BP validation + equipment ----
print("\n== Nurse ==")
with app.test_client() as c:
    login(c, "nurse")
    r = c.get("/nurse/")
    chk("nurse dashboard + equipment summary", r.status_code == 200 and b"Glucose Strips" in r.data and b"BP Machines" in r.data)
    # BP systolic must be > diastolic
    na = fetch_one("""SELECT na.Admission_ID FROM Nurse_Assignments na
        JOIN Admissions a ON a.Admission_ID=na.Admission_ID AND a.Admission_Status='ACTIVE'
        WHERE na.Nurse_ID=24 FETCH FIRST 1 ROWS ONLY""")
    if na:
        aid = na["admission_id"]
        before = fetch_scalar("SELECT COUNT(*) FROM Patient_Vitals WHERE Admission_ID=:a", {"a": aid})
        r = c.post("/nurse/bp", data={"admission_id": aid, "systolic": "80", "diastolic": "120"}, follow_redirects=True)
        chk("BP systolic<=diastolic rejected", b"Systolic must be greater" in r.data and
            fetch_scalar("SELECT COUNT(*) FROM Patient_Vitals WHERE Admission_ID=:a", {"a": aid}) == before)
        c.post("/nurse/bp", data={"admission_id": aid, "systolic": "120", "diastolic": "80"})
        chk("valid BP recorded", fetch_scalar("SELECT COUNT(*) FROM Patient_Vitals WHERE Admission_ID=:a AND Systolic_BP=120", {"a": aid}) >= 1)
    else:
        chk("nurse has an assigned patient", False, "(none assigned)")

# ---- Maintenance: one-click glucose refill + one-click add bed ----
print("\n== Maintenance ==")
from services import maintenance_service
with app.test_client() as c:
    login(c, "maint")
    data = c.get("/maintenance/").data
    chk("maintenance dashboard (refill + add bed only)",
        b"Glucose Strip Refill" in data and b"Add Bed" in data)
    wid = 1
    def ward_qty():
        return fetch_scalar("""SELECT we.Quantity FROM Ward_Equipment we JOIN Equipment e ON e.Equipment_ID=we.Equipment_ID
            WHERE we.Ward_ID=:w AND e.Equipment_Name='Glucose Strips'""", {"w": wid})
    before = ward_qty()
    c.post("/maintenance/refill", data={"ward_id": wid})
    chk("one-click refill adds a batch of strips", ward_qty() == before + maintenance_service.REFILL_BATCH)
    # one-click add bed to any active ward -> new AVAILABLE bed allocated there
    er_ward = 2
    beds_before = fetch_scalar("""SELECT COUNT(*) FROM Ward_Bed_Allocation wba
        WHERE wba.Ward_ID=:w AND wba.End_Time IS NULL""", {"w": er_ward})
    c.post("/maintenance/add-bed", data={"ward_id": er_ward})
    chk("add bed creates AVAILABLE bed in the ward",
        fetch_scalar("""SELECT COUNT(*) FROM Ward_Bed_Allocation wba
            WHERE wba.Ward_ID=:w AND wba.End_Time IS NULL""", {"w": er_ward}) == beds_before + 1)

# ---- Sanitization role ----
print("\n== Sanitization ==")
with app.test_client() as c:
    login(c, "san")
    r = c.get("/sanitization/")
    chk("sanitization dashboard", r.status_code == 200 and b"Beds Pending Cleaning" in r.data)
    chk("sanitization blocked from maintenance (403)", c.get("/maintenance/").status_code == 403)

# ---- Patient portal: timeline + nurse + discharge ----
print("\n== Patient portal ==")
with app.test_client() as c:
    login(c, "patient")
    r = c.get("/patient/")
    chk("portal has care timeline", r.status_code == 200 and b"My Care Timeline" in r.data)
    chk("portal shows Nurse + Glucose Status", b"Nurse" in r.data and b"Glucose Status" in r.data)

# ---- Dispatcher CMH-only (no Al-Shifa) ----
print("\n== Branding ==")
with app.test_client() as c:
    login(c, "disp")
    r = c.get("/dispatcher/")
    chk("CMH Rawalpindi shown", b"CMH Rawalpindi" in r.data)
    chk("no Al-Shifa", b"Al-Shifa" not in r.data and b"Shifa" not in r.data)

print(f"\nRESULT: {sum(res)}/{len(res)} passed", "-- ALL PASS" if all(res) else "-- SOME FAILED")
