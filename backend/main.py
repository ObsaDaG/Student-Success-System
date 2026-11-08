from fastapi import FastAPI
app=FastAPI()
@app.get("/")
def home():
    return {"message" : "Student-Success-System API is running"}
