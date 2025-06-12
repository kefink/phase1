/**
 * Academic Performance Analytics Dashboard - UPDATED VERSION 20250609
 * Handles loading, displaying, and managing analytics data
 */

console.log("🚀 Analytics Dashboard JavaScript loaded - UPDATED VERSION");

// Global analytics state
let analyticsData = {
  topPerformers: [],
  subjectAnalytics: [],
  topSubject: null,
  leastPerformingSubject: null,
  summary: {},
  context: {},
  lastUpdated: null,
};

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

// Initialize analytics dashboard only if we're on the analytics page
document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on an analytics page by looking for analytics-specific elements
  const analyticsContainer =
    document.getElementById("analytics-dashboard-container") ||
    document.getElementById("top-performers-container") ||
    document.getElementById("subject-performance-container") ||
    document.querySelector(".analytics-dashboard");

  if (analyticsContainer) {
    console.log("Analytics page detected - initializing analytics dashboard");
    initializeAnalyticsDashboard();
  } else {
    console.log("Not on analytics page - skipping analytics initialization");
  }
});

// ============================================================================
// INITIALIZATION FUNCTIONS
// ============================================================================

async function initializeAnalyticsDashboard() {
  try {
    // Load available filter options
    await loadFilterOptions();

    // Populate filter dropdowns
    populateFilterDropdowns();

    // Load initial analytics data
    await loadAnalyticsData();

    // Set up auto-refresh (every 5 minutes)
    setInterval(refreshAnalyticsData, 300000);
  } catch (error) {
    console.error("Error initializing analytics dashboard:", error);
    showAnalyticsError("Failed to initialize analytics dashboard");
  }
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
        analyticsFilters.termId = term.id;
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
    availableOptions.assessmentTypes.forEach((assessment) => {
      const option = document.createElement("option");
      option.value = assessment.id;
      option.textContent = assessment.name;
      assessmentSelect.appendChild(option);
    });
  }

  // Populate grades (only for headteacher)
  const gradeSelect = document.getElementById("analytics-grade-filter");
  const gradeGroup = document.getElementById("analytics-grade-filter-group");
  if (gradeSelect && gradeGroup && availableOptions.grades.length > 0) {
    gradeGroup.style.display = "block";
    gradeSelect.innerHTML = '<option value="">All Grades</option>';
    availableOptions.grades.forEach((grade) => {
      const option = document.createElement("option");
      option.value = grade.id;
      option.textContent = grade.name;
      gradeSelect.appendChild(option);
    });

    // Add event listener for grade change to update streams
    gradeSelect.addEventListener("change", updateStreamsForGrade);
  }

  // Initialize streams dropdown (empty initially)
  const streamSelect = document.getElementById("analytics-stream-filter");
  if (streamSelect) {
    streamSelect.innerHTML = '<option value="">All Streams</option>';
  }
}

// Function to update streams based on selected grade
async function updateStreamsForGrade() {
  const gradeSelect = document.getElementById("analytics-grade-filter");
  const streamSelect = document.getElementById("analytics-stream-filter");

  if (!gradeSelect || !streamSelect) return;

  const selectedGradeId = gradeSelect.value;

  // Reset streams dropdown
  streamSelect.innerHTML = '<option value="">All Streams</option>';
  analyticsFilters.streamId = null;

  if (!selectedGradeId) {
    return; // No grade selected, keep streams empty
  }

  try {
    // Fetch streams for the selected grade
    const response = await fetch(
      `/api/analytics/streams?grade_id=${selectedGradeId}`,
      {
        credentials: "same-origin",
      }
    );

    if (response.ok) {
      const data = await response.json();
      const streams = data.streams || [];

      streams.forEach((stream) => {
        const option = document.createElement("option");
        option.value = stream.id;
        option.textContent = stream.name;
        streamSelect.appendChild(option);
      });
    }
  } catch (error) {
    console.error("Error loading streams for grade:", error);
  }
}

// ============================================================================
// DATA LOADING FUNCTIONS
// ============================================================================

