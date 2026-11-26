import time
from collections import defaultdict, deque
import os
import secrets
from fastapi import FastAPI,Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import (
    create_tables, get_connection, create_demo_student, create_account,
    find_account, verify_password, create_session, get_session_student, delete_session
)
from gpa import calculate_gpa
from analytics import strongest_and_weakest, gpa_by_semester, gpa_trend, grade_distribution
from advisor import get_recommendations, answer_question, SUGGESTED_QUESTIONS

app = FastAPI()

create_tables()

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://127.0.0.1:5500,http://localhost:5500"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Course(BaseModel):
    course_name: str = Field(min_length=1)
    credits: int = Field(ge=1, le=30)
    semester: str = Field(min_length=1)
    grade: float = Field(ge=0, le=4)

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
MAX_FAILED_LOGINS = 8
LOGIN_WINDOW_SECONDS = 900
_failed_logins = defaultdict(deque)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=254)
    password: str = Field(min_length=1, max_length=128)


def require_session(student_id: int, x_session_token: str = Header(default="")):
    if get_session_student(x_session_token) != student_id:
        raise HTTPException(status_code=403, detail="Invalid or missing session")


@app.post("/api/session")
def start_session():
    try:
        student_id, token = create_demo_student()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Too many demo sessions right now")
    return {"student_id": student_id, "token": token, "name": "Guest"}


@app.post("/api/register")
def register(request: RegisterRequest):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Please enter your name")

    email = request.email.strip().lower()
    try:
        student_id = create_account(name, email, request.password)
    except ValueError:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Registrations are closed for now")

    return {"student_id": student_id, "token": create_session(student_id), "name": name}


@app.post("/api/login")
def login(request: LoginRequest):
    email = request.email.strip().lower()
    now = time.time()

    attempts = _failed_logins[email]
    while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= MAX_FAILED_LOGINS:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in a few minutes.")

    account = find_account(email)
    if account is None or not verify_password(request.password, account["password_hash"]):
        attempts.append(now)
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    attempts.clear()
    return {
        "student_id": account["student_id"],
        "token": create_session(account["student_id"]),
        "name": account["name"]
    }


@app.post("/api/logout")
def logout(x_session_token: str = Header(default="")):
    delete_session(x_session_token)
    return {"message": "Logged out"}



def load_courses(student_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT course_name, credits, grade, semester FROM courses WHERE student_id = ?",
        (student_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/students/{student_id}/advisor", dependencies=[Depends(require_session)])
def get_advisor(student_id: int):
    courses = load_courses(student_id)
    source, recommendations = get_recommendations(courses)
    return {
        "student_id": student_id,
        "source": source,
        "recommendations": recommendations,
        "suggested_questions": SUGGESTED_QUESTIONS
    }


@app.post("/api/students/{student_id}/advisor/ask", dependencies=[Depends(require_session)])
def ask_advisor(student_id: int, request: AskRequest):
    courses = load_courses(student_id)
    source, answer = answer_question(courses, request.question)
    return {
        "student_id": student_id,
        "source": source,
        "answer": answer
    }




@app.get("/")
def home():
    return {"message": "Student-Success-System API is running"}

@app.get("/api/students/{student_id}/courses", dependencies=[Depends(require_session)])
def get_courses(student_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM courses WHERE student_id = ?",
        (student_id,)
    ).fetchall()
    conn.close()
    return {
        "student_id": student_id,
        "courses": [dict(row) for row in rows]
    }
@app.post("/api/students/{student_id}/courses", dependencies=[Depends(require_session)])
def add_course(student_id: int, course: Course):
    conn = get_connection()
    student = conn.execute(
        "SELECT 1 FROM students WHERE student_id = ?",
        (student_id,)
    ).fetchone()
    if student is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    cursor = conn.execute(
        "INSERT INTO courses (student_id, course_name, credits, grade, semester) VALUES (?, ?, ?, ?, ?)",
        (student_id, course.course_name, course.credits, course.grade, course.semester)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    saved = course.model_dump()
    saved["course_id"] = new_id
    return {
        "message": "Course added successfully",
        "student_id": student_id,
        "course": saved
    }
@app.get("/api/students/{student_id}/gpa/cumulative", dependencies=[Depends(require_session)])
def get_cumulative_gpa(student_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT credits, grade FROM courses WHERE student_id = ?",
        (student_id,)
    ).fetchall()
    conn.close()

    courses = [dict(row) for row in rows]

    return {
        "student_id": student_id,
        "gpa": calculate_gpa(courses),
        "total_credits": sum(course["credits"] for course in courses),
        "course_count": len(courses)
    }

@app.get("/api/students/{student_id}/gpa/semesters/{semester}", dependencies=[Depends(require_session)])
def get_semester_gpa(student_id: int, semester: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT credits, grade FROM courses WHERE student_id = ? AND semester = ?",
        (student_id, semester)
    ).fetchall()
    conn.close()

    courses = [dict(row) for row in rows]

    return {
        "student_id": student_id,
        "semester": semester,
        "gpa": calculate_gpa(courses),
        "total_credits":sum(course["credits"] for course in courses),
        "course_count": len(courses)
    }

@app.delete("/api/students/{student_id}/courses/{course_id}", dependencies=[Depends(require_session)])
def delete_course(student_id: int, course_id: int):
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM courses WHERE course_id = ? AND student_id = ?",
        (course_id, student_id)
    )
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    return {"message": "Course deleted successfully", "course_id": course_id}

@app.put("/api/students/{student_id}/courses/{course_id}", dependencies=[Depends(require_session)])
def update_course(student_id: int, course_id: int, course: Course):
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE courses SET course_name = ?, credits = ?, grade = ?, semester = ? WHERE course_id = ? AND student_id = ?",
        (course.course_name, course.credits, course.grade, course.semester, course_id, student_id)
    )
    conn.commit()
    updated = cursor.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Course not found")

    saved = course.model_dump()
    saved["course_id"] = course_id
    return {
        "message": "Course updated successfully",
        "student_id": student_id,
        "course": saved
    }

@app.get("/api/students/{student_id}/analytics", dependencies=[Depends(require_session)])
def get_analytics(student_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT course_name, credits, grade, semester FROM courses WHERE student_id = ?",
        (student_id,)
    ).fetchall()
    conn.close()

    courses = [dict(row) for row in rows]
    semester_gpas = gpa_by_semester(courses)

    return {
        "student_id": student_id,
        "course_count": len(courses),
        "total_credits": sum(course["credits"] for course in courses),
        "cumulative_gpa": calculate_gpa(courses),
        "strongest_and_weakest": strongest_and_weakest(courses),
        "semester_gpas": semester_gpas,
        "trend": gpa_trend(semester_gpas),
        "grade_distribution": grade_distribution(courses)
    }