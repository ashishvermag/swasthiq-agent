import sqlite3
import json
import os
from pathlib import Path

def load_clinic_data():
    # Dynamically find the root directory of the project (two levels up from backend/database.py)
    # This ensures the path works on both your Windows machine and the evaluator's machine.
    base_dir = Path(__file__).resolve().parent.parent
    file_path = base_dir / "data" / "clinic.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_fresh_db() -> sqlite3.Connection:
    """
    Creates a completely fresh, in-memory SQLite database for a single conversation run.
    This guarantees state resets between conversations.
    """
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Appointments Table (Our primary mutable state)
    # Using UNIQUE constraint on doctor_id, date, and start to prevent double-booking at the DB level
    cursor.execute('''
        CREATE TABLE appointments (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            doctor_id TEXT,
            date TEXT,
            start TEXT,
            end TEXT,
            status TEXT,
            UNIQUE(doctor_id, date, start)
        )
    ''')

    # 2. Patients Table
    cursor.execute('''
        CREATE TABLE patients (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT,
            dob TEXT,
            guardian_of TEXT 
        )
    ''')

    data = load_clinic_data()

    # Seed Patients
    for p in data['patients']:
        guardian_of_str = json.dumps(p['guardian_of']) # Store array as JSON string
        cursor.execute(
            "INSERT INTO patients (id, name, phone, dob, guardian_of) VALUES (?, ?, ?, ?, ?)",
            (p['id'], p['name'], p['phone'], p['dob'], guardian_of_str)
        )

    # Seed Appointments
    for a in data['appointments']:
        cursor.execute(
            "INSERT INTO appointments (id, patient_id, doctor_id, date, start, end, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (a['id'], a['patient_id'], a['doctor_id'], a['date'], a['start'], a['end'], a['status'])
        )

    conn.commit()
    return conn