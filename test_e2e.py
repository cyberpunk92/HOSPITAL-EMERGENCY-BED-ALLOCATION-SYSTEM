"""End-to-end test: every role dashboard + the core clinical workflow."""
from app import app
from services import bed_service, maintenance_service
from config.db import fetch_one, fetch_scalar

app.config.update(TESTING=True)
PW = "Hebas@123"
USERS = {
    "Admin Staff":          "zara.i@hebas.pk",
    "Emergency Doctor":     "ali.khan@hebas.pk",
    "Ward Doctor":          "kamran.m@hebas.pk",
    "Nurse":                "amna.soh@hebas.pk",
    "Maintenance Staff":    "ayesha.n@hebas.pk",
    "Ambulance Dispatcher": "pervez.g@hebas.pk",
    "Service Dispatcher":   "tariq.meh@hebas.pk",
}
results = []
def check(name, cond, extra=""):
    results.append(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {extra}")

def login(c, email):
    return c.post("/login", data={"email": email, "password": PW}, follow_redirects=True)

# ---- 1. Each role can load its key pages ----
PAGES = {
    "Admin Staff": ["/admin/", "/admin/users", "/patients/", "/beds/", "/admissions/", "/reports/"],
    "Emergency Doctor": ["/doctor/"],
    "Ward Doctor": ["/doctor/"],
    "Nurse": ["/nurse/"],
    "Maintenance Staff": ["/maintenance/"],
    "Ambulance Dispatcher": ["/dispatcher/"],
    "Service Dispatcher": ["/dispatcher/"],
}
print("== Role page loads ==")
for role, pages in PAGES.items():
    with app.test_client() as c:
        login(c, USERS[role])
        for path in pages:
            r = c.get(path)
            check(f"{role} GET {path}", r.status_code == 200, f"(got {r.status_code})")

# ---- 2. RBAC denials ----
print("\n== RBAC denials ==")
with app.test_client() as c:
    login(c, USERS["Nurse"])
    check("nurse blocked from /admin/users", c.get("/admin/users").status_code == 403)
    check("nurse blocked from /reports/", c.get("/reports/").status_code == 403)

# ---- 3. Core clinical workflow (role split: admin + doctor) ----
print("\n== Clinical workflow ==")
import random
nid = f"99999-{random.randint(1000000,9999999)}-9"
DOCTOR = "ali.khan@hebas.pk"  # Emergency Doctor, Doctor_ID 1
admin = app.test_client(); login(admin, USERS["Admin Staff"])
doc = app.test_client(); login(doc, DOCTOR)

# Free pending-cleaning beds, then choose a complaint whose ward has a free bed.
from config.db import execute as _exec
_exec("UPDATE Beds SET Current_Status='AVAILABLE' WHERE Current_Status='PENDING_CLEANING'")
WARD_COMPLAINT = {1: "Chest Pain", 2: "Accident", 3: "Burn Injury", 4: "Child Emergency", 5: "Stroke/Seizure"}
avail = bed_service.available_beds()
tgt = next((b for b in avail if b["ward_id"] in WARD_COMPLAINT), None)
complaint = WARD_COMPLAINT[tgt["ward_id"]] if tgt else "Chest Pain"

# Admin: register patient + admission, assign doctor 1.
r = admin.post("/patients/new", data={"full_name": "Auto Test Patient", "dob": "1990-01-01",
               "gender": "M", "national_id": nid}, follow_redirects=False)
loc = r.headers.get("Location", "")
pid = int(loc.rstrip("/").split("/")[-1]) if "/patients/" in loc else None
check("admin registers patient", pid is not None, f"(loc {loc})")
r = admin.post("/admissions/new", data={"patient_id": pid, "triage_priority": "4",
               "chief_complaint": complaint}, follow_redirects=False)
loc = r.headers.get("Location", "")
aid = int(loc.rstrip("/").split("/")[-1]) if "/admissions/" in loc else None
check("admin creates admission", aid is not None, f"(loc {loc})")
admin.post(f"/admissions/{aid}/assign-doctor", data={"doctor_id": "1"})
check("admin assigned doctor", fetch_scalar("SELECT Assigned_Doctor FROM Admissions WHERE Admission_ID=:a", {"a": aid}) == 1)

# Doctor: admit BEFORE diagnosis -> rejected (no bed assigned).
doc.post(f"/admissions/{aid}/admit", follow_redirects=True)
check("admit blocked without diagnosis",
      fetch_scalar("SELECT COUNT(*) FROM Bed_Assignments WHERE Admission_ID=:a", {"a": aid}) == 0)
check("admin cannot diagnose (403)", admin.post(f"/admissions/{aid}/diagnose", data={"diagnosis": "x"}).status_code == 403)

# Doctor: diagnose + admit -> system AUTO-ASSIGNS a bed.
doc.post(f"/admissions/{aid}/diagnose", data={"diagnosis": "E2E Diagnosis"})
doc.post(f"/admissions/{aid}/admit", follow_redirects=True)
check("doctor admitted patient", fetch_scalar("SELECT Admit_Status FROM Admissions WHERE Admission_ID=:a", {"a": aid}) == "ADMITTED")
adm = fetch_one("""SELECT ba.Bed_ID, b.Current_Status FROM Bed_Assignments ba
                   JOIN Beds b ON b.Bed_ID=ba.Bed_ID
                   WHERE ba.Admission_ID=:a AND ba.Assignment_Status='CURRENT'""", {"a": aid})
check("bed AUTO-assigned on admit", adm is not None, "(no free bed in ward)" if adm is None else "")
check("auto-assigned bed OCCUPIED (trigger)", adm and adm["current_status"] == "OCCUPIED")
bed_id = adm["bed_id"] if adm else None

# Doctor: discharge (admin cannot).
check("admin cannot discharge (403)", admin.post(f"/admissions/{aid}/discharge").status_code == 403)
doc.post(f"/admissions/{aid}/discharge", follow_redirects=True)
check("admission discharged", fetch_scalar("SELECT Admission_Status FROM Admissions WHERE Admission_ID=:a", {"a": aid}) == "DISCHARGED")
if bed_id:
    check("bed PENDING_CLEANING on discharge (trigger)",
          fetch_scalar("SELECT Current_Status FROM Beds WHERE Bed_ID=:b", {"b": bed_id}) == "PENDING_CLEANING")
    san = fetch_one("""SELECT Sanitization_ID FROM Sanitization_Logs
                       WHERE Bed_ID=:b AND Checking_Status<>'COMPLETED'
                       ORDER BY Sanitization_ID DESC FETCH FIRST 1 ROWS ONLY""", {"b": bed_id})
    check("sanitization log auto-dispatched (trigger)", san is not None)
else:
    san = None

# ---- 4. Maintenance completes sanitization -> bed AVAILABLE ----
print("\n== Maintenance completion ==")
if san and bed_id:
    n = maintenance_service.complete_sanitization(san["sanitization_id"])
    bed_status = fetch_scalar("SELECT Current_Status FROM Beds WHERE Bed_ID=:b", {"b": bed_id})
    check("sanitization completed -> bed AVAILABLE", n == 1 and bed_status == "AVAILABLE", f"(status {bed_status})")

print(f"\nRESULT: {sum(results)}/{len(results)} passed",
      "-- ALL PASS" if all(results) else "-- SOME FAILED")
