def calculate_gpa(courses):
    if len(courses) == 0:
        return 0.0

    total_points = 0
    total_credits = 0

    for course in courses:
        total_points += course["credits"] * course["grade"]
        total_credits += course["credits"]

    return round(total_points / total_credits, 2)

if __name__ == "__main__":
    test = [
       
        {"credits": 4, "grade": 3.5},
        {"credits": 3, "grade": 4.0},
    ]
    print(calculate_gpa(test))