from fastapi import FastAPI

from pydantic import BaseModel, Field

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


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


courses_db = {}
next_course_id = 1



@app.get("/")
def home():
    return {"message": "Student-Success-System API is running"}

@app.get("/api/students/{student_id}/courses")
def get_courses(student_id: int):
    return {
        "student_id": student_id,
        "courses": [
            {"course_id": 1, "course_name": "Economics", "credits": 3, "grade": 3.5, "semester": "Fall 2026"},
            {"course_id": 2, "course_name": "Math", "credits": 3, "grade": 3.25, "semester": "Fall 2026"}
        ]
    }
@app.post("/api/students/{student_id}/courses")
def add_course(student_id: int, course: Course):
    global next_course_id
    saved = course.model_dump()
    saved["course_id"] = next_course_id
    courses_db.setdefault(student_id, []).append(saved)
    next_course_id += 1
    return {
        "message": "Course added successfully",
        "student_id": student_id,
        "course": saved
    }