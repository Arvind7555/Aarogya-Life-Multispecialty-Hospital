import os
import json
import csv
import io
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, Response, send_file
)
from database import get_db_connection, init_db
from seed_data import seed_database

app = Flask(__name__)
app.secret_key = 'hospital-management-secret-key-super-secure'

# Initialize database and auto-seed on startup
init_db()
seed_database()

# Custom Jinja filters
@app.template_filter('currency')
def currency_filter(value):
    try:
        val = float(value or 0)
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"

@app.template_filter('from_json')
def from_json_filter(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []

@app.context_processor
def inject_global_data():
    """Inject common stats and current date across all templates."""
    today_str = date.today().isoformat()
    return {
        'today_date': today_str,
        'current_year': date.today().year,
        'hospital_name': 'Aarogya Life Multispecialty Hospital',
        'hospital_tagline': 'Advanced Healthcare & Compassionate Clinic Care',
        'hospital_phone': '+91 11 4567 8900 / +91 98765 00000',
        'hospital_address': 'Plot 45, Sector 12, Medical Enclave, New Delhi - 110075'
    }

# ==========================================
# 1. DASHBOARD ROUTE
# ==========================================
@app.route('/')
def dashboard():
    conn = get_db_connection()
    today_str = date.today().isoformat()

    # Total counts
    total_patients = conn.execute('SELECT COUNT(*) FROM patients').fetchone()[0]
    total_doctors = conn.execute("SELECT COUNT(*) FROM doctors WHERE status = 'Active'").fetchone()[0]
    total_appointments = conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0]

    # Today's appointments stats
    today_appointments_count = conn.execute(
        'SELECT COUNT(*) FROM appointments WHERE appointment_date = ?', (today_str,)
    ).fetchone()[0]

    # Financial stats
    financial_summary = conn.execute('''
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_billed,
            COALESCE(SUM(paid_amount), 0) AS total_collected,
            COALESCE(SUM(balance_due), 0) AS total_due,
            COUNT(*) AS total_invoices
        FROM invoices
    ''').fetchone()

    # Today's scheduled appointments list
    today_appointments = conn.execute('''
        SELECT a.*, p.name AS patient_name, p.phone AS patient_phone, p.patient_id AS patient_code,
               d.name AS doctor_name, d.cabin_no, s.name AS specialization_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN specializations s ON d.specialization_id = s.id
        WHERE a.appointment_date = ?
        ORDER BY a.appointment_time ASC
    ''', (today_str,)).fetchall()

    # Recent Invoices
    recent_invoices = conn.execute('''
        SELECT i.*, p.name AS patient_name, d.name AS doctor_name
        FROM invoices i
        JOIN patients p ON i.patient_id = p.id
        JOIN doctors d ON i.doctor_id = d.id
        ORDER BY i.id DESC LIMIT 5
    ''').fetchall()

    # Specialization appointment distribution for Chart
    spec_data = conn.execute('''
        SELECT s.name, COUNT(a.id) AS count
        FROM specializations s
        LEFT JOIN doctors d ON s.id = d.specialization_id
        LEFT JOIN appointments a ON d.id = a.doctor_id
        GROUP BY s.id
        ORDER BY count DESC
    ''').fetchall()

    # Appointment status distribution for Chart
    status_data = conn.execute('''
        SELECT status, COUNT(*) AS count
        FROM appointments
        GROUP BY status
    ''').fetchall()

    # Doctors list for quick appointment modal
    doctors = conn.execute('''
        SELECT d.id, d.name, d.consultation_fee, s.name AS spec_name 
        FROM doctors d
        JOIN specializations s ON d.specialization_id = s.id
        WHERE d.status = 'Active'
    ''').fetchall()

    # Patients list for quick appointment modal
    patients = conn.execute('SELECT id, patient_id, name, phone FROM patients ORDER BY name ASC').fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        today_appointments_count=today_appointments_count,
        financial=financial_summary,
        today_appointments=today_appointments,
        recent_invoices=recent_invoices,
        spec_chart_labels=[row['name'] for row in spec_data],
        spec_chart_values=[row['count'] for row in spec_data],
        status_chart_labels=[row['status'] for row in status_data],
        status_chart_values=[row['count'] for row in status_data],
        doctors=doctors,
        patients=patients
    )

