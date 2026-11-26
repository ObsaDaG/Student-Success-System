const API_BASE =
  window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://student-success-api-hllh.onrender.com";

    const SESSION_KEY = "student-success-session";
let session = null;
let sessionPromise = null;

function forgetSession() {
  session = null;
  sessionPromise = null;
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (error) {}
}

async function startSession() {
  try {
    const saved = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    if (saved && saved.student_id && saved.token) {
      session = saved;
      return;
    }
  } catch (error) {}

  const response = await fetch(`${API_BASE}/api/session`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Could not start a session");
  }
  session = await response.json();
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch (error) {}
}

function ensureSession() {
  if (!sessionPromise) {
    sessionPromise = startSession();
  }
  return sessionPromise;
}

async function apiFetch(path, options = {}) {
  for (let attempt = 0; attempt < 2; attempt++) {
    await ensureSession();
    const response = await fetch(`${API_BASE}/api/students/${session.student_id}${path}`, {
      ...options,
      headers: { ...(options.headers || {}), "X-Session-Token": session.token }
    });
    if (response.status !== 403) {
      return response;
    }
    forgetSession();
  }
  throw new Error("Could not start a session");
}


const form = document.getElementById("courseForm");
const table = document.getElementById("courseTable");
const message = document.getElementById("formMessage");
const submitButton = document.getElementById("submitCourseButton");
const cancelEditButton = document.getElementById("cancelEditButton");

let courses = [];
let chart = null;
let editingCourseId = null;



function resetFormState() {
  editingCourseId = null;
  form.reset();
  document.getElementById("credits").value = 3;
  submitButton.textContent = "+ Add course";
  cancelEditButton.classList.add("hidden");
  message.style.color = "#b42318";
  message.textContent = "";
}





async function loadCoursesFromBackend() {
  try {
    const response = await apiFetch("/courses");
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
    message.style.color = "#b42318";
    message.textContent = "Could not load courses. Is the backend running?";
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

async function deleteCourse(id) {
  try {
    const response = await apiFetch(`/courses/${id}`, {
      method: "DELETE"
    });
    if (!response.ok) {
      message.style.color = "#b42318";
      message.textContent = "Could not delete this course.";
      return;
    }
  } catch (error) {
    message.style.color = "#b42318";
    message.textContent = "Could not reach the backend.";
    return;
  }

  if (editingCourseId === id) {
    resetFormState();
  }

  await loadCoursesFromBackend();
  message.style.color = "#18845b";
  message.textContent = "Course deleted.";
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
        renderChart();
  updateCourseDrops();  
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
    try {
      const response =await apiFetch(/courses/${editingCourseId}, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_name: name,
          credits,
          semester,
          grade
        })
      });
      if (!response.ok) {
        message.textContent = "The server rejected this update.";
        return;
      }
    } catch (error) {
      message.textContent = "Could not reach the backend.";
      return;
    }

    resetFormState();
    await loadCoursesFromBackend();
    message.style.color = "#18845b";
    message.textContent = "Course updated successfully.";
    return;
  }

  try {
const response = await apiFetch("/courses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_name: name,
        credits,
        semester,
        grade
      })
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


function fillDrop(listId, list, note) {
  const dropList = document.getElementById(listId);
  if (!dropList) {
    return;
  }
  dropList.replaceChildren();

  if (list.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No courses yet.";
    dropList.appendChild(empty);
    return;
  }

  if (note) {
    const noteItem = document.createElement("li");
    noteItem.className = "drop-note";
    noteItem.textContent = note;
    dropList.appendChild(noteItem);
  }

  list.forEach(course => {
    const li = document.createElement("li");

    const name = document.createElement("span");
    name.className = "drop-name";
    name.textContent = course.name;

    const grade = document.createElement("span");
    grade.className = "drop-grade";
    grade.textContent = course.grade.toFixed(2);

    const meta = document.createElement("span");
    meta.className = "drop-meta";
    meta.textContent = `${course.semester || "No semester"} · ${course.credits} credits`;

    li.append(name, grade, meta);
    dropList.appendChild(li);
  });
}