async function loadAnalyticsData() {
  try {
    showLoadingState();

    // Build query parameters
    const params = new URLSearchParams();
    if (analyticsFilters.termId)
      params.append("term_id", analyticsFilters.termId);
    if (analyticsFilters.assessmentTypeId)
      params.append("assessment_type_id", analyticsFilters.assessmentTypeId);
    if (analyticsFilters.gradeId)
      params.append("grade_id", analyticsFilters.gradeId);
    if (analyticsFilters.streamId)
      params.append("stream_id", analyticsFilters.streamId);

    // Load analytics data
    const response = await fetch(
      `/api/analytics/comprehensive?${params.toString()}`,
      {
        credentials: "same-origin",
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.success) {
      analyticsData = data.analytics;
      analyticsData.lastUpdated = new Date();

      // Update the dashboard
      updateAnalyticsDashboard();
    } else {
      throw new Error(data.message || "Failed to load analytics data");
    }
  } catch (error) {
    console.error("Error loading analytics data:", error);
    showAnalyticsError(error.message);
  }
}

// ============================================================================
// DISPLAY FUNCTIONS
// ============================================================================

function updateAnalyticsDashboard() {
  console.log("🎯 updateAnalyticsDashboard called - UPDATED VERSION");

  // Always load enhanced top performers regardless of comprehensive data
  console.log("📊 Loading enhanced top performers independently...");
  loadEnhancedTopPerformers();

  // Check if comprehensive analytics has sufficient data
  if (!analyticsData.summary || !analyticsData.summary.has_sufficient_data) {
    console.log(
      "❌ No sufficient comprehensive data, but still loading enhanced analytics"
    );
    // Don't return early - still load enhanced analytics

    // Only show no data state for summary cards, not the whole dashboard
    const summaryCards = document.querySelectorAll(".summary-card");
    summaryCards.forEach((card) => {
      const valueElement = card.querySelector(".summary-value");
      if (valueElement) {
        valueElement.textContent = "-";
      }
    });

    // Still load other enhanced analytics
    updateSubjectPerformance();
    loadClassStreamPerformance();
    return;
  }

  console.log("✅ Sufficient comprehensive data found, updating dashboard");
  hideNoDataState();
  updateSummaryCards();

  // Load other analytics
  updateSubjectPerformance();
  loadClassStreamPerformance();
}

function updateSummaryCards() {
  // Update summary statistics
  const elements = {
    "total-students-analyzed":
      analyticsData.summary.total_students_analyzed || 0,
    "total-subjects-analyzed":
      analyticsData.summary.total_subjects_analyzed || 0,
    "top-subject-performance": analyticsData.topSubject
      ? `${analyticsData.topSubject.average_percentage}%`
      : "-",
    "top-student-performance":
      analyticsData.topPerformers.length > 0
        ? `${analyticsData.topPerformers[0].average_percentage}%`
        : "-",
  };

  Object.entries(elements).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  });
}

// Old updateTopPerformers function removed - now using loadEnhancedTopPerformers instead

