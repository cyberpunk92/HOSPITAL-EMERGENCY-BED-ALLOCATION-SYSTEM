-- ============================================================================
-- HEBAS - 03_programmable.sql
-- Views, procedures, triggers. Created AFTER seeding so that
-- TRG_Validate_Bed_Assignment (which requires a diagnosis before bed
-- assignment) does not block the historical seed data.
-- De-dup vs reference: only one "occupy bed on assignment" trigger is kept
-- (TRG_Auto_Occupy_Bed); the duplicate TRG_Bed_Occupy is dropped.
-- Views end with ';'. PL/SQL blocks end with a lone '/'.
-- ============================================================================

-- -------------------- VIEWS --------------------
CREATE OR REPLACE VIEW View_Public_Bed_Availability AS
SELECT w.Ward_ID, w.Ward_Type, b.Bed_ID, b.Bed_Number, b.Current_Status
FROM Wards w
JOIN Ward_Bed_Allocation wba ON w.Ward_ID = wba.Ward_ID
JOIN Beds b ON wba.Bed_ID = b.Bed_ID
WHERE b.Current_Status = 'AVAILABLE' AND wba.End_Time IS NULL;

CREATE OR REPLACE VIEW View_Ward_Capacity_Summary AS
SELECT w.Ward_ID, w.Ward_Type, w.Total_Capacity,
       COUNT(CASE WHEN b.Current_Status = 'OCCUPIED' THEN 1 END) AS Beds_Occupied,
       COUNT(CASE WHEN b.Current_Status = 'AVAILABLE' THEN 1 END) AS Beds_Available,
       COUNT(CASE WHEN b.Current_Status = 'PENDING_CLEANING' THEN 1 END) AS Beds_In_Maintenance,
       CURRENT_TIMESTAMP AS Last_Updated
FROM Wards w
LEFT JOIN Ward_Bed_Allocation wba ON w.Ward_ID = wba.Ward_ID AND wba.End_Time IS NULL
LEFT JOIN Beds b ON wba.Bed_ID = b.Bed_ID
GROUP BY w.Ward_ID, w.Ward_Type, w.Total_Capacity;

CREATE OR REPLACE VIEW View_Active_Triage_List AS
SELECT a.Admission_ID, p.Full_Name, p.Gender, a.Arrival_Timestamp,
       a.Triage_Priority, a.Chief_Complaint
FROM Admissions a
JOIN Patient_Profile p ON a.Patient_ID = p.Patient_ID
WHERE a.Admission_Status = 'ACTIVE' AND a.Assigned_Doctor IS NULL
ORDER BY a.Triage_Priority DESC, a.Arrival_Timestamp ASC;

CREATE OR REPLACE VIEW View_Hospital_Capacity AS
SELECT w.Ward_ID, w.Ward_Type,
       COUNT(b.Bed_ID) AS Total_Beds,
       SUM(CASE WHEN b.Current_Status = 'OCCUPIED'  THEN 1 ELSE 0 END) AS Occupied_Beds,
       SUM(CASE WHEN b.Current_Status = 'AVAILABLE' THEN 1 ELSE 0 END) AS Available_Beds
FROM Wards w
JOIN Ward_Bed_Allocation wb ON w.Ward_ID = wb.Ward_ID
JOIN Beds b ON wb.Bed_ID = b.Bed_ID
GROUP BY w.Ward_ID, w.Ward_Type;

-- -------------------- PROCEDURES --------------------
CREATE OR REPLACE PROCEDURE Auto_Assign_Doctor (p_Admission_ID NUMBER)
AS
    v_complaint VARCHAR2(255);
    v_doctor    NUMBER;
BEGIN
    SELECT Chief_Complaint INTO v_complaint
    FROM Admissions WHERE Admission_ID = p_Admission_ID;

    SELECT Recommended_Doctor_ID INTO v_doctor
    FROM Complaint_Mapping WHERE UPPER(Complaint_Name) = UPPER(v_complaint);

    UPDATE Admissions SET Assigned_Doctor = v_doctor
    WHERE Admission_ID = p_Admission_ID;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        NULL; -- no mapping; leave unassigned for manual triage
END;
/

