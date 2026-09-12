-- ============================================================================
-- HEBAS - 06_role_cleanup.sql
-- Additive only. Nothing dropped; all views/triggers/procedures/packages kept.
-- Apply: venv\Scripts\python.exe database\run_db.py --apply 06_role_cleanup.sql
-- ============================================================================

-- 1. Admit_Status on Admissions (doctor "admits" -> admin may then assign a bed)
BEGIN
    BEGIN EXECUTE IMMEDIATE 'ALTER TABLE Admissions ADD Admit_Status VARCHAR2(20)';
    EXCEPTION WHEN OTHERS THEN IF SQLCODE NOT IN (-1430) THEN RAISE; END IF; END;
END;
/

-- 2. Per-ward consumable stock (nurse uses from ward; maintenance refills ward).
--    50 units of each consumable per ward, only where not already present.
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity)
SELECT w.Ward_ID, e.Equipment_ID, 50
FROM Wards w
CROSS JOIN Equipment e
WHERE e.Equipment_Name IN ('Glucose Strips', 'BP Machine', 'Sugar Machine')
  AND NOT EXISTS (SELECT 1 FROM Ward_Equipment we
                  WHERE we.Ward_ID = w.Ward_ID AND we.Equipment_ID = e.Equipment_ID);
COMMIT;
