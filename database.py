import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hospital.db')

def get_db_connection():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialize database tables with full constraints and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Specializations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS specializations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        icon TEXT DEFAULT 'fa-stethoscope',
        default_fee REAL NOT NULL DEFAULT 500.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Doctors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization_id INTEGER NOT NULL,
        qualification TEXT NOT NULL,
        experience_years INTEGER DEFAULT 5,
        phone TEXT NOT NULL,
        email TEXT,
        cabin_no TEXT,
        consultation_fee REAL NOT NULL,
        available_days TEXT DEFAULT 'Mon - Sat',
        available_time TEXT DEFAULT '09:00 AM - 02:00 PM, 05:00 PM - 08:00 PM',
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (specialization_id) REFERENCES specializations (id) ON DELETE RESTRICT
    )
    ''')

    # 3. Patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        blood_group TEXT DEFAULT 'Unknown',
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT,
        emergency_contact TEXT,
        medical_history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 4. Appointments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_no TEXT UNIQUE NOT NULL,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        visit_type TEXT DEFAULT 'Consultation',
        reason TEXT,
        status TEXT DEFAULT 'Scheduled',
        doctor_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE RESTRICT
    )
    ''')

    # 5. Invoices table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        appointment_id INTEGER,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        consultation_fee REAL NOT NULL DEFAULT 0.0,
        additional_charges REAL NOT NULL DEFAULT 0.0,
        charges_breakdown TEXT,
        discount REAL NOT NULL DEFAULT 0.0,
        tax_percentage REAL NOT NULL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        paid_amount REAL NOT NULL DEFAULT 0.0,
        balance_due REAL NOT NULL DEFAULT 0.0,
        payment_status TEXT DEFAULT 'Unpaid',
        payment_method TEXT DEFAULT 'Cash',
        transaction_ref TEXT,
        invoice_date TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE SET NULL,
        FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
        FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE RESTRICT
    )
    ''')

    # Create helpful indexes for fast lookup and query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors(specialization_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_patient ON invoices(patient_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_doctor ON invoices(doctor_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(payment_status)')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", DB_PATH)
