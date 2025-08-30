// analytics_dashboard_fixed.js - CORRECTED CORE LOGIC

// ============================================================================
// GLOBAL STATE VARIABLES
// ============================================================================
let analyticsData = {};
let analyticsFilters = {
  termId: null,
  assessmentTypeId: null,
  gradeId: null,
  streamId: null,
  enhancedMode: false,
};
let availableOptions = {
  terms: [],
  assessmentTypes: [],
  grades: [],
  streams: [],
};
let isInitialLoad = true; // CRITICAL FLAG
let serverSideDataPresent = false; // Helper flag

console.log("🚀 Analytics Dashboard JavaScript FIXED VERSION loaded");

// ============================================================================
// INITIALIZATION
// ============================================================================
async function initializeAnalyticsDashboard() {
  console.log("🚀 initializeAnalyticsDashboard called");
  try {
    // Load available filter options first
    await loadFilterOptions();
    populateFilterDropdowns();

    // Load initial analytics data
    await loadAnalyticsData();

    // Mark initial load as complete AFTER data is loaded
    isInitialLoad = false;
    console.log("✅ Initial dashboard load complete");
  } catch (error) {
    console.error("Error initializing dashboard:", error);
    showAnalyticsError(
      "Failed to initialize dashboard. Please try refreshing the page."
    );
  }
}

