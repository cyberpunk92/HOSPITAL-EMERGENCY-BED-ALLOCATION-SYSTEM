-- ============================================================================
-- HEBAS - 02_seed.sql
-- Ordered seed data. MUST run on a fresh schema so IDENTITY values line up
-- with the explicit IDs referenced below (UserIDs, Ward_IDs, Bed_IDs).
-- Password_Hash values here are placeholders; run_db.py rewrites every user's
-- hash to a real Werkzeug hash of the default password after seeding.
-- Deviations from reference (intentional, documented in analysis):
--   * Admission 2 is assigned a single bed (ICU-02 / Bed 7); the tutorial's
--     redundant second assignment to Bed 5 is omitted to avoid double-booking.
--   * RBAC roles + assignments seeded (set-based from subclass membership).
--   * A few Complaint_Mapping + 1 Hospital row added for working dashboards.
-- ============================================================================

-- ============== 1. USERS (UserIDs 1..15) ==============
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Ali', 'Khan', 'ali.khan@hebas.pk', 'seed_pw', '03001234567', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Sara', 'Ahmed', 'sara.ahmed@hebas.pk', 'seed_pw', '03331234568', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Kamran', 'Malik', 'kamran.m@hebas.pk', 'seed_pw', '03451234569', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Fatima', 'Bibi', 'fatima.b@hebas.pk', 'seed_pw', '03111234570', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Usman', 'Tariq', 'usman.t@hebas.pk', 'seed_pw', '03211234571', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Ayesha', 'Noor', 'ayesha.n@hebas.pk', 'seed_pw', '03011234572', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Bilal', 'Hussain', 'bilal.h@hebas.pk', 'seed_pw', '03341234573', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Zainab', 'Raza', 'zainab.r@hebas.pk', 'seed_pw', '03461234574', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Omer', 'Farooq', 'omer.f@hebas.pk', 'seed_pw', '03121234575', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Hira', 'Shah', 'hira.s@hebas.pk', 'seed_pw', '03221234576', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Tariq', 'Javed', 'tariq.j@hebas.pk', 'seed_pw', '03021234577', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Nida', 'Yasir', 'nida.y@hebas.pk', 'seed_pw', '03351234578', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Qasim', 'Ali', 'qasim.a@hebas.pk', 'seed_pw', '03471234579', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Sana', 'Mir', 'sana.m@hebas.pk', 'seed_pw', '03131234580', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Fahad', 'Mustafa', 'fahad.m@hebas.pk', 'seed_pw', '03231234581', 1);

-- ============== 2. DOCTORS (UserIDs 1..5) ==============
INSERT INTO Doctor_Profiles (Doctor_ID, Specialization, License_No, Department, Shift_Timing) VALUES (1, 'Trauma Surgery', 'PMDC-1001', 'Emergency', 'Morning');
INSERT INTO Doctor_Profiles (Doctor_ID, Specialization, License_No, Department, Shift_Timing) VALUES (2, 'Cardiology', 'PMDC-1002', 'Emergency', 'Evening');
INSERT INTO Doctor_Profiles (Doctor_ID, Specialization, License_No, Department, Shift_Timing) VALUES (3, 'Neurology', 'PMDC-1003', 'Recovery', 'Night');
INSERT INTO Doctor_Profiles (Doctor_ID, Specialization, License_No, Department, Shift_Timing) VALUES (4, 'General Medicine', 'PMDC-1004', 'Emergency', 'Morning');
INSERT INTO Doctor_Profiles (Doctor_ID, Specialization, License_No, Department, Shift_Timing) VALUES (5, 'Pediatrics', 'PMDC-1005', 'Recovery', 'Evening');

