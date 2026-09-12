"""
HEBAS database builder.

Runs (in order) against ORCLPDB:
    01_schema.sql  -> tables
    02_seed.sql    -> seed data (placeholder password hashes)
    03_programmable.sql -> views, procedures, triggers

Then rewrites every HEBAS_Users.Password_Hash to a real Werkzeug hash of the
default password so seeded accounts can actually log in.

Usage:
    venv/Scripts/python.exe database/run_db.py            # build (drops first)
    venv/Scripts/python.exe database/run_db.py --verify   # just report objects
"""

import os
import sys

import oracledb
from werkzeug.security import generate_password_hash

DSN = "localhost:1521/ORCLPDB"
DB_USER = "HEBAS"
DB_PASSWORD = "hebas123"

DEFAULT_LOGIN_PASSWORD = "Hebas@123"  # every seeded user shares this for demo/login

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["01_schema.sql", "02_seed.sql", "03_programmable.sql",
         "04_enhancements.sql", "05_refinements.sql",
         "06_role_cleanup.sql",
         "07_realistic.sql"]

_PLSQL_STARTERS = (
    "CREATE OR REPLACE TRIGGER",
    "CREATE OR REPLACE PROCEDURE",
    "CREATE OR REPLACE FUNCTION",
    "CREATE OR REPLACE PACKAGE",
    "CREATE TRIGGER",
    "CREATE PROCEDURE",
    "CREATE FUNCTION",
    "DECLARE",
    "BEGIN",
)


def split_statements(sql_text):
    """Yield individual statements. PL/SQL blocks are terminated by a lone '/';
    plain SQL statements are terminated by a trailing ';'."""
    buffer = []
    in_plsql = False
    for raw_line in sql_text.splitlines():
        stripped = raw_line.strip()

        # Skip blank / full-line comments only when no statement is in progress.
        if not buffer and (stripped == "" or stripped.startswith("--")):
            continue

        if not buffer:
            in_plsql = stripped.upper().startswith(_PLSQL_STARTERS)

        if in_plsql:
            if stripped == "/":
                stmt = "\n".join(buffer).strip()
                if stmt:
                    yield stmt
                buffer = []
                in_plsql = False
            else:
                buffer.append(raw_line)
        else:
            buffer.append(raw_line)
            if stripped.endswith(";"):
                stmt = "\n".join(buffer).strip()
                stmt = stmt[:-1].strip()  # drop trailing ';'
                if stmt:
                    yield stmt
                buffer = []

    tail = "\n".join(buffer).strip()
    if tail:
        yield tail


def drop_all_objects(cur):
    """Drop every object in the HEBAS schema so the build is idempotent."""
    for trg, in cur.execute(
        "SELECT trigger_name FROM user_triggers"
    ).fetchall():
        cur.execute(f'DROP TRIGGER "{trg}"')
    for view, in cur.execute("SELECT view_name FROM user_views").fetchall():
        cur.execute(f'DROP VIEW "{view}"')
    for name, otype in cur.execute(
        "SELECT object_name, object_type FROM user_objects "
        "WHERE object_type IN ('PROCEDURE','FUNCTION','PACKAGE')"
    ).fetchall():
        cur.execute(f'DROP {otype} "{name}"')
    for tab, in cur.execute("SELECT table_name FROM user_tables").fetchall():
        cur.execute(f'DROP TABLE "{tab}" CASCADE CONSTRAINTS PURGE')
    for seq, in cur.execute("SELECT sequence_name FROM user_sequences").fetchall():
        cur.execute(f'DROP SEQUENCE "{seq}"')


def run_file(cur, path):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    count = 0
    for stmt in split_statements(text):
        try:
            cur.execute(stmt)
            count += 1
        except Exception as exc:  # surface the offending statement, then stop
            head = stmt.strip().splitlines()[0][:120]
            print(f"\n  ERROR in {os.path.basename(path)} at statement #{count + 1}:")
            print(f"    {head} ...")
            print(f"    -> {exc}")
            raise
    return count


def set_real_passwords(conn, cur):
    pw_hash = generate_password_hash(DEFAULT_LOGIN_PASSWORD)
    cur.execute("UPDATE HEBAS_Users SET Password_Hash = :h", h=pw_hash)
    conn.commit()
    return cur.rowcount


def verify(cur):
    print("\n=== Object inventory ===")
    for label, sql in [
        ("Tables", "SELECT COUNT(*) FROM user_tables"),
        ("Views", "SELECT COUNT(*) FROM user_views"),
        ("Triggers", "SELECT COUNT(*) FROM user_triggers"),
        ("Procedures", "SELECT COUNT(*) FROM user_objects WHERE object_type='PROCEDURE'"),
        ("Invalid objects", "SELECT COUNT(*) FROM user_objects WHERE status='INVALID'"),
    ]:
        cur.execute(sql)
        print(f"  {label:18}: {cur.fetchone()[0]}")

    print("\n=== Row counts (key tables) ===")
    for t in ["HEBAS_Users", "User_Roles", "User_Role_Assignment", "Wards",
              "Beds", "Patient_Profile", "Admissions", "Bed_Assignments",
              "Sanitization_Logs", "Equipment"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t:22}: {cur.fetchone()[0]}")

    cur.execute("SELECT object_name, object_type FROM user_objects WHERE status='INVALID'")
    bad = cur.fetchall()
    if bad:
        print("\n  INVALID OBJECTS:", bad)


def _apply_arg():
    """Return the filename passed via --apply <file>, or None."""
    if "--apply" in sys.argv:
        i = sys.argv.index("--apply")
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def main():
    verify_only = "--verify" in sys.argv
    apply_file = _apply_arg()
    conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DSN)
    cur = conn.cursor()
    try:
        if verify_only:
            verify(cur)
            return

        if apply_file:
            # Apply a single .sql file to the live DB WITHOUT dropping anything.
            path = os.path.join(HERE, apply_file)
            n = run_file(cur, path)
            conn.commit()
            print(f"  {apply_file:22}: {n} statements OK")
            verify(cur)
            print("\n=== APPLY COMPLETE ===")
            return

        print("Dropping existing objects ...")
        drop_all_objects(cur)
        conn.commit()

        for fname in FILES:
            path = os.path.join(HERE, fname)
            n = run_file(cur, path)
            conn.commit()
            print(f"  {fname:22}: {n} statements OK")

        updated = set_real_passwords(conn, cur)
        print(f"\nPassword hashes set for {updated} users "
              f"(default password: {DEFAULT_LOGIN_PASSWORD!r})")

        verify(cur)
        print("\n=== BUILD COMPLETE ===")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
