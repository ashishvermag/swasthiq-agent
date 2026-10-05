import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

# Dynamically calculate the path to data/clinic.json
BASE_DIR = Path(__file__).resolve().parent.parent
CLINIC_FILE_PATH = BASE_DIR / "data" / "clinic.json"

# Load read-only clinic rules (holidays, windows, leaves) in memory
with open(CLINIC_FILE_PATH, 'r', encoding='utf-8') as f:
    CLINIC_DATA = json.load(f)

def get_day_of_week(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a")

def search_slots(conn: sqlite3.Connection, doctor_id: str, date: str) -> Dict[str, Any]:
    """Free slots for a doctor on a date."""
    if date in CLINIC_DATA['holidays']:
        return {"error": "The clinic is closed on this date for a holiday."}
    
    doctor = next((d for d in CLINIC_DATA['doctors'] if d['id'] == doctor_id), None)
    if not doctor:
        return {"error": f"Doctor {doctor_id} not found."}
        
    if date in doctor.get('leave_dates', []):
        return {"error": "The doctor is on leave on this date."}

    day_of_week = get_day_of_week(date)
    windows = [w for w in doctor['windows'] if w['day'] == day_of_week]
    
    if not windows:
        return {"error": f"Doctor {doctor_id} does not consult on {day_of_week}s."}

    # Generate all possible 15-minute slots for the day's windows
    possible_slots = []
    slot_minutes = CLINIC_DATA['clinic']['slot_minutes']
    
    for w in windows:
        start_time = datetime.strptime(f"{date} {w['start']}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{date} {w['end']}", "%Y-%m-%d %H:%M")
        
        current = start_time
        while current + timedelta(minutes=slot_minutes) <= end_time:
            possible_slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=slot_minutes)

    # Query DB to remove booked slots
    cursor = conn.cursor()
    cursor.execute(
        "SELECT start FROM appointments WHERE doctor_id = ? AND date = ? AND status = 'booked'",
        (doctor_id, date)
    )
    booked_slots = {row['start'] for row in cursor.fetchall()}
    
    available_slots = [slot for slot in possible_slots if slot not in booked_slots]
    return {"available_slots": available_slots}

def book_appointment(conn: sqlite3.Connection, patient_id: str, doctor_id: str, date: str, start: str) -> Dict[str, Any]:
    """Create an appointment in a free slot."""
    # Verify slot availability first to provide a clean business error
    slots_check = search_slots(conn, doctor_id, date)
    if "error" in slots_check:
        return slots_check
    if start not in slots_check.get("available_slots", []):
        return {"error": f"Slot {start} on {date} is not available for {doctor_id}."}

    appointment_id = f"ap_{uuid.uuid4().hex[:6]}"
    
    # Calculate end time based on clinic slot duration
    start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=CLINIC_DATA['clinic']['slot_minutes'])
    end_str = end_dt.strftime("%H:%M")

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO appointments (id, patient_id, doctor_id, date, start, end, status) 
               VALUES (?, ?, ?, ?, ?, ?, 'booked')""",
            (appointment_id, patient_id, doctor_id, date, start, end_str)
        )
        conn.commit()
        return {"success": True, "appointment_id": appointment_id, "status": "booked"}
    except sqlite3.IntegrityError:
        # Prevents double-booking if two parallel processes race for the same slot
        return {"error": "Slot was just booked by another user. Please select a different slot."}

def reschedule_appointment(conn: sqlite3.Connection, appointment_id: str, new_date: str, new_start: str) -> Dict[str, Any]:
    """Move an existing appointment."""
    cursor = conn.cursor()
    cursor.execute("SELECT doctor_id FROM appointments WHERE id = ?", (appointment_id,))
    row = cursor.fetchone()
    
    if not row:
        return {"error": f"Appointment {appointment_id} not found."}
        
    doctor_id = row['doctor_id']
    
    # Validate new slot
    slots_check = search_slots(conn, doctor_id, new_date)
    if "error" in slots_check:
        return slots_check
    if new_start not in slots_check.get("available_slots", []):
        return {"error": f"Slot {new_start} on {new_date} is not available."}

    start_dt = datetime.strptime(f"{new_date} {new_start}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=CLINIC_DATA['clinic']['slot_minutes'])
    new_end = end_dt.strftime("%H:%M")

    try:
        cursor.execute(
            "UPDATE appointments SET date = ?, start = ?, end = ?, status = 'booked' WHERE id = ?",
            (new_date, new_start, new_end, appointment_id)
        )
        conn.commit()
        return {"success": True, "appointment_id": appointment_id, "status": "rescheduled"}
    except sqlite3.IntegrityError:
        return {"error": "New slot double-booked during transaction. Please try again."}

def cancel_appointment(conn: sqlite3.Connection, appointment_id: str) -> Dict[str, Any]:
    """Cancel an existing appointment."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM appointments WHERE id = ?", (appointment_id,))
    if not cursor.fetchone():
        return {"error": f"Appointment {appointment_id} not found."}

    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    conn.commit()
    return {"success": True, "appointment_id": appointment_id, "status": "cancelled"}

def lookup_patient(conn: sqlite3.Connection, name: str) -> Dict[str, Any]:
    """Resolve a caller to a patient record. Returns candidates, never a guess."""
    cursor = conn.cursor()
    # Use LIKE for partial matches to handle ambiguous names safely
    cursor.execute("SELECT * FROM patients WHERE name LIKE ?", ('%' + name + '%',))
    rows = cursor.fetchall()
    
    candidates = []
    for r in rows:
        patient_dict = dict(r)
        patient_dict['guardian_of'] = json.loads(patient_dict['guardian_of'])
        candidates.append(patient_dict)
        
    if not candidates:
        return {"error": f"No patient found matching '{name}'."}
        
    return {"candidates": candidates}

def escalate_to_human(reason: str, detail: str) -> Dict[str, Any]:
    """Hand the conversation off."""
    # This tool doesn't modify DB state; it triggers the agent loop to terminate and escalate.
    return {"status": "escalating", "reason": reason, "detail": detail}