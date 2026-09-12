# 🏥 Hospital Emergency Bed Allocation System (HEBAS)

HEBAS is a comprehensive, role-based web application designed to streamline the management of emergency hospital beds, patient admissions, and inter-departmental coordination. 

Developed as a robust database and software engineering solution, HEBAS ensures real-time tracking of bed availability, seamless staff communication, and efficient patient routing during critical emergency scenarios.

## ✨ Key Features

* **Role-Based Access Control (RBAC):** Tailored dashboards and permissions for Admins, Doctors, Nurses, Dispatchers, and Maintenance/Sanitization staff.
* **Real-Time Bed Tracking:** Monitor ward capacities, bed statuses (Available, Occupied, Maintenance, Cleaning), and automated bed allocation.
* **Patient & Admission Management:** End-to-end tracking of patient data from triage to discharge.
* **Automated Workflow Triggers:** SQL-level triggers and procedures to handle automated status updates and readiness checks.
* **Analytics & Reporting:** Exportable admissions and operational reports (CSV format).

## 📸 Comprehensive System Walkthrough

### 🔐 Authentication & UI Components
![Login Screen](screenshots/01_login.png)
![Mobile Sidebar](screenshots/13_mobile_sidebar.png)
![System Toasts & Notifications](screenshots/adm_toast.png)

### 👑 Administrator & Management
![Admin Dashboard 1](screenshots/02_admin_dashboard.png)
![Admin Dashboard 2](screenshots/adm_dashboard.png)
![Admin Dashboard 3](screenshots/dash_admin.png)
![Admin Ref View](screenshots/ref2_admin.png)
![Admin Users](screenshots/03_admin_users.png)
![Admin Staff Management](screenshots/adm_staff.png)
![System Reports](screenshots/06_reports.png)

### 🛏️ Admissions, Patients & Bed Allocation
![Admissions Management](screenshots/04_admissions.png)
![Bed Allocation](screenshots/05_beds.png)
![Patients Page 1](screenshots/patients_page.png)
![Patients Page 2](screenshots/adm_patients.png)

### 🩺 Medical Staff (Doctors & Nurses)
![Doctor Dashboard 1](screenshots/07_doctor.png)
![Emergency Doctor Dashboard](screenshots/dash_edoctor.png)
![Ward Doctor Dashboard](screenshots/dash_wdoctor.png)
![Nurse Dashboard 1](screenshots/08_nurse.png)
![Nurse Dashboard 2](screenshots/dash_nurse.png)

### 🚑 Dispatch & Logistics
![Dispatcher Overview 1](screenshots/09_dispatcher.png)
![Dispatcher Overview 2](screenshots/dash_dispatcher.png)

### 🧹 Maintenance & Sanitization
![Maintenance Dashboard 1](screenshots/10_maintenance.png)
![Maintenance Dashboard 2](screenshots/dash_maintenance.png)
![Sanitization Dashboard](screenshots/dash_sanitization.png)

### 👤 Patient Portal
![Patient Portal 1](screenshots/11_patient_portal.png)
![Patient Portal 2](screenshots/patient_portal.png)
![Patient Portal Dashboard](screenshots/dash_patient.png)
![Patient Reference View](screenshots/ref_patient.png)
![Patient Details](screenshots/12_patient_detail.png)

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** SQL (Normalized relational models with Enhanced ER diagrams, triggers, and stored procedures)
* **Frontend:** HTML, CSS, JavaScript (Responsive templates)

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* A supported SQL database server (e.g., Oracle SQL Developer / MySQL)

### Installation

1. **Clone the repository**
   ```bash
   git clone [https://github.com/cyberpunk92/HOSPITAL-EMERGENCY-BED-ALLOCATION-SYSTEM.git](https://github.com/cyberpunk92/HOSPITAL-EMERGENCY-BED-ALLOCATION-SYSTEM.git)
   cd HOSPITAL-EMERGENCY-BED-ALLOCATION-SYSTEM
