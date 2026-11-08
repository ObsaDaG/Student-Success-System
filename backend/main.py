from fastapi import FastAPI

app = FastAPI()

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