// Student Dashboard - Dashboard JavaScript

// Initialize dashboard charts and data visualizations
document.addEventListener("DOMContentLoaded", function () {
  // Initialize progress charts
  initProgressCharts();

  // Initialize grade charts
  initGradeCharts();

  // Initialize attendance chart
  initAttendanceChart();

  // Setup dashboard refresh
  setupDashboardRefresh();

  // Initialize calendar
  initCalendar();
});

// Initialize progress charts
function initProgressCharts() {
  const progressCharts = document.querySelectorAll(".progress-chart");

  progressCharts.forEach(function (chartElement) {
    const percentage =
      parseInt(chartElement.getAttribute("data-percentage")) || 0;
    const color = chartElement.getAttribute("data-color") || "#2aa198";

    drawProgressChart(chartElement, percentage, color);
  });
}

// Draw progress chart
function drawProgressChart(element, percentage, color) {
  if (!element) return;

  const canvas = document.createElement("canvas");
  element.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) * 0.8;

  // Draw background circle
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
  ctx.lineWidth = 10;
  ctx.stroke();

  // Draw progress arc
  const startAngle = -0.5 * Math.PI; // Start at top (0 degrees in radians)
  const endAngle = startAngle + (percentage / 100) * 2 * Math.PI;

  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, startAngle, endAngle);
  ctx.strokeStyle = color;
  ctx.lineWidth = 10;
  ctx.stroke();

  // Draw percentage text
  ctx.font = "bold 24px Inter, sans-serif";
  ctx.fillStyle = "#fff";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(percentage + "%", centerX, centerY);
}

// Initialize grade charts
function initGradeCharts() {
  const gradeChartElements = document.querySelectorAll(".grade-chart");

  gradeChartElements.forEach(function (chartElement) {
    // Extract data from element
    const subjectName = chartElement.getAttribute("data-subject");
    const grades = JSON.parse(chartElement.getAttribute("data-grades") || "[]");

    drawGradeChart(chartElement, subjectName, grades);
  });
}

// Draw grade chart
function drawGradeChart(element, subjectName, grades) {
  if (!element || !grades.length) return;

  const canvas = document.createElement("canvas");
  element.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  // Chart dimensions
  const width = canvas.width;
  const height = canvas.height;
  const padding = 40;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;

  // Scale for y-axis (grades)
  const maxGrade = Math.max(...grades.map((g) => g.value), 100);
  const yScale = chartHeight / maxGrade;

  // Scale for x-axis (time periods)
  const xScale = chartWidth / (grades.length - 1);

  // Draw axes
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
  ctx.lineWidth = 1;
  ctx.stroke();

  // Draw grade line
  ctx.beginPath();
  ctx.moveTo(padding, height - padding - grades[0].value * yScale);

  for (let i = 1; i < grades.length; i++) {
    const x = padding + i * xScale;
    const y = height - padding - grades[i].value * yScale;
    ctx.lineTo(x, y);
  }

  ctx.strokeStyle = "#2aa198";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Draw points
  for (let i = 0; i < grades.length; i++) {
    const x = padding + i * xScale;
    const y = height - padding - grades[i].value * yScale;

    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fillStyle = "#2aa198";
    ctx.fill();
  }

  // Draw labels
  ctx.font = "10px Inter, sans-serif";
  ctx.fillStyle = "rgba(255, 255, 255, 0.7)";
  ctx.textAlign = "center";

  for (let i = 0; i < grades.length; i++) {
    const x = padding + i * xScale;
    const y = height - padding + 15;
    ctx.fillText(grades[i].label, x, y);
  }

  // Draw subject name
  ctx.font = "bold 14px Inter, sans-serif";
  ctx.fillStyle = "#fff";
  ctx.textAlign = "center";
  ctx.fillText(subjectName, width / 2, padding / 2);
}

// Initialize attendance chart
function initAttendanceChart() {
  const attendanceChartElement = document.getElementById("attendance-chart");

  if (!attendanceChartElement) return;

  const attendance = JSON.parse(
    attendanceChartElement.getAttribute("data-attendance") || "{}"
  );

  drawAttendanceChart(attendanceChartElement, attendance);
}

