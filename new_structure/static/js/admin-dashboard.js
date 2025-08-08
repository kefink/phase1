/**
 * Admin Dashboard JavaScript
 * Handles dashboard-specific functionality and charts
 */

document.addEventListener("DOMContentLoaded", function () {
  initSystemPerformanceChart();
  initUserRegistrationChart();
  setupDashboardRefresh();
  handlePeriodSelection();
});

/**
 * Initialize the system performance chart
 */
function initSystemPerformanceChart() {
  const systemChart = document.getElementById("system-performance-chart");
  if (!systemChart) return;

  // Get data from the element's data attribute
  let chartData;
  try {
    chartData = JSON.parse(systemChart.dataset.stats);
  } catch (e) {
    console.error("Error parsing system stats data:", e);
    // Fallback data for development/testing
    chartData = {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      memory: [78, 65, 82, 75, 85, 72],
      cpu: [45, 53, 60, 40, 48, 50],
      storage: [65, 66, 68, 70, 72, 75],
    };
  }

  // Create canvas element for the chart
  const canvas = document.createElement("canvas");
  systemChart.appendChild(canvas);

  // Initialize chart using Chart.js
  if (typeof Chart !== "undefined") {
    new Chart(canvas, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: "Memory Usage",
            data: chartData.memory,
            backgroundColor: "rgba(42, 161, 152, 0.1)",
            borderColor: "rgba(42, 161, 152, 1)",
            borderWidth: 2,
            pointBackgroundColor: "rgba(42, 161, 152, 1)",
            tension: 0.3,
          },
          {
            label: "CPU Load",
            data: chartData.cpu,
            backgroundColor: "rgba(38, 139, 210, 0.1)",
            borderColor: "rgba(38, 139, 210, 1)",
            borderWidth: 2,
            pointBackgroundColor: "rgba(38, 139, 210, 1)",
            tension: 0.3,
          },
          {
            label: "Storage",
            data: chartData.storage,
            backgroundColor: "rgba(133, 153, 0, 0.1)",
            borderColor: "rgba(133, 153, 0, 1)",
            borderWidth: 2,
            pointBackgroundColor: "rgba(133, 153, 0, 1)",
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
          tooltip: {
            mode: "index",
            intersect: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
  } else {
    // Fallback if Chart.js is not available
    systemChart.innerHTML =
      '<div class="chart-fallback">Chart library not loaded. Please check your internet connection.</div>';
  }
}

/**
 * Initialize the user registration chart
 */
function initUserRegistrationChart() {
  const registrationChart = document.getElementById("user-registration-chart");
  if (!registrationChart) return;

  // Get data from the element's data attribute
  let chartData;
  try {
    chartData = JSON.parse(registrationChart.dataset.stats);
  } catch (e) {
    console.error("Error parsing registration stats data:", e);
    // Fallback data for development/testing
    chartData = {
      day: {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        students: [3, 5, 2, 7, 4, 2, 1],
        teachers: [1, 0, 2, 1, 1, 0, 0],
        parents: [2, 4, 1, 5, 3, 1, 0],
      },
      week: {
        labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
        students: [12, 18, 15, 22],
        teachers: [3, 2, 4, 5],
        parents: [8, 12, 10, 15],
      },
      month: {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        students: [45, 52, 38, 65, 48, 56],
        teachers: [8, 12, 5, 15, 10, 14],
        parents: [32, 38, 25, 42, 30, 45],
      },
    };
  }

  // Create canvas element for the chart
  const canvas = document.createElement("canvas");
  registrationChart.appendChild(canvas);

  // Initialize chart with day data by default
  let currentPeriod = "day";
  let chart;

  if (typeof Chart !== "undefined") {
    chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: chartData[currentPeriod].labels,
        datasets: [
          {
            label: "Students",
            data: chartData[currentPeriod].students,
            backgroundColor: "rgba(38, 139, 210, 0.7)",
            borderColor: "rgba(38, 139, 210, 1)",
            borderWidth: 1,
          },
          {
            label: "Teachers",
            data: chartData[currentPeriod].teachers,
            backgroundColor: "rgba(42, 161, 152, 0.7)",
            borderColor: "rgba(42, 161, 152, 1)",
            borderWidth: 1,
          },
          {
            label: "Parents",
            data: chartData[currentPeriod].parents,
            backgroundColor: "rgba(133, 153, 0, 0.7)",
            borderColor: "rgba(133, 153, 0, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
          },
          tooltip: {
            mode: "index",
            intersect: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
            },
          },
        },
      },
    });

    // Store chart instance for later updates
    registrationChart.chart = chart;
  } else {
    // Fallback if Chart.js is not available
    registrationChart.innerHTML =
      '<div class="chart-fallback">Chart library not loaded. Please check your internet connection.</div>';
  }
}

