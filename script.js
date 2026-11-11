
const STORAGE_KEY = "student-success-courses";
const form = document.getElementById("courseForm");
const table = document.getElementById("courseTable");
const message = document.getElementById("formMessage");
const submitButton = document.getElementById("submitCourseButton");
const cancelEditButton = document.getElementById("cancelEditButton");

let courses = loadCourses();
let chart = null;
let editingCourseId = null;

function createCourseId() {
  if (window.crypto && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `course-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function resetFormState() {
  editingCourseId = null;
  form.reset();
  document.getElementById("credits").value = 3;
  submitButton.textContent = "+ Add course";
  cancelEditButton.classList.add("hidden");
  message.style.color = "#b42318";
  message.textContent = "";
}

function loadCourses() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(saved) ? saved.filter(course =>
      course &&
      typeof course.name === "string" &&
      Number.isFinite(course.credits) &&
      course.credits > 0 &&
      Number.isFinite(course.grade) &&
      course.grade >= 0 &&
      course.grade <= 4.0
    ).map(course => ({
      ...course,
      grade: course.grade === 4.3 ? 4 : course.grade,
      semester: typeof course.semester === "string" ? course.semester.trim() : ""
    })) : [];
  } catch {
    return [];
  }
}

function saveCourses() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(courses));
    return true;
  } catch {
    message.textContent = "Could not save data in this browser.";
    return false;
  }
}

async function loadCoursesFromBackend() {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/students/1/courses");
    const data = await response.json();

    courses.length = 0;
    data.courses.forEach(course => {
      courses.push({
        id: course.course_id,
        name: course.course_name,
        credits: course.credits,
        semester: course.semester,
        grade: course.grade
      });
    });

    renderDashboard();
  } catch (error) {
    console.log("Could not load from backend:", error);
  }
}

function calculateGPA(items) {
  const totalCredits = items.reduce((sum, course) => sum + course.credits, 0);
  if (totalCredits === 0) return 0;

  const weightedPoints = items.reduce(
    (sum, course) => sum + course.grade * course.credits, 0
  );

  return weightedPoints / totalCredits;
}

function startEditCourse(id) {
  const course = courses.find(item => item.id === id);
  if (!course) return;

  editingCourseId = id;
  document.getElementById("courseName").value = course.name;
  document.getElementById("credits").value = course.credits;
  document.getElementById("semester").value = course.semester || "";
  document.getElementById("grade").value = String(course.grade);
  submitButton.textContent = "Save changes";
  cancelEditButton.classList.remove("hidden");
  message.style.color = "#172a46";
  message.textContent = "Editing selected course.";
  document.getElementById("courseName").focus();
}

function deleteCourse(id) {
  const previousCourses = courses;
  courses = courses.filter(course => course.id !== id);

  if (editingCourseId === id) {
    resetFormState();
  }

  if (!saveCourses()) {
    courses = previousCourses;
    return;
  }

  message.style.color = "#18845b";
  message.textContent = "Course deleted.";
  renderDashboard();
}

function renderDashboard() {
  const totalCredits = courses.reduce((sum, course) => sum + course.credits, 0);
  const gpa = calculateGPA(courses);

  document.getElementById("gpaValue").textContent = gpa.toFixed(2);
  document.getElementById("courseCount").textContent = courses.length;
  document.getElementById("creditCount").textContent = totalCredits;
  document.getElementById("tableCount").textContent =
    `${courses.length} ${courses.length === 1 ? "course" : "courses"}`;

  if (courses.length === 0) {
    table.innerHTML = '<tr><td colspan="6" class="empty-state">No courses yet. Add your first course above.</td></tr>';
  } else {
    table.replaceChildren();

    courses.forEach(course => {
      const row = document.createElement("tr");

      const values = [
        course.name,
        course.semester || "-",
        String(course.credits),
        course.grade.toFixed(2),
        (course.credits * course.grade).toFixed(2)
      ];

      values.forEach(value => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      });

      const actionCell = document.createElement("td");
      const editButton = document.createElement("button");
      editButton.className = "edit-button";
      editButton.textContent = "Edit";
      editButton.type = "button";
      editButton.addEventListener("click", () => startEditCourse(course.id));

      const deleteButton = document.createElement("button");
      deleteButton.className = "delete-button";
      deleteButton.textContent = "Delete";
      deleteButton.type = "button";
      deleteButton.addEventListener("click", () => deleteCourse(course.id));

      actionCell.appendChild(editButton);
      actionCell.appendChild(deleteButton);
      row.appendChild(actionCell);
      table.appendChild(row);
    });
  }

  renderChart();
}

function renderChart() {
  const canvas = document.getElementById("gradeChart");
  const emptyMessage = document.getElementById("emptyChart");

  if (chart) {
    chart.destroy();
    chart = null;
  }

  emptyMessage.hidden = courses.length > 0;

  if (courses.length === 0) return;

  chart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: courses.map(course => course.name),
      datasets: [{
        label: "Grade points",
        data: courses.map(course => course.grade),
        backgroundColor: [
          "#3867e8",
          "#4c8dff",
          "#7a9cff",
          "#6db7ff",
          "#5b73d8",
          "#7c8cff"
        ],
        borderColor: "#1d4ed8",
        borderWidth: 1,
        borderRadius: 8,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 700, easing: "easeOutQuart" },
      scales: {
        y: {
          beginAtZero: true,
          max: 4,
          suggestedMax: 4,
          ticks: { stepSize: 0.5 },
          grid: { color: "rgba(120, 135, 165, 0.15)" }
        },
        x: {
          ticks: { maxRotation: 35, minRotation: 0 },
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#172a46",
          padding: 10,
          displayColors: false,
          callbacks: {
            label: context => `Grade: ${context.parsed.y.toFixed(2)}`
          }
        }
      }
    }
  });
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  message.style.color = "#b42318";
  message.textContent = "";

  const name = document.getElementById("courseName").value.trim();
  const credits = Number(document.getElementById("credits").value);
  const semester = document.getElementById("semester").value.trim();
  const grade = Number(document.getElementById("grade").value);

  if (!name || !semester || !Number.isInteger(credits) || credits < 1 || credits > 30 ||
      !Number.isFinite(grade) || grade < 0 || grade > 4) {
    message.textContent = "Enter a valid course name, semester, credit value, and grade.";
    return;
  }

  if (editingCourseId) {
    const course = courses.find(item => item.id === editingCourseId);
    if (!course) {
      message.textContent = "Could not find the course to update.";
      return;
    }

    course.name = name;
    course.credits = credits;
    course.semester = semester;
    course.grade = grade;

    if (!saveCourses()) {
      return;
    }

    message.style.color = "#18845b";
    message.textContent = "Course updated successfully.";
    resetFormState();
    renderDashboard();
    return;
  }

  try {
    const response = await fetch("http://127.0.0.1:8000/api/students/1/courses", {
      method: "POST",
      ...
    });
    if (!response.ok) {
      message.textContent = "The server rejected this course.";
      return;
    }
  } catch (error) {
    message.textContent = "Could not reach the backend.";
    return;
  }

  await loadCoursesFromBackend();
  form.reset();
  document.getElementById("credits").value = 3;
  message.style.color = "#18845b";
  message.textContent = "Course added successfully.";
});

cancelEditButton.addEventListener("click", () => {
  resetFormState();
  message.style.color = "#18845b";
  message.textContent = "Edit cancelled.";
});

renderDashboard();

loadCoursesFromBackend();