function updateSubjectPerformance() {
  const container = document.getElementById("subject-performance-container");
  if (!container) return;

  // Check if we should load enhanced subject performance
  if (analyticsFilters.enhancedMode) {
    loadEnhancedSubjectPerformance();
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

  let html = `
    <div class="subject-performance-header">
      <div class="performance-mode-toggle">
        <button class="modern-btn btn-sm" onclick="toggleEnhancedSubjectMode()">
          <i class="fas fa-chart-bar"></i> Enhanced Analysis
        </button>
      </div>
    </div>
  `;

  // Show top and least performing subjects prominently
  if (analyticsData.topSubject) {
    html += `
            <div class="subject-highlight top-subject">
                <h4><i class="fas fa-trophy"></i> Top Performing Subject</h4>
                <div class="subject-analytics-item">
                    <div class="subject-info">
                        <div class="subject-name">${
                          analyticsData.topSubject.subject_name
                        }</div>
                        <div class="subject-details">
                            ${
                              analyticsData.topSubject.student_count
                            } students • ${
      analyticsData.topSubject.total_marks
    } marks
                        </div>
                    </div>
                    <div class="subject-metrics">
                        <div class="performance-score">
                            <strong>${
                              analyticsData.topSubject.average_percentage
                            }%</strong>
                        </div>
                        <div class="performance-badge ${getPerformanceClass(
                          analyticsData.topSubject.performance_category
                        )}">
                            ${analyticsData.topSubject.performance_category}
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  if (
    analyticsData.leastPerformingSubject &&
    analyticsData.leastPerformingSubject.subject_id !==
      analyticsData.topSubject?.subject_id
  ) {
    html += `
            <div class="subject-highlight least-subject">
                <h4><i class="fas fa-exclamation-triangle"></i> Needs Attention</h4>
                <div class="subject-analytics-item">
                    <div class="subject-info">
                        <div class="subject-name">${
                          analyticsData.leastPerformingSubject.subject_name
                        }</div>
                        <div class="subject-details">
                            ${
                              analyticsData.leastPerformingSubject.student_count
                            } students • ${
      analyticsData.leastPerformingSubject.total_marks
    } marks
                        </div>
                    </div>
                    <div class="subject-metrics">
                        <div class="performance-score">
                            <strong>${
                              analyticsData.leastPerformingSubject
                                .average_percentage
                            }%</strong>
                        </div>
                        <div class="performance-badge ${getPerformanceClass(
                          analyticsData.leastPerformingSubject
                            .performance_category
                        )}">
                            ${
                              analyticsData.leastPerformingSubject
                                .performance_category
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  // Show all subjects
  if (analyticsData.subjectAnalytics.length > 2) {
    html +=
      '<div class="subject-list"><h4><i class="fas fa-list"></i> All Subjects</h4>';
    analyticsData.subjectAnalytics.forEach((subject) => {
      const performanceClass = getPerformanceClass(
        subject.performance_category
      );
      html += `
                <div class="subject-analytics-item">
                    <div class="subject-info">
                        <div class="subject-name">${subject.subject_name}</div>
                        <div class="subject-details">
                            ${subject.student_count} students • ${subject.total_marks} marks
                        </div>
                    </div>
                    <div class="subject-metrics">
                        <div class="performance-score">
                            <strong>${subject.average_percentage}%</strong>
                        </div>
                        <div class="performance-badge ${performanceClass}">
                            ${subject.performance_category}
                        </div>
                    </div>
                </div>
            `;
    });
    html += "</div>";
  }

  container.innerHTML = html;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getPerformanceClass(category) {
  // Handle both percentage values and category strings
  if (typeof category === "number") {
    if (category >= 75) return "performance-exceeding-expectation";
    if (category >= 41) return "performance-meeting-expectation";
    if (category >= 21) return "performance-approaching-expectation";
    return "performance-below-expectation";
  }

  const classMap = {
    "Exceeding Expectation": "performance-exceeding-expectation",
    "Meeting Expectation": "performance-meeting-expectation",
    "Approaching Expectation": "performance-approaching-expectation",
    "Below Expectation": "performance-below-expectation",
    // Legacy support
    "Exceeding Expectations": "performance-exceeding-expectation",
    "Meeting Expectations": "performance-meeting-expectation",
    "Approaching Expectations": "performance-approaching-expectation",
    "Below Expectations": "performance-below-expectation",
    "Well Below Expectations": "performance-below-expectation",
    "Significantly Below Expectations": "performance-below-expectation",
    Excellent: "performance-exceeding-expectation",
    "Very Good": "performance-meeting-expectation",
    Good: "performance-approaching-expectation",
    Satisfactory: "performance-approaching-expectation",
    "Needs Improvement": "performance-below-expectation",
  };
  return classMap[category] || "performance-unknown";
}

function showLoadingState() {
  // Only show loading for subject performance, not top performers
  // Top performers will handle its own loading state
  const containers = ["subject-performance-container"];
  containers.forEach((containerId) => {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML =
        '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i> Loading analytics...</div>';
    }
  });
}

function showNoDataState() {
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
  // Only show error for subject performance, not top performers
  // Top performers will handle its own error state
  const containers = ["subject-performance-container"];
  containers.forEach((containerId) => {
    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
    }
  });
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

function updateAnalytics() {
  // Update filters from form
  analyticsFilters.termId =
    document.getElementById("analytics-term-filter")?.value || null;
  analyticsFilters.assessmentTypeId =
    document.getElementById("analytics-assessment-filter")?.value || null;
  analyticsFilters.gradeId =
    document.getElementById("analytics-grade-filter")?.value || null;
  analyticsFilters.streamId =
    document.getElementById("analytics-stream-filter")?.value || null;

  // Reload analytics data
  loadAnalyticsData();
}

function resetAnalyticsFilters() {
  // Reset all filters
  analyticsFilters = {
    termId: null,
    assessmentTypeId: null,
    gradeId: null,
    streamId: null,
  };

  // Reset form elements
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

function refreshAnalytics(component) {
  if (component === "top_performers" || component === "subject_performance") {
    loadAnalyticsData();
  }
}

async function refreshAnalyticsData() {
  // Silent refresh without loading indicators
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
      `/api/analytics/comprehensive?${params.toString()}`,
      {
        credentials: "same-origin",
      }
    );

    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        analyticsData = data.analytics;
        analyticsData.lastUpdated = new Date();
        updateAnalyticsDashboard();
      }
    }
  } catch (error) {
    console.error("Error refreshing analytics data:", error);
  }
}