-- ============== 3. WARDS (Ward_IDs 1..5) ==============
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (1, 'EMERGENCY', 20, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (1, 'EMERGENCY', 15, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'RECOVERY', 30, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'RECOVERY', 10, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 25, 0);

-- ============== 4. BEDS (Bed_IDs 1..15) ==============
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ER-01', 'Triage', 'Standard', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ER-02', 'Triage', 'Standard', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ER-03', 'Triage', 'Standard', 'OCCUPIED');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ER-04', 'Trauma Bay', 'Large', 'PENDING_CLEANING');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ER-05', 'Trauma Bay', 'Large', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ICU-01', 'Intensive Care', 'Standard', 'OCCUPIED');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ICU-02', 'Intensive Care', 'Standard', 'OCCUPIED');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ICU-03', 'Intensive Care', 'Standard', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('ICU-04', 'Intensive Care', 'Standard', 'PENDING_CLEANING');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('BW-01', 'Burn Care', 'Specialized', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('BW-02', 'Burn Care', 'Specialized', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('REC-01', 'General Recovery', 'Standard', 'OCCUPIED');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('REC-02', 'General Recovery', 'Standard', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('REC-03', 'General Recovery', 'Standard', 'AVAILABLE');
INSERT INTO Beds (Bed_Number, Bed_Type, Bed_Size, Current_Status) VALUES ('PED-01', 'Pediatric', 'Small', 'AVAILABLE');

-- ============== 5. PATIENTS (Patient_IDs 1..15) ==============
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Ahmad Raza', TO_DATE('1985-06-15','YYYY-MM-DD'), 'M', '37405-1111111-1', 'INS-1001', '03331112233');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Sadia Imran', TO_DATE('1992-04-20','YYYY-MM-DD'), 'F', '37405-2222222-2', 'INS-1002', '03002223344');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Zohaib Hassan', TO_DATE('1978-11-05','YYYY-MM-DD'), 'M', '37405-3333333-3', NULL, '03453334455');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Maryam Nawaz', TO_DATE('2001-08-30','YYYY-MM-DD'), 'F', '37405-4444444-4', 'INS-1004', '03114445566');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Kashif Mehmood', TO_DATE('1965-12-12','YYYY-MM-DD'), 'M', '37405-5555555-5', 'INS-1005', '03215556677');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Amna Gul', TO_DATE('1995-02-18','YYYY-MM-DD'), 'F', '37405-6666666-6', NULL, '03016667788');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Rizwan Waqar', TO_DATE('1988-09-25','YYYY-MM-DD'), 'M', '37405-7777777-7', 'INS-1007', '03347778899');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Sania Mirza', TO_DATE('1990-01-10','YYYY-MM-DD'), 'F', '37405-8888888-8', 'INS-1008', '03468889900');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Asad Umar', TO_DATE('1975-07-07','YYYY-MM-DD'), 'M', '37405-9999999-9', 'INS-1009', '03129990011');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Nida Yasir', TO_DATE('1982-05-14','YYYY-MM-DD'), 'F', '37405-1010101-0', NULL, '03221011122');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Taha Shah', TO_DATE('2005-03-22','YYYY-MM-DD'), 'M', '37405-1212121-1', 'INS-1011', '03022122233');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Bushra Ansari', TO_DATE('1960-10-30','YYYY-MM-DD'), 'F', '37405-1313131-2', 'INS-1012', '03353233344');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Imran Nazir', TO_DATE('1981-12-01','YYYY-MM-DD'), 'M', '37405-1414141-3', 'INS-1013', '03474344455');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Rabia Anum', TO_DATE('1998-06-08','YYYY-MM-DD'), 'F', '37405-1515151-4', NULL, '03135455566');
INSERT INTO Patient_Profile (Full_Name, Date_of_Birth, Gender, National_ID, Insurance_ID, Emergency_Contact) VALUES ('Faisal Qureshi', TO_DATE('1973-11-19','YYYY-MM-DD'), 'M', '37405-1616161-5', 'INS-1015', '03236566677');

-- ============== 6. MAINTENANCE STAFF (UserIDs 6,7,8) ==============
INSERT INTO Maintenance_Staff (Maintenance_ID, Shift_Timing, Assigned_Ward) VALUES (6, 'Morning', 1);
INSERT INTO Maintenance_Staff (Maintenance_ID, Shift_Timing, Assigned_Ward) VALUES (7, 'Evening', 3);
INSERT INTO Maintenance_Staff (Maintenance_ID, Shift_Timing, Assigned_Ward) VALUES (8, 'Night', 4);