// Draw attendance chart
function drawAttendanceChart(element, attendance) {
  if (!element) return;

  const canvas = document.createElement("canvas");
  element.appendChild(canvas);

  const ctx = canvas.getContext("2d");

  // Chart dimensions
  const width = canvas.width;
  const height = canvas.height;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(centerX, centerY) * 0.8;

  // Calculate angles
  const present = attendance.present || 0;
  const absent = attendance.absent || 0;
  const late = attendance.late || 0;
  const total = present + absent + late;

  const presentAngle = (present / total) * 2 * Math.PI;
  const absentAngle = (absent / total) * 2 * Math.PI;
  const lateAngle = (late / total) * 2 * Math.PI;

  // Draw pie chart
  let startAngle = 0;

  // Present slice
  ctx.beginPath();
  ctx.moveTo(centerX, centerY);
  ctx.arc(centerX, centerY, radius, startAngle, startAngle + presentAngle);
  ctx.closePath();
  ctx.fillStyle = "#859900"; // Green
  ctx.fill();

  startAngle += presentAngle;

  // Absent slice
  ctx.beginPath();
  ctx.moveTo(centerX, centerY);
  ctx.arc(centerX, centerY, radius, startAngle, startAngle + absentAngle);
  ctx.closePath();
  ctx.fillStyle = "#dc322f"; // Red
  ctx.fill();

  startAngle += absentAngle;

  // Late slice
  ctx.beginPath();
  ctx.moveTo(centerX, centerY);
  ctx.arc(centerX, centerY, radius, startAngle, startAngle + lateAngle);
  ctx.closePath();
  ctx.fillStyle = "#b58900"; // Yellow
  ctx.fill();

  // Draw legend
  const legendItems = [
    { label: "Present", color: "#859900", value: present },
    { label: "Absent", color: "#dc322f", value: absent },
    { label: "Late", color: "#b58900", value: late },
  ];

  const legendY = height - 60;
  const legendX = 20;
  const legendSpacing = 80;

  legendItems.forEach((item, index) => {
    const x = legendX + index * legendSpacing;

    // Color box
    ctx.beginPath();
    ctx.rect(x, legendY, 12, 12);
    ctx.fillStyle = item.color;
    ctx.fill();

    // Label
    ctx.font = "12px Inter, sans-serif";
    ctx.fillStyle = "#fff";
    ctx.textAlign = "left";
    ctx.fillText(`${item.label}: ${item.value}`, x + 18, legendY + 10);
  });
}

// Setup dashboard refresh
function setupDashboardRefresh() {
  const refreshBtn = document.getElementById("refresh-dashboard");

  if (refreshBtn) {
    refreshBtn.addEventListener("click", function () {
      refreshDashboard();
    });
  }
}