# ==========================================
# 2. PATIENTS MANAGEMENT
# ==========================================
@app.route('/patients')
def patients_list():
    search_query = request.args.get('q', '').strip()
    conn = get_db_connection()

    if search_query:
        query_pattern = f'%{search_query}%'
        patients = conn.execute('''
            SELECT p.*,
                (SELECT COUNT(*) FROM appointments WHERE patient_id = p.id) AS total_visits,
                (SELECT COALESCE(SUM(balance_due), 0) FROM invoices WHERE patient_id = p.id) AS pending_due
            FROM patients p
            WHERE p.name LIKE ? OR p.patient_id LIKE ? OR p.phone LIKE ? OR p.blood_group LIKE ?
            ORDER BY p.id DESC
        ''', (query_pattern, query_pattern, query_pattern, query_pattern)).fetchall()
    else:
        patients = conn.execute('''
            SELECT p.*,
                (SELECT COUNT(*) FROM appointments WHERE patient_id = p.id) AS total_visits,
                (SELECT COALESCE(SUM(balance_due), 0) FROM invoices WHERE patient_id = p.id) AS pending_due
            FROM patients p
            ORDER BY p.id DESC
        ''').fetchall()

    conn.close()
    return render_template('patients.html', patients=patients, search_query=search_query)

@app.route('/patients/add', methods=['POST'])
def add_patient():
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', 'Male')
    blood_group = request.form.get('blood_group', 'Unknown')
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    emergency_contact = request.form.get('emergency_contact', '').strip()
    medical_history = request.form.get('medical_history', '').strip()

    if not name or not age or not phone:
        flash('Please fill required patient details (Name, Age, Phone)!', 'danger')
        return redirect(url_for('patients_list'))

    conn = get_db_connection()
    # Generate unique patient UHID code
    last_id_row = conn.execute('SELECT MAX(id) FROM patients').fetchone()
    next_id = (last_id_row[0] or 1000) + 1
    patient_id = f"PAT-{next_id:04d}"

    try:
        conn.execute('''
            INSERT INTO patients (patient_id, name, age, gender, blood_group, phone, email, address, emergency_contact, medical_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, name, int(age), gender, blood_group, phone, email, address, emergency_contact, medical_history))
        conn.commit()
        flash(f'Patient {name} ({patient_id}) registered successfully!', 'success')
    except Exception as e:
        flash(f'Error registering patient: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('patients_list'))

@app.route('/patients/<int:patient_id>')
def patient_detail(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        flash('Patient not found!', 'warning')
        conn.close()
        return redirect(url_for('patients_list'))

    # Appointments history
    appointments = conn.execute('''
        SELECT a.*, d.name AS doctor_name, s.name AS specialization_name, d.cabin_no
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        JOIN specializations s ON d.specialization_id = s.id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (patient_id,)).fetchall()

    # Invoices history
    invoices = conn.execute('''
        SELECT i.*, d.name AS doctor_name
        FROM invoices i
        JOIN doctors d ON i.doctor_id = d.id
        WHERE i.patient_id = ?
        ORDER BY i.invoice_date DESC, i.id DESC
    ''', (patient_id,)).fetchall()

    # Doctors list for quick appointment modal
    doctors = conn.execute('''
        SELECT d.id, d.name, d.consultation_fee, s.name AS spec_name 
        FROM doctors d
        JOIN specializations s ON d.specialization_id = s.id
        WHERE d.status = 'Active'
    ''').fetchall()

    conn.close()
    return render_template(
        'patient_detail.html',
        patient=patient,
        appointments=appointments,
        invoices=invoices,
        doctors=doctors
    )

