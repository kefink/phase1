/**
 * Academic Performance Analytics Dashboard
 * Handles loading, displaying, and managing analytics data
 */

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
    const termsResponse = await fetch("/api/analytics/terms");
    if (termsResponse.ok) {
      const termsData = await termsResponse.json();
      availableOptions.terms = termsData.terms || [];
    }

    // Load assessment types
    const assessmentResponse = await fetch("/api/analytics/assessment_types");
    if (assessmentResponse.ok) {
      const assessmentData = await assessmentResponse.json();
      availableOptions.assessmentTypes = assessmentData.assessment_types || [];
    }

    // Load grades (for headteacher view)
    const gradesResponse = await fetch("/api/analytics/grades");
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
      `/api/analytics/comprehensive?${params.toString()}`
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
  if (!analyticsData.summary || !analyticsData.summary.has_sufficient_data) {
    showNoDataState();
    return;
  }

  hideNoDataState();
  updateSummaryCards();

  // Load enhanced analytics
  loadEnhancedTopPerformers();
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

function updateTopPerformers() {
  const container = document.getElementById("top-performers-container");
  if (!container) return;

  if (
    !analyticsData.topPerformers ||
    analyticsData.topPerformers.length === 0
  ) {
    container.innerHTML =
      '<div class="no-data-message">No top performers data available</div>';
    return;
  }

  let html = "";
  analyticsData.topPerformers.forEach((performer) => {
    const rankClass =
      performer.rank <= 3 ? `rank-${performer.rank}` : "rank-other";
    const performanceClass = getPerformanceClass(
      performer.performance_category
    );

    html += `
            <div class="top-performer-card premium-card">
                <div class="performer-rank ${rankClass}">
                    <i class="fas fa-trophy"></i>
                    <span>${performer.rank}</span>
                </div>
                <div class="performer-info">
                    <div class="performer-name">${performer.name}</div>
                    <div class="performer-details">
                        <span><i class="fas fa-id-card"></i> ${performer.admission_number}</span>
                        <span><i class="fas fa-chart-line"></i> ${performer.total_marks} marks</span>
                    </div>
                </div>
                <div class="performer-metrics">
                    <div class="performance-score">
                        <strong>${performer.average_percentage}%</strong>
                        <div class="grade-letter">${performer.grade_letter}</div>
                    </div>
                    <div class="performance-badge ${performanceClass}">
                        ${performer.performance_category}
                    </div>
                </div>
            </div>
        `;
  });

  container.innerHTML = html;
}

function updateSubjectPerformance() {
  const container = document.getElementById("subject-performance-container");
  if (!container) return;

  if (
    !analyticsData.subjectAnalytics ||
    analyticsData.subjectAnalytics.length === 0
  ) {
    container.innerHTML =
      '<div class="no-data-message">No subject performance data available</div>';
    return;
  }

  let html = "";

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
  const containers = [
    "top-performers-container",
    "subject-performance-container",
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
  const containers = [
    "top-performers-container",
    "subject-performance-container",
  ];
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
      `/api/analytics/comprehensive?${params.toString()}`
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

async function loadEnhancedTopPerformers() {
  const container = document.getElementById("top-performers-container");
  if (!container) return;

  try {
    // Show loading state
    container.innerHTML = `
      <div class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading enhanced top performers...
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
    if (analyticsFilters.streamId)
      params.append("stream_id", analyticsFilters.streamId);
    params.append("limit", "5"); // Top 5 per grade/stream

    const response = await fetch(
      `/api/analytics/enhanced-top-performers?${params.toString()}`
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
          const rankIcon =
            index === 0
              ? "🥇"
              : index === 1
              ? "🥈"
              : index === 2
              ? "🥉"
              : `#${index + 1}`;
          const performanceClass = getPerformanceClass(
            performer.average_percentage
          );

          html += `
            <div class="enhanced-performer-card ${performanceClass}">
              <div class="performer-header">
                <div class="performer-rank">${rankIcon}</div>
                <div class="performer-basic">
                  <h6>${performer.name}</h6>
                  <p class="admission-number">${performer.admission_number}</p>
                </div>
                <div class="performer-grade">
                  <span class="grade-badge ${performanceClass}">${performer.grade_letter}</span>
                  <span class="percentage">${performer.average_percentage}%</span>
                </div>
              </div>

              <div class="performer-details">
                <div class="performance-summary">
                  <div class="stat-mini">
                    <span class="value">${performer.total_assessments}</span>
                    <span class="label">Assessments</span>
                  </div>
                  <div class="stat-mini">
                    <span class="value">${performer.min_percentage}%</span>
                    <span class="label">Min</span>
                  </div>
                  <div class="stat-mini">
                    <span class="value">${performer.max_percentage}%</span>
                    <span class="label">Max</span>
                  </div>
                </div>

                <div class="subject-marks">
                  <h6>Subject Performance:</h6>
                  <div class="subjects-grid">`;

          performer.subject_marks.forEach((subject) => {
            const subjectClass = getPerformanceClass(subject.percentage);
            html += `
              <div class="subject-mark ${subjectClass}">
                <span class="subject-name">${subject.subject_name}</span>
                <span class="subject-grade">${subject.grade_letter}</span>
                <span class="subject-percentage">${subject.percentage}%</span>
                <span class="subject-raw">${subject.raw_marks}/${subject.total_marks}</span>
              </div>`;
          });

          html += `
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
      `/api/analytics/class-stream-performance?${params.toString()}`
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
            <span class="grade-badge ${performanceClass}">${classData.grade_letter}</span>
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
      </div>`;
  });

  html += `</div>`;
  container.innerHTML = html;
}
