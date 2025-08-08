/**
 * Class Teacher Report Management JavaScript
 * Functions for sorting, filtering, and managing reports
 */

// ====================================================================
// REPORT FILTERING AND SORTING FUNCTIONS
// ====================================================================

/**
 * Sort reports by specified criteria
 * @param {string} sortBy - The sort criteria (e.g., 'date', 'grade', 'name')
 */
function sortReports(sortBy) {
  // Get current URL parameters
  const urlParams = new URLSearchParams(window.location.search);

  // Update or add the sort parameter
  urlParams.set("sort", sortBy);

  // Redirect to the new URL with updated parameters
  window.location.href = window.location.pathname + "?" + urlParams.toString();
}

/**
 * Filter reports based on grade and term selections
 */
function filterReports() {
  // Get current URL parameters
  const urlParams = new URLSearchParams(window.location.search);

  // Get filter values
  const gradeFilter = document.getElementById("filter-grade")?.value;
  const termFilter = document.getElementById("filter-term")?.value;

  // Update parameters
  if (gradeFilter) {
    urlParams.set("filter_grade", gradeFilter);
  } else {
    urlParams.delete("filter_grade");
  }

  if (termFilter) {
    urlParams.set("filter_term", termFilter);
  } else {
    urlParams.delete("filter_term");
  }

  // Redirect to the new URL with updated parameters
  window.location.href = window.location.pathname + "?" + urlParams.toString();
}

/**
 * Reset all report filters while preserving sort parameters
 */
function resetFilters() {
  // Get current URL parameters
  const urlParams = new URLSearchParams(window.location.search);

  // Remove filter parameters
  urlParams.delete("filter_grade");
  urlParams.delete("filter_term");

  // Keep sort parameter if it exists
  const sortParam = urlParams.get("sort");

  // Clear all parameters
  urlParams.forEach((value, key) => {
    urlParams.delete(key);
  });

  // Add back sort parameter if it existed
  if (sortParam) {
    urlParams.set("sort", sortParam);
  }

  // Redirect to the new URL with updated parameters
  window.location.href = window.location.pathname + "?" + urlParams.toString();
}

// ====================================================================
// COMPONENT MARKS MANAGEMENT
// ====================================================================

/**
 * Update component max marks and recalculate all student marks
 * @param {string} subjectId - The subject ID
 * @param {string} componentId - The component ID
 * @param {HTMLElement} maxMarkInput - The max mark input element
 */
function updateComponentMaxMarks(subjectId, componentId, maxMarkInput) {
  const newMaxMark = parseInt(maxMarkInput.value) || 100;

  // Update all student input fields for this component with the new max mark
  const componentMarkInputs = document.querySelectorAll(
    `input.component-mark[data-subject="${subjectId}"][data-component="${componentId}"]`
  );

  componentMarkInputs.forEach((input) => {
    // Update the max mark data attribute
    input.dataset.maxMark = newMaxMark;
    input.max = newMaxMark;

    // If current value exceeds new max, cap it
    const currentValue = parseInt(input.value) || 0;
    if (currentValue > newMaxMark) {
      input.value = newMaxMark;
    }

    // Recalculate the overall mark for this student
    const student = input.dataset.student;
    if (window.calculateOverallSubjectMark) {
      calculateOverallSubjectMark(student, subjectId);
    }
  });

  // Update the proportional weight display for this subject
  updateProportionalWeights(subjectId);
}

/**
 * Calculate and display proportional weights for a subject
 * @param {string} subjectId - The subject ID
 */
function updateProportionalWeights(subjectId) {
  const componentMaxInputs = document.querySelectorAll(
    `input.component-max-mark[data-subject="${subjectId}"]`
  );
  const weightDisplays = document.querySelectorAll(
    `.component-weight[data-subject="${subjectId}"]`
  );

  let totalMaxMarks = 0;
  const componentMaxMarks = {};

  // Calculate total max marks for the subject
  componentMaxInputs.forEach((input) => {
    const componentId = input.dataset.component;
    const maxMark = parseInt(input.value) || 100;
    componentMaxMarks[componentId] = maxMark;
    totalMaxMarks += maxMark;
  });

  // Update weight displays
  weightDisplays.forEach((display) => {
    const componentId = display.dataset.component;
    if (componentMaxMarks[componentId] && totalMaxMarks > 0) {
      const weight = (
        (componentMaxMarks[componentId] / totalMaxMarks) *
        100
      ).toFixed(1);
      display.textContent = `${weight}%`;
    }
  });
}

// ====================================================================
// INITIALIZATION
// ====================================================================

/**
 * Initialize report management functionality when DOM is loaded
 */
document.addEventListener("DOMContentLoaded", function () {
  // Initialize filter controls
  const gradeFilter = document.getElementById("filter-grade");
  const termFilter = document.getElementById("filter-term");

  if (gradeFilter) {
    gradeFilter.addEventListener("change", filterReports);
  }

  if (termFilter) {
    termFilter.addEventListener("change", filterReports);
  }

  // Initialize component max mark inputs
  const componentMaxInputs = document.querySelectorAll(
    "input.component-max-mark"
  );
  componentMaxInputs.forEach((input) => {
    input.addEventListener("change", function () {
      const subjectId = this.dataset.subject;
      const componentId = this.dataset.component;
      updateComponentMaxMarks(subjectId, componentId, this);
    });
  });

  // Initialize proportional weights for all subjects
  const subjects = [
    ...new Set(
      Array.from(componentMaxInputs).map((input) => input.dataset.subject)
    ),
  ];
  subjects.forEach((subjectId) => {
    updateProportionalWeights(subjectId);
  });
});
