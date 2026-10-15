# 🏥 Aarogya Life - Hospital & Clinic Appointment & Billing System

A complete, production-grade, and modern **Hospital & Clinic Management ERP System** developed with Python, Flask, SQLite, Tailwind CSS, and Chart.js.

> **फोकस:** Patients, Doctors, Specializations, Appointments और Billing tracking का पूरा automatic & interactive solution.

---

## 🌟 Key Features (मुख्य विशेषताएं)

### 1. 🧑‍🤝‍🧑 Patients Management (मरीज़ प्रबंधन)
- **Unique UHID Generation:** Har patient ke liye unique identification number (e.g. `PAT-1001`).
- **Demographics & Profile:** Name, Age, Gender, Blood Group, Phone, Email, Address, Emergency Contact.
- **Medical History & Allergies:** Chronic illnesses (Diabetes, Hypertension, Asthma), previous surgeries aur drug allergies ka record.
- **Patient 360° View:** Ek hi page par patient ke saare past & upcoming appointments, doctor consultation notes aur billing receipts.
- **Search & Filter:** Search by Name, UHID, Phone number ya Blood group.
- **CSV Data Export:** Patients list ko 1-click me Excel/CSV format me download karein.

### 2. 👨‍⚕️ Doctors & Specializations (डॉक्टर्स एवं विभाग)
- **Specializations / Departments:** Cardiology, Neurology, Orthopedics, Pediatrics, Dermatology, General Medicine, ENT, Gynecology आदि।
- **Specialist Profile:** Qualification (MBBS, MD, MS, DM), clinical experience years, consulting fees, cabin/OPD room number.
- **OPD Schedules & Hours:** Dedicated consulting days (e.g. Mon - Sat) aur time slots (Morning & Evening sessions).
- **Status Indicator:** Doctor active ya leave status tracking.
- **Doctor Analytics:** Doctor ke total patients aur generate hua revenue share.

### 3. 📅 Appointments & Consultation Scheduler (अपॉइंटमेंट शेड्यूलर)
- **Appointment Booking:** Patient aur Doctor select karke date, time slot, visit type (Consultation, Routine checkup, Follow-up, Emergency) book karein.
- **Slot Conflict Prevention:** Ek hi doctor ke same date aur time slot par double booking se protection.
- **Live Status Workflow:**
  $$\text{Scheduled} \longrightarrow \text{Confirmed} \longrightarrow \text{Completed} \ (\text{or Cancelled / No-Show})$$
- **Inline Status Triggers:** Table se hi 1-click status update (Confirm, Complete, Cancel).
- **Doctor Rx & Clinical Notes:** Doctor findings, diagnosis aur prescriptions note karne ka modal.
- **Direct Billing Link:** Appointment complete hone par sidha "Generate Bill" button dabane par patient, doctor aur consultation fee auto-fill ho jate hain!

### 4. 💳 Billing & Invoicing Tracking (बिलिंग एवं रेवेन्यू ट्रैकिंग)
- **Unique Invoice Numbering:** Tax invoice code (e.g. `INV-2026-0001`).
- **Dynamic Itemized Charges:** Consultation fee ke sath Lab tests (ECG, CBC, X-Ray), Medicines aur Procedures add karne ka live dynamic form.
- **Discount & GST Tax Calculation:** Real-time automatic subtotal, discount, tax % aur grand total calculation.
- **Payment Clearances & Due Tracking:**
  - `Paid` (Full payment received)
  - `Partially Paid` (Part payment received with pending balance)
  - `Unpaid` (Due balance)
- **Payment Modes:** Cash counter, UPI / QR (GPay, PhonePe, Paytm), Debit/Credit Card, Health Insurance (TPA).
- **Settle Dues Modal:** Partial ya Unpaid bills ka balance payment easily update karein.
- **Printable Medical Receipt:** Official hospital header, patient UHID, doctor name, line items, watermark stamp (PAID / DUE), authorized signature box, aur clean `@media print` layout!