// ============================================================================
// ENHANCED ANALYTICS FUNCTIONS
// ============================================================================

async function loadEnhancedTopPerformers(viewType = "summary") {
  console.log("🚀 loadEnhancedTopPerformers called - UPDATED VERSION", {
    viewType,
  });
  const container = document.getElementById("top-performers-container");
  if (!container) {
    console.log("❌ top-performers-container not found");
    return;
  }

  try {
    // Show loading state
    container.innerHTML = `
      <div class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading enhanced top performers...
      </div>
    `;
    console.log("📊 Loading enhanced top performers...");

    // Build query parameters
    const params = new URLSearchParams();
    if (analyticsFilters.termId)
      params.append("term_id", analyticsFilters.termId);
    if (analyticsFilters.assessmentTypeId)
      params.append("assessment_type_id", analyticsFilters.assessmentTypeId);
    if (analyticsFilters.gradeId)
      params.append("grade_id", analyticsFilters.gradeId);
    if (analyticsFilters.streamId)
      params.append("stream_id", analyticsFilters.streamId);
    params.append("limit", "5"); // Top 5 per grade/stream
    params.append("view_type", viewType); // Add view type parameter

    const response = await fetch(
      `/api/analytics/enhanced-top-performers?${params.toString()}`,
      {
        credentials: "same-origin",
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.message || "Failed to load enhanced top performers");
    }

    displayEnhancedTopPerformers(data.enhanced_top_performers);
  } catch (error) {
    console.error("Error loading enhanced top performers:", error);
    container.innerHTML = `
      <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Error loading top performers: ${error.message}</p>
        <button onclick="loadEnhancedTopPerformers()" class="retry-btn">
          <i class="fas fa-redo"></i> Retry
        </button>
      </div>
    `;
  }
}

