import json
from datetime import datetime, timedelta
from database import get_db_connection, init_db

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if database already has specializations
    cursor.execute('SELECT COUNT(*) FROM specializations')
    if cursor.fetchone()[0] > 0:
        print("Database already contains data. Skipping re-seed.")
        conn.close()
        return

    print("Seeding fresh hospital data...")

    # 1. Specializations
    specialties = [
        ("Cardiology", "Heart, cardiovascular diseases, hypertension, and cardiac surgery consultations", "fa-heart-pulse", 800.0),
        ("Neurology", "Disorders of the brain, spinal cord, nerves, migraines, and stroke management", "fa-brain", 1000.0),
        ("Orthopedics", "Bones, joints, ligaments, fractures, arthritis, and sports injuries", "fa-bone", 700.0),
        ("Pediatrics", "Infant, child, and adolescent healthcare, immunizations, and developmental checks", "fa-baby", 500.0),
        ("Dermatology", "Skin disorders, hair, nails, allergies, acne, and aesthetic dermatology", "fa-hand-dots", 600.0),
        ("General Medicine", "Primary healthcare, fever, viral infections, diabetes, routine wellness exams", "fa-user-doctor", 400.0),
        ("ENT (Otolaryngology)", "Ear infections, hearing loss, nasal allergies, sinus, throat disorders", "fa-head-side-cough", 500.0),
        ("Gynecology & Obstetrics", "Women's reproductive health, prenatal care, maternity, and hormonal care", "fa-person-pregnant", 750.0),
    ]

    cursor.executemany('''
    INSERT INTO specializations (name, description, icon, default_fee)
    VALUES (?, ?, ?, ?)
    ''', specialties)

    # 2. Doctors
    doctors = [
        ("Dr. Rajesh Sharma", 1, "MBBS, MD, DM (Cardiology)", 14, "+91 98101 23456", "rajesh.sharma@hospital.org", "Cabin 101", 800.0, "Mon - Sat", "09:00 AM - 01:00 PM, 04:00 PM - 07:00 PM", "Active"),
        ("Dr. Priya Patel", 6, "MBBS, MD (Internal Medicine)", 9, "+91 98202 34567", "priya.patel@hospital.org", "Cabin 102", 400.0, "Mon - Sat", "08:30 AM - 02:00 PM, 05:00 PM - 08:30 PM", "Active"),
        ("Dr. Amitav Verma", 3, "MBBS, MS (Orthopedics), DNB", 12, "+91 98303 45678", "amitav.verma@hospital.org", "Cabin 103", 700.0, "Mon, Wed, Fri, Sat", "10:00 AM - 02:00 PM, 04:00 PM - 07:30 PM", "Active"),
        ("Dr. Ananya Mukherjee", 4, "MBBS, DCH, MD (Pediatrics)", 8, "+91 98404 56789", "ananya.m@hospital.org", "Cabin 104", 500.0, "Mon - Fri", "09:30 AM - 01:30 PM, 04:30 PM - 08:00 PM", "Active"),
        ("Dr. Vikram Singhania", 2, "MBBS, MD, DM (Neurology)", 16, "+91 98505 67890", "vikram.s@hospital.org", "Cabin 105", 1000.0, "Tue, Thu, Sat", "10:30 AM - 03:00 PM, 06:00 PM - 08:30 PM", "Active"),
        ("Dr. Sneha Rao", 5, "MBBS, MD (Dermatology & Venereology)", 7, "+91 98606 78901", "sneha.rao@hospital.org", "Cabin 106", 600.0, "Mon - Sat", "11:00 AM - 03:00 PM, 05:00 PM - 08:00 PM", "Active"),
        ("Dr. Farhan Khan", 7, "MBBS, MS (ENT)", 10, "+91 98707 89012", "farhan.khan@hospital.org", "Cabin 107", 500.0, "Mon - Fri", "09:00 AM - 01:00 PM, 04:00 PM - 07:00 PM", "Active"),
        ("Dr. Meenakshi Sundaram", 8, "MBBS, MS (Obstetrics & Gynaecology)", 15, "+91 98808 90123", "meenakshi.s@hospital.org", "Cabin 108", 750.0, "Mon - Sat", "09:00 AM - 02:00 PM, 05:00 PM - 08:00 PM", "Active"),
    ]

    cursor.executemany('''
    INSERT INTO doctors (name, specialization_id, qualification, experience_years, phone, email, cabin_no, consultation_fee, available_days, available_time, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', doctors)

    # 3. Patients
    patients = [
        ("PAT-1001", "Ramesh Gupta", 48, "Male", "B+", "+91 98765 43210", "ramesh.gupta@example.com", "Flat 402, Shanti Vihar, Civil Lines", "+91 98765 00001 (Wife)", "Hypertension, Type 2 Diabetes for 5 years"),
        ("PAT-1002", "Sunita Devi", 36, "Female", "O+", "+91 98112 23344", "sunita.devi@example.com", "Plot 12, Green Park Extension", "+91 98112 00002 (Husband)", "No known chronic illness, Penicillin allergy"),
        ("PAT-1003", "Aarav Joshi", 7, "Male", "A+", "+91 98223 34455", "joshi.family@example.com", "House 77, Sector 14", "+91 98223 00003 (Father)", "Childhood asthma, dust pollen allergy"),
        ("PAT-1004", "Mohammad Zaid", 52, "Male", "AB+", "+91 98334 45566", "m.zaid@example.com", "B-24, Al-Falah Colony, Old City", "+91 98334 00004 (Son)", "Cardiac stent placed in 2023, on blood thinners"),
        ("PAT-1005", "Kavita Nair", 29, "Female", "O-", "+91 98445 56677", "kavita.nair@example.com", "Tower 3, Apt 1104, Sunrise Heights", "+91 98445 00005 (Brother)", "Frequent migraine episodes, neck tension"),
        ("PAT-1006", "Harpreet Singh", 42, "Male", "B+", "+91 98556 67788", "harpreet.singh@example.com", "Guru Nanak Nagar, Street 4", "+91 98556 00006 (Wife)", "L4-L5 lumbar disc bulge, chronic back ache"),
        ("PAT-1007", "Pooja Mehra", 31, "Female", "A-", "+91 98667 78899", "pooja.mehra@example.com", "15-B, Malviya Nagar", "+91 98667 00007 (Sister)", "Severe eczema on hands, dry skin flares"),
        ("PAT-1008", "Suresh Kumar Yadav", 63, "Male", "O+", "+91 98778 89900", "suresh.yadav@example.com", "Vill. Kanganheri, Najafgarh Road", "+91 98778 00008 (Son)", "Bilateral knee osteoarthritis, high uric acid"),
        ("PAT-1009", "Deepa Iyer", 27, "Female", "B-", "+91 98889 90011", "deepa.iyer@example.com", "Flat 205, Kaveri Apartments", "+91 98889 00009 (Husband)", "Routine 2nd trimester prenatal follow-up"),
        ("PAT-1010", "Rakesh Bansal", 55, "Male", "AB-", "+91 98990 01122", "rakesh.bansal@example.com", "Shop & Residence, Cloth Market", "+91 98990 00010 (Daughter)", "Chronic sinusitis, nasal polyps history"),
        ("PAT-1011", "Anjali Deshmukh", 41, "Female", "A+", "+91 98101 12233", "anjali.d@example.com", "Row House 9, Shivaji Enclave", "+91 98101 00011 (Husband)", "Hypothyroidism, taking Thyroxine 50mcg"),
        ("PAT-1012", "Devendra Rathore", 38, "Male", "O+", "+91 98212 23344", "devendra.r@example.com", "C-88, Defence Colony", "+91 98212 00012 (Brother)", "Seasonal allergic rhinitis, frequent sneezing")
    ]

    cursor.executemany('''
    INSERT INTO patients (patient_id, name, age, gender, blood_group, phone, email, address, emergency_contact, medical_history)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients)

    # 4. Appointments
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)
    tomorrow = today + timedelta(days=1)
    in_three_days = today + timedelta(days=3)

    appointments = [
        # Past appointments
        ("APT-2026-0001", 1, 1, two_days_ago.isoformat(), "10:00 AM", "Follow-up", "Blood pressure check and ECG follow-up", "Completed", "BP is 130/84. ECG normal. Advised to continue Telmisartan 40mg."),
        ("APT-2026-0002", 2, 2, two_days_ago.isoformat(), "11:30 AM", "Consultation", "High fever, body chills, fatigue since 2 days", "Completed", "Viral fever symptoms. Prescribed Paracetamol and hydration."),
        ("APT-2026-0003", 6, 3, yesterday.isoformat(), "04:30 PM", "Consultation", "Severe lower back stiffness after lifting heavy load", "Completed", "Acute muscle spasm. Prescribed muscle relaxant and physical rest."),
        ("APT-2026-0004", 7, 6, yesterday.isoformat(), "05:00 PM", "Consultation", "Severe itching and red rash on forearms", "Completed", "Contact dermatitis diagnosed. Prescribed topical steroid cream."),

        # Today's appointments (Active dashboard items)
        ("APT-2026-0005", 3, 4, today.isoformat(), "09:30 AM", "Routine Checkup", "Recurrent wheezing and dry night cough", "Confirmed", "Chest examination needed, review inhaler technique"),
        ("APT-2026-0006", 4, 1, today.isoformat(), "10:30 AM", "Follow-up", "Post-angioplasty 6-month routine review", "Scheduled", "Review lipid profile and echo report"),
        ("APT-2026-0007", 5, 5, today.isoformat(), "11:15 AM", "Consultation", "Pulsating headache with visual aura", "Confirmed", "Suspected migraine with aura, neurological exam planned"),
        ("APT-2026-0008", 8, 3, today.isoformat(), "12:00 PM", "Consultation", "Difficulty walking due to sharp bilateral knee pain", "Scheduled", "X-Ray bilateral knees requested"),
        ("APT-2026-0009", 9, 8, today.isoformat(), "04:00 PM", "Routine Checkup", "24-week gestational ultrasound and blood sugar check", "Scheduled", "Second trimester routine checkup"),
        ("APT-2026-0010", 10, 7, today.isoformat(), "05:30 PM", "Consultation", "Persistent blocked nose and facial pressure", "Confirmed", "Nasal endoscopy suggested if symptoms persist"),

        # Future appointments
        ("APT-2026-0011", 11, 2, tomorrow.isoformat(), "10:00 AM", "Follow-up", "TSH thyroid levels recheck", "Scheduled", None),
        ("APT-2026-0012", 12, 7, in_three_days.isoformat(), "11:00 AM", "Consultation", "Seasonal sneezing and watery eyes", "Scheduled", None)
    ]

    cursor.executemany('''
    INSERT INTO appointments (appointment_no, patient_id, doctor_id, appointment_date, appointment_time, visit_type, reason, status, doctor_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', appointments)

    # 5. Invoices (Billing tracking)
    # Line items stored as JSON array of {description, amount}
    inv_1_breakdown = json.dumps([
        {"item": "Doctor Consultation Fee", "amount": 800.0},
        {"item": "12-Lead Resting ECG", "amount": 350.0},
        {"item": "Lipid Profile & Glucose Lab Test", "amount": 650.0}
    ])
    inv_2_breakdown = json.dumps([
        {"item": "General OPD Consultation", "amount": 400.0},
        {"item": "Complete Blood Count (CBC)", "amount": 300.0},
        {"item": "IV Paracetamol Infusion & Nursing", "amount": 250.0}
    ])
    inv_3_breakdown = json.dumps([
        {"item": "Orthopedic Specialist Consultation", "amount": 700.0},
        {"item": "Lumbosacral Spine Digital X-Ray", "amount": 800.0},
        {"item": "Physiotherapy Session (TENS + Heat)", "amount": 500.0}
    ])
    inv_4_breakdown = json.dumps([
        {"item": "Dermatology Specialist Consultation", "amount": 600.0},
        {"item": "Skin Allergy Patch Testing", "amount": 900.0}
    ])
    inv_5_breakdown = json.dumps([
        {"item": "Pediatric Consultation", "amount": 500.0},
        {"item": "Nebulization Treatment (2 Cycles)", "amount": 300.0},
        {"item": "Peak Flow Measurement", "amount": 150.0}
    ])
    inv_6_breakdown = json.dumps([
        {"item": "Cardiology Consultation", "amount": 800.0},
        {"item": "Echocardiogram (2D Echo)", "amount": 1800.0}
    ])

    invoices = [
        # 1. Paid invoice
        ("INV-2026-0001", 1, 1, 1, 800.0, 1000.0, inv_1_breakdown, 100.0, 0.0, 1700.0, 1700.0, 0.0, "Paid", "UPI / Online", "UPI-8849201948", two_days_ago.isoformat(), "Payment received in full via Google Pay."),
        # 2. Paid invoice
        ("INV-2026-0002", 2, 2, 2, 400.0, 550.0, inv_2_breakdown, 0.0, 0.0, 950.0, 950.0, 0.0, "Paid", "Cash", "CASH-REC-102", two_days_ago.isoformat(), "Cash received at reception counter."),
        # 3. Partially Paid invoice
        ("INV-2026-0003", 3, 6, 3, 700.0, 1300.0, inv_3_breakdown, 0.0, 0.0, 2000.0, 1000.0, 1000.0, "Partially Paid", "Debit Card", "POS-TXN-55410", yesterday.isoformat(), "Patient paid 1000 advance. Remaining 1000 due on follow-up visit."),
        # 4. Paid invoice
        ("INV-2026-0004", 4, 7, 6, 600.0, 900.0, inv_4_breakdown, 50.0, 0.0, 1450.0, 1450.0, 0.0, "Paid", "Credit Card", "VISA-992147", yesterday.isoformat(), "Paid via Visa credit card."),
        # 5. Unpaid invoice
        ("INV-2026-0005", 5, 3, 4, 500.0, 450.0, inv_5_breakdown, 0.0, 0.0, 950.0, 0.0, 950.0, "Unpaid", "Cash", None, today.isoformat(), "Awaiting billing counter payment post-consultation."),
        # 6. Unpaid invoice
        ("INV-2026-0006", 6, 4, 1, 800.0, 1800.0, inv_6_breakdown, 100.0, 0.0, 2500.0, 0.0, 2500.0, "Unpaid", "UPI / Online", None, today.isoformat(), "Scheduled for echo test, bill generated.")
    ]

    cursor.executemany('''
    INSERT INTO invoices (invoice_no, appointment_id, patient_id, doctor_id, consultation_fee, additional_charges, charges_breakdown, discount, tax_percentage, total_amount, paid_amount, balance_due, payment_status, payment_method, transaction_ref, invoice_date, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', invoices)

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