// ============================================================================
// CORE DATA LOADING
// ============================================================================
async function loadAnalyticsData() {
  console.log("📊 loadAnalyticsData called");

  // CRITICAL FIX: Don't interfere with server-side rendered data on initial load
  if (isInitialLoad) {
    console.log(
      "🚫 BLOCKED: Initial load detected, preserving server-side data"
    );
    // Check if server-side data is present (basic check)
    const serverDataCheck = document.querySelector("#students-analyzed-value");
    if (serverDataCheck && serverDataCheck.textContent.trim() !== "") {
      console.log(
        "✅ Server-side data detected, skipping JS data load on initial load"
      );
      serverSideDataPresent = true;
      // We don't load data here, we let the server-rendered data stand.
      // The DOMContentLoaded event will trigger this function again after initial load if needed.
      return;
    }
  }

  console.log("🔥 Proceeding with JS data loading...");
  showLoadingState();

  try {
    const params = new URLSearchParams();
    if (analyticsFilters.termId)
      params.append("term_id", analyticsFilters.termId);
    if (analyticsFilters.assessmentTypeId)
      params.append("assessment_type_id", analyticsFilters.assessmentTypeId);
    if (analyticsFilters.gradeId)
      params.append("grade_id", analyticsFilters.gradeId);
    if (analyticsFilters.streamId)
      params.append("stream_id", analyticsFilters.streamId);

    const response = await fetch(
      `/api/analytics/dashboard?${params.toString()}`,
      {
        method: "GET",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      analyticsData = data.analytics_data;
      console.log("✅ Analytics data loaded:", analyticsData);
      updateAnalyticsDashboard(); // This will now run safely
    } else {
      throw new Error(data.message || "Failed to load analytics data");
    }
  } catch (error) {
    console.error("Error loading analytics data:", error);
    showAnalyticsError(`Failed to load analytics data: ${error.message}`);
  }
}

// ============================================================================
// DISPLAY FUNCTIONS
// ============================================================================
function updateAnalyticsDashboard() {
  console.log("🎯 updateAnalyticsDashboard called");

  // CRITICAL FIX: Don't interfere with server-side rendered data on initial load
  if (isInitialLoad) {
    console.log(
      "🚫 BLOCKED: Initial load detected in updateAnalyticsDashboard, preserving server-side data"
    );
    // Check if server-side data is present
    const serverDataCheck = document.querySelector("#students-analyzed-value");
    if (serverDataCheck && serverDataCheck.textContent.trim() !== "") {
      console.log(
        "✅ Server-side data confirmed, dashboard update blocked to prevent flicker"
      );
      return; // EXIT FUNCTION EARLY - THIS IS THE FIX
    }
  }

  console.log("📊 Updating dashboard with JS data...");
  hideNoDataState();

  // Update Summary Cards
  updateSummaryCards();

  // Update Top Performers
  updateTopPerformers();

  // Update Subject Performance
  updateSubjectPerformance();

  console.log("✅ Dashboard updated with JS data");
}

function updateSummaryCards() {
  if (!analyticsData.summary) return;

  console.log("📊 Updating summary cards with data:", analyticsData.summary);

  const summaryData = analyticsData.summary;

  // Update Students Analyzed
  const studentsElement = document.getElementById("students-analyzed-value");
  if (studentsElement) {
    studentsElement.textContent = summaryData.students_analyzed || 0;
    console.log(
      "Updated students analyzed:",
      summaryData.students_analyzed || 0
    );
  }

  // Update Subjects Analyzed
  const subjectsElement = document.getElementById("subjects-analyzed-value");
  if (subjectsElement) {
    subjectsElement.textContent = summaryData.subjects_analyzed || 0;
    console.log(
      "Updated subjects analyzed:",
      summaryData.subjects_analyzed || 0
    );
  }

  // Update Top Subject Performance
  const topSubjectElement = document.getElementById(
    "top-subject-performance-value"
  );
  if (topSubjectElement) {
    topSubjectElement.textContent = `${summaryData.top_subject_average || 0}%`;
    console.log(
      "Updated top subject average:",
      `${summaryData.top_subject_average || 0}%`
    );
  }

  // Update Top Student Performance
  const topStudentElement = document.getElementById(
    "best-student-performance-value"
  );
  if (topStudentElement) {
    topStudentElement.textContent = `${summaryData.top_student_average || 0}%`;
    console.log(
      "Updated top student average:",
      `${summaryData.top_student_average || 0}%`
    );
  }
}

function updateTopPerformers() {
  const container = document.getElementById("top-performers-container");
  if (!container) {
    console.log("⚠️ top-performers-container not found");
    return;
  }

  if (
    !analyticsData.top_performers ||
    analyticsData.top_performers.length === 0
  ) {
    container.innerHTML =
      '<div class="no-data-message">No top performers data available</div>';
    return;
  }

  let html = '<div class="top-performers-list">';
  analyticsData.top_performers.forEach((student, index) => {
    const rank = index + 1;
    html += `
            <div class="performer-item">
                <div class="performer-rank">${rank}</div>
                <div class="performer-info">
                    <div class="performer-name">${student.name}</div>
                    <div class="performer-details">
                        <span class="admission-number">${student.admission_number}</span>
                        <span class="class-info">${student.grade_name} ${student.stream_name}</span>
                    </div>
                </div>
                <div class="performer-score">
                    <div class="score-value">${student.average_percentage}%</div>
                    <div class="score-max">(${student.total_raw_marks}/${student.total_max_marks})</div>
                </div>
            </div>
        `;
  });
  html += "</div>";

  container.innerHTML = html;
  console.log("✅ Top performers updated");
}

function updateSubjectPerformance() {
  const container = document.getElementById("subject-performance-container");
  if (!container) {
    console.log("⚠️ subject-performance-container not found");
    return;
  }

  if (
    !analyticsData.subjectAnalytics ||
    analyticsData.subjectAnalytics.length === 0
  ) {
    container.innerHTML =
      '<div class="no-data-message">No subject performance data available</div>';
    return;
  }

  let html = '<div class="subject-performance-list">';
  // Example: Show top and least performing subjects
  if (analyticsData.topSubject) {
    html += `
            <div class="subject-highlight top-subject">
                <h4>Top Performing Subject</h4>
                <div class="subject-name">${analyticsData.topSubject.name}</div>
                <div class="subject-score">${analyticsData.topSubject.average_percentage}%</div>
            </div>
        `;
  }
  if (analyticsData.leastPerformingSubject) {
    html += `
            <div class="subject-highlight least-subject">
                <h4>Least Performing Subject</h4>
                <div class="subject-name">${analyticsData.leastPerformingSubject.name}</div>
                <div class="subject-score">${analyticsData.leastPerformingSubject.average_percentage}%</div>
            </div>
        `;
  }
  html += "</div>";

  container.innerHTML = html;
  console.log("✅ Subject performance updated");
}

// ============================================================================
// FILTER HANDLING
// ============================================================================
function applyAnalyticsFilters() {
  console.log("🔄 applyAnalyticsFilters called");

  // Update filter object based on dropdown values
  analyticsFilters.termId =
    document.getElementById("analytics-term-filter")?.value || null;
  analyticsFilters.assessmentTypeId =
    document.getElementById("analytics-assessment-filter")?.value || null;
  analyticsFilters.gradeId =
    document.getElementById("analytics-grade-filter")?.value || null;
  analyticsFilters.streamId =
    document.getElementById("analytics-stream-filter")?.value || null;

  console.log("🎯 Filters applied:", analyticsFilters);

  // Reload data with new filters
  loadAnalyticsData();
}

async function loadFilterOptions() {
  try {
    // Load terms
    const termsResponse = await fetch("/api/analytics/terms", {
      credentials: "same-origin",
    });
    if (termsResponse.ok) {
      const termsData = await termsResponse.json();
      availableOptions.terms = termsData.terms || [];
    }

    // Load assessment types
    const assessmentResponse = await fetch("/api/analytics/assessment_types", {
      credentials: "same-origin",
    });
    if (assessmentResponse.ok) {
      const assessmentData = await assessmentResponse.json();
      availableOptions.assessmentTypes = assessmentData.assessment_types || [];
    }

    // Load grades (for headteacher view)
    const gradesResponse = await fetch("/api/analytics/grades", {
      credentials: "same-origin",
    });
    if (gradesResponse.ok) {
      const gradesData = await gradesResponse.json();
      availableOptions.grades = gradesData.grades || [];
    }

    console.log("✅ Filter options loaded:", availableOptions);
  } catch (error) {
    console.error("Error loading filter options:", error);
  }
}

function populateFilterDropdowns() {
  // Populate terms
  const termSelect = document.getElementById("analytics-term-filter");
  if (termSelect) {
    termSelect.innerHTML = '<option value="">All Terms</option>';
    availableOptions.terms.forEach((term) => {
      const option = document.createElement("option");
      option.value = term.id;
      option.textContent = term.name;
      if (term.is_current) {
        option.selected = true;
        analyticsFilters.termId = term.id; // Set initial filter
      }
      termSelect.appendChild(option);
    });
  }

  // Populate assessment types
  const assessmentSelect = document.getElementById(
    "analytics-assessment-filter"
  );
  if (assessmentSelect) {
    assessmentSelect.innerHTML = '<option value="">All Assessments</option>';
    availableOptions.assessmentTypes.forEach((type) => {
      const option = document.createElement("option");
      option.value = type.id;
      option.textContent = type.name;
      assessmentSelect.appendChild(option);
    });
  }

  // Populate grades (if user is headteacher)
  const gradeSelect = document.getElementById("analytics-grade-filter");
  const streamSelect = document.getElementById("analytics-stream-filter");
  if (gradeSelect && streamSelect) {
    // Check if user is headteacher (this should be set by the template)
    const isHeadteacher = window.isHeadteacher || false;
    if (isHeadteacher) {
      gradeSelect.disabled = false;
      streamSelect.disabled = false;

      gradeSelect.innerHTML = '<option value="">All Grades</option>';
      availableOptions.grades.forEach((grade) => {
        const option = document.createElement("option");
        option.value = grade.id;
        option.textContent = grade.name;
        gradeSelect.appendChild(option);
      });
    }
  }
}

function resetAnalyticsFilters() {
  console.log("🔄 resetAnalyticsFilters called");
  // Reset filter object
  analyticsFilters = {
    termId: null,
    assessmentTypeId: null,
    gradeId: null,
    streamId: null,
    enhancedMode: false,
  };

  // Reset dropdowns to default
  const filterElements = [
    "analytics-term-filter",
    "analytics-assessment-filter",
    "analytics-grade-filter",
    "analytics-stream-filter",
  ];
  filterElements.forEach((elementId) => {
    const element = document.getElementById(elementId);
    if (element) {
      element.selectedIndex = 0;
    }
  });

  // Reload analytics data
  loadAnalyticsData();
}

// ============================================================================
// UI STATE MANAGEMENT
// ============================================================================
function showLoadingState() {
  console.log("🔄 Showing loading state");
  const containers = [
    "top-performers-container",
    "subject-performance-container",
    "detailed-performance-container",
  ];
  containers.forEach((containerId) => {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML =
        '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading analytics...</div>';
    }
  });
}