// Refresh dashboard data
function refreshDashboard() {
  const dashboardContent = document.querySelector(".dashboard-content");

  if (!dashboardContent) return;

  // Show loading overlay
  const loadingOverlay = document.createElement("div");
  loadingOverlay.className = "loading-overlay";
  loadingOverlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
        </div>
    `;

  dashboardContent.appendChild(loadingOverlay);

  // Fetch updated dashboard data
  fetch("/student/dashboard/refresh", {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      // Update dashboard with new data
      updateDashboardContent(data);

      // Show success message
      showToast("Dashboard refreshed successfully!", "success");
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast(
        "Failed to refresh dashboard. Please try again later.",
        "danger"
      );
    })
    .finally(() => {
      // Remove loading overlay
      loadingOverlay.remove();
    });
}

// Update dashboard content with new data
function updateDashboardContent(data) {
  // Update upcoming assignments
  updateUpcomingAssignments(data.upcomingAssignments);

  // Update recent grades
  updateRecentGrades(data.recentGrades);

  // Update attendance
  updateAttendance(data.attendance);

  // Update announcements
  updateAnnouncements(data.announcements);

  // Update calendar events
  updateCalendarEvents(data.events);
}

// Update upcoming assignments
function updateUpcomingAssignments(assignments) {
  const assignmentsList = document.querySelector(".upcoming-assignments-list");

  if (!assignmentsList || !assignments) return;

  // Clear existing assignments
  assignmentsList.innerHTML = "";

  if (assignments.length === 0) {
    assignmentsList.innerHTML =
      '<p class="empty-state">No upcoming assignments</p>';
    return;
  }

  // Add new assignments
  assignments.forEach((assignment) => {
    const assignmentItem = document.createElement("div");
    assignmentItem.className = "assignment-item";
    assignmentItem.innerHTML = `
            <div class="assignment-item-header">
                <h4 class="assignment-item-title">${assignment.title}</h4>
                <span class="assignment-item-subject">${
                  assignment.subject
                }</span>
            </div>
            <div class="assignment-item-details">
                <span class="assignment-item-due-date">
                    <i class="fas fa-calendar-alt"></i> Due: ${formatDate(
                      assignment.dueDate
                    )}
                </span>
                <a href="/student/assignment/${
                  assignment.id
                }" class="btn-sm btn-primary">View</a>
            </div>
        `;

    assignmentsList.appendChild(assignmentItem);
  });
}

// Update recent grades
function updateRecentGrades(grades) {
  const gradesList = document.querySelector(".recent-grades-list");

  if (!gradesList || !grades) return;

  // Clear existing grades
  gradesList.innerHTML = "";

  if (grades.length === 0) {
    gradesList.innerHTML = '<p class="empty-state">No recent grades</p>';
    return;
  }

  // Add new grades
  grades.forEach((grade) => {
    const gradeItem = document.createElement("div");
    gradeItem.className = "grade-item";

    let gradeClass = "";
    if (grade.score >= 80) {
      gradeClass = "text-success";
    } else if (grade.score >= 60) {
      gradeClass = "text-warning";
    } else {
      gradeClass = "text-danger";
    }

    gradeItem.innerHTML = `
            <div class="grade-item-header">
                <h4 class="grade-item-title">${grade.title}</h4>
                <span class="grade-item-subject">${grade.subject}</span>
            </div>
            <div class="grade-item-details">
                <span class="grade-item-score ${gradeClass}">${
      grade.score
    }%</span>
                <span class="grade-item-date">${formatDate(grade.date)}</span>
            </div>
        `;

    gradesList.appendChild(gradeItem);
  });
}

// Update attendance
function updateAttendance(attendance) {
  const attendanceElement = document.getElementById("attendance-chart");

  if (!attendanceElement || !attendance) return;

  // Update attendance data attribute
  attendanceElement.setAttribute("data-attendance", JSON.stringify(attendance));

  // Clear existing chart
  attendanceElement.innerHTML = "";

  // Draw new chart
  drawAttendanceChart(attendanceElement, attendance);

  // Update attendance stats
  const attendanceStats = document.querySelector(".attendance-stats");
  if (attendanceStats) {
    const total = attendance.present + attendance.absent + attendance.late;
    const presentPercentage = Math.round((attendance.present / total) * 100);

    attendanceStats.innerHTML = `
            <div class="stat-item">
                <span class="stat-value">${presentPercentage}%</span>
                <span class="stat-label">Attendance Rate</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${attendance.present}</span>
                <span class="stat-label">Present</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${attendance.absent}</span>
                <span class="stat-label">Absent</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${attendance.late}</span>
                <span class="stat-label">Late</span>
            </div>
        `;
  }
}

// Update announcements
function updateAnnouncements(announcements) {
  const announcementsList = document.querySelector(".announcements-list");

  if (!announcementsList || !announcements) return;

  // Clear existing announcements
  announcementsList.innerHTML = "";

  if (announcements.length === 0) {
    announcementsList.innerHTML = '<p class="empty-state">No announcements</p>';
    return;
  }

  // Add new announcements
  announcements.forEach((announcement) => {
    const announcementItem = document.createElement("div");
    announcementItem.className = "announcement-item";
    announcementItem.innerHTML = `
            <div class="announcement-item-header">
                <h4 class="announcement-item-title">${announcement.title}</h4>
                <span class="announcement-item-date">${formatDate(
                  announcement.date
                )}</span>
            </div>
            <div class="announcement-item-content">
                <p>${announcement.content}</p>
            </div>
            <div class="announcement-item-footer">
                <span class="announcement-item-author">Posted by: ${
                  announcement.author
                }</span>
            </div>
        `;

    announcementsList.appendChild(announcementItem);
  });
}

// Initialize calendar
function initCalendar() {
  const calendarElement = document.getElementById("student-calendar");

  if (!calendarElement) return;

  const events = JSON.parse(
    calendarElement.getAttribute("data-events") || "[]"
  );

  renderCalendar(calendarElement, events);
}

// Render calendar
function renderCalendar(element, events) {
  if (!element) return;

  // Get current date
  const currentDate = new Date();
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  // Create calendar header
  const calendarHeader = document.createElement("div");
  calendarHeader.className = "calendar-header";
  calendarHeader.innerHTML = `
        <button class="btn-sm btn-outline calendar-prev-month">
            <i class="fas fa-chevron-left"></i>
        </button>
        <h4 class="calendar-title">${getMonthName(
          currentMonth
        )} ${currentYear}</h4>
        <button class="btn-sm btn-outline calendar-next-month">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;

  element.appendChild(calendarHeader);

  // Create calendar grid
  const calendarGrid = document.createElement("div");
  calendarGrid.className = "calendar-grid";

  // Add day headers
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  dayNames.forEach((day) => {
    const dayHeader = document.createElement("div");
    dayHeader.className = "calendar-day-header";
    dayHeader.textContent = day;
    calendarGrid.appendChild(dayHeader);
  });

  // Get first day of month and number of days in month
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

  // Add empty cells for days before first day of month
  for (let i = 0; i < firstDayOfMonth; i++) {
    const emptyCell = document.createElement("div");
    emptyCell.className = "calendar-day empty";
    calendarGrid.appendChild(emptyCell);
  }

  // Add cells for each day of the month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayCell = document.createElement("div");
    dayCell.className = "calendar-day";

    // Highlight current day
    if (
      day === currentDate.getDate() &&
      currentMonth === currentDate.getMonth() &&
      currentYear === currentDate.getFullYear()
    ) {
      dayCell.classList.add("today");
    }

    // Add day number
    const dayNumber = document.createElement("div");
    dayNumber.className = "calendar-day-number";
    dayNumber.textContent = day;
    dayCell.appendChild(dayNumber);

    // Add events for this day
    const dayEvents = events.filter((event) => {
      const eventDate = new Date(event.date);
      return (
        eventDate.getDate() === day &&
        eventDate.getMonth() === currentMonth &&
        eventDate.getFullYear() === currentYear
      );
    });

    if (dayEvents.length > 0) {
      const eventsList = document.createElement("div");
      eventsList.className = "calendar-day-events";

      dayEvents.forEach((event) => {
        const eventItem = document.createElement("div");
        eventItem.className = `calendar-event ${event.type}-event`;
        eventItem.setAttribute("data-tooltip", event.title);
        eventItem.textContent = event.title;
        eventsList.appendChild(eventItem);
      });

      dayCell.appendChild(eventsList);
    }

    calendarGrid.appendChild(dayCell);
  }

  element.appendChild(calendarGrid);

  // Setup calendar navigation
  const prevMonthBtn = element.querySelector(".calendar-prev-month");
  const nextMonthBtn = element.querySelector(".calendar-next-month");

  prevMonthBtn.addEventListener("click", function () {
    navigateCalendar(element, events, -1);
  });

  nextMonthBtn.addEventListener("click", function () {
    navigateCalendar(element, events, 1);
  });
}

