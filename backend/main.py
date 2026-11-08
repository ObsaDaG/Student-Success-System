from fastapi import FastAPI

from pydantic import BaseModel, Field

from fastapi.middleware.cors import CORSMiddleware

from database import create_tables , get_connection

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