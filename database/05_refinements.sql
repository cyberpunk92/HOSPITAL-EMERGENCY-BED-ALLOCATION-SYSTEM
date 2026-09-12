-- ============================================================================
-- HEBAS - 05_refinements.sql
-- Additive refinements only. Nothing is dropped or rebuilt; every existing
-- table, view, trigger, procedure, package and function is preserved.
-- Idempotent: ALTERs / indexes are guarded so the file can be re-applied.
-- Apply: venv\Scripts\python.exe database\run_db.py --apply 05_refinements.sql
-- ============================================================================

-- 1. Additive columns (Archive support + per-dispatcher arrival scoping) -------
BEGIN
    BEGIN EXECUTE IMMEDIATE
        'ALTER TABLE Patient_Profile ADD Is_Active NUMBER(1) DEFAULT 1 CHECK (Is_Active IN (0,1))';
    EXCEPTION WHEN OTHERS THEN IF SQLCODE NOT IN (-1430) THEN RAISE; END IF; END;

    BEGIN EXECUTE IMMEDIATE 'ALTER TABLE Arrival_Queue ADD Dispatcher_ID NUMBER';
    EXCEPTION WHEN OTHERS THEN IF SQLCODE NOT IN (-1430) THEN RAISE; END IF; END;

    BEGIN EXECUTE IMMEDIATE
        'ALTER TABLE Arrival_Queue ADD CONSTRAINT fk_aq_disp FOREIGN KEY (Dispatcher_ID) REFERENCES HEBAS_Users(UserID)';
    EXCEPTION WHEN OTHERS THEN IF SQLCODE NOT IN (-2275, -955) THEN RAISE; END IF; END;
END;
/

-- Backfill: a nullable ADD COLUMN leaves existing rows NULL, so set them active.
UPDATE Patient_Profile SET Is_Active = 1 WHERE Is_Active IS NULL;
COMMIT;

-- 2. Sanitization Staff role + reassign one maintenance user (UserID 8) --------
INSERT INTO User_Roles (Role_Name)
SELECT 'Sanitization Staff' FROM dual
WHERE NOT EXISTS (SELECT 1 FROM User_Roles WHERE Role_Name = 'Sanitization Staff');

DELETE FROM User_Role_Assignment
WHERE UserID = 8
  AND Role_ID = (SELECT Role_ID FROM User_Roles WHERE Role_Name = 'Maintenance Staff');

INSERT INTO User_Role_Assignment (UserID, Role_ID)
SELECT 8, (SELECT Role_ID FROM User_Roles WHERE Role_Name = 'Sanitization Staff')
FROM dual
WHERE NOT EXISTS (
    SELECT 1 FROM User_Role_Assignment
    WHERE UserID = 8 AND Role_ID = (SELECT Role_ID FROM User_Roles WHERE Role_Name = 'Sanitization Staff'));
COMMIT;

-- 3. Resolve pre-existing duplicate state (test data) so unique indexes apply --
-- Keep only the newest ACTIVE admission per patient; mark older ones CANCELLED
-- (CANCELLED does not fire discharge/sanitization triggers).
UPDATE Admissions a
SET Admission_Status = 'CANCELLED'
WHERE a.Admission_Status = 'ACTIVE'
  AND a.Admission_ID < (SELECT MAX(a2.Admission_ID) FROM Admissions a2
                        WHERE a2.Patient_ID = a.Patient_ID AND a2.Admission_Status = 'ACTIVE');

-- Keep only the newest CURRENT bed assignment per bed and per admission.
UPDATE Bed_Assignments b
SET Assignment_Status = 'COMPLETED', End_Time = CURRENT_TIMESTAMP
WHERE b.Assignment_Status = 'CURRENT'
  AND b.Assignment_ID < (SELECT MAX(b2.Assignment_ID) FROM Bed_Assignments b2
                         WHERE b2.Bed_ID = b.Bed_ID AND b2.Assignment_Status = 'CURRENT');

UPDATE Bed_Assignments b
SET Assignment_Status = 'COMPLETED', End_Time = CURRENT_TIMESTAMP
WHERE b.Assignment_Status = 'CURRENT'
  AND b.Assignment_ID < (SELECT MAX(b2.Assignment_ID) FROM Bed_Assignments b2
                         WHERE b2.Admission_ID = b.Admission_ID AND b2.Assignment_Status = 'CURRENT');
COMMIT;

-- 3b. Consumable equipment + inventory (nurse summary / maintenance refill) ----
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Status)
SELECT 'Glucose Strips', 'Consumable', 'FUNCTIONAL' FROM dual
WHERE NOT EXISTS (SELECT 1 FROM Equipment WHERE Equipment_Name = 'Glucose Strips');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Status)
SELECT 'BP Machine', 'Device', 'FUNCTIONAL' FROM dual
WHERE NOT EXISTS (SELECT 1 FROM Equipment WHERE Equipment_Name = 'BP Machine');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Status)
SELECT 'Sugar Machine', 'Device', 'FUNCTIONAL' FROM dual
WHERE NOT EXISTS (SELECT 1 FROM Equipment WHERE Equipment_Name = 'Sugar Machine');

INSERT INTO Equipment_Inventory (Equipment_ID, Quantity)
SELECT e.Equipment_ID, 50 FROM Equipment e
WHERE e.Equipment_Name IN ('Glucose Strips', 'BP Machine', 'Sugar Machine')
  AND NOT EXISTS (SELECT 1 FROM Equipment_Inventory ei WHERE ei.Equipment_ID = e.Equipment_ID);
COMMIT;

-- 4. DB-level dedup via function-based UNIQUE indexes --------------------------
-- (one ACTIVE admission per patient; one CURRENT assignment per bed and per admission)
BEGIN
    FOR s IN (
        SELECT 'UQ_ACTIVE_ADMISSION'  nm,
               'Admissions (CASE WHEN Admission_Status=''ACTIVE'' THEN Patient_ID END)' col FROM dual UNION ALL
        SELECT 'UQ_CURRENT_BED',
               'Bed_Assignments (CASE WHEN Assignment_Status=''CURRENT'' THEN Bed_ID END)' FROM dual UNION ALL
        SELECT 'UQ_CURRENT_BED_ADM',
               'Bed_Assignments (CASE WHEN Assignment_Status=''CURRENT'' THEN Admission_ID END)' FROM dual
    ) LOOP
        BEGIN
            EXECUTE IMMEDIATE 'CREATE UNIQUE INDEX ' || s.nm || ' ON ' || s.col;
        EXCEPTION WHEN OTHERS THEN
            -- 955 exists, 1408 already indexed, 1452 dup keys remain (fall back to app checks)
            IF SQLCODE NOT IN (-955, -1408, -1452) THEN RAISE; END IF;
        END;
    END LOOP;
END;
/