-- ============== 7. WARD-BED ALLOCATION (Allocation 1..15) ==============
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 1, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 2, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 3, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 4, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (2, 5, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 6, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 7, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (1, 8, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (2, 9, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (4, 10, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (4, 11, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (3, 12, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (3, 13, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (3, 14, CURRENT_TIMESTAMP - INTERVAL '30' DAY);
INSERT INTO Ward_Bed_Allocation (Ward_ID, Bed_ID, Start_Time) VALUES (5, 15, CURRENT_TIMESTAMP - INTERVAL '30' DAY);

-- ============== 8. ADMISSIONS (Admission_IDs 1..7) ==============
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Admission_Status) VALUES (1, CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 5, 'Severe chest pain, suspected myocardial infarction', 2, 'ACTIVE');
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Admission_Status) VALUES (2, CURRENT_TIMESTAMP - INTERVAL '5' HOUR, 4, 'Blunt force trauma from motor vehicle accident', 1, 'ACTIVE');
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Admission_Status) VALUES (3, CURRENT_TIMESTAMP - INTERVAL '1' DAY, 3, 'High grade fever and shortness of breath', 4, 'ACTIVE');
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Discharge_Timestamp, Admission_Status) VALUES (4, CURRENT_TIMESTAMP - INTERVAL '3' DAY, 2, 'Minor laceration on right arm', 1, CURRENT_TIMESTAMP - INTERVAL '2' DAY, 'DISCHARGED');
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Admission_Status) VALUES (5, CURRENT_TIMESTAMP - INTERVAL '30' MINUTE, 5, 'Unresponsive, suspected stroke', 3, 'ACTIVE');
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Admission_Status) VALUES (6, CURRENT_TIMESTAMP, 5, 'Anaphylactic shock, difficulty breathing', NULL, 'ACTIVE');
INSERT INTO Admissions (Patient_ID, Arrival_Timestamp, Triage_Priority, Chief_Complaint, Assigned_Doctor, Admission_Status) VALUES (7, CURRENT_TIMESTAMP, 2, 'Sprained ankle', NULL, 'ACTIVE');

-- Diagnosis taken on admission 2 (demo data)
UPDATE Admissions SET Primary_Diagnosis = 'Compound Femur Fracture', Diagnosis_Timestamp = CURRENT_TIMESTAMP, Assigned_Doctor = 1 WHERE Admission_ID = 2;

-- ============== 9. BED ASSIGNMENTS (active patients only) ==============
INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status, Start_Time) VALUES (1, 6, 'CURRENT', CURRENT_TIMESTAMP - INTERVAL '1' HOUR);
INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status, Start_Time) VALUES (2, 7, 'CURRENT', CURRENT_TIMESTAMP - INTERVAL '4' HOUR);
INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status, Start_Time) VALUES (3, 12, 'CURRENT', CURRENT_TIMESTAMP - INTERVAL '20' HOUR);
INSERT INTO Bed_Assignments (Admission_ID, Bed_ID, Assignment_Status, Start_Time) VALUES (5, 3, 'CURRENT', CURRENT_TIMESTAMP - INTERVAL '15' MINUTE);