function displayEnhancedTopPerformers(enhancedData) {
  const container = document.getElementById("top-performers-container");
  if (!container) return;

  if (!enhancedData || Object.keys(enhancedData).length === 0) {
    container.innerHTML = `
      <div class="no-data-message">
        <i class="fas fa-user-graduate"></i>
        <p>No top performers data available</p>
      </div>
    `;
    return;
  }

  let html = '<div class="enhanced-performers-container">';

  // Display by grade and stream
  Object.entries(enhancedData).forEach(([gradeName, streams]) => {
    html += `<div class="grade-section">
      <h4 class="grade-title"><i class="fas fa-layer-group"></i> ${gradeName}</h4>`;

    Object.entries(streams).forEach(([streamName, performers]) => {
      if (performers && performers.length > 0) {
        html += `<div class="stream-section">
          <h5 class="stream-title"><i class="fas fa-users"></i> ${streamName}</h5>
          <div class="performers-grid">`;

        performers.forEach((performer, index) => {
          const rankClass = index + 1 <= 3 ? `rank-${index + 1}` : "rank-other";
          const performanceClass = getPerformanceClass(
            performer.average_percentage
          );

          // Calculate total marks display
          const totalMarksDisplay =
            performer.total_raw_marks && performer.total_max_marks
              ? `${performer.total_raw_marks}/${performer.total_max_marks}`
              : "N/A";

          html += `
            <div class="enhanced-performer-card ${rankClass}" data-student-id="${
            performer.student_id
          }">
              <!-- Summary Compact View (for summary mode) -->
              <div class="performer-summary-compact">
                <div class="summary-compact-info">
                  <div class="summary-compact-name">${performer.name}</div>
                  <div class="summary-compact-admission">${
                    performer.admission_number
                  }</div>
                </div>
                <div class="summary-compact-score">
                  <div class="summary-compact-total">${totalMarksDisplay}</div>
                  <div class="summary-compact-percentage">${
                    performer.average_percentage
                  }%</div>
                </div>
                <div class="performer-actions">
                  ${getDeleteButtonHTML(
                    performer.grade ||
                      (performer.grade_name
                        ? performer.grade_name.replace("Grade ", "")
                        : "Unknown"),
                    performer.stream ||
                      (performer.stream_name
                        ? performer.stream_name.replace("Stream ", "")
                        : "Unknown"),
                    performer.term || "All Terms",
                    performer.assessment_type || "All Assessments"
                  )}
                </div>
              </div>

              <!-- Detailed View (for detailed mode) -->
              <div class="performer-detailed-view">
                <!-- Clean Header -->
                <div class="performer-card-header">
                  <div class="performer-rank-badge ${performanceClass}">
                    ${index + 1}
                  </div>
                  <div class="performer-basic-info">
                    <div class="performer-name">${performer.name}</div>
                    <div class="performer-admission">${
                      performer.admission_number
                    }</div>
                  </div>
                  <div class="performer-grade-badge">
                    ${performer.grade_letter}
                  </div>
                </div>

                <!-- Position and Class Info -->
                <div class="performer-position">
                  <div class="position-info">
                    <span class="position-rank">#${
                      performer.class_position || index + 1
                    }</span>
                    <span class="position-text">of ${
                      performer.total_students_in_class || "N/A"
                    } students</span>
                  </div>
                  <div class="percentage-display">${
                    performer.average_percentage
                  }%</div>
                </div>

                <!-- Summary Stats -->
                <div class="performer-summary">
                  <div class="summary-item">
                    <span class="summary-value">${totalMarksDisplay}</span>
                    <span class="summary-label">Total Marks</span>
                  </div>
                  <div class="summary-item">
                    <span class="summary-value">${
                      performer.total_assessments
                    }</span>
                    <span class="summary-label">Subjects</span>
                  </div>
                </div>

                <!-- Toggle Button -->
                <button class="details-toggle" onclick="togglePerformerDetails('${
                  performer.student_id
                }')">
                  <i class="fas fa-chevron-down"></i>
                  View Detailed Performance
                </button>

                <!-- Detailed Performance (Hidden by default) -->
                <div class="performer-details" id="details-${
                  performer.student_id
                }">
                  <div class="detailed-stats">
                    <div class="detailed-stat">
                      <span class="detailed-stat-value">${
                        performer.min_percentage
                      }%</span>
                      <span class="detailed-stat-label">Lowest</span>
                    </div>
                    <div class="detailed-stat">
                      <span class="detailed-stat-value">${
                        performer.average_percentage
                      }%</span>
                      <span class="detailed-stat-label">Average</span>
                    </div>
                    <div class="detailed-stat">
                      <span class="detailed-stat-value">${
                        performer.max_percentage
                      }%</span>
                      <span class="detailed-stat-label">Highest</span>
                    </div>
                  </div>

                  <div class="subject-performance-grid">`;

          // Display subject performance in compact grid
          performer.subject_marks.forEach((subject) => {
            const subjectGradeClass = getGradeClass(subject.grade_letter);
            html += `
              <div class="subject-item">
                <div class="subject-name-small">${subject.subject_name}</div>
                <div class="subject-grade-small ${subjectGradeClass}">${subject.grade_letter}</div>
                <div class="subject-percentage-small">${subject.percentage}%</div>
              </div>`;
          });

          html += `
                  </div>

                  <!-- Delete button for detailed view -->
                  <div class="detailed-actions">
                    ${getDeleteButtonHTML(
                      performer.grade ||
                        (performer.grade_name
                          ? performer.grade_name.replace("Grade ", "")
                          : "Unknown"),
                      performer.stream ||
                        (performer.stream_name
                          ? performer.stream_name.replace("Stream ", "")
                          : "Unknown"),
                      performer.term || "All Terms",
                      performer.assessment_type || "All Assessments"
                    )}
                  </div>
                </div>
              </div>
            </div>`;
        });

        html += `</div></div>`;
      }
    });

    html += `</div>`;
  });

  html += "</div>";
  container.innerHTML = html;
}

// Helper function to get grade class for styling
function getGradeClass(gradeLetter) {
  switch (gradeLetter) {
    case "EE1":
      return "grade-ee1";
    case "EE2":
      return "grade-ee2";
    case "ME1":
      return "grade-me1";
    case "ME2":
      return "grade-me2";
    case "AE1":
      return "grade-ae1";
    case "AE2":
      return "grade-ae2";
    case "BE1":
      return "grade-be1";
    case "BE2":
      return "grade-be2";
    default:
      return "grade-default";
  }
}

// Toggle function for performer details
function togglePerformerDetails(studentId) {
  const detailsElement = document.getElementById(`details-${studentId}`);
  const toggleButton = document.querySelector(
    `[data-student-id="${studentId}"] .details-toggle`
  );

  if (!detailsElement || !toggleButton) return;

  const isExpanded = detailsElement.classList.contains("expanded");

  if (isExpanded) {
    // Collapse
    detailsElement.classList.remove("expanded");
    toggleButton.classList.remove("expanded");
    toggleButton.innerHTML =
      '<i class="fas fa-chevron-down"></i> View Detailed Performance';
  } else {
    // Expand
    detailsElement.classList.add("expanded");
    toggleButton.classList.add("expanded");
    toggleButton.innerHTML =
      '<i class="fas fa-chevron-up"></i> Hide Detailed Performance';
  }
}