function updateCourseDrops() {
  console.log("updateCourseDrops sees", courses.length, "courses:", JSON.stringify(courses));

  if (courses.length === 0) {
    fillDrop("strongestDrop", [], "");
    fillDrop("weakestDrop", [], "");
    return;
  }

  const grades = courses.map(course => Number(course.grade));
  const best = Math.max(...grades);
  const worst = Math.min(...grades);
  console.log("best grade:", best, "worst grade:", worst);

  const strongest = courses
    .filter(course => Number(course.grade) === best)
    .sort((a, b) => b.credits - a.credits);
  const weakest = courses
    .filter(course => Number(course.grade) === worst)
    .sort((a, b) => b.credits - a.credits);

  const sameNote = best === worst && courses.length > 1
    ? "All your courses share the same grade, so each one is both the strongest and the weakest."
    : "";

  fillDrop("strongestDrop", strongest, sameNote);
  fillDrop("weakestDrop", weakest, sameNote);
}

function setupCardToggle(cardId, dropId) {
  const card = document.getElementById(cardId);
  const drop = document.getElementById(dropId);

  function toggle() {
    const isOpen = card.getAttribute("aria-expanded") === "true";
    card.setAttribute("aria-expanded", String(!isOpen));
    card.classList.toggle("open", !isOpen);
    drop.hidden = isOpen;
  }

  card.addEventListener("click", event => {
    if (event.target.closest(".course-drop")) {
      return;
    }
    toggle();
  });

  card.addEventListener("keydown", event => {
    if (event.target !== card) {
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle();
    }
  });
}

setupCardToggle("strongestCard", "strongestDrop");
setupCardToggle("weakestCard", "weakestDrop");

const ADVISOR_URL = await apiFetch("/advisor")

function sourceLabel(source) {
  return source === "ai" ? "AI-generated" : "Rule-based";
}

function addLogEntry(kind, text) {
  const log = document.getElementById("advisorLog");
  const entry = document.createElement("div");
  entry.className = `log-entry ${kind}`;
  entry.textContent = text;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
  return entry;
}

function renderSuggestions(questions) {
  const box = document.getElementById("advisorSuggestions");
  box.replaceChildren();
  questions.forEach(item => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "suggestion";
    button.textContent = item.text;
    button.addEventListener("click", () => askAdvisor(item.text));
    box.appendChild(button);
  });
}

async function loadAdvisor() {
  const list = document.getElementById("advisorList");
  const badge = document.getElementById("advisorSource");

  try {
    const response = await apiFetch("/advisor");
    if (!response.ok) {
      throw new Error("Advisor request failed");
    }
    const data = await response.json();

    list.replaceChildren();
    data.recommendations.forEach(item => {
      const li = document.createElement("li");
      li.textContent = item.message;
      list.appendChild(li);
    });
    badge.textContent = sourceLabel(data.source);
    renderSuggestions(data.suggested_questions);
  } catch (error) {
    badge.textContent = "-";
    list.replaceChildren();
    const li = document.createElement("li");
    li.textContent = "Could not load recommendations. Is the backend running?";
    list.appendChild(li);
  }
}

