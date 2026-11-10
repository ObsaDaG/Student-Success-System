from fastapi import FastAPI, HTTPException

from pydantic import BaseModel, Field

from fastapi.middleware.cors import CORSMiddleware

from database import create_tables , get_connection

from gpa import calculate_gpa

app = FastAPI()

create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Course(BaseModel):
    course_name: str = Field(min_length=1)
    credits: int = Field(ge=1, le=30)
    semester: str = Field(min_length=1)
    grade: float = Field(ge=0, le=4)






@app.get("/")
def home():
    return {"message": "Student-Success-System API is running"}

@app.get("/api/students/{student_id}/courses")
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
@app.post("/api/students/{student_id}/courses")
def add_course(student_id: int, course: Course):
    conn = get_connection()
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

@app.get("/api/students/{student_id}/gpa/cumulative")
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

@app.get("/api/students/{student_id}/gpa/semesters/{semester}")
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

@app.delete("/api/students/{student_id}/courses/{course_id}")
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

@app.put("/api/students/{student_id}/courses/{course_id}")
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