CREATE OR REPLACE PROCEDURE Create_Notification (p_user NUMBER, p_message VARCHAR2)
AS
BEGIN
    INSERT INTO Notifications (User_ID, Message) VALUES (p_user, p_message);
END;
/

-- -------------------- TRIGGERS --------------------
-- Gatekeeper: a bed cannot be assigned without a diagnosis and must be free.
CREATE OR REPLACE TRIGGER TRG_Validate_Bed_Assignment
BEFORE INSERT ON Bed_Assignments
FOR EACH ROW
DECLARE
    v_diagnosis  VARCHAR2(255);
    v_bed_status VARCHAR2(20);
BEGIN
    SELECT Primary_Diagnosis INTO v_diagnosis
    FROM Admissions WHERE Admission_ID = :NEW.Admission_ID;

    IF v_diagnosis IS NULL THEN
        RAISE_APPLICATION_ERROR(-20001, 'Patient must have a Primary Diagnosis before a bed can be assigned.');
    END IF;

    SELECT Current_Status INTO v_bed_status
    FROM Beds WHERE Bed_ID = :NEW.Bed_ID;

    IF v_bed_status != 'AVAILABLE' THEN
        RAISE_APPLICATION_ERROR(-20002, 'Bed ' || :NEW.Bed_ID || ' is currently ' || v_bed_status || ' and cannot be assigned.');
    END IF;
END;
/

-- Occupy the bed once an assignment is created (single canonical trigger).
CREATE OR REPLACE TRIGGER TRG_Auto_Occupy_Bed
AFTER INSERT ON Bed_Assignments
FOR EACH ROW
BEGIN
    UPDATE Beds SET Current_Status = 'OCCUPIED' WHERE Bed_ID = :NEW.Bed_ID;
END;
/

-- On discharge: close the bed assignment, flag bed for cleaning, dispatch a
-- sanitization log to the first available maintenance staff member.
CREATE OR REPLACE TRIGGER TRG_Auto_Discharge_Workflow
AFTER UPDATE OF Discharge_Timestamp ON Admissions
FOR EACH ROW
WHEN (NEW.Discharge_Timestamp IS NOT NULL AND OLD.Discharge_Timestamp IS NULL)
DECLARE
    v_bed_id         NUMBER;
    v_maintenance_id NUMBER;
BEGIN
    SELECT Bed_ID INTO v_bed_id
    FROM Bed_Assignments
    WHERE Admission_ID = :NEW.Admission_ID AND Assignment_Status = 'CURRENT';

    UPDATE Bed_Assignments
    SET Assignment_Status = 'COMPLETED', End_Time = :NEW.Discharge_Timestamp
    WHERE Admission_ID = :NEW.Admission_ID AND Assignment_Status = 'CURRENT';

    UPDATE Beds SET Current_Status = 'PENDING_CLEANING' WHERE Bed_ID = v_bed_id;

    SELECT MIN(Maintenance_ID) INTO v_maintenance_id FROM Maintenance_Staff;

    INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, Checking_Status)
    VALUES (v_bed_id, v_maintenance_id, CURRENT_TIMESTAMP, 'IN_PROGRESS');
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        NULL; -- patient had no physical bed; discharge normally
END;
/

-- Audit every bed status change.
CREATE OR REPLACE TRIGGER TRG_Audit_Bed_Status
AFTER UPDATE OF Current_Status ON Beds
FOR EACH ROW
WHEN (NEW.Current_Status != OLD.Current_Status)
BEGIN
    INSERT INTO Audit_Trails (Action_Type, Table_Name, Record_ID, Old_Value, New_Value)
    VALUES ('UPDATE', 'Beds', :NEW.Bed_ID, :OLD.Current_Status, :NEW.Current_Status);
END;
/

-- Notify admin when an admission is marked DISCHARGED.
CREATE OR REPLACE TRIGGER TRG_Discharge_Notification
AFTER UPDATE OF Admission_Status ON Admissions
FOR EACH ROW
WHEN (NEW.Admission_Status = 'DISCHARGED')
BEGIN
    INSERT INTO Notifications (User_ID, Message)
    VALUES (14, 'Patient discharged and bed requires sanitization.');
END;
/
