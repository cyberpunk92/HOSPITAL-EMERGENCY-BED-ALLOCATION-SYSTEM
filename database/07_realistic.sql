-- ============================================================================
-- HEBAS - 07_realistic.sql
-- Readable ward names + clean complaint mapping + clean realistic reseed.
-- Additive schema (Ward_Name); preserves all views/triggers/procedures/packages.
-- Dynamic + patient data is WIPED and replaced with realistic data (confirmed).
-- Apply: venv\Scripts\python.exe database\run_db.py --apply 07_realistic.sql
-- ============================================================================

-- 1. Ward_Name column ---------------------------------------------------------
BEGIN
    BEGIN EXECUTE IMMEDIATE 'ALTER TABLE Wards ADD Ward_Name VARCHAR2(60)';
    EXCEPTION WHEN OTHERS THEN IF SQLCODE NOT IN (-1430) THEN RAISE; END IF; END;
END;
/

-- 2. Designate 5 emergency specialty wards + 1 medical; readable names ---------
UPDATE Wards SET Ward_Type='EMERGENCY', Ward_Name='Emergency - Cardiac Ward'   WHERE Ward_ID=1;
UPDATE Wards SET Ward_Type='EMERGENCY', Ward_Name='Emergency - Trauma Ward'    WHERE Ward_ID=2;
UPDATE Wards SET Ward_Type='EMERGENCY', Ward_Name='Emergency - Burn Ward'      WHERE Ward_ID=3;
UPDATE Wards SET Ward_Type='EMERGENCY', Ward_Name='Emergency - Pediatric Ward' WHERE Ward_ID=4;
UPDATE Wards SET Ward_Type='EMERGENCY', Ward_Name='Emergency - Neurology Ward' WHERE Ward_ID=5;
UPDATE Wards SET Ward_Name='Medical Ward' WHERE Ward_ID=15;
UPDATE Wards SET Ward_Name = INITCAP(Ward_Type) || ' Ward ' || LPAD(Ward_ID, 2, '0')
WHERE Ward_Name IS NULL;
COMMIT;

-- 3. Clean complaint mapping (readable complaint -> specialty ward + ER doctor)-
DELETE FROM Complaint_Mapping;
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Chest Pain', 1, 2);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Accident', 2, 1);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Burn Injury', 3, 4);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Child Emergency', 4, 4);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Stroke/Seizure', 5, 2);
COMMIT;

-- 4. Wipe dynamic + patient data (FK-safe). Staff + structure preserved. -------
DELETE FROM Glucose_Strip_Results;
DELETE FROM Patient_Vitals;
DELETE FROM Medical_Measurements;
DELETE FROM Nurse_Tasks;
DELETE FROM Nurse_Assignments;
DELETE FROM Doctor_Assignment_History;
DELETE FROM Patient_Priority;
DELETE FROM Bed_Assignments;
DELETE FROM Bed_Status_History;
DELETE FROM Patient_Transfers;
DELETE FROM Sanitization_Logs;
DELETE FROM Admissions;
DELETE FROM Arrival_Queue;
DELETE FROM Notifications;
DELETE FROM Ambulance_Cases;
-- remove patient login accounts cleanly
UPDATE Patient_Profile SET User_ID = NULL;
DELETE FROM User_Role_Assignment
 WHERE Role_ID = (SELECT Role_ID FROM User_Roles WHERE Role_Name = 'Patient');
DELETE FROM HEBAS_Users
 WHERE UserID NOT IN (SELECT UserID FROM User_Role_Assignment)
   AND (LOWER(Email) LIKE '%patient%' OR LOWER(Email) LIKE '%gmail%');
DELETE FROM Patient_Profile;
UPDATE Beds SET Current_Status = 'AVAILABLE';
COMMIT;

-- 5. Realistic reseed: 20 patients, 3 ER doctors (1,2,4), realistic complaints -
DECLARE
    TYPE t_str IS TABLE OF VARCHAR2(100);
    names t_str := t_str(
        'Ahmed Raza','Bilal Khan','Sana Tariq','Hina Malik','Usman Ali',
        'Ayesha Noor','Imran Sheikh','Fatima Zahra','Kamran Akmal','Maria Wasim',
        'Tariq Mehmood','Nadia Hassan','Saad Iqbal','Rabia Sultan','Faisal Iqbal',
        'Zara Ahmed','Hamza Yousaf','Komal Riaz','Adnan Siddiqui','Maham Butt');
    complaints t_str := t_str('Chest Pain','Accident','Burn Injury','Child Emergency','Stroke/Seizure');
    diags      t_str := t_str('Acute coronary syndrome','Multiple trauma','Second-degree burns','Pediatric respiratory distress','Suspected ischemic stroke');
    docs       t_str := t_str('1','2','4');
    v_pid NUMBER; v_aid NUMBER; v_doc NUMBER; v_ward NUMBER; v_bed NUMBER;
    v_idx NUMBER;