@app.route('/patients/<int:patient_id>/edit', methods=['POST'])
def edit_patient(patient_id):
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    gender = request.form.get('gender', 'Male')
    blood_group = request.form.get('blood_group', 'Unknown')
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    emergency_contact = request.form.get('emergency_contact', '').strip()
    medical_history = request.form.get('medical_history', '').strip()

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE patients
            SET name = ?, age = ?, gender = ?, blood_group = ?, phone = ?, email = ?, address = ?, emergency_contact = ?, medical_history = ?
            WHERE id = ?
        ''', (name, int(age), gender, blood_group, phone, email, address, emergency_contact, medical_history, patient_id))
        conn.commit()
        flash('Patient details updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating patient: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('patient_detail', patient_id=patient_id))

# ==========================================
# 3. DOCTORS MANAGEMENT
# ==========================================
@app.route('/doctors')
def doctors_list():
    spec_filter = request.args.get('specialization', '')
    conn = get_db_connection()

    specializations = conn.execute('SELECT * FROM specializations ORDER BY name ASC').fetchall()

    if spec_filter:
        doctors = conn.execute('''
            SELECT d.*, s.name AS specialization_name, s.icon AS spec_icon,
                   (SELECT COUNT(*) FROM appointments WHERE doctor_id = d.id) AS total_appointments
            FROM doctors d
            JOIN specializations s ON d.specialization_id = s.id
            WHERE d.specialization_id = ?
            ORDER BY d.name ASC
        ''', (spec_filter,)).fetchall()
    else:
        doctors = conn.execute('''
            SELECT d.*, s.name AS specialization_name, s.icon AS spec_icon,
                   (SELECT COUNT(*) FROM appointments WHERE doctor_id = d.id) AS total_appointments
            FROM doctors d
            JOIN specializations s ON d.specialization_id = s.id
            ORDER BY d.name ASC
        ''').fetchall()

    conn.close()
    return render_template('doctors.html', doctors=doctors, specializations=specializations, current_spec=spec_filter)

@app.route('/doctors/add', methods=['POST'])
def add_doctor():
    name = request.form.get('name', '').strip()
    specialization_id = request.form.get('specialization_id')
    qualification = request.form.get('qualification', '').strip()
    experience_years = request.form.get('experience_years', 1)
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    cabin_no = request.form.get('cabin_no', '').strip()
    consultation_fee = request.form.get('consultation_fee', 500)
    available_days = request.form.get('available_days', 'Mon - Sat').strip()
    available_time = request.form.get('available_time', '09:00 AM - 01:00 PM, 04:00 PM - 07:00 PM').strip()
    status = request.form.get('status', 'Active')

    if not name or not specialization_id or not phone or not consultation_fee:
        flash('Please fill in doctor name, specialization, phone, and fee!', 'danger')
        return redirect(url_for('doctors_list'))

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO doctors (name, specialization_id, qualification, experience_years, phone, email, cabin_no, consultation_fee, available_days, available_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, int(specialization_id), qualification, int(experience_years), phone, email, cabin_no, float(consultation_fee), available_days, available_time, status))
        conn.commit()
        flash(f'Doctor {name} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding doctor: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('doctors_list'))

@app.route('/doctors/<int:doctor_id>')
def doctor_detail(doctor_id):
    conn = get_db_connection()
    doctor = conn.execute('''
        SELECT d.*, s.name AS specialization_name, s.icon AS spec_icon
        FROM doctors d
        JOIN specializations s ON d.specialization_id = s.id
        WHERE d.id = ?
    ''', (doctor_id,)).fetchone()

    if not doctor:
        flash('Doctor not found!', 'warning')
        conn.close()
        return redirect(url_for('doctors_list'))

    # Appointments list
    appointments = conn.execute('''
        SELECT a.*, p.name AS patient_name, p.phone AS patient_phone, p.patient_id AS patient_code
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE a.doctor_id = ?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    ''', (doctor_id,)).fetchall()

    # Total revenue generated by doctor
    revenue = conn.execute('''
        SELECT COALESCE(SUM(total_amount), 0) AS total_revenue,
               COALESCE(SUM(paid_amount), 0) AS collected
        FROM invoices WHERE doctor_id = ?
    ''', (doctor_id,)).fetchone()

    specializations = conn.execute('SELECT * FROM specializations ORDER BY name ASC').fetchall()
    conn.close()

    return render_template(
        'doctor_detail.html',
        doctor=doctor,
        appointments=appointments,
        revenue=revenue,
        specializations=specializations
    )

@app.route('/doctors/<int:doctor_id>/edit', methods=['POST'])
def edit_doctor(doctor_id):
    name = request.form.get('name', '').strip()
    specialization_id = request.form.get('specialization_id')
    qualification = request.form.get('qualification', '').strip()
    experience_years = request.form.get('experience_years', 1)
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    cabin_no = request.form.get('cabin_no', '').strip()
    consultation_fee = request.form.get('consultation_fee', 500)
    available_days = request.form.get('available_days', 'Mon - Sat').strip()
    available_time = request.form.get('available_time', '').strip()
    status = request.form.get('status', 'Active')

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE doctors
            SET name = ?, specialization_id = ?, qualification = ?, experience_years = ?, phone = ?, email = ?,
                cabin_no = ?, consultation_fee = ?, available_days = ?, available_time = ?, status = ?
            WHERE id = ?
        ''', (name, int(specialization_id), qualification, int(experience_years), phone, email, cabin_no, float(consultation_fee), available_days, available_time, status, doctor_id))
        conn.commit()
        flash('Doctor profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating doctor: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('doctor_detail', doctor_id=doctor_id))

# ==========================================
# 4. SPECIALIZATIONS MANAGEMENT
# ==========================================
@app.route('/specializations')
def specializations_list():
    conn = get_db_connection()
    specs = conn.execute('''
        SELECT s.*, 
            (SELECT COUNT(*) FROM doctors WHERE specialization_id = s.id) AS doctor_count,
            (SELECT COUNT(*) FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE d.specialization_id = s.id) AS appointment_count
        FROM specializations s
        ORDER BY s.name ASC
    ''').fetchall()
    conn.close()
    return render_template('specializations.html', specializations=specs)

@app.route('/specializations/add', methods=['POST'])
def add_specialization():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'fa-stethoscope').strip()
    default_fee = request.form.get('default_fee', 500)

    if not name:
        flash('Specialization name is required!', 'danger')
        return redirect(url_for('specializations_list'))

    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO specializations (name, description, icon, default_fee)
            VALUES (?, ?, ?, ?)
        ''', (name, description, icon, float(default_fee)))
        conn.commit()
        flash(f'Specialization "{name}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error adding specialization (maybe already exists?): {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('specializations_list'))

@app.route('/specializations/<int:spec_id>/edit', methods=['POST'])
def edit_specialization(spec_id):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'fa-stethoscope').strip()
    default_fee = request.form.get('default_fee', 500)

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE specializations
            SET name = ?, description = ?, icon = ?, default_fee = ?
            WHERE id = ?
        ''', (name, description, icon, float(default_fee), spec_id))
        conn.commit()
        flash('Specialization updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating specialization: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('specializations_list'))

@app.route('/specializations/<int:spec_id>/delete', methods=['POST'])
def delete_specialization(spec_id):
    conn = get_db_connection()
    # Check if doctors are assigned
    doc_count = conn.execute('SELECT COUNT(*) FROM doctors WHERE specialization_id = ?', (spec_id,)).fetchone()[0]
    if doc_count > 0:
        flash(f'Cannot delete specialization! {doc_count} doctor(s) are assigned to it.', 'danger')
        conn.close()
        return redirect(url_for('specializations_list'))

    try:
        conn.execute('DELETE FROM specializations WHERE id = ?', (spec_id,))
        conn.commit()
        flash('Specialization deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting specialization: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('specializations_list'))

# ==========================================
# 5. APPOINTMENTS MANAGEMENT
# ==========================================
@app.route('/appointments')
def appointments_list():
    date_filter = request.args.get('date', '')
    doctor_filter = request.args.get('doctor_id', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('q', '').strip()

    conn = get_db_connection()

    sql = '''
        SELECT a.*, p.name AS patient_name, p.phone AS patient_phone, p.patient_id AS patient_code,
               d.name AS doctor_name, d.cabin_no, d.consultation_fee, s.name AS specialization_name,
               (SELECT id FROM invoices WHERE appointment_id = a.id LIMIT 1) AS invoice_id
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN specializations s ON d.specialization_id = s.id
        WHERE 1=1
    '''
    params = []

    if date_filter == 'today':
        sql += ' AND a.appointment_date = ?'
        params.append(date.today().isoformat())
    elif date_filter and date_filter != 'all':
        sql += ' AND a.appointment_date = ?'
        params.append(date_filter)

    if doctor_filter:
        sql += ' AND a.doctor_id = ?'
        params.append(doctor_filter)

    if status_filter:
        sql += ' AND a.status = ?'
        params.append(status_filter)

    if search_query:
        sql += ' AND (p.name LIKE ? OR a.appointment_no LIKE ? OR p.phone LIKE ?)'
        pattern = f'%{search_query}%'
        params.extend([pattern, pattern, pattern])

    sql += ' ORDER BY a.appointment_date DESC, a.appointment_time ASC'

    appointments = conn.execute(sql, params).fetchall()

    doctors = conn.execute('''
        SELECT d.id, d.name, d.consultation_fee, s.name AS spec_name 
        FROM doctors d
        JOIN specializations s ON d.specialization_id = s.id
        WHERE d.status = 'Active'
        ORDER BY d.name ASC
    ''').fetchall()

    patients = conn.execute('SELECT id, patient_id, name, phone FROM patients ORDER BY name ASC').fetchall()
    conn.close()

    return render_template(
        'appointments.html',
        appointments=appointments,
        doctors=doctors,
        patients=patients,
        current_date_filter=date_filter,
        current_doctor_filter=doctor_filter,
        current_status_filter=status_filter,
        search_query=search_query
    )

@app.route('/appointments/book', methods=['POST'])
def book_appointment():
    patient_id = request.form.get('patient_id')
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    visit_type = request.form.get('visit_type', 'Consultation')
    reason = request.form.get('reason', '').strip()

    if not patient_id or not doctor_id or not appointment_date or not appointment_time:
        flash('Please fill in all mandatory appointment fields!', 'danger')
        return redirect(request.referrer or url_for('appointments_list'))

    conn = get_db_connection()

    # Slot conflict check
    conflict = conn.execute('''
        SELECT id FROM appointments 
        WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND status NOT IN ('Cancelled')
    ''', (doctor_id, appointment_date, appointment_time)).fetchone()

    if conflict:
        flash(f'This Doctor already has an appointment booked on {appointment_date} at {appointment_time}! Please choose another slot.', 'warning')
        conn.close()
        return redirect(request.referrer or url_for('appointments_list'))

    # Generate appointment number
    last_apt = conn.execute('SELECT MAX(id) FROM appointments').fetchone()
    next_id = (last_apt[0] or 0) + 1
    appointment_no = f"APT-{date.today().year}-{next_id:04d}"

    try:
        conn.execute('''
            INSERT INTO appointments (appointment_no, patient_id, doctor_id, appointment_date, appointment_time, visit_type, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Scheduled')
        ''', (appointment_no, int(patient_id), int(doctor_id), appointment_date, appointment_time, visit_type, reason))
        conn.commit()
        flash(f'Appointment {appointment_no} booked successfully for {appointment_date} at {appointment_time}!', 'success')
    except Exception as e:
        flash(f'Error booking appointment: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(request.referrer or url_for('appointments_list'))

@app.route('/appointments/<int:apt_id>/status', methods=['POST'])
def update_appointment_status(apt_id):
    new_status = request.form.get('status')
    doctor_notes = request.form.get('doctor_notes', '')

    valid_statuses = ['Scheduled', 'Confirmed', 'Completed', 'Cancelled', 'No-Show']
    if new_status not in valid_statuses:
        flash('Invalid appointment status!', 'danger')
        return redirect(request.referrer or url_for('appointments_list'))

    conn = get_db_connection()
    try:
        if doctor_notes:
            conn.execute('UPDATE appointments SET status = ?, doctor_notes = ? WHERE id = ?', (new_status, doctor_notes, apt_id))
        else:
            conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (new_status, apt_id))
        conn.commit()
        flash(f'Appointment status updated to "{new_status}"!', 'success')
    except Exception as e:
        flash(f'Error updating status: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(request.referrer or url_for('appointments_list'))

# ==========================================
# 6. BILLING & INVOICING TRACKING
# ==========================================
@app.route('/billing')
def billing_list():
    status_filter = request.args.get('status', '')
    search_query = request.args.get('q', '').strip()
    conn = get_db_connection()

    sql = '''
        SELECT i.*, p.name AS patient_name, p.patient_id AS patient_code, p.phone AS patient_phone,
               d.name AS doctor_name, s.name AS specialization_name
        FROM invoices i
        JOIN patients p ON i.patient_id = p.id
        JOIN doctors d ON i.doctor_id = d.id
        JOIN specializations s ON d.specialization_id = s.id
        WHERE 1=1
    '''
    params = []

    if status_filter:
        sql += ' AND i.payment_status = ?'
        params.append(status_filter)

    if search_query:
        sql += ' AND (i.invoice_no LIKE ? OR p.name LIKE ? OR p.phone LIKE ? OR i.transaction_ref LIKE ?)'
        pat = f'%{search_query}%'
        params.extend([pat, pat, pat, pat])

    sql += ' ORDER BY i.id DESC'

    invoices = conn.execute(sql, params).fetchall()

    # Financial stats
    financial = conn.execute('''
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_billed,
            COALESCE(SUM(paid_amount), 0) AS total_collected,
            COALESCE(SUM(balance_due), 0) AS total_due,
            COUNT(*) AS count_invoices
        FROM invoices
    ''').fetchone()

    # Doctors & Patients for Create Bill modal
    doctors = conn.execute('''
        SELECT d.id, d.name, d.consultation_fee, s.name AS spec_name 
        FROM doctors d
        JOIN specializations s ON d.specialization_id = s.id
        ORDER BY d.name ASC
    ''').fetchall()

    patients = conn.execute('SELECT id, patient_id, name, phone FROM patients ORDER BY name ASC').fetchall()
    
    # Recent completed/confirmed appointments that might need bills
    unbilled_appointments = conn.execute('''
        SELECT a.id, a.appointment_no, a.appointment_date, a.appointment_time, 
               p.id AS patient_id, p.name AS patient_name,
               d.id AS doctor_id, d.name AS doctor_name, d.consultation_fee
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        LEFT JOIN invoices i ON a.id = i.appointment_id
        WHERE i.id IS NULL AND a.status IN ('Confirmed', 'Completed')
        ORDER BY a.appointment_date DESC LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template(
        'billing.html',
        invoices=invoices,
        financial=financial,
        doctors=doctors,
        patients=patients,
        unbilled_appointments=unbilled_appointments,
        current_status=status_filter,
        search_query=search_query
    )

@app.route('/billing/create', methods=['POST'])
def create_invoice():
    patient_id = request.form.get('patient_id')
    doctor_id = request.form.get('doctor_id')
    appointment_id = request.form.get('appointment_id') or None
    consultation_fee = float(request.form.get('consultation_fee', 0.0) or 0.0)
    discount = float(request.form.get('discount', 0.0) or 0.0)
    tax_percentage = float(request.form.get('tax_percentage', 0.0) or 0.0)
    paid_amount = float(request.form.get('paid_amount', 0.0) or 0.0)
    payment_method = request.form.get('payment_method', 'Cash')
    transaction_ref = request.form.get('transaction_ref', '').strip()
    invoice_date = request.form.get('invoice_date', date.today().isoformat())
    notes = request.form.get('notes', '').strip()

    # Dynamic line items
    item_names = request.form.getlist('item_name[]')
    item_costs = request.form.getlist('item_cost[]')

    breakdown_list = []
    # Always include consultation fee as the primary item if > 0
    if consultation_fee > 0:
        breakdown_list.append({"item": "Doctor Consultation Fee", "amount": consultation_fee})

    additional_charges_sum = 0.0
    for name, cost in zip(item_names, item_costs):
        name = name.strip()
        if name and cost:
            try:
                amt = float(cost)
                if amt > 0:
                    breakdown_list.append({"item": name, "amount": amt})
                    additional_charges_sum += amt
            except ValueError:
                continue

    subtotal = consultation_fee + additional_charges_sum
    discounted = max(0.0, subtotal - discount)
    tax_amount = (discounted * tax_percentage) / 100.0
    total_amount = round(discounted + tax_amount, 2)
    balance_due = round(max(0.0, total_amount - paid_amount), 2)

    # Determine status
    if paid_amount >= total_amount and total_amount > 0:
        payment_status = 'Paid'
        paid_amount = total_amount
        balance_due = 0.0
    elif paid_amount > 0 and paid_amount < total_amount:
        payment_status = 'Partially Paid'
    else:
        payment_status = 'Unpaid'
        paid_amount = 0.0
        balance_due = total_amount

    conn = get_db_connection()
    last_inv = conn.execute('SELECT MAX(id) FROM invoices').fetchone()
    next_id = (last_inv[0] or 0) + 1
    invoice_no = f"INV-{date.today().year}-{next_id:04d}"

    try:
        conn.execute('''
            INSERT INTO invoices (
                invoice_no, appointment_id, patient_id, doctor_id, consultation_fee, additional_charges,
                charges_breakdown, discount, tax_percentage, total_amount, paid_amount, balance_due,
                payment_status, payment_method, transaction_ref, invoice_date, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_no, appointment_id, int(patient_id), int(doctor_id), consultation_fee,
            additional_charges_sum, json.dumps(breakdown_list), discount, tax_percentage,
            total_amount, paid_amount, balance_due, payment_status, payment_method,
            transaction_ref, invoice_date, notes
        ))
        conn.commit()
        flash(f'Invoice {invoice_no} created successfully for {currency_filter(total_amount)}!', 'success')
    except Exception as e:
        flash(f'Error creating invoice: {str(e)}', 'danger')
        conn.close()
        return redirect(url_for('billing_list'))

    conn.close()
    return redirect(url_for('invoice_detail', invoice_id=next_id))

@app.route('/billing/<int:invoice_id>')
def invoice_detail(invoice_id):
    conn = get_db_connection()
    invoice = conn.execute('''
        SELECT i.*, 
               p.name AS patient_name, p.patient_id AS patient_code, p.age AS patient_age, 
               p.gender AS patient_gender, p.phone AS patient_phone, p.address AS patient_address,
               p.blood_group,
               d.name AS doctor_name, d.qualification AS doctor_qualification, d.cabin_no,
               s.name AS specialization_name,
               a.appointment_no, a.appointment_date, a.appointment_time, a.visit_type
        FROM invoices i
        JOIN patients p ON i.patient_id = p.id
        JOIN doctors d ON i.doctor_id = d.id
        JOIN specializations s ON d.specialization_id = s.id
        LEFT JOIN appointments a ON i.appointment_id = a.id
        WHERE i.id = ?
    ''', (invoice_id,)).fetchone()

    if not invoice:
        flash('Invoice not found!', 'warning')
        conn.close()
        return redirect(url_for('billing_list'))

    items = []
    if invoice['charges_breakdown']:
        try:
            items = json.loads(invoice['charges_breakdown'])
        except Exception:
            items = []

    conn.close()
    return render_template('invoice_detail.html', invoice=invoice, items=items)

@app.route('/billing/<int:invoice_id>/pay', methods=['POST'])
def pay_invoice(invoice_id):
    additional_payment = float(request.form.get('additional_payment', 0.0) or 0.0)
    payment_method = request.form.get('payment_method', 'Cash')
    transaction_ref = request.form.get('transaction_ref', '').strip()

    if additional_payment <= 0:
        flash('Payment amount must be greater than zero!', 'warning')
        return redirect(url_for('invoice_detail', invoice_id=invoice_id))

    conn = get_db_connection()
    invoice = conn.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,)).fetchone()
    if not invoice:
        flash('Invoice not found!', 'danger')
        conn.close()
        return redirect(url_for('billing_list'))

    new_paid = invoice['paid_amount'] + additional_payment
    total = invoice['total_amount']

    if new_paid >= total:
        new_paid = total
        new_balance = 0.0
        new_status = 'Paid'
    else:
        new_balance = total - new_paid
        new_status = 'Partially Paid'

    ref = transaction_ref or invoice['transaction_ref']

    try:
        conn.execute('''
            UPDATE invoices
            SET paid_amount = ?, balance_due = ?, payment_status = ?, payment_method = ?, transaction_ref = ?
            WHERE id = ?
        ''', (new_paid, new_balance, new_status, payment_method, ref, invoice_id))
        conn.commit()
        flash(f'Payment of {currency_filter(additional_payment)} recorded successfully! Invoice status: {new_status}.', 'success')
    except Exception as e:
        flash(f'Error recording payment: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('invoice_detail', invoice_id=invoice_id))

# ==========================================
# 7. REPORTS & EXPORTS
# ==========================================
@app.route('/reports')
def reports():
    conn = get_db_connection()

    # Financial totals
    financial = conn.execute('''
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_billed,
            COALESCE(SUM(paid_amount), 0) AS total_collected,
            COALESCE(SUM(balance_due), 0) AS total_due,
            COUNT(*) AS total_invoices
        FROM invoices
    ''').fetchone()

    # Revenue by Doctor
    doctor_revenue = conn.execute('''
        SELECT d.name, s.name AS spec_name,
               COUNT(DISTINCT a.id) AS appointment_count,
               COALESCE(SUM(i.total_amount), 0) AS total_billed,
               COALESCE(SUM(i.paid_amount), 0) AS total_collected
        FROM doctors d
        JOIN specializations s ON d.specialization_id = s.id
        LEFT JOIN appointments a ON d.id = a.doctor_id
        LEFT JOIN invoices i ON d.id = i.doctor_id
        GROUP BY d.id
        ORDER BY total_billed DESC
    ''').fetchall()

    # Payment Methods breakdown
    payment_methods = conn.execute('''
        SELECT payment_method, COUNT(*) AS count, SUM(paid_amount) AS total_collected
        FROM invoices
        WHERE paid_amount > 0
        GROUP BY payment_method
        ORDER BY total_collected DESC
    ''').fetchall()

    # Top Specializations by visits
    top_specs = conn.execute('''
        SELECT s.name, COUNT(a.id) AS visit_count
        FROM specializations s
        LEFT JOIN doctors d ON s.id = d.specialization_id
        LEFT JOIN appointments a ON d.id = a.doctor_id
        GROUP BY s.id
        ORDER BY visit_count DESC
    ''').fetchall()

    conn.close()

    return render_template(
        'reports.html',
        financial=financial,
        doctor_revenue=doctor_revenue,
        payment_methods=payment_methods,
        top_specs=top_specs
    )

# CSV Exports
@app.route('/export/patients')
def export_patients():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients ORDER BY id ASC').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Patient Code', 'Name', 'Age', 'Gender', 'Blood Group', 'Phone', 'Email', 'Address', 'Emergency Contact', 'Medical History', 'Registered At'])

    for p in patients:
        writer.writerow([
            p['patient_id'], p['name'], p['age'], p['gender'], p['blood_group'],
            p['phone'], p['email'], p['address'], p['emergency_contact'],
            p['medical_history'], p['created_at']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=patients_report_{date.today().isoformat()}.csv"}
    )

@app.route('/export/appointments')
def export_appointments():
    conn = get_db_connection()
    appointments = conn.execute('''
        SELECT a.appointment_no, p.patient_id, p.name AS patient_name, p.phone AS patient_phone,
               d.name AS doctor_name, s.name AS specialization, a.appointment_date, a.appointment_time,
               a.visit_type, a.status, a.reason, a.doctor_notes
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN specializations s ON d.specialization_id = s.id
        ORDER BY a.appointment_date DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Appointment No', 'Patient ID', 'Patient Name', 'Phone', 'Doctor', 'Specialization', 'Date', 'Time', 'Visit Type', 'Status', 'Reason', 'Doctor Notes'])

    for a in appointments:
        writer.writerow([
            a['appointment_no'], a['patient_id'], a['patient_name'], a['patient_phone'],
            a['doctor_name'], a['specialization'], a['appointment_date'], a['appointment_time'],
            a['visit_type'], a['status'], a['reason'], a['doctor_notes']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=appointments_report_{date.today().isoformat()}.csv"}
    )

@app.route('/export/billing')
def export_billing():
    conn = get_db_connection()
    invoices = conn.execute('''
        SELECT i.invoice_no, p.patient_id, p.name AS patient_name, d.name AS doctor_name,
               i.consultation_fee, i.additional_charges, i.discount, i.tax_percentage,
               i.total_amount, i.paid_amount, i.balance_due, i.payment_status,
               i.payment_method, i.transaction_ref, i.invoice_date
        FROM invoices i
        JOIN patients p ON i.patient_id = p.id
        JOIN doctors d ON i.doctor_id = d.id
        ORDER BY i.id DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Invoice No', 'Patient ID', 'Patient Name', 'Doctor Name', 'Consultation Fee', 'Addl Charges', 'Discount', 'Tax %', 'Total Amount', 'Paid Amount', 'Balance Due', 'Status', 'Method', 'Transaction Ref', 'Date'])

    for i in invoices:
        writer.writerow([
            i['invoice_no'], i['patient_id'], i['patient_name'], i['doctor_name'],
            i['consultation_fee'], i['additional_charges'], i['discount'], i['tax_percentage'],
            i['total_amount'], i['paid_amount'], i['balance_due'], i['payment_status'],
            i['payment_method'], i['transaction_ref'], i['invoice_date']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=billing_report_{date.today().isoformat()}.csv"}
    )

# ==========================================
# 8. HELPER REST API FOR FRONTEND INTERACTIVITY
# ==========================================
@app.route('/api/doctor/<int:doc_id>')
def api_doctor_info(doc_id):
    conn = get_db_connection()
    doc = conn.execute('''
        SELECT d.*, s.name AS spec_name 
        FROM doctors d 
        JOIN specializations s ON d.specialization_id = s.id 
        WHERE d.id = ?
    ''', (doc_id,)).fetchone()
    conn.close()
    if not doc:
        return jsonify({'error': 'Doctor not found'}), 404
    return jsonify({
        'id': doc['id'],
        'name': doc['name'],
        'specialization': doc['spec_name'],
        'consultation_fee': doc['consultation_fee'],
        'cabin_no': doc['cabin_no'],
        'available_time': doc['available_time'],
        'available_days': doc['available_days']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("  Aarogya Life Multispecialty Hospital & Clinic System")
    print(f"  Server is starting on http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