function showNoDataState() {
  console.log("😭 Showing no data state");
  const noDataElement = document.getElementById("no-data-state");
  if (noDataElement) {
    noDataElement.style.display = "block";
  }
  // Hide other components
  const components = document.querySelectorAll(".analytics-component");
  components.forEach((component) => {
    component.style.display = "none";
  });
}

function hideNoDataState() {
  console.log("🙈 Hiding no data state");
  const noDataElement = document.getElementById("no-data-state");
  if (noDataElement) {
    noDataElement.style.display = "none";
  }
  // Show other components
  const components = document.querySelectorAll(".analytics-component");
  components.forEach((component) => {
    component.style.display = "block";
  });
}

function showAnalyticsError(message) {
  console.error("❌ Analytics error:", message);
  // Show error in all main containers
  const containers = [
    "top-performers-container",
    "subject-performance-container",
    "detailed-performance-container",
  ];
  containers.forEach((containerId) => {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = `
                <div class="error-state" style="text-align: center; padding: 40px; color: #dc3545;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2em; margin-bottom: 10px;"></i>
                    <h3>Error Loading Analytics</h3>
                    <p>${message}</p>
                </div>
            `;
    }
  });
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================
function refreshAnalyticsData() {
  console.log("🔄 Refreshing analytics data");
  showNotification("Refreshing analytics data...", "info");
  loadAnalyticsData()
    .then(() => {
      showNotification("Analytics data refreshed!", "success");
    })
    .catch((error) => {
      showNotification(`Error refreshing data: ${error.message}`, "error");
    });
}

function showNotification(message, type = "info") {
  // Simple notification function
  console.log(`[${type.toUpperCase()}] ${message}`);
}

// Make functions globally available
window.initializeAnalyticsDashboard = initializeAnalyticsDashboard;
window.applyAnalyticsFilters = applyAnalyticsFilters;
window.resetAnalyticsFilters = resetAnalyticsFilters;
window.refreshAnalyticsData = refreshAnalyticsData;