async function askAdvisor(question) {
  const text = question.trim();
  if (!text) {
    return;
  }

  const input = document.getElementById("advisorInput");
  const send = document.getElementById("advisorSend");
  const buttons = document.querySelectorAll(".suggestion");

  addLogEntry("question", text);
  const pending = addLogEntry("answer", "Thinking...");
  input.value = "";
  send.disabled = true;
  buttons.forEach(button => { button.disabled = true; });

  try {
    const response = await fetch(`${ADVISOR_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text })
    });
    if (!response.ok) {
      throw new Error("Request failed");
    }
    const data = await response.json();

    pending.textContent = data.answer;
    const tag = document.createElement("small");
    tag.className = "log-source";
    tag.textContent = sourceLabel(data.source);
    pending.appendChild(tag);
  } catch (error) {
    pending.textContent = "Could not get an answer. Please try again.";
  } finally {
    send.disabled = false;
    buttons.forEach(button => { button.disabled = false; });
  }
}

document.getElementById("advisorSend").addEventListener("click", () => {
  askAdvisor(document.getElementById("advisorInput").value);
});

document.getElementById("advisorInput").addEventListener("keydown", event => {
  if (event.key === "Enter") {
    askAdvisor(event.target.value);
  }
});

function describeCourses(list) {
  if (list.length === 0) {
    return { title: "-", note: "" };
  }
  const extra = list.length > 1 ? ` +${list.length - 1} more` : "";
  return {
    title: list[0].course_name + extra,
    note: `Grade ${list[0].grade.toFixed(2)}`
  };
}

async function loadAnalytics() {
  try {
    const response = await apiFetch("/analytics");
    const data = await response.json();

     updateCourseDrops();

    const trendLabels = {
      "improving": "Improving ↑",
      "declining": "Declining ↓",
      "stable": "Stable →",
      "not enough data": "Not enough data"
    };
    document.getElementById("trendValue").textContent = trendLabels[data.trend] || "-";
    document.getElementById("trendNote").textContent =
      data.trend === "not enough data"
        ? "Add a second semester to see your trend"
        : "Compared with your previous semester";

    const best = describeCourses(data.strongest_and_weakest.strongest);
    const worst = describeCourses(data.strongest_and_weakest.weakest);
    document.getElementById("strongestValue").textContent = best.title;
    document.getElementById("strongestNote").textContent = best.note;
    document.getElementById("weakestValue").textContent = worst.title;
    document.getElementById("weakestNote").textContent = worst.note;

    const list = document.getElementById("semesterList");
    list.replaceChildren();
    data.semester_gpas.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.semester}: ${item.gpa.toFixed(2)}`;
      list.appendChild(li);
    });
  } catch (error) {
    console.log("Could not load analytics:", error);
  }
}

const sidebarToggle = document.getElementById("sidebarToggle");
const sidebarBackdrop = document.getElementById("sidebarBackdrop");
const mobileQuery = window.matchMedia("(max-width: 768px)");

function setSidebar(collapsed, save = true) {
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
  if (save && !mobileQuery.matches) {
    try {
      localStorage.setItem("sidebarCollapsed", collapsed ? "1" : "0");
    } catch (e) {}
  }
}

function applyDefaultSidebar() {
  if (mobileQuery.matches) {
    setSidebar(true, false);          // closed by default on phones
  } else {
    let saved = false;
    try {
      saved = localStorage.getItem("sidebarCollapsed") === "1";
    } catch (e) {}
    setSidebar(saved, false);
  }
}

sidebarToggle.addEventListener("click", () => {
  setSidebar(!document.body.classList.contains("sidebar-collapsed"));
});

sidebarBackdrop.addEventListener("click", () => setSidebar(true));

// on mobile, close the sidebar after choosing a section
document.querySelectorAll(".sidebar a").forEach(link => {
  link.addEventListener("click", event => {
    const id = link.getAttribute("href");
    const target = id && id.startsWith("#") ? document.querySelector(id) : null;
    if (!target) return;

    event.preventDefault();

    // update the active link highlight
    document.querySelectorAll(".sidebar a").forEach(a => a.classList.remove("active"));
    link.classList.add("active");

    if (mobileQuery.matches) setSidebar(true);

    // wait one frame so the sidebar starts closing, then scroll
    requestAnimationFrame(() => {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", id);
    });
  });
});


renderDashboard();
loadAnalytics();
loadCoursesFromBackend();
loadAdvisor();
