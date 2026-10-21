import sqlite3
import random
import string
import time
from datetime import datetime

DB_NAME = "attendance.db"

def get_connection():
    """Establishes high-concurrency database connection with WAL mode."""
    conn = sqlite3.connect(DB_NAME, timeout=10.0)  # Waits up to 10 seconds if busy
    conn.execute("PRAGMA journal_mode=WAL;")        # Enables instant parallel writes for 100+ students
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            instructor_name TEXT NOT NULL,
            department TEXT NOT NULL,
            year_semester TEXT NOT NULL,
            instructor_telegram_id INTEGER NOT NULL
        )
    """)
   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            telegram_id INTEGER,
            full_name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            course_code TEXT NOT NULL,
            PRIMARY KEY (student_id, course_code)
        )
    """)
    
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            pin TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at REAL NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            student_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            method TEXT NOT NULL
        )
    """)

   
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            course_code TEXT NOT NULL,
            date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING'
        )
    """)

    conn.commit()
    conn.close()


def create_course(instructor_telegram_id: int, instructor_name: str, department: str, course_name: str, year_semester: str):
    conn = get_connection()
    cursor = conn.cursor()
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    course_code = f"{course_name[:4].upper()}_{random_suffix}"
    
    cursor.execute("""
        INSERT INTO courses (course_code, course_name, instructor_name, department, year_semester, instructor_telegram_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (course_code, course_name, instructor_name, department, year_semester, instructor_telegram_id))
    
    conn.commit()
    conn.close()
    return course_code

def get_instructor_courses(instructor_telegram_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_code, course_name, department, year_semester FROM courses WHERE instructor_telegram_id = ?", (instructor_telegram_id,))
    courses = cursor.fetchall()
    conn.close()
    return courses

def get_course_details(course_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_name, instructor_name, department, year_semester FROM courses WHERE course_code = ?", (course_code,))
    row = cursor.fetchone()
    conn.close()
    return row



def enroll_student(telegram_id: int, full_name: str, student_id: str, course_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO students (telegram_id, full_name, student_id, course_code)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, full_name, student_id, course_code))
    conn.commit()
    conn.close()

def get_enrolled_count(course_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students WHERE course_code = ?", (course_code,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_enrolled_students(course_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, full_name FROM students WHERE course_code = ? ORDER BY full_name ASC", (course_code,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_student_by_telegram_id(telegram_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, full_name, course_code FROM students WHERE telegram_id = ? ORDER BY student_id DESC LIMIT 1", (telegram_id,))
    student = cursor.fetchone()
    conn.close()
    return student


def create_session(course_code: str, duration_seconds: int = 60):
    """Creates a session with a strict 60-second anti-cheat window."""
    conn = get_connection()
    cursor = conn.cursor()
    pin = str(random.randint(1000, 9999))
    now = time.time()
    expires_at = now + duration_seconds
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO sessions (course_code, pin, created_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (course_code, pin, date_str, expires_at))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id, pin, expires_at

def close_session(session_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def verify_and_record_pin(telegram_id: int, entered_pin: str):
    """Directly verifies PIN, validates course enrollment, and records attendance in parallel."""
    conn = get_connection()
    cursor = conn.cursor()
    now = time.time()
    
    
    cursor.execute("""
        SELECT s.id, s.course_code, s.expires_at, c.course_name
        FROM sessions s
        JOIN courses c ON s.course_code = c.course_code
        WHERE s.pin = ? AND s.is_active = 1
        ORDER BY s.id DESC LIMIT 1
    """, (entered_pin,))
    session = cursor.fetchone()
    
    if not session:
        conn.close()
        return "INVALID_PIN", None, None, None
        
    session_id, course_code, expires_at, course_name = session
    
    if now > expires_at:
        cursor.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        return "EXPIRED", None, None, None
        
   
    cursor.execute("""
        SELECT student_id, full_name FROM students 
        WHERE telegram_id = ? AND course_code = ?
    """, (telegram_id, course_code))
    student = cursor.fetchone()
    
    if not student:
        # Check if student is registered in university at all
        cursor.execute("SELECT student_id FROM students WHERE telegram_id = ? LIMIT 1", (telegram_id,))
        if cursor.fetchone():
            conn.close()
            return "NOT_ENROLLED_IN_THIS_COURSE", None, None, course_name
        conn.close()
        return "NOT_ENROLLED", None, None, None
        
    student_id, full_name = student
    
  
    cursor.execute("SELECT id FROM attendance WHERE session_id = ? AND student_id = ?", (session_id, student_id))
    if cursor.fetchone():
        conn.close()
        return "ALREADY_PRESENT", student_id, full_name, course_name
        
    now_date = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%I:%M:%S %p")
    
    cursor.execute("""
        INSERT INTO attendance (session_id, course_code, student_id, full_name, date, time, method)
        VALUES (?, ?, ?, ?, ?, ?, 'PIN')
    """, (session_id, course_code, student_id, full_name, now_date, now_time))
    
    conn.commit()
    conn.close()
    return "SUCCESS", student_id, full_name, course_name


def record_attendance(session_id: int, course_code: str, student_id: str, full_name: str, method: str):
    conn = get_connection()
    cursor = conn.cursor()
    now_date = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%I:%M:%S %p")
    
    cursor.execute("SELECT id FROM attendance WHERE session_id = ? AND student_id = ?", (session_id, student_id))
    if cursor.fetchone():
        conn.close()
        return False
        
    cursor.execute("""
        INSERT INTO attendance (session_id, course_code, student_id, full_name, date, time, method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, course_code, student_id, full_name, now_date, now_time, method))
    conn.commit()
    conn.close()
    return True

def get_present_students(session_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_id, full_name, time, method FROM attendance WHERE session_id = ? ORDER BY full_name ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_absent_students(session_id: int, course_code: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_id, full_name FROM students 
        WHERE course_code = ? AND student_id NOT IN (
            SELECT student_id FROM attendance WHERE session_id = ?
        )
        ORDER BY full_name ASC
    """, (course_code, session_id))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_critical_absences(course_code: str, threshold: int = 3):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT id) FROM sessions WHERE course_code = ? AND is_active = 0", (course_code,))
    total_closed = cursor.fetchone()[0]
    
    if total_closed < threshold:
        conn.close()
        return []
        
    cursor.execute("""
        SELECT s.student_id, s.full_name, COUNT(a.id) as attended_count
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND s.course_code = a.course_code
        WHERE s.course_code = ?
        GROUP BY s.student_id
    """, (course_code,))
    
    results = []
    for student_id, full_name, attended in cursor.fetchall():
        missed = total_closed - attended
        if missed >= threshold:
            results.append((student_id, full_name, missed))
            
    conn.close()
    return results

def submit_leave_request(student_id: str, full_name: str, course_code: str, date: str, reason: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leave_requests (student_id, full_name, course_code, date, reason, status)
        VALUES (?, ?, ?, ?, ?, 'PENDING')
    """, (student_id, full_name, course_code, date, reason))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return req_id