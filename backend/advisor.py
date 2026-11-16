import hashlib
import json

from analytics import gpa_by_semester, gpa_trend, grade_distribution, strongest_and_weakest
from gpa import calculate_gpa
from ai_service import generate_text

TARGET_GPA = 3.5
NEXT_SEMESTER_CREDITS = 15

SUGGESTED_QUESTIONS = [
    {"id": "overview", "text": "Give me an overview of my performance"},
    {"id": "focus", "text": "What should I focus on first?"},
    {"id": "plan", "text": "Make me a study plan"},
    {"id": "target", "text": "What GPA do I need next semester to reach 3.5?"},
]

RULES = (
    "You are an academic advisor inside a student dashboard. "
    "Rules about the student's data: use ONLY the numbers and courses in the FACTS section. "
    "Never invent grades, courses, deadlines, habits, past study methods or personal circumstances. "
    "Do not do your own arithmetic: use the numbers given. "
    "Do not predict future grades or outcomes. "
    "Rules about advice: you MAY give general, widely accepted study advice, such as spaced "
    "practice, working through practice problems, reviewing mistakes, going to office hours or "
    "forming a study group. Present it as a general suggestion, never as something the student "
    "already did and never as a guaranteed result. Link the advice to the student's courses "
    "and grades from the FACTS when it fits, starting with the courses that affect the GPA most. "
    "If an answer needs information you do not have, such as the student's schedule or free "
    "hours, give a short general answer and ask one question about it. "
    "Keep the answer short, practical and encouraging. Plain text only, no markdown."
)

_cache = {}


def points_lost(course):
    return course["credits"] * (4.0 - course["grade"])


def gpa_needed(courses, target, next_credits):
    total_credits = sum(course["credits"] for course in courses)
    points = sum(course["credits"] * course["grade"] for course in courses)
    needed = (target * (total_credits + next_credits) - points) / next_credits
    return round(needed, 2)


def build_facts(courses):
    semester_gpas = gpa_by_semester(courses)
    return {
        "course_count": len(courses),
        "total_credits": sum(course["credits"] for course in courses),
        "cumulative_gpa": calculate_gpa(courses),
        "courses": courses,
        "semester_gpas": semester_gpas,
        "trend": gpa_trend(semester_gpas),
        "grade_distribution": grade_distribution(courses),
        "strongest_and_weakest": strongest_and_weakest(courses),
        "gpa_needed_for_target": {
            "target_gpa": TARGET_GPA,
            "assumed_next_semester_credits": NEXT_SEMESTER_CREDITS,
            "required_gpa": gpa_needed(courses, TARGET_GPA, NEXT_SEMESTER_CREDITS),
        },
    }


# ---------- Rule-based versions (the fallback) ----------

def build_recommendations(courses):
    if len(courses) == 0:
        return [{"type": "info", "message": "Add your courses to get recommendations."}]

    recommendations = []
    cumulative = calculate_gpa(courses)

    biggest = max(courses, key=points_lost)
    if points_lost(biggest) > 0:
        recommendations.append({
            "type": "focus",
            "message": f"{biggest['course_name']} affects your GPA the most: "
                       f"{biggest['credits']} credits at a grade of {biggest['grade']:.2f}."
        })

    low = [course["course_name"] for course in courses if course["grade"] < 3.0]
    if low:
        recommendations.append({
            "type": "attention",
            "message": "These courses are below 3.0: " + ", ".join(low) + "."
        })

    trend = gpa_trend(gpa_by_semester(courses))
    if trend == "declining":
        recommendations.append({
            "type": "trend",
            "message": "Your GPA dropped compared with your previous semester."
        })
    elif trend == "improving":
        recommendations.append({
            "type": "trend",
            "message": "Your GPA is rising compared with your previous semester."
        })

    if cumulative >= 3.5:
        recommendations.append({
            "type": "strength",
            "message": f"Your cumulative GPA of {cumulative:.2f} is strong."
        })

    if len(recommendations) == 0:
        recommendations.append({
            "type": "info",
            "message": "Your grades look steady. Keep going."
        })

    return recommendations


def rule_answer(courses, question):
    if len(courses) == 0:
        return "Add your courses first, then I can help with that."

    q = question.lower()

    if "reach" in q or "need" in q:
        needed = gpa_needed(courses, TARGET_GPA, NEXT_SEMESTER_CREDITS)
        if needed > 4.0:
            return (f"Reaching {TARGET_GPA} in one semester is not possible with "
                    f"{NEXT_SEMESTER_CREDITS} credits. It would take more than one semester.")
        if needed <= 0:
            return (f"You already stay above {TARGET_GPA} whatever you score next semester "
                    f"(assuming {NEXT_SEMESTER_CREDITS} credits).")
        return (f"To reach a cumulative GPA of {TARGET_GPA}, you would need about {needed:.2f} "
                f"next semester, assuming {NEXT_SEMESTER_CREDITS} credits.")

    if "plan" in q:
        ranked = sorted(courses, key=points_lost, reverse=True)[:3]
        names = ", ".join(course["course_name"] for course in ranked)
        return ("Give the most study time to the courses that affect your GPA most: "
                + names + ". Review them a little every day instead of all at once.")

    if "focus" in q:
        biggest = max(courses, key=points_lost)
        return (f"Start with {biggest['course_name']}: it has {biggest['credits']} credits "
                f"at a grade of {biggest['grade']:.2f}, so improving it helps your GPA most.")

    return " ".join(item["message"] for item in build_recommendations(courses))


# ---------- AI versions ----------

def ai_recommendations(courses):
    facts = json.dumps(build_facts(courses), indent=2)
    prompt = (
        f"{RULES}\n\nFACTS:\n{facts}\n\n"
        "TASK: Write 3 to 5 short recommendations for this student. "
        "Put each recommendation on its own line, starting with '- '."
    )
    text = generate_text(prompt)
    lines = [line.strip()[2:].strip() for line in text.splitlines() if line.strip().startswith("- ")]
    if not lines:
        raise ValueError("The AI returned no recommendations")
    return [{"type": "ai", "message": line} for line in lines]


def get_recommendations(courses):
    if len(courses) == 0:
        return "rules", build_recommendations(courses)

    key = hashlib.sha256(json.dumps(courses, sort_keys=True).encode()).hexdigest()
    if key in _cache:
        return "ai", _cache[key]

    try:
        result = ai_recommendations(courses)
    except Exception as error:
        print("AI unavailable, using rules:", error)
        return "rules", build_recommendations(courses)

    _cache[key] = result
    return "ai", result


def answer_question(courses, question):
    if len(courses) == 0:
        return "rules", rule_answer(courses, question)

    facts = json.dumps(build_facts(courses), indent=2)
    prompt = (
        f"{RULES}\n\nFACTS:\n{facts}\n\n"
        f"The student asks: {question}\n"
        "Answer in at most 6 sentences. Give practical advice, not only a summary of the numbers."
    )

    try:
        return "ai", generate_text(prompt).strip()
    except Exception as error:
        print("AI unavailable, using rules:", error)
        return "rules", rule_answer(courses, question)

if __name__ == "__main__":
    test = [
        {"course_name": "Economics", "credits": 3, "grade": 4.0, "semester": "Fall 2025"},
        {"course_name": "Statistics", "credits": 6, "grade": 2.5, "semester": "Fall 2025"},
        {"course_name": "Programming", "credits": 3, "grade": 3.5, "semester": "Spring 2026"},
    ]
    source, items = get_recommendations(test)
    print("Source:", source)
    for item in items:
        print("-", item["message"])
    print()
    print(answer_question(test, "What GPA do I need next semester to reach 3.5?"))