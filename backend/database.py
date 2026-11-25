import os
import sqlite3

DB_NAME = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_success.db")
)

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
            email TEXT NOT NULL UNIQUE
        )
    """)
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
        INSERT OR IGNORE INTO students (student_id, name, email)
        VALUES (1, 'Demo Student', 'demo@example.com')
    """)

    course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if course_count == 0 and os.getenv("SEED_DEMO_DATA", "1") == "1":
        conn.executemany(
            "INSERT INTO courses (student_id, course_name, credits, grade, semester) "
            "VALUES (1, ?, ?, ?, ?)",
            DEMO_COURSES
        )

    conn.commit()
    conn.close()