/**
 * Update chart data based on selected period
 * @param {string} period - The selected period (day, week, month)
 */
function updateRegistrationChart(period) {
  const registrationChart = document.getElementById("user-registration-chart");
  if (!registrationChart || !registrationChart.chart) return;

  // Get data from the element's data attribute
  let chartData;
  try {
    chartData = JSON.parse(registrationChart.dataset.stats);
  } catch (e) {
    console.error("Error parsing registration stats data:", e);
    return;
  }

  // Update chart data
  const chart = registrationChart.chart;
  chart.data.labels = chartData[period].labels;
  chart.data.datasets[0].data = chartData[period].students;
  chart.data.datasets[1].data = chartData[period].teachers;
  chart.data.datasets[2].data = chartData[period].parents;

  // Update chart
  chart.update();
}

/**
 * Set up handlers for period selection buttons
 */
function handlePeriodSelection() {
  const periodButtons = document.querySelectorAll("[data-period]");

  periodButtons.forEach((button) => {
    button.addEventListener("click", function () {
      // Remove active class from all buttons
      periodButtons.forEach((btn) => {
        btn.classList.remove("active");
      });

      // Add active class to clicked button
      this.classList.add("active");

      // Update chart with selected period
      const period = this.getAttribute("data-period");
      updateRegistrationChart(period);
    });
  });
}

/**
 * Set up dashboard refresh functionality
 */
function setupDashboardRefresh() {
  const refreshButton = document.getElementById("refresh-dashboard");

  if (refreshButton) {
    refreshButton.addEventListener("click", function () {
      // Show loading state
      this.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
      this.disabled = true;

      // Simulate refresh (in a real app, this would fetch new data from the server)
      setTimeout(() => {
        // Refresh charts
        initSystemPerformanceChart();
        initUserRegistrationChart();

        // Reset button
        this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        this.disabled = false;

        // Show success message
        showToast("Dashboard data refreshed successfully", "success");
      }, 1500);
    });
  }
}

/**
 * Show toast notification
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error, warning, info)
 * @param {number} duration - The duration to show the notification in ms
 */
function showToast(message, type = "info", duration = 3000) {
  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector(".toast-container");

  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.classList.add("toast-container");
    document.body.appendChild(toastContainer);
  }

  // Create toast element
  const toast = document.createElement("div");
  toast.classList.add("toast", `toast-${type}`);

  // Add toast content
  toast.innerHTML = `
        <div class="toast-content">
            <i class="toast-icon fas fa-${getToastIcon(type)}"></i>
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close">&times;</button>
    `;

  // Add toast to container
  toastContainer.appendChild(toast);

  // Show toast (add animation)
  setTimeout(() => {
    toast.classList.add("show");
  }, 10);

  // Set up close button
  const closeBtn = toast.querySelector(".toast-close");
  closeBtn.addEventListener("click", () => {
    closeToast(toast);
  });

  // Auto-close after duration
  if (duration) {
    setTimeout(() => {
      closeToast(toast);
    }, duration);
  }
}

/**
 * Close toast notification
 * @param {HTMLElement} toast - The toast element to close
 */
function closeToast(toast) {
  toast.classList.remove("show");

  // Remove from DOM after animation
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 300);
}

/**
 * Get icon for toast notification type
 * @param {string} type - The notification type
 * @returns {string} Icon name
 */
function getToastIcon(type) {
  switch (type) {
    case "success":
      return "check-circle";
    case "error":
      return "exclamation-circle";
    case "warning":
      return "exclamation-triangle";
    case "info":
    default:
      return "info-circle";
  }
}
