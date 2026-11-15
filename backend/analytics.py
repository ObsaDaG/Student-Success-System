from gpa import calculate_gpa

def strongest_and_weakest(courses):
    if len(courses) == 0:
        return {"strongest": [], "weakest": []}

    best_grade = max(course["grade"] for course in courses)
    worst_grade = min(course["grade"] for course in courses)

    return {
        "strongest": [course for course in courses if course["grade"] == best_grade],
        "weakest": [course for course in courses if course["grade"] == worst_grade]
    }

def gpa_by_semester(courses):
    semesters = {}
    for course in courses:
        semesters.setdefault(course["semester"], []).append(course)

    return [
        {"semester": name, "gpa": calculate_gpa(group)}
        for name, group in semesters.items()
    ]

def gpa_trend(semester_gpas):
    if len(semester_gpas) < 2:
        return "not enough data"
   

    change = semester_gpas[-1]["gpa"] - semester_gpas[-2]["gpa"]

    if change > 0.1:
        return "improving"
    if change < -0.1:
        return "declining"
    return "stable"

def grade_distribution(courses):
    bands = {"4.0": 0, "3.0 to 3.99": 0, "2.0 to 2.99": 0, "below 2.0": 0}

    for course in courses:
        grade = course["grade"]
        if grade == 4.0:
            bands["4.0"] += 1
        elif grade >= 3.0:
            bands["3.0 to 3.99"] += 1
        elif grade >= 2.0:
            bands["2.0 to 2.99"] += 1
        else:
            bands["below 2.0"] += 1

    return bands