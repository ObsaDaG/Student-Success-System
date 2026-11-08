import sqlite3

DB_NAME = "student_success.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn= get_connection()
    conn.execute( """
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
        semester TEXT NOT NULL,
        grade REAL NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id) 
    )
    """)

    conn.execute("""
        INSERT OR IGNORE INTO students (student_id, name, email)
        VALUES (1, 'Test Student', 'test@example.com')
    """)

    conn.commit()
    conn.close()