-- ============== 10. SANITIZATION LOGS ==============
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, Checking_Status, Equipment_Type) VALUES (4, 6, CURRENT_TIMESTAMP - INTERVAL '10' MINUTE, 'IN_PROGRESS', 'Bed Frame');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, Checking_Status, Equipment_Type) VALUES (9, 6, CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'PENDING_INSPECTION', 'ICU Bed Unit');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (1, 6, CURRENT_TIMESTAMP - INTERVAL '5' DAY, CURRENT_TIMESTAMP - INTERVAL '5' DAY + INTERVAL '2' HOUR, 'COMPLETED', 'Triage Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (2, 7, CURRENT_TIMESTAMP - INTERVAL '4' DAY, CURRENT_TIMESTAMP - INTERVAL '4' DAY + INTERVAL '1' HOUR, 'COMPLETED', 'Triage Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (5, 8, CURRENT_TIMESTAMP - INTERVAL '3' DAY, CURRENT_TIMESTAMP - INTERVAL '3' DAY + INTERVAL '3' HOUR, 'COMPLETED', 'Trauma Bay Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (6, 6, CURRENT_TIMESTAMP - INTERVAL '2' DAY, NULL, 'PENDING_INSPECTION', 'ICU Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (10, 7, CURRENT_TIMESTAMP - INTERVAL '1' DAY, CURRENT_TIMESTAMP - INTERVAL '1' DAY + INTERVAL '2' HOUR, 'COMPLETED', 'Burn Care Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (11, 8, CURRENT_TIMESTAMP - INTERVAL '12' HOUR, NULL, 'IN_PROGRESS', 'Burn Care Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (12, 6, CURRENT_TIMESTAMP - INTERVAL '6' HOUR, NULL, 'IN_PROGRESS', 'Recovery Bed');
INSERT INTO Sanitization_Logs (Bed_ID, Maintenance_ID, Start_Timestamp, End_Timestamp, Checking_Status, Equipment_Type) VALUES (15, 7, CURRENT_TIMESTAMP - INTERVAL '3' HOUR, NULL, 'PENDING_INSPECTION', 'Pediatric Bed');

-- ============== 11. USER_CONTACT (UserIDs 1..10) ==============
INSERT INTO User_Contact (UserID, Phone) VALUES (1, '03001234567');
INSERT INTO User_Contact (UserID, Phone) VALUES (2, '03331234568');
INSERT INTO User_Contact (UserID, Phone) VALUES (3, '03451234569');
INSERT INTO User_Contact (UserID, Phone) VALUES (4, '03111234570');
INSERT INTO User_Contact (UserID, Phone) VALUES (5, '03211234571');
INSERT INTO User_Contact (UserID, Phone) VALUES (6, '03011234572');
INSERT INTO User_Contact (UserID, Phone) VALUES (7, '03341234573');
INSERT INTO User_Contact (UserID, Phone) VALUES (8, '03461234574');
INSERT INTO User_Contact (UserID, Phone) VALUES (9, '03121234575');
INSERT INTO User_Contact (UserID, Phone) VALUES (10, '03221234576');

-- ============== 12. ADMIN STAFF (new UserIDs 16..23) ==============
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Zara', 'Iqbal', 'zara.i@hebas.pk', 'seed_pw', '03001112233', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Hassan', 'Butt', 'hassan.b@hebas.pk', 'seed_pw', '03331112234', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Maham', 'Zafar', 'maham.z@hebas.pk', 'seed_pw', '03451112235', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Adnan', 'Siddiqui', 'adnan.s@hebas.pk', 'seed_pw', '03111112236', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Laiba', 'Waheed', 'laiba.w@hebas.pk', 'seed_pw', '03211112237', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Saad', 'Nawaz', 'saad.n@hebas.pk', 'seed_pw', '03011112238', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Huma', 'Aslam', 'huma.a@hebas.pk', 'seed_pw', '03341112239', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Danish', 'Riaz', 'danish.r@hebas.pk', 'seed_pw', '03461112240', 1);
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (14, 'Administration', 'Senior', 'Level-3', 'Morning', 'Karachi', 'Block-5 Clifton', 'H-12');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (15, 'Finance', 'Junior', 'Level-1', 'Evening', 'Lahore', 'Gulberg III', 'H-45');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (16, 'HR', 'Mid', 'Level-2', 'Morning', 'Islamabad', 'F-7/2', 'H-8');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (17, 'IT', 'Senior', 'Level-3', 'Night', 'Rawalpindi', 'Saddar', 'H-3');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (18, 'Records', 'Junior', 'Level-1', 'Morning', 'Peshawar', 'Hayatabad', 'H-67');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (19, 'Operations', 'Mid', 'Level-2', 'Evening', 'Quetta', 'Jinnah Road', 'H-22');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (20, 'Administration', 'Senior', 'Level-3', 'Morning', 'Multan', 'Cantt Area', 'H-5');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (21, 'Finance', 'Mid', 'Level-2', 'Night', 'Faisalabad', 'D-Ground', 'H-14');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (22, 'HR', 'Junior', 'Level-1', 'Evening', 'Sialkot', 'Cantt', 'H-9');
INSERT INTO Admin_Staff (Admin_ID, Department, Seniority_Level, Access_Level, Duty_Timing, City, Street, House_No) VALUES (23, 'IT', 'Senior', 'Level-3', 'Morning', 'Hyderabad', 'Latifabad', 'H-31');

-- ============== 13. NURSES (new UserIDs 24..33) ==============
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Amna', 'Sohail', 'amna.soh@hebas.pk', 'seed_pw', '03001119901', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Rabia', 'Malik', 'rabia.mal@hebas.pk', 'seed_pw', '03331119902', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Kiran', 'Bano', 'kiran.b@hebas.pk', 'seed_pw', '03451119903', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Nadia', 'Saleem', 'nadia.sal@hebas.pk', 'seed_pw', '03111119904', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Saima', 'Aziz', 'saima.az@hebas.pk', 'seed_pw', '03211119905', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Hina', 'Farhan', 'hina.far@hebas.pk', 'seed_pw', '03011119906', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Maria', 'Qureshi', 'maria.qur@hebas.pk', 'seed_pw', '03341119907', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Shazia', 'Baig', 'shazia.b@hebas.pk', 'seed_pw', '03461119908', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Uzma', 'Toor', 'uzma.t@hebas.pk', 'seed_pw', '03121119909', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Faria', 'Noon', 'faria.n@hebas.pk', 'seed_pw', '03221119910', 1);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (24, 'Morning', 1);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (25, 'Evening', 1);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (26, 'Night', 2);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (27, 'Morning', 2);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (28, 'Evening', 3);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (29, 'Night', 3);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (30, 'Morning', 4);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (31, 'Evening', 4);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (32, 'Night', 5);
INSERT INTO Nurses (Nurse_ID, Shift_Timing, Assigned_Ward) VALUES (33, 'Morning', 5);

-- ============== 14. AMBULANCE DISPATCHERS (new UserIDs 34..43) ==============
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Tariq', 'Mehmood', 'tariq.meh@hebas.pk', 'seed_pw', '03001231101', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Asif', 'Chaudhry', 'asif.ch@hebas.pk', 'seed_pw', '03331231102', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Ghulam', 'Abbas', 'ghulam.a@hebas.pk', 'seed_pw', '03451231103', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Sameer', 'Lodhi', 'sameer.l@hebas.pk', 'seed_pw', '03111231104', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Junaid', 'Akram', 'junaid.ak@hebas.pk', 'seed_pw', '03211231105', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Pervez', 'Gilani', 'pervez.g@hebas.pk', 'seed_pw', '03011231106', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Rohail', 'Hayat', 'rohail.h@hebas.pk', 'seed_pw', '03341231107', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Shehzad', 'Roy', 'shehzad.r@hebas.pk', 'seed_pw', '03461231108', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Waqas', 'Channa', 'waqas.ch@hebas.pk', 'seed_pw', '03121231109', 1);
INSERT INTO HEBAS_Users (FName, LName, Email, Password_Hash, Phone, Is_Active) VALUES ('Nadeem', 'Babar', 'nadeem.b@hebas.pk', 'seed_pw', '03221231110', 1);
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (34, 'M', 'Advanced Life Support');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (35, 'M', 'Basic Life Support');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (36, 'M', 'Neonatal Transport');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (37, 'M', 'Advanced Life Support');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (38, 'M', 'Basic Life Support');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (39, 'M', 'Air Ambulance');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (40, 'M', 'Advanced Life Support');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (41, 'M', 'Basic Life Support');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (42, 'M', 'Bariatric Transport');
INSERT INTO Ambulance_Dispatcher (AD_ID, Gender, Ambulance_Type) VALUES (43, 'M', 'Advanced Life Support');
INSERT INTO Service_Dispatcher (SD_ID, Service_Name, Contact_Radio, Shift_Timing, Assigned_Region) VALUES (34, 'Rescue 1122', 'CH-01', 'Morning', 'Lahore Central');
INSERT INTO Service_Dispatcher (SD_ID, Service_Name, Contact_Radio, Shift_Timing, Assigned_Region) VALUES (35, 'Edhi Foundation', 'CH-02', 'Evening', 'Karachi South');
INSERT INTO Service_Dispatcher (SD_ID, Service_Name, Contact_Radio, Shift_Timing, Assigned_Region) VALUES (36, 'Chhipa Welfare', 'CH-03', 'Night', 'Karachi East');
INSERT INTO Service_Dispatcher (SD_ID, Service_Name, Contact_Radio, Shift_Timing, Assigned_Region) VALUES (37, 'Rescue 1122', 'CH-04', 'Morning', 'Rawalpindi');
INSERT INTO Service_Dispatcher (SD_ID, Service_Name, Contact_Radio, Shift_Timing, Assigned_Region) VALUES (38, 'PRCS Ambulance', 'CH-05', 'Evening', 'Islamabad');
INSERT INTO Individual_Dispatcher (ID_ID, Contact_No, Location) VALUES (39, '03011231106', 'Gulberg, Lahore');
INSERT INTO Individual_Dispatcher (ID_ID, Contact_No, Location) VALUES (40, '03341231107', 'DHA Phase 2, Karachi');
INSERT INTO Individual_Dispatcher (ID_ID, Contact_No, Location) VALUES (41, '03461231108', 'F-8 Markaz, Islamabad');
INSERT INTO Individual_Dispatcher (ID_ID, Contact_No, Location) VALUES (42, '03121231109', 'Saddar, Peshawar');
INSERT INTO Individual_Dispatcher (ID_ID, Contact_No, Location) VALUES (43, '03221231110', 'Cantt, Quetta');

-- ============== 15. WARD MANAGERS ==============
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (1, 1, 'Head of Emergency');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (2, 2, 'Deputy Emergency Manager');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (3, 3, 'Recovery Ward Lead');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (4, 4, 'Burn Unit Coordinator');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (5, 5, 'Pediatric Ward Head');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (1, 14, 'Admin Liaison - ER');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (2, 15, 'Admin Liaison - ER2');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (3, 16, 'Admin Liaison - Recovery');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (4, 17, 'IT Support - Burn Unit');
INSERT INTO Ward_Manager (Ward_ID, UserID, Role) VALUES (5, 18, 'Records - Pediatric');

-- ============== 16. EMERGENCY_ROOM (+ wards 6..13) ==============
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (1, 5, 10, 25);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (2, 4, 8, 20);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (1, 'EMERGENCY', 12, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (1, 'EMERGENCY', 18, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'EMERGENCY', 8, 0);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (6, 3, 6, 15);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (7, 5, 9, 22);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (8, 4, 7, 18);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'EMERGENCY', 14, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'EMERGENCY', 20, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'EMERGENCY', 10, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'EMERGENCY', 16, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (1, 'EMERGENCY', 11, 0);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (9, 3, 5, 12);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (10, 5, 11, 28);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (11, 2, 4, 10);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (12, 4, 8, 20);
INSERT INTO Emergency_Room (Ward_ID, Priority_Level, High_Concern_Patient_Capacity, Total_Staff) VALUES (13, 1, 3, 8);

-- ============== 17. RECOVERY_ROOM (+ wards 14..20) ==============
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (3, 'General', 0, 1, 0, 20);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (4, 'Burn', 1, 0, 0, 15);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (5, 'Pediatric', 0, 0, 1, 18);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 20, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 15, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'RECOVERY', 12, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'RECOVERY', 10, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'RECOVERY', 25, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'RECOVERY', 8, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'RECOVERY', 30, 0);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (14, 'Trauma', 0, 1, 0, 22);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (15, 'Medical', 0, 1, 0, 17);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (16, 'Burn', 1, 0, 0, 14);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (17, 'Pediatric', 0, 0, 1, 16);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (18, 'General', 0, 1, 0, 19);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (19, 'Trauma', 0, 1, 0, 21);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (20, 'Medical', 0, 1, 0, 23);

-- ============== 18. MEDICAL_WARD (+ wards 21..27) ==============
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (15, 1);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (18, 0);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (20, 1);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 14, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'RECOVERY', 16, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'RECOVERY', 18, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'RECOVERY', 22, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 20, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'RECOVERY', 12, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'RECOVERY', 10, 0);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (21, 'Medical', 0, 1, 0, 14);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (22, 'Medical', 0, 1, 0, 16);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (23, 'Medical', 0, 1, 0, 18);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (24, 'Medical', 0, 1, 0, 12);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (25, 'Medical', 0, 1, 0, 20);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (26, 'Medical', 0, 1, 0, 15);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (27, 'Medical', 0, 1, 0, 17);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (21, 0);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (22, 1);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (23, 0);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (24, 1);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (25, 1);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (26, 0);
INSERT INTO Medical_Ward (Ward_ID, Chronic_Condition_Flag) VALUES (27, 1);

