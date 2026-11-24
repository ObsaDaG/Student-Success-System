# Student Success System

A web application that helps university students track courses, calculate their GPA, understand their academic performance, and get AI-powered study recommendations.



## Features

- Add, edit, delete and view courses (name, credits, semester, grade points)
- Semester GPA and cumulative GPA, calculated on request from the stored courses
- Academic analytics: GPA trend across semesters, strongest and weakest courses, grade distribution
- AI Academic Advisor: personalised recommendations and answers to student questions
- Automatic rule-based fallback when the AI service is unavailable
- Responsive layout with a collapsible sidebar

## Architecture

```
Browser (HTML, CSS, JavaScript)
        |  fetch() over HTTP / JSON
        v
FastAPI backend (Python): validation, GPA logic, analytics, advisor
        |                              |
        v                              v
SQLite database               Gemini API (key stays on the backend)
```

Design decisions:

- The frontend never talks to the database. Every change goes through the API, and the page redraws from what the API returns, so the database is the single source of truth.
- Python validates all input with Pydantic, even though the browser also checks it.
- GPA is calculated from course records on request and is never stored, so it cannot become outdated.
- Python calculates every number. The AI only turns those numbers into readable advice and is told not to invent data or make predictions.
- The API key lives in `backend/.env`, which is excluded from Git. If the AI call fails, rule-based recommendations are returned instead, and the response states which source produced them.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite (`sqlite3`) |
| AI | Google Gemini API (`google-genai`) |
| Tools | Git, GitHub, VS Code |

## Project structure

```
student-success-system/
├── index.html, style.css, script.js     frontend
├── requirements.txt
└── backend/
    ├── main.py          API endpoints
    ├── database.py      connection and table creation
    ├── gpa.py           GPA calculation
    ├── analytics.py     trend, strongest/weakest, grade distribution
    ├── advisor.py       recommendations, questions, rule-based fallback
    ├── ai_service.py    the only file that talks to Gemini
    └── .env.example     template for your API key
```

## Run it locally (Windows)

1. Clone the repository and open the folder in VS Code.
2. Create and activate a virtual environment:

```
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install the dependencies:

```
python -m pip install -r ../requirements.txt
```

4. Copy `.env.example` to `.env` and add your own Gemini API key from Google AI Studio. The app also works without a key, using the rule-based advisor.
5. Start the backend:

```
python -m uvicorn main:app --reload
```

6. Open `index.html` with the VS Code Live Server extension (default `http://127.0.0.1:5500`). The backend allows this address through CORS.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/students/{student_id}/courses` | List a student's courses |
| POST | `/api/students/{student_id}/courses` | Add a course |
| PUT | `/api/students/{student_id}/courses/{course_id}` | Edit a course |
| DELETE | `/api/students/{student_id}/courses/{course_id}` | Delete a course |
| GET | `/api/students/{student_id}/gpa/cumulative` | Cumulative GPA |
| GET | `/api/students/{student_id}/gpa/semesters/{semester}` | GPA for one semester |
| GET | `/api/students/{student_id}/analytics` | Trend, strongest and weakest courses, grade distribution |
| GET | `/api/students/{student_id}/advisor` | Recommendations and suggested questions |
| POST | `/api/students/{student_id}/advisor/ask` | Ask the advisor a question |

GPA = sum(credits × grade points) ÷ sum(credits), rounded to 2 decimals. A student with no courses gets `0.0` along with `total_credits: 0`, so "no data" can be told apart from a real 0.0.

## Known limitations

- There is no login yet: the app uses a fixed student (ID 1). The student ID is already part of every endpoint, so authentication can be added without redesigning the API.
- Semesters are free text, so the trend assumes courses are added in chronological order.
- The backend runs locally and is not deployed.
- AI requests send the student's course data to Google's Gemini API, and the free tier has rate limits and may have different data-use terms from paid tiers. Use sample data when demoing, and review the provider's terms before using real student records.
- Test coverage is manual, using the `/docs` page and the browser.

## Roadmap

- User accounts and authentication
- SQLAlchemy and database migrations, then PostgreSQL for multi-user use
- A structured semester field for reliable ordering
- A floating chat assistant with conversation history
- Automated tests and deployment

## Author

Built by Obsa Bekuma as a first project. GitHub: github.com/ObsaDaG