// Navigate calendar to previous or next month
function navigateCalendar(element, events, direction) {
  // Get current month and year from calendar title
  const calendarTitle = element.querySelector(".calendar-title");
  const [monthName, year] = calendarTitle.textContent.split(" ");

  let month = getMonthIndex(monthName);
  let newYear = parseInt(year);

  // Calculate new month and year
  month += direction;

  if (month < 0) {
    month = 11;
    newYear--;
  } else if (month > 11) {
    month = 0;
    newYear++;
  }

  // Clear calendar
  element.innerHTML = "";

  // Create new calendar with updated month and year
  renderCalendarWithDate(element, events, month, newYear);
}

// Render calendar with specific month and year
function renderCalendarWithDate(element, events, month, year) {
  if (!element) return;

  // Create calendar header
  const calendarHeader = document.createElement("div");
  calendarHeader.className = "calendar-header";
  calendarHeader.innerHTML = `
        <button class="btn-sm btn-outline calendar-prev-month">
            <i class="fas fa-chevron-left"></i>
        </button>
        <h4 class="calendar-title">${getMonthName(month)} ${year}</h4>
        <button class="btn-sm btn-outline calendar-next-month">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;

  element.appendChild(calendarHeader);

  // Create calendar grid
  const calendarGrid = document.createElement("div");
  calendarGrid.className = "calendar-grid";

  // Add day headers
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  dayNames.forEach((day) => {
    const dayHeader = document.createElement("div");
    dayHeader.className = "calendar-day-header";
    dayHeader.textContent = day;
    calendarGrid.appendChild(dayHeader);
  });

  // Get first day of month and number of days in month
  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Add empty cells for days before first day of month
  for (let i = 0; i < firstDayOfMonth; i++) {
    const emptyCell = document.createElement("div");
    emptyCell.className = "calendar-day empty";
    calendarGrid.appendChild(emptyCell);
  }

  // Get current date for comparison
  const currentDate = new Date();
  const currentDay = currentDate.getDate();
  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  // Add cells for each day of the month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayCell = document.createElement("div");
    dayCell.className = "calendar-day";

    // Highlight current day
    if (day === currentDay && month === currentMonth && year === currentYear) {
      dayCell.classList.add("today");
    }

    // Add day number
    const dayNumber = document.createElement("div");
    dayNumber.className = "calendar-day-number";
    dayNumber.textContent = day;
    dayCell.appendChild(dayNumber);

    // Add events for this day
    const dayEvents = events.filter((event) => {
      const eventDate = new Date(event.date);
      return (
        eventDate.getDate() === day &&
        eventDate.getMonth() === month &&
        eventDate.getFullYear() === year
      );
    });

    if (dayEvents.length > 0) {
      const eventsList = document.createElement("div");
      eventsList.className = "calendar-day-events";

      dayEvents.forEach((event) => {
        const eventItem = document.createElement("div");
        eventItem.className = `calendar-event ${event.type}-event`;
        eventItem.setAttribute("data-tooltip", event.title);
        eventItem.textContent = event.title;
        eventsList.appendChild(eventItem);
      });

      dayCell.appendChild(eventsList);
    }

    calendarGrid.appendChild(dayCell);
  }

  element.appendChild(calendarGrid);

  // Setup calendar navigation
  const prevMonthBtn = element.querySelector(".calendar-prev-month");
  const nextMonthBtn = element.querySelector(".calendar-next-month");

  prevMonthBtn.addEventListener("click", function () {
    navigateCalendar(element, events, -1);
  });

  nextMonthBtn.addEventListener("click", function () {
    navigateCalendar(element, events, 1);
  });
}

// Update calendar events
function updateCalendarEvents(events) {
  const calendarElement = document.getElementById("student-calendar");

  if (!calendarElement || !events) return;

  // Update events data attribute
  calendarElement.setAttribute("data-events", JSON.stringify(events));

  // Get current month and year from calendar title
  const calendarTitle = calendarElement.querySelector(".calendar-title");
  if (!calendarTitle) return;

  const [monthName, year] = calendarTitle.textContent.split(" ");
  const month = getMonthIndex(monthName);

  // Clear calendar
  calendarElement.innerHTML = "";

  // Recreate calendar with updated events
  renderCalendarWithDate(calendarElement, events, month, parseInt(year));
}

// Helper function to get month name
function getMonthName(monthIndex) {
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  return months[monthIndex];
}

// Helper function to get month index from name
function getMonthIndex(monthName) {
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  return months.indexOf(monthName);
}

// Helper function to format date
function formatDate(dateString) {
  const date = new Date(dateString);

  // Format date as "Month DD, YYYY"
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}