-- ============== 19. PEDIATRIC_WARD (+ wards 28..35) ==============
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (5, 'ALLOWED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (17, 'RESTRICTED');
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'RECOVERY', 10, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 12, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'RECOVERY', 8, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'RECOVERY', 14, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (2, 'RECOVERY', 16, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (3, 'RECOVERY', 9, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (4, 'RECOVERY', 11, 0);
INSERT INTO Wards (Floor_Number, Ward_Type, Total_Capacity, Current_Capacity) VALUES (5, 'RECOVERY', 13, 0);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (28, 'Pediatric', 0, 0, 1, 12);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (29, 'Pediatric', 0, 0, 1, 10);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (30, 'Pediatric', 0, 0, 1, 14);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (31, 'Pediatric', 0, 0, 1, 11);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (32, 'Pediatric', 0, 0, 1, 13);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (33, 'Pediatric', 0, 0, 1, 9);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (34, 'Pediatric', 0, 0, 1, 15);
INSERT INTO Recovery_Room (Ward_ID, Recovery_Type, Is_Burn_Ward, Is_Trauma_Or_Medical, Is_Pediatrics, Total_Staff) VALUES (35, 'Pediatric', 0, 0, 1, 16);
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (28, 'ALLOWED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (29, 'ALLOWED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (30, 'RESTRICTED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (31, 'ALLOWED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (32, 'RESTRICTED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (33, 'ALLOWED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (34, 'RESTRICTED');
INSERT INTO Pediatric_Ward (Ward_ID, Parental_Accompaniment_Status) VALUES (35, 'ALLOWED');

-- ============== 20. EQUIPMENT (Equipment_IDs 1..10) ==============
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Ventilator A', 'Respiratory', 'Large', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('ECG Monitor', 'Cardiac', 'Medium', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Defibrillator', 'Cardiac', 'Medium', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('IV Pump', 'Infusion', 'Small', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Ultrasound Machine', 'Imaging', 'Large', 'MAINTENANCE');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('X-Ray Unit', 'Imaging', 'XLarge', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Suction Machine', 'Surgical', 'Medium', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Pulse Oximeter', 'Monitoring', 'Small', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Burn Dressing Kit', 'Wound Care', 'Small', 'FUNCTIONAL');
INSERT INTO Equipment (Equipment_Name, Equipment_Type, Size_Area, Status) VALUES ('Crash Cart', 'Emergency', 'Large', 'FUNCTIONAL');

-- ============== 21. WARD_EQUIPMENT ==============
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (1, 1, 3);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (1, 2, 5);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (1, 3, 2);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (1, 4, 8);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (2, 5, 1);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (2, 6, 1);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (3, 7, 2);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (4, 9, 10);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (4, 8, 6);
INSERT INTO Ward_Equipment (Ward_ID, Equipment_ID, Quantity) VALUES (1, 10, 2);

-- ============== 22. BED FEATURES ==============
INSERT INTO Bed_Feature (Feature_Name) VALUES ('CALL_BUTTON');
INSERT INTO Bed_Feature (Feature_Name) VALUES ('SIDE_TABLE');
INSERT INTO Bed_Feature (Feature_Name) VALUES ('GLUCOSE_STRIP');
INSERT INTO Bed_Feature (Feature_Name) VALUES ('BP_MACHINE');
INSERT INTO Bed_Buttons (Feature_Name, Button_Types) VALUES ('CALL_BUTTON', 'Nurse Call, Code Blue, Code Red');
INSERT INTO Side_Table (Feature_Name, Side_Table_Category) VALUES ('SIDE_TABLE', 'Foldable');
INSERT INTO Glucose_Strip (Feature_Name, Size_Strip) VALUES ('GLUCOSE_STRIP', '50-Strip Pack');
INSERT INTO BP_Machine (Feature_Name, BP_Category) VALUES ('BP_MACHINE', 'Digital Automatic');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (1, 'CALL_BUTTON');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (1, 'SIDE_TABLE');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (2, 'CALL_BUTTON');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (3, 'CALL_BUTTON');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (3, 'BP_MACHINE');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (4, 'GLUCOSE_STRIP');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (5, 'CALL_BUTTON');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (6, 'BP_MACHINE');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (6, 'CALL_BUTTON');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (7, 'SIDE_TABLE');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (8, 'GLUCOSE_STRIP');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (9, 'CALL_BUTTON');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (10, 'BP_MACHINE');
INSERT INTO Bed_Feature_Assignment (Bed_ID, Feature_Name) VALUES (10, 'SIDE_TABLE');

-- ============== 23. COMPLAINT MAPPING (drives Auto_Assign_Doctor) ==============
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Severe chest pain, suspected myocardial infarction', 1, 2);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Blunt force trauma from motor vehicle accident', 1, 1);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('High grade fever and shortness of breath', 3, 4);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Unresponsive, suspected stroke', 2, 3);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Anaphylactic shock, difficulty breathing', 1, 2);
INSERT INTO Complaint_Mapping (Complaint_Name, Recommended_Ward_ID, Recommended_Doctor_ID) VALUES ('Sprained ankle', 1, 4);

-- ============== 24. HOSPITAL (dashboard summary row) ==============
INSERT INTO Hospitals (Hospital_Name, Total_Beds, Occupied_Beds, Available_Beds) VALUES ('HEBAS Central Hospital', 15, 4, 8);

-- ============== 25. RBAC ROLES + ASSIGNMENTS ==============
INSERT INTO User_Roles (Role_Name) VALUES ('Admin Staff');
INSERT INTO User_Roles (Role_Name) VALUES ('Emergency Doctor');
INSERT INTO User_Roles (Role_Name) VALUES ('Ward Doctor');
INSERT INTO User_Roles (Role_Name) VALUES ('Nurse');
INSERT INTO User_Roles (Role_Name) VALUES ('Ambulance Dispatcher');
INSERT INTO User_Roles (Role_Name) VALUES ('Service Dispatcher');
INSERT INTO User_Roles (Role_Name) VALUES ('Maintenance Staff');
INSERT INTO User_Roles (Role_Name) VALUES ('Patient');

-- Assign roles from subclass membership (set-based)
INSERT INTO User_Role_Assignment (UserID, Role_ID)
    SELECT d.Doctor_ID, r.Role_ID FROM Doctor_Profiles d
    JOIN User_Roles r ON r.Role_Name = CASE WHEN UPPER(d.Department) = 'EMERGENCY' THEN 'Emergency Doctor' ELSE 'Ward Doctor' END;

INSERT INTO User_Role_Assignment (UserID, Role_ID)
    SELECT n.Nurse_ID, r.Role_ID FROM Nurses n JOIN User_Roles r ON r.Role_Name = 'Nurse';

INSERT INTO User_Role_Assignment (UserID, Role_ID)
    SELECT a.Admin_ID, r.Role_ID FROM Admin_Staff a JOIN User_Roles r ON r.Role_Name = 'Admin Staff';

INSERT INTO User_Role_Assignment (UserID, Role_ID)
    SELECT m.Maintenance_ID, r.Role_ID FROM Maintenance_Staff m JOIN User_Roles r ON r.Role_Name = 'Maintenance Staff';

INSERT INTO User_Role_Assignment (UserID, Role_ID)
    SELECT s.SD_ID, r.Role_ID FROM Service_Dispatcher s JOIN User_Roles r ON r.Role_Name = 'Service Dispatcher';

INSERT INTO User_Role_Assignment (UserID, Role_ID)
    SELECT ad.AD_ID, r.Role_ID FROM Ambulance_Dispatcher ad
    JOIN User_Roles r ON r.Role_Name = 'Ambulance Dispatcher'
    WHERE ad.AD_ID NOT IN (SELECT SD_ID FROM Service_Dispatcher);

COMMIT;