async function loadClassStreamPerformance() {
  const container = document.getElementById(
    "class-stream-performance-container"
  );
  if (!container) return;

  try {
    // Show loading state
    container.innerHTML = `
      <div class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading class & stream performance...
      </div>
    `;

    // Build query parameters
    const params = new URLSearchParams();
    if (analyticsFilters.termId)
      params.append("term_id", analyticsFilters.termId);
    if (analyticsFilters.assessmentTypeId)
      params.append("assessment_type_id", analyticsFilters.assessmentTypeId);

    const response = await fetch(
      `/api/analytics/class-stream-performance?${params.toString()}`,
      {
        credentials: "same-origin",
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(
        data.message || "Failed to load class/stream performance"
      );
    }

    displayClassStreamPerformance(data);
  } catch (error) {
    console.error("Error loading class/stream performance:", error);
    container.innerHTML = `
      <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Error loading class performance: ${error.message}</p>
        <button onclick="loadClassStreamPerformance()" class="retry-btn">
          <i class="fas fa-redo"></i> Retry
        </button>
      </div>
    `;
  }
}

function displayClassStreamPerformance(data) {
  const container = document.getElementById(
    "class-stream-performance-container"
  );
  if (!container) return;

  const classStreamData = data.class_stream_performance || [];

  if (classStreamData.length === 0) {
    container.innerHTML = `
      <div class="no-data-message">
        <i class="fas fa-school"></i>
        <p>No class/stream performance data available</p>
      </div>
    `;
    return;
  }

  let html = `
    <div class="class-stream-overview">
      <div class="overview-stats">
        <div class="stat-card">
          <div class="stat-value">${data.total_classes_analyzed || 0}</div>
          <div class="stat-label">Classes Analyzed</div>
        </div>
        <div class="stat-card best-class">
          <div class="stat-value">${
            data.best_performing_class
              ? data.best_performing_class.average_percentage + "%"
              : "N/A"
          }</div>
          <div class="stat-label">Best Class Average</div>
          <div class="stat-detail">${
            data.best_performing_class
              ? data.best_performing_class.grade_name +
                " " +
                data.best_performing_class.stream_name
              : ""
          }</div>
        </div>
        <div class="stat-card lowest-class">
          <div class="stat-value">${
            data.lowest_performing_class
              ? data.lowest_performing_class.average_percentage + "%"
              : "N/A"
          }</div>
          <div class="stat-label">Needs Attention</div>
          <div class="stat-detail">${
            data.lowest_performing_class
              ? data.lowest_performing_class.grade_name +
                " " +
                data.lowest_performing_class.stream_name
              : ""
          }</div>
        </div>
      </div>
    </div>

    <div class="class-stream-grid">`;

  classStreamData.forEach((classData, index) => {
    const performanceClass = getPerformanceClass(classData.average_percentage);
    const rankIcon =
      index === 0 ? "🏆" : index === 1 ? "🥈" : index === 2 ? "🥉" : "";

    html += `
      <div class="class-stream-card ${performanceClass}">
        <div class="class-header">
          <div class="class-rank">${rankIcon}</div>
          <div class="class-info">
            <h4>${classData.grade_name}</h4>
            <p class="stream-name">${classData.stream_name}</p>
          </div>
          <div class="class-grade">
            <span class="grade-badge ${performanceClass}">${
      classData.grade_letter
    }</span>
          </div>
        </div>

        <div class="class-metrics">
          <div class="primary-metric">
            <span class="metric-value">${classData.average_percentage}%</span>
            <span class="metric-label">Class Average</span>
          </div>

          <div class="secondary-metrics">
            <div class="metric-item">
              <span class="metric-value">${classData.student_count}</span>
              <span class="metric-label">Students</span>
            </div>
            <div class="metric-item">
              <span class="metric-value">${classData.total_marks}</span>
              <span class="metric-label">Assessments</span>
            </div>
          </div>

          <div class="performance-range">
            <div class="range-item">
              <span class="range-label">Min:</span>
              <span class="range-value">${classData.min_percentage}%</span>
            </div>
            <div class="range-item">
              <span class="range-label">Max:</span>
              <span class="range-value">${classData.max_percentage}%</span>
            </div>
          </div>
        </div>

        <div class="performance-badge ${performanceClass}">
          ${classData.performance_category}
        </div>

        <div class="class-actions">
          ${getDeleteButtonHTML(
            classData.grade_name,
            classData.stream_name,
            classData.term_name || "Current Term",
            classData.assessment_type_name || "Current Assessment"
          )}
        </div>
      </div>`;
  });

  html += `</div>`;
  container.innerHTML = html;
}

// Enhanced Subject Performance Functions
function toggleEnhancedSubjectMode() {
  analyticsFilters.enhancedMode = !analyticsFilters.enhancedMode;
  updateSubjectPerformance();
}

async function loadEnhancedSubjectPerformance() {
  const container = document.getElementById("subject-performance-container");
  if (!container) return;

  try {
    // Show loading state
    container.innerHTML = `
      <div class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading enhanced subject analytics...
      </div>
    `;

    // Build query parameters
    const params = new URLSearchParams();
    if (analyticsFilters.termId)
      params.append("term_id", analyticsFilters.termId);
    if (analyticsFilters.assessmentTypeId)
      params.append("assessment_type_id", analyticsFilters.assessmentTypeId);
    if (analyticsFilters.gradeId)
      params.append("grade_id", analyticsFilters.gradeId);

    const response = await fetch(
      `/api/analytics/enhanced_subject_performance?${params.toString()}`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      displayEnhancedSubjectPerformance(data);
    } else {
      throw new Error(
        data.message || "Failed to load enhanced subject performance"
      );
    }
  } catch (error) {
    console.error("Error loading enhanced subject performance:", error);
    container.innerHTML = `
      <div class="error-state">
        <i class="fas fa-exclamation-triangle"></i>
        <p>Error loading enhanced subject analytics</p>
        <button class="retry-btn" onclick="loadEnhancedSubjectPerformance()">
          <i class="fas fa-redo"></i> Retry
        </button>
      </div>
    `;
  }
}

function displayEnhancedSubjectPerformance(data) {
  const container = document.getElementById("subject-performance-container");
  if (!container) return;

  const { grade_subject_analytics, subject_stream_comparisons } = data;

  if (
    !grade_subject_analytics ||
    Object.keys(grade_subject_analytics).length === 0
  ) {
    container.innerHTML = `
      <div class="no-data-message">
        <i class="fas fa-chart-bar"></i>
        <p>No enhanced subject performance data available</p>
        <button class="modern-btn btn-sm" onclick="toggleEnhancedSubjectMode()">
          <i class="fas fa-arrow-left"></i> Back to Basic View
        </button>
      </div>
    `;
    return;
  }

  let html = `
    <div class="enhanced-subject-performance">
      <div class="subject-performance-header">
        <div class="performance-mode-toggle">
          <button class="modern-btn btn-sm" onclick="toggleEnhancedSubjectMode()">
            <i class="fas fa-arrow-left"></i> Basic View
          </button>
        </div>
      </div>

      <div class="subject-performance-tabs">
        <button class="tab-button active" onclick="switchSubjectTab('by-grade')">
          <i class="fas fa-layer-group"></i> By Grade
        </button>
        <button class="tab-button" onclick="switchSubjectTab('by-subject')">
          <i class="fas fa-book"></i> By Subject
        </button>
      </div>

      <div id="by-grade-tab" class="tab-content active">
        ${generateGradeSubjectView(grade_subject_analytics)}
      </div>

      <div id="by-subject-tab" class="tab-content">
        ${generateSubjectComparisonView(subject_stream_comparisons)}
      </div>
    </div>
  `;

  container.innerHTML = html;
}

function generateGradeSubjectView(gradeSubjectData) {
  let html = "";

  Object.entries(gradeSubjectData).forEach(([gradeName, subjects]) => {
    html += `
      <div class="grade-subject-section">
        <h3 class="grade-subject-title">
          <i class="fas fa-layer-group"></i> ${gradeName}
        </h3>
        <div class="subjects-grid-enhanced">
    `;

    Object.entries(subjects).forEach(([subjectName, subjectData]) => {
      const streams = subjectData.streams;
      const gradeAverage = subjectData.grade_average;

      html += `
        <div class="subject-card-enhanced">
          <div class="subject-header-enhanced">
            <div class="subject-name-enhanced">${subjectName}</div>
            <div class="subject-grade-average">${gradeAverage}%</div>
            <div class="subject-actions">
              ${getDeleteButtonHTML(
                gradeName,
                "All Streams",
                "Current Term",
                subjectName
              )}
            </div>
          </div>
          <div class="streams-comparison">
      `;

      Object.entries(streams).forEach(([streamName, streamData]) => {
        const performanceClass = getPerformanceClass(
          streamData.performance_category
        );

        // Format teacher information
        const teacherInfo =
          streamData.teacher_name && streamData.teacher_name !== "Not Assigned"
            ? streamData.teacher_name
            : "No teacher assigned";

        html += `
          <div class="stream-performance">
            <div class="stream-name-enhanced">Stream ${streamName}</div>
            <div class="stream-teacher">
              <i class="fas fa-user-tie"></i> ${teacherInfo}
            </div>
            <div class="stream-stats">
              <div class="stream-average">${streamData.average_percentage}%</div>
              <div class="stream-students">${streamData.student_count} students</div>
            </div>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  });

  return html;
}

function generateSubjectComparisonView(subjectStreamData) {
  let html = "";

  Object.entries(subjectStreamData).forEach(([subjectName, gradeData]) => {
    html += `
      <div class="grade-subject-section">
        <h3 class="grade-subject-title">
          <i class="fas fa-book"></i> ${subjectName}
        </h3>
    `;

    Object.entries(gradeData).forEach(([gradeName, streams]) => {
      if (Object.keys(streams).length > 1) {
        html += `
          <div class="subject-comparison-chart">
            <div class="chart-title">${gradeName} - Stream Comparison</div>
            <div class="comparison-bars">
        `;

        // Find max percentage for scaling
        const maxPercentage = Math.max(
          ...Object.values(streams).map((s) => s.average_percentage)
        );

        Object.entries(streams).forEach(([streamName, streamData]) => {
          const barWidth =
            (streamData.average_percentage / maxPercentage) * 100;

          // Format teacher information
          const teacherInfo =
            streamData.teacher_name &&
            streamData.teacher_name !== "Not Assigned"
              ? streamData.teacher_name
              : "No teacher assigned";

          html += `
            <div class="comparison-bar">
              <div class="bar-label">
                <div class="stream-name">Stream ${streamName}</div>
                <div class="teacher-name"><i class="fas fa-user-tie"></i> ${teacherInfo}</div>
              </div>
              <div class="bar-container">
                <div class="bar-fill" style="width: ${barWidth}%">
                  <div class="bar-value">${streamData.average_percentage}%</div>
                </div>
              </div>
            </div>
          `;
        });

        html += `
            </div>
          </div>
        `;
      }
    });

    html += `
      </div>
    `;
  });

  return html;
}

function switchSubjectTab(tabName) {
  // Remove active class from all tabs and content
  document
    .querySelectorAll(".tab-button")
    .forEach((btn) => btn.classList.remove("active"));
  document
    .querySelectorAll(".tab-content")
    .forEach((content) => content.classList.remove("active"));

  // Add active class to selected tab and content
  event.target.classList.add("active");
  document.getElementById(`${tabName}-tab`).classList.add("active");
}

// Duplicate DOMContentLoaded listener removed - using the one at the top of the file

// Test function to verify JavaScript is loaded
function testEnhancedTopPerformers() {
  console.log("🧪 Testing enhanced top performers manually...");
  loadEnhancedTopPerformers();
}

// Helper function to generate delete button HTML for headteachers
function getDeleteButtonHTML(grade, stream, term, assessmentType) {
  // Check if user is headteacher
  const isHeadteacher = window.isHeadteacher || false; // This should be set by the template

  if (!isHeadteacher) {
    return "";
  }

  // Debug logging
  console.log("🗑️ Delete button parameters:", {
    grade: grade,
    stream: stream,
    term: term,
    assessmentType: assessmentType,
  });

  // Ensure all parameters have values
  const safeGrade = grade || "Unknown";
  const safeStream = stream || "Unknown";
  const safeTerm = term || "Current Term";
  const safeAssessmentType = assessmentType || "Current Assessment";

  return `
    <button class="delete-report-btn"
            onclick="deleteReportFromAnalytics('${safeGrade}', '${safeStream}', '${safeTerm}', '${safeAssessmentType}')"
            title="Delete this report and all associated marks">
      <i class="fas fa-trash"></i>
    </button>
  `;
}

// Make functions available globally
window.testEnhancedTopPerformers = testEnhancedTopPerformers;
window.loadTopPerformers = loadEnhancedTopPerformers;
window.updateStreamsForGrade = updateStreamsForGrade;
window.getDeleteButtonHTML = getDeleteButtonHTML;
