import os
import secrets
import sqlite3
import uuid

DB_NAME = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_success.db")
)
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "500"))

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
            token TEXT
        )
    """)
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(students)")]
    if "token" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN token TEXT")

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
    conn.commit()
    conn.close()


def create_demo_student():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if count >= MAX_SESSIONS:
        conn.close()
        raise RuntimeError("Too many demo sessions")

    token = secrets.token_urlsafe(24)
    cursor = conn.execute(
        "INSERT INTO students (name, email, token) VALUES (?, ?, ?)",
        ("Demo Visitor", f"{uuid.uuid4().hex}@demo.local", token)
    )
    student_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO courses (student_id, course_name, credits, grade, semester) "
        "VALUES (?, ?, ?, ?, ?)",
        [(student_id, *course) for course in DEMO_COURSES]
    )
    conn.commit()
    conn.close()
    return student_id, token