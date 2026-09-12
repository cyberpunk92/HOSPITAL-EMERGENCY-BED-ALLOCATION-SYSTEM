"""Increment 1 tests: standards layer + Admin module (validation, CRUD, pagination, staff, arrivals)."""
import random
from app import app
from config.db import fetch_scalar

app.config.update(TESTING=True)
PW = "Hebas@123"; ADMIN = "sana.m@hebas.pk"; NURSE = "amna.soh@hebas.pk"
res = []
def chk(n, c, extra=""):
    res.append(c); print(f"  [{'PASS' if c else 'FAIL'}] {n} {extra}")
def login(c, e): c.post("/login", data={"email": e, "password": PW})

with app.test_client() as c:
    login(c, ADMIN)

    # ---- Dashboard new stats ----
    r = c.get("/admin/")
    chk("dashboard shows Total Patients", b"Total Patients" in r.data)
    chk("dashboard shows 6 summary cards", b"Active Admissions" in r.data and b"Pending Arrivals" in r.data)

    # ---- New admin routes ----
    chk("GET /admin/staff", c.get("/admin/staff").status_code == 200)
    chk("GET /admin/arrivals", c.get("/admin/arrivals").status_code == 200)

    # ---- Pagination ----
    r = c.get("/patients/?page=1")
    chk("patients list paginated", r.status_code == 200 and b"pagination" in r.data.lower())

    # ---- Validation: bad name rejected (no insert) ----
    before = fetch_scalar("SELECT COUNT(*) FROM Patient_Profile")
    r = c.post("/patients/new", data={"full_name": "John123", "dob": "1990-01-01",
               "gender": "M", "national_id": "1234567890123"}, follow_redirects=True)
    chk("name validation error shown", b"must contain letters only" in r.data)
    chk("invalid patient NOT inserted", fetch_scalar("SELECT COUNT(*) FROM Patient_Profile") == before)
    # ---- CNIC required (letters-only normalizes to empty) ----
    r = c.post("/patients/new", data={"full_name": "Valid Name", "dob": "1990-01-01",
               "gender": "M", "national_id": "abcd"}, follow_redirects=True)
    chk("empty/non-numeric CNIC rejected", b"CNIC is required" in r.data)

    # ---- Future DOB rejected ----
    r = c.post("/patients/new", data={"full_name": "Future Kid", "dob": "2099-01-01",
               "gender": "M", "national_id": "1234567890123"}, follow_redirects=True)
    chk("future DOB rejected", b"cannot be in the future" in r.data)

    # ---- Valid create -> update -> delete ----
    nid = str(random.randint(1000000000000, 9999999999999))
    r = c.post("/patients/new", data={"full_name": "Test Person", "dob": "1991-02-03",
               "gender": "M", "national_id": nid}, follow_redirects=False)
    pid = int(r.headers["Location"].rstrip("/").split("/")[-1])
    chk("valid patient created", fetch_scalar("SELECT COUNT(*) FROM Patient_Profile WHERE Patient_ID=:p", {"p": pid}) == 1)

    # duplicate CNIC blocked
    r = c.post("/patients/new", data={"full_name": "Dup Person", "dob": "1991-02-03",
               "gender": "F", "national_id": nid}, follow_redirects=True)
    chk("duplicate CNIC blocked", b"already exists" in r.data)

    # update
    c.post(f"/patients/{pid}/edit", data={"full_name": "Test Person Updated", "dob": "1991-02-03",
           "gender": "M", "national_id": nid})
    chk("patient updated", fetch_scalar("SELECT Full_Name FROM Patient_Profile WHERE Patient_ID=:p", {"p": pid}) == "Test Person Updated")

    # archive (no active admission) -> Is_Active=0, row preserved
    c.post(f"/patients/{pid}/archive")
    chk("patient archived (Is_Active=0)", fetch_scalar("SELECT Is_Active FROM Patient_Profile WHERE Patient_ID=:p", {"p": pid}) == 0)
    chk("archived patient hidden from active list", b"Test Person Updated" not in c.get("/patients/").data)

    # archive patient WITH active admission -> blocked
    active_pid = fetch_scalar("SELECT Patient_ID FROM Admissions WHERE Admission_Status='ACTIVE' FETCH FIRST 1 ROWS ONLY")
    c.post(f"/patients/{active_pid}/archive", follow_redirects=True)
    chk("archive blocked when active admission", fetch_scalar("SELECT Is_Active FROM Patient_Profile WHERE Patient_ID=:p", {"p": active_pid}) == 1)

    # ---- Staff user duplicate-license validation ----
    r = c.post("/admin/users/new", data={"fname": "Doc", "lname": "Test", "email": f"doc{random.randint(1,99999)}@hebas.pk",
               "password": "secret1", "role": "Emergency Doctor", "license_no": "PMDC-1001"}, follow_redirects=True)
    chk("duplicate license blocked", b"License No already exists" in r.data)

# ---- RBAC: nurse cannot edit patients ----
with app.test_client() as c:
    login(c, NURSE)
    chk("nurse blocked from patient edit (403)", c.get("/patients/1/edit").status_code == 403)

# ---- Dispatcher: scoped queue + complaint mapping + CNIC dedup ----
with app.test_client() as c:
    login(c, "tariq.meh@hebas.pk")  # Service Dispatcher
    r = c.get("/dispatcher/")
    chk("dispatcher dashboard loads", r.status_code == 200 and b"Register Emergency Patient" in r.data)
    chk("dispatcher shows CMH bed summary", b"Available" in r.data)
    cnic = str(random.randint(1000000000000, 9999999999999))
    c.post("/dispatcher/register", data={"cnic": cnic, "patient_name": "Test Arrival", "chief_complaint": "Sprained ankle"})
    chk("dispatcher registered to queue", fetch_scalar("SELECT COUNT(*) FROM Arrival_Queue WHERE CNIC=:c", {"c": cnic}) == 1)
    # duplicate same CNIC same dispatcher -> blocked
    r = c.post("/dispatcher/register", data={"cnic": cnic, "patient_name": "Test Arrival", "chief_complaint": "Sprained ankle"}, follow_redirects=True)
    chk("duplicate arrival CNIC blocked", b"already registered this CNIC" in r.data and
        fetch_scalar("SELECT COUNT(*) FROM Arrival_Queue WHERE CNIC=:c", {"c": cnic}) == 1)

print(f"\nRESULT: {sum(res)}/{len(res)} passed", "-- ALL PASS" if all(res) else "-- SOME FAILED")