### 5. 📊 Analytics, Reports & Dashboard (डैशबोर्ड एवं रिपोर्ट्स)
- **Real-time KPI Cards:** Total Patients, Active Doctors, Today's Appointments Queue, Total Invoiced Revenue, Total Collected, Pending Dues.
- **Interactive Chart.js Visualizations:**
  - Department Consultations Distribution (Bar chart)
  - Appointment Status Overview (Doughnut chart)
- **Payment Channels Breakdown:** Cash vs UPI vs Cards collections.
- **Doctor Revenue Sharing:** Har doctor ke total consultations aur revenue contribution ki table.
- **1-Click Master CSV Exports:**
  - Export Patients Master CSV
  - Export Appointments Master CSV
  - Export Invoices & Billing Master CSV

---

## 📁 Project Structure (प्रोजेक्ट संरचना)

```
Library Management System/
├── app.py                   # Main Flask Backend (All routes, logic, APIs, and CSV exports)
├── database.py              # SQLite database schema, foreign keys, tables & indexes
├── seed_data.py             # Realistic pre-seeded hospital sample data
├── requirements.txt         # Dependencies list (Flask)
├── run.bat                  # Windows 1-Click Launch Script
├── hospital.db              # SQLite Database file (Auto-created)
├── static/
│   ├── css/
│   │   └── custom.css       # Theme styles, badges, stamps & print invoice CSS
│   └── js/
│       └── app.js           # Modal handlers, dynamic fee calculation & API fetch
└── templates/
    ├── base.html            # Responsive Sidebar & Top Navigation bar layout
    ├── dashboard.html       # Analytics KPIs, Today's OPD queue & live charts
    ├── patients.html        # Patients directory, search, & registration modal
    ├── patient_detail.html  # Patient 360° view, visits timeline & bills
    ├── doctors.html         # Doctors directory & specialty filter chips
    ├── doctor_detail.html   # Doctor schedule, performance KPIs & edit modal
    ├── specializations.html # Medical departments grid & fee manager
    ├── appointments.html    # Full appointment scheduler & conflict prevention
    ├── billing.html         # Billing desk, unbilled alerts & invoice creator
    ├── invoice_detail.html  # Official printable invoice receipt with watermark
    └── reports.html         # Detailed financial breakdown & CSV export downloads
```

---

## 🚀 How to Run (कैसे चलाएं)

### Method 1: One-Click Startup on Windows (सबसे आसान तरीका)
Double-click on `run.bat` file in this directory.
It will:
1. Automatically verify Python & seed the initial database.
2. Automatically launch your default web browser to `http://127.0.0.1:5000`.
3. Start the Flask application server.

---

### Method 2: Command Line (टर्मिनल के जरिए)
Open PowerShell or Command Prompt in this folder and run:

```powershell
# 1. Install dependencies (if not already installed)
python -m pip install -r requirements.txt

# 2. Seed database with realistic sample data
python seed_data.py

# 3. Start the application
python app.py
```

Now open your browser and go to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Pre-seeded Sample Test Data (तैयार टेस्ट डेटा)

System me pehle se hi realistic data load kiya gaya hai:
- **8 Departments:** Cardiology, Neurology, Orthopedics, Pediatrics, Dermatology, General Medicine, ENT, Gynecology.
- **8 Doctors:** Dr. Rajesh Sharma, Dr. Priya Patel, Dr. Amitav Verma, Dr. Ananya Mukherjee, etc.
- **12 Patients:** Ramesh Gupta (PAT-1001), Sunita Devi (PAT-1002), Aarav Joshi (PAT-1003), Mohammad Zaid, etc.
- **Live Today's Appointments:** Today ke din ke liye pre-scheduled OPD appointments test karne ke liye.
- **Invoices:** Paid, Partially Paid, aur Unpaid invoices with itemized charges.
