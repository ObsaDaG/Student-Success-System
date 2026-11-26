import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import uuid

DB_NAME = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_success.db")
)
MAX_GUESTS = int(os.getenv("MAX_SESSIONS", "500"))
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", "500"))
SESSION_SECONDS = 30 * 24 * 3600
PASSWORD_ROUNDS = 600_000

DEMO_COURSES = [
    ("Introduction to Programming", 3, 3.5, "Fall 2025"),
    ("Calculus I", 4, 3.0, "Fall 2025"),
    ("English Composition", 3, 4.0, "Fall 2025"),
    ("Data Structures", 3, 3.75, "Spring 2026"),
    ("Statistics", 3, 2.5, "Spring 2026"),
    ("Microeconomics", 3, 4.0, "Spring 2026"),
    ("Database Systems", 3, 3.5, "Fall 2026"),
    ("Business Ethics", 2, 4.0, "Fall 2026"),
]


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            token TEXT,
            password_hash TEXT
        )
    """)
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(students)")]
    if "token" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN token TEXT")
    if "password_hash" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN password_hash TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            credits INTEGER NOT NULL,
            grade REAL NOT NULL,
            semester TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            student_id INTEGER NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ROUNDS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    if not stored or "$" not in stored:
        return False
    salt_hex, digest_hex = stored.split("$", 1)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PASSWORD_ROUNDS
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_session(student_id):
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (token, student_id, created_at) VALUES (?, ?, ?)",
        (token, student_id, time.time())
    )
    conn.commit()
    conn.close()
    return token


def get_session_student(token):
    if not token:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT student_id, created_at FROM sessions WHERE token = ?",
        (token,)
    ).fetchone()
    conn.close()
    if row is None or time.time() - row["created_at"] > SESSION_SECONDS:
        return None
    return row["student_id"]


def delete_session(token):
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def create_account(name, email, password):
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM students WHERE password_hash IS NOT NULL"
    ).fetchone()[0]
    if count >= MAX_ACCOUNTS:
        conn.close()
        raise RuntimeError("Too many accounts")

    try:
        cursor = conn.execute(
            "INSERT INTO students (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password))
        )
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already registered")

    conn.commit()
    student_id = cursor.lastrowid
    conn.close()
    return student_id


def find_account(email):
    conn = get_connection()
    row = conn.execute(
        "SELECT student_id, name, password_hash FROM students "
        "WHERE email = ? AND password_hash IS NOT NULL",
        (email,)
    ).fetchone()
    conn.close()
    return row


def create_demo_student():
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM students WHERE password_hash IS NULL"
    ).fetchone()[0]
    if count >= MAX_GUESTS:
        conn.close()
        raise RuntimeError("Too many demo sessions")

    cursor = conn.execute(
        "INSERT INTO students (name, email) VALUES (?, ?)",
        ("Guest", f"{uuid.uuid4().hex}@demo.local")
    )
    student_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO courses (student_id, course_name, credits, grade, semester) "
        "VALUES (?, ?, ?, ?, ?)",
        [(student_id, *course) for course in DEMO_COURSES]
    )
    conn.commit()
    conn.close()
    return student_id, create_session(student_id)