BEGIN
    FOR i IN 1 .. names.COUNT LOOP
        v_idx := MOD(i - 1, complaints.COUNT) + 1;
        v_doc := TO_NUMBER(docs(MOD(i - 1, docs.COUNT) + 1));

        INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact, Is_Active)
        VALUES (names(i),
                TO_DATE('19' || LPAD(60 + MOD(i, 35), 2, '0') || '-' || LPAD(MOD(i, 12) + 1, 2, '0') || '-' || LPAD(MOD(i, 27) + 1, 2, '0'), 'YYYY-MM-DD'),
                CASE WHEN MOD(i, 2) = 0 THEN 'F' ELSE 'M' END,
                '3520' || LPAD(i, 2, '0') || TO_CHAR(1000000 + i * 37),
                'INS-' || (2000 + i), '03' || LPAD(100000000 + i * 131, 9, '0'), 1)
        RETURNING Patient_ID INTO v_pid;

        SELECT Recommended_Ward_ID INTO v_ward FROM Complaint_Mapping WHERE Complaint_Name = complaints(v_idx);

        INSERT INTO Admissions (Patient_ID, Triage_Priority, Chief_Complaint, Assigned_Doctor,
                                Primary_Diagnosis, Diagnosis_Timestamp, Admission_Status)
        VALUES (v_pid, 2 + MOD(i, 4), complaints(v_idx), v_doc, diags(v_idx), CURRENT_TIMESTAMP, 'ACTIVE')
        RETURNING Admission_ID INTO v_aid;

        INSERT INTO Doctor_Assignment_History (Admission_ID, Doctor_ID, Assignment_Time)
        VALUES (v_aid, v_doc, CURRENT_TIMESTAMP);

        -- Admit the first 12 and auto-assign a bed in the recommended ward.
        IF i <= 12 THEN
            UPDATE Admissions SET Admit_Status = 'ADMITTED' WHERE Admission_ID = v_aid;
            BEGIN
                SELECT b.Bed_ID INTO v_bed
                FROM Beds b
                JOIN Ward_Bed_Allocation wba ON wba.Bed_ID = b.Bed_ID AND wba.End_Time IS NULL
                WHERE wba.Ward_ID = v_ward AND b.Current_Status = 'AVAILABLE'
                FETCH FIRST 1 ROWS ONLY;
                INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status)
                VALUES (v_aid, v_bed, 'CURRENT');   -- triggers set OCCUPIED + capacity
            EXCEPTION WHEN NO_DATA_FOUND THEN NULL;  -- no bed: patient waits
            END;
        END IF;
    END LOOP;
    COMMIT;
END;
/

-- 6. Assign 2 patients from each doctor to the 2 nurses (24, 25) + sample tasks-
DECLARE
    v_seq NUMBER := 0;
    v_nurse NUMBER;
BEGIN
    FOR rec IN (
        SELECT Admission_ID,
               ROW_NUMBER() OVER (PARTITION BY Assigned_Doctor ORDER BY Admission_ID) rn
        FROM Admissions WHERE Admit_Status = 'ADMITTED'
    ) LOOP
        IF rec.rn <= 2 THEN
            v_nurse := 24 + MOD(v_seq, 2);
            INSERT INTO Nurse_Assignments (Nurse_ID, Admission_ID) VALUES (v_nurse, rec.Admission_ID);
            INSERT INTO Nurse_Tasks (Admission_ID, Nurse_ID, Task_Type, Task_Status)
            VALUES (rec.Admission_ID, v_nurse, 'BP Check', 'PENDING');
            INSERT INTO Nurse_Tasks (Admission_ID, Nurse_ID, Task_Type, Task_Status)
            VALUES (rec.Admission_ID, v_nurse, 'Sugar Check', 'PENDING');
            v_seq := v_seq + 1;
        END IF;
    END LOOP;
    COMMIT;
END;
/

-- 7. Refresh hospital summary -------------------------------------------------
BEGIN
    PR_GENERATE_DAILY_REPORT;
    COMMIT;
END;
/
