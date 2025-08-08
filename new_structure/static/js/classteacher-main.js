/**
 * Class Teacher Dashboard JavaScript
 * Main functionality for marks management, form handling, and UI interactions
 */

// ====================================================================
// CORE UTILITY FUNCTIONS
// ====================================================================

/**
 * Get CSRF token for secure form submissions
 */
function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

/**
 * Show notification to user
 */
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `alert alert-${type} notification-toast`;
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
        animation: slideInRight 0.3s ease-out;
    `;
  notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas fa-${
              type === "success"
                ? "check-circle"
                : type === "danger"
                ? "exclamation-triangle"
                : "info-circle"
            }"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="
                background: none; border: none; color: inherit; font-size: 16px; cursor: pointer; margin-left: auto;
            ">&times;</button>
        </div>
    `;

  document.body.appendChild(notification);
  setTimeout(() => notification.remove(), 5000);
}

// ====================================================================
// MARKS CALCULATION FUNCTIONS
// ====================================================================

/**
 * Update component max marks and recalculate all student marks
 */
function updateComponentMaxMarks(subjectId, componentId, maxMarkInput) {
  const newMaxMark = parseInt(maxMarkInput.value) || 100;
  const componentMarkInputs = document.querySelectorAll(
    `input.component-mark[data-subject="${subjectId}"][data-component="${componentId}"]`
  );

  componentMarkInputs.forEach((input) => {
    input.dataset.maxMark = newMaxMark;
    input.max = newMaxMark;

    const currentValue = parseInt(input.value) || 0;
    if (currentValue > newMaxMark) {
      input.value = newMaxMark;
    }

    const student = input.dataset.student;
    calculateOverallSubjectMark(student, subjectId);
  });

  updateProportionalWeights(subjectId);
}

/**
 * Calculate and display proportional weights for a subject
 */
function updateProportionalWeights(subjectId) {
  const componentMaxInputs = document.querySelectorAll(
    `input.component-max-marks[data-subject="${subjectId}"]`
  );
  let totalMaxMarks = 0;
  const componentData = [];

  componentMaxInputs.forEach((input) => {
    const maxMark = parseInt(input.value) || 100;
    const componentId = input.dataset.component;
    totalMaxMarks += maxMark;
    componentData.push({ componentId, maxMark });
  });

  componentData.forEach((data) => {
    const proportion =
      totalMaxMarks > 0 ? ((data.maxMark / totalMaxMarks) * 100).toFixed(1) : 0;
    const proportionElement = document.getElementById(
      `proportion_${subjectId}_${data.componentId}`
    );
    if (proportionElement) {
      proportionElement.textContent = `Weight: ${proportion}% (${data.maxMark}/${totalMaxMarks})`;
    }
  });
}

/**
 * Update percentage based on raw mark and total marks
 */
function updatePercentage(inputElement) {
  const student = inputElement.dataset.student;
  const subject = inputElement.dataset.subject;
  const subjectIndex = inputElement.dataset.subjectIndex;

  const totalMarksInput = document.getElementById(
    `total_marks_${subjectIndex}`
  );
  const maxRawMark = totalMarksInput
    ? parseFloat(totalMarksInput.value)
    : parseFloat(inputElement.dataset.maxMark) || 100;
  let rawMark = parseFloat(inputElement.value) || 0;

  if (rawMark > maxRawMark) {
    rawMark = maxRawMark;
    inputElement.value = maxRawMark;
  }

  // Visual feedback
  inputElement.classList.toggle("has-value", rawMark > 0);
  if (rawMark > 0) {
    inputElement.classList.add("mark-updated");
    setTimeout(() => inputElement.classList.remove("mark-updated"), 500);
  }

  // Calculate percentage
  const percentage = maxRawMark > 0 ? (rawMark / maxRawMark) * 100 : 0;
  const roundedPercentage = Math.round(Math.min(percentage, 100));

  // Update display
  const percentageSpan = document.getElementById(
    `percentage_${student}_${subject}`
  );
  if (percentageSpan) {
    percentageSpan.textContent = `${roundedPercentage}%`;
    updatePerformanceIndicator(percentageSpan, roundedPercentage);
    updatePercentageBar(percentageSpan, roundedPercentage);
  }

  // Update hidden field
  const hiddenPercentageInput = document.getElementById(
    `hidden_percentage_${student}_${subject}`
  );
  if (hiddenPercentageInput) {
    hiddenPercentageInput.value = roundedPercentage;
  }
}

/**
 * Update performance indicator styling
 */
function updatePerformanceIndicator(element, percentage) {
  element.classList.remove(
    "performance-ee",
    "performance-me",
    "performance-ae",
    "performance-be"
  );

  if (percentage >= 75) {
    element.classList.add("performance-ee");
  } else if (percentage >= 50) {
    element.classList.add("performance-me");
  } else if (percentage >= 30) {
    element.classList.add("performance-ae");
  } else {
    element.classList.add("performance-be");
  }
}

/**
 * Update percentage bar visualization
 */
function updatePercentageBar(percentageSpan, percentage) {
  const percentageBar = percentageSpan
    .closest(".percentage-display")
    ?.querySelector(".percentage-fill");
  if (percentageBar) {
    percentageBar.style.width = `${Math.min(percentage, 100)}%`;

    // Set color based on performance
    let color = "#dc3545"; // Below Expectation
    if (percentage >= 75) color = "#28a745"; // Exceeding
    else if (percentage >= 50) color = "#17a2b8"; // Meeting
    else if (percentage >= 30) color = "#ffc107"; // Approaching

    percentageBar.style.backgroundColor = color;
  }
}

/**
 * Calculate overall subject mark from component marks
 */
function calculateOverallSubjectMark(student, subject) {
  const componentInputs = document.querySelectorAll(
    `input.component-mark[data-student="${student}"][data-subject="${subject}"]`
  );
  if (componentInputs.length === 0) return;

  let totalMaxMarks = 0;
  let totalRawMarks = 0;

  componentInputs.forEach((input) => {
    const rawMark = parseInt(input.value) || 0;
    const maxMark = parseInt(input.dataset.maxMark) || 100;
    totalRawMarks += rawMark;
    totalMaxMarks += maxMark;
  });

  const overallPercentage =
    totalMaxMarks > 0 ? (totalRawMarks / totalMaxMarks) * 100 : 0;
  const roundedOverallPercentage = Math.round(overallPercentage);

  // Update hidden fields
  const overallMarkField = document.getElementById(
    `overall_mark_${student}_${subject}`
  );
  const overallPercentageField = document.getElementById(
    `hidden_percentage_${student}_${subject}`
  );

  if (overallMarkField && overallPercentageField) {
    overallMarkField.value = roundedOverallPercentage;
    overallPercentageField.value = roundedOverallPercentage;
  }

  // Update display
  const overallPercentageDisplay = document.getElementById(
    `overall_percentage_display_${student}_${subject}`
  );
  if (overallPercentageDisplay) {
    overallPercentageDisplay.textContent = `${roundedOverallPercentage}%`;
    updatePerformanceIndicator(
      overallPercentageDisplay,
      roundedOverallPercentage
    );
    updatePercentageBar(overallPercentageDisplay, roundedOverallPercentage);
  }
}

// ====================================================================
// FORM HANDLING FUNCTIONS
// ====================================================================

/**
 * Validate maximum marks input
 */
function validateMaxMarks(inputElement) {
  const value = parseFloat(inputElement.value) || 0;
  const maxAllowed = 100;

  if (value > maxAllowed) {
    inputElement.value = maxAllowed;
    showNotification(
      `Maximum raw marks cannot exceed ${maxAllowed}. Value capped at ${maxAllowed}.`,
      "warning"
    );
  }

  if (value < 1 && value !== 0) {
    inputElement.value = 1;
  }
}

/**
 * Add selected subjects to form before submission
 */
function addSelectedSubjectsToForm() {
  const form = document.getElementById("marks-form");
  if (!form) return false;

  const selectedSubjects = [];
  const checkboxes = document.querySelectorAll(".subject-checkbox:checked");
  checkboxes.forEach((checkbox) => selectedSubjects.push(checkbox.value));

  // Remove existing inputs
  const existingInputs = form.querySelectorAll(
    'input[name="selected_subjects"]'
  );
  existingInputs.forEach((input) => input.remove());

  // Add new inputs
  selectedSubjects.forEach((subjectId) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "selected_subjects";
    input.value = subjectId;
    form.appendChild(input);
  });

  return selectedSubjects.length > 0;
}

/**
 * Validate form before submission
 */
function validateAndSubmitForm() {
  const hasSelectedSubjects = addSelectedSubjectsToForm();

  if (!hasSelectedSubjects) {
    showNotification(
      "Please select at least one subject before submitting marks.",
      "danger"
    );
    return false;
  }

  // Check if any marks have been entered
  const markInputs = document.querySelectorAll(
    ".student-mark, .component-mark"
  );
  let hasMarks = false;

  markInputs.forEach((input) => {
    if (input.value && parseInt(input.value) > 0) {
      hasMarks = true;
    }
  });

  if (!hasMarks) {
    showConfirmationDialog(
      "No marks have been entered. Are you sure you want to submit an empty marksheet?",
      () => submitMarksForm()
    );
    return false;
  }

  return true;
}

/**
 * Show confirmation dialog
 */
function showConfirmationDialog(message, onConfirm) {
  const existingDialog = document.querySelector(".confirmation-dialog");
  if (existingDialog) existingDialog.remove();

  const dialogDiv = document.createElement("div");
  dialogDiv.className = "confirmation-dialog";
  dialogDiv.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.5); display: flex; align-items: center;
        justify-content: center; z-index: 10001;
    `;

  dialogDiv.innerHTML = `
        <div class="modal-content" style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                <i class="fas fa-question-circle" style="color: #ffc107; font-size: 24px;"></i>
                <h3 style="margin: 0; color: #333;">Confirm Submission</h3>
            </div>
            <p style="margin-bottom: 25px; color: #666; line-height: 1.5;">${message}</p>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="closeConfirmationDialog()" class="btn btn-secondary">Cancel</button>
                <button onclick="confirmSubmission()" class="btn btn-primary">Yes, Submit</button>
            </div>
        </div>
    `;

  document.body.appendChild(dialogDiv);
  window.confirmationCallback = onConfirm;
}

/**
 * Close confirmation dialog
 */
function closeConfirmationDialog() {
  const dialog = document.querySelector(".confirmation-dialog");
  if (dialog) dialog.remove();
  window.confirmationCallback = null;
}

/**
 * Confirm submission
 */
function confirmSubmission() {
  closeConfirmationDialog();
  if (window.confirmationCallback) {
    window.confirmationCallback();
  }
}

/**
 * Submit marks form programmatically
 */
function submitMarksForm() {
  const form = document.getElementById("marks-form");
  if (form) {
    const submitBtn = document.createElement("input");
    submitBtn.type = "hidden";
    submitBtn.name = "submit_marks";
    submitBtn.value = "1";
    form.appendChild(submitBtn);
    form.submit();
  }
}

// ====================================================================
// NAVIGATION FUNCTIONS
// ====================================================================

/**
 * Navigate to specific feature/tab
 */
function navigateToFeature(feature) {
  try {
    updateActiveNavigation(feature);

    switch (feature) {
      case "upload-marks":
        switchMainTab("upload-marks");
        setTimeout(() => scrollToSection("upload-marks-tab"), 300);
        break;
      case "recent-reports":
        switchMainTab("recent-reports");
        setTimeout(() => scrollToSection("recent-reports-tab"), 300);
        break;
      case "generate-reports":
        switchMainTab("generate-marksheet");
        setTimeout(() => scrollToSection("generate-marksheet-tab"), 300);
        break;
      case "management":
        scrollToSection("management-section");
        break;
    }
  } catch (error) {
    console.error("Navigation error:", error);
  }
  return false;
}

/**
 * Update active navigation state
 */
function updateActiveNavigation(activeFeature) {
  document.querySelectorAll(".nav-item[data-feature]").forEach((item) => {
    item.classList.remove("active");
  });

  const activeItem = document.querySelector(
    `.nav-item[data-feature="${activeFeature}"]`
  );
  if (activeItem) {
    activeItem.classList.add("active");
  }
}

/**
 * Switch main tab
 */
function switchMainTab(tabId) {
  // Hide all tab content
  document.querySelectorAll(".tab-content-container").forEach((tab) => {
    tab.classList.remove("active");
  });

  // Deactivate all navigation items
  document.querySelectorAll(".nav-item").forEach((navItem) => {
    navItem.classList.remove("active");
  });

  // Deactivate all tab buttons
  document.querySelectorAll(".tab-button").forEach((tab) => {
    tab.classList.remove("active");
  });

  // Show the selected tab content
  const targetTab = document.getElementById(tabId + "-tab");
  if (targetTab) {
    targetTab.classList.add("active");
  }

  // Activate corresponding navigation
  const navItem = document.querySelector(`[data-feature="${tabId}"]`);
  if (navItem) {
    navItem.classList.add("active");
  }

  // Activate corresponding tab button
  const tabButton = document.querySelector(`.tab-button[onclick*="${tabId}"]`);
  if (tabButton) {
    tabButton.classList.add("active");
  }

  // Store active tab
  sessionStorage.setItem("activeTab", tabId);
}

/**
 * Smooth scroll to section
 */
function scrollToSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// ====================================================================
// FLOATING ACTION BUTTON FUNCTIONS
// ====================================================================

/**
 * Toggle enhanced FAB menu
 */
function toggleEnhancedFab() {
  const fabMenu = document.getElementById("fab-menu");
  const fabIcon = document.getElementById("fab-icon");
  const fabMain = document.getElementById("fab-main-btn");

  if (fabMenu.classList.contains("active")) {
    fabMenu.classList.remove("active");
    fabMain.classList.remove("active");
    fabIcon.className = "fas fa-plus";
  } else {
    fabMenu.classList.add("active");
    fabMain.classList.add("active");
    fabIcon.className = "fas fa-times";
  }
}

// ====================================================================
// UTILITY FUNCTIONS
// ====================================================================

/**
 * Select all subjects
 */
function selectAllSubjects() {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = true;
    if (typeof toggleSubjectVisibility === "function") {
      toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
    }
  });
}

/**
 * Deselect all subjects
 */
function deselectAllSubjects() {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = false;
    if (typeof toggleSubjectVisibility === "function") {
      toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
    }
  });
}

/**
 * Restore active tab after page reload
 */
function restoreActiveTab() {
  const serverActiveTab = document.querySelector("[data-server-active-tab]")
    ?.dataset.serverActiveTab;
  if (!serverActiveTab || serverActiveTab === "recent-reports") {
    const activeTab = sessionStorage.getItem("activeTab");
    if (activeTab) {
      switchMainTab(activeTab);
    }
  }
}

// ====================================================================
// INITIALIZATION
// ====================================================================

/**
 * Initialize selected subjects functionality
 */
function initializeSelectedSubjects() {
  addSelectedSubjectsToForm();

  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", () => addSelectedSubjectsToForm());
  });
}

/**
 * Initialize enhanced navigation
 */
function initializeEnhancedNavigation() {
  // Close FAB menu when clicking outside
  document.addEventListener("click", function (event) {
    const fabSystem = document.querySelector(".floating-action-system");
    if (fabSystem && !fabSystem.contains(event.target)) {
      const menu = document.getElementById("fab-menu");
      const icon = document.getElementById("fab-icon");
      const main = document.getElementById("fab-main-btn");
      if (menu && menu.classList.contains("active")) {
        menu.classList.remove("active");
        main.classList.remove("active");
        icon.className = "fas fa-plus";
      }
    }
  });

  const activeTab = sessionStorage.getItem("activeTab") || "recent-reports";
  updateActiveNavigation(activeTab);
}

/**
 * Store original grade options for filtering
 */
function storeOriginalGradeOptions() {
  // This function would be implemented based on specific requirements
  // for grade filtering functionality
}

/**
 * Main DOMContentLoaded initialization
 */
document.addEventListener("DOMContentLoaded", function () {
  // Initialize core functionality
  initializeSelectedSubjects();
  initializeEnhancedNavigation();
  storeOriginalGradeOptions();

  // Initialize proportional weights for composite subjects
  const allSubjects = document.querySelectorAll("input.component-max-marks");
  const processedSubjects = new Set();

  allSubjects.forEach((input) => {
    const subjectId = input.dataset.subject;
    if (!processedSubjects.has(subjectId)) {
      updateProportionalWeights(subjectId);
      processedSubjects.add(subjectId);
    }
  });

  // Restore active tab
  restoreActiveTab();

  // Auto-scroll to student list if needed
  const showStudents = document.querySelector("[data-show-students]");
  if (showStudents) {
    setTimeout(() => {
      const pupilsList = document.getElementById("pupils-list");
      if (pupilsList) {
        pupilsList.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 500);
  }

  console.log("Class Teacher Dashboard initialized successfully");
});

// ====================================================================
// MISSING FUNCTIONS REFERENCED IN TEMPLATE
// ====================================================================

/**
 * Download marks template
 */
function downloadTemplate() {
  window.location.href = "/classteacher/download_template";
}

/**
 * Refresh permission status
 */
function refreshPermissionStatus() {
  const contentDiv = document.getElementById("permission-status-content");
  if (contentDiv) {
    contentDiv.innerHTML =
      '<div style="text-align: center; color: var(--gray-500);"><i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; margin-bottom: var(--space-2);"></i><p>Loading permission status...</p></div>';

    // Reload the page to refresh permissions
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  }
}

/**
 * Reset filters
 */
function resetFilters() {
  const filterInputs = document.querySelectorAll(
    "#recent-reports-tab input, #recent-reports-tab select"
  );
  filterInputs.forEach((input) => {
    if (input.type === "text" || input.type === "search") {
      input.value = "";
    } else if (input.tagName === "SELECT") {
      input.selectedIndex = 0;
    }
  });
  // Trigger filter update if there's a function for it
  if (typeof updateReportFilters === "function") {
    updateReportFilters();
  }
}

/**
 * Confirm delete report
 */
function confirmDeleteReport(grade, stream, term, assessmentType) {
  if (
    confirm(
      `Are you sure you want to delete the marksheet for Grade ${grade} Stream ${stream}, ${term}, ${assessmentType}? This action cannot be undone.`
    )
  ) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/classteacher/delete_report";

    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      .getAttribute("content");

    const fields = {
      csrf_token: csrfToken,
      grade: grade,
      stream: stream,
      term: term,
      assessment_type: assessmentType,
    };

    Object.keys(fields).forEach((key) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = key;
      input.value = fields[key];
      form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
  }
}

/**
 * Check stream status
 */
function checkStreamStatus() {
  const grade = document.getElementById("stream_grade").value;
  const term = document.getElementById("stream_term").value;
  const assessmentType = document.getElementById(
    "stream_assessment_type"
  ).value;

  if (!grade || !term || !assessmentType) {
    return;
  }

  // Show loading state
  const statusContainer = document.getElementById("stream-status-container");
  if (statusContainer) {
    statusContainer.style.display = "block";
    statusContainer.innerHTML =
      '<div style="text-align: center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Checking stream status...</div>';
  }

  // Simulate checking status (replace with actual API call)
  setTimeout(() => {
    if (statusContainer) {
      statusContainer.innerHTML =
        '<div style="padding: 20px; color: #28a745;">‚úÖ All streams ready for marksheet generation</div>';

      // Enable buttons
      const previewBtn = document.getElementById("preview-marksheet-btn");
      const downloadBtn = document.getElementById("download-marksheet-btn");
      if (previewBtn) previewBtn.disabled = false;
      if (downloadBtn) downloadBtn.disabled = false;
    }
  }, 1500);
}

/**
 * Sort assignments table
 */
function sortAssignments(column) {
  console.log(`Sorting assignments by: ${column}`);
  // Add sorting logic here if needed
}

/**
 * Select all subjects checkbox functionality
 */
function selectAllSubjects() {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = true;
    if (checkbox.dataset.subjectId) {
      toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
    }
  });
}

/**
 * Deselect all subjects checkbox functionality
 */
function deselectAllSubjects() {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = false;
    if (checkbox.dataset.subjectId) {
      toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
    }
  });
}

/**
 * Toggle subject visibility in table
 */
function toggleSubjectVisibility(checkbox, subjectId) {
  const subjectHeaders = document.querySelectorAll(
    `th[data-subject-id="${subjectId}"]`
  );
  const subjectCells = document.querySelectorAll(
    `td[data-subject-id="${subjectId}"]`
  );

  if (checkbox.checked) {
    subjectHeaders.forEach((header) => (header.style.display = ""));
    subjectCells.forEach((cell) => (cell.style.display = ""));
  } else {
    subjectHeaders.forEach((header) => (header.style.display = "none"));
    subjectCells.forEach((cell) => (cell.style.display = "none"));
  }
}

/**
 * Navigate to a specific feature/tab
 */
function navigateToFeature(feature) {
  console.log(`Navigating to feature: ${feature}`);

  switch (feature) {
    case "upload-marks":
      switchMainTab("upload-marks");
      break;
    case "recent-reports":
      switchMainTab("recent-reports");
      break;
    case "generate-reports":
      switchMainTab("generate-marksheet");
      break;
    case "management":
      // Scroll to management section
      const managementSection = document.getElementById("management-section");
      if (managementSection) {
        managementSection.scrollIntoView({ behavior: "smooth" });
      }
      break;
    default:
      console.log("Unknown feature:", feature);
  }
}

/**
 * Toggle enhanced floating action button menu
 */
function toggleEnhancedFab() {
  const fabMenu = document.getElementById("fab-menu");
  const fabIcon = document.getElementById("fab-icon");
  const fabMainBtn = document.getElementById("fab-main-btn");

  if (fabMenu && fabIcon && fabMainBtn) {
    const isOpen = fabMenu.classList.contains("open");

    if (isOpen) {
      fabMenu.classList.remove("open");
      fabIcon.classList.remove("fa-times");
      fabIcon.classList.add("fa-plus");
      fabMainBtn.classList.remove("open");
    } else {
      fabMenu.classList.add("open");
      fabIcon.classList.remove("fa-plus");
      fabIcon.classList.add("fa-times");
      fabMainBtn.classList.add("open");
    }
  }
}

/**
 * Download all individual reports
 */
function downloadAllIndividualReports(grade, stream, term, assessmentType) {
  // Create a form to submit for downloading all reports
  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/classteacher/download_all_individual_reports";

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");

  const fields = {
    csrf_token: csrfToken,
    grade: grade,
    stream: stream,
    term: term,
    assessment_type: assessmentType,
  };

  Object.keys(fields).forEach((key) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = key;
    input.value = fields[key];
    form.appendChild(input);
  });

  document.body.appendChild(form);
  form.submit();
  document.body.removeChild(form);
}

/**
 * Close delete report modal
 */
function closeDeleteReportModal() {
  const modal = document.getElementById("deleteReportModal");
  if (modal) {
    modal.style.display = "none";
  }
}

/**
 * Update bulk grades based on education level
 */
function updateBulkGrades() {
  const educationLevel = document.getElementById("bulk_education_level").value;
  const gradeSelect = document.getElementById("bulk_grade");

  // Clear existing options
  gradeSelect.innerHTML = '<option value="">Select Grade</option>';

  // Add grades based on education level
  const gradesByLevel = {
    lower_primary: ["Grade 1", "Grade 2", "Grade 3"],
    upper_primary: ["Grade 4", "Grade 5", "Grade 6"],
    junior_secondary: ["Grade 7", "Grade 8", "Grade 9"],
  };

  if (gradesByLevel[educationLevel]) {
    gradesByLevel[educationLevel].forEach((grade) => {
      const option = document.createElement("option");
      option.value = grade;
      option.textContent = grade;
      gradeSelect.appendChild(option);
    });
  }
}

/**
 * Fetch streams for selected grade
 */
function fetchBulkStreams() {
  const grade = document.getElementById("bulk_grade").value;
  const streamSelect = document.getElementById("bulk_stream");

  // Clear existing options
  streamSelect.innerHTML = '<option value="">Select Stream</option>';

  if (!grade) return;

  // Simulate fetching streams (in real app, this would be an AJAX call)
  const streams = ["A", "B"]; // Default streams

  streams.forEach((stream) => {
    const option = document.createElement("option");
    option.value = stream;
    option.textContent = `Stream ${stream}`;
    streamSelect.appendChild(option);
  });
}

/**
 * Update all marks for a subject when total marks changes
 */
function updateAllMarksForSubject(subjectId, subjectIndex) {
  const totalMarksInput = document.getElementById(
    `total_marks_${subjectIndex}`
  );
  const totalMarks = parseInt(totalMarksInput.value) || 100;

  // Update subject info display
  const subjectInfo = document.getElementById(`subject_info_${subjectIndex}`);
  if (subjectInfo) {
    subjectInfo.textContent = `Max Raw: ${totalMarks}`;
  }

  // Recalculate all percentages for this subject
  const markInputs = document.querySelectorAll(
    `input[data-subject-id="${subjectId}"]`
  );
  markInputs.forEach((input) => {
    if (input.type === "number" && input.name.includes("mark_")) {
      updatePercentage(input);
    }
  });
}

/**
 * Validate max marks input
 */
function validateMaxMarks(input) {
  const value = parseInt(input.value);
  const min = parseInt(input.min) || 1;
  const max = parseInt(input.max) || 100;

  if (value < min) {
    input.value = min;
    showNotification(`Minimum marks value is ${min}`, "warning");
  } else if (value > max) {
    input.value = max;
    showNotification(`Maximum marks value is ${max}`, "warning");
  }
}

/* ===============================
 * ENHANCED GENERATE MARKSHEET FUNCTIONALITY
 * =============================== */

// Enhanced stream status checking with better visual feedback
function checkStreamStatus() {
  const grade = document.getElementById('stream_grade').value;
  const term = document.getElementById('stream_term').value;
  const assessmentType = document.getElementById('stream_assessment_type').value;
  
  const statusContainer = document.getElementById('stream-status-container');
  const statusList = document.getElementById('stream-status-list');
  const previewBtn = document.getElementById('preview-marksheet-btn');
  const downloadBtn = document.getElementById('download-marksheet-btn');
  
  // Reset buttons
  previewBtn.disabled = true;
  downloadBtn.disabled = true;
  
  if (!grade || !term || !assessmentType) {
    statusContainer.style.display = 'none';
    return;
  }
  
  // Show loading state
  statusContainer.style.display = 'block';
  statusList.innerHTML = `
    <div class="loading-status" style="text-align: center; padding: 2rem; color: #2aa198;">
      <i class="fas fa-spinner fa-spin" style="font-size: 2rem; margin-bottom: 1rem;"></i>
      <p>Checking stream status...</p>
    </div>
  `;
  
  // Make API call to check stream status
  fetch(`/classteacher/api/stream-status?grade=${encodeURIComponent(grade)}&term=${encodeURIComponent(term)}&assessment_type=${encodeURIComponent(assessmentType)}`)
    .then(response => response.json())
    .then(data => {
      updateStreamStatusDisplay(data);
    })
    .catch(error => {
      console.error('Error checking stream status:', error);
      statusList.innerHTML = `
        <div class="error-status" style="text-align: center; padding: 2rem; color: #cb4b16;">
          <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
          <p>Error checking stream status. Please try again.</p>
        </div>
      `;
    });
}

// Enhanced status display with better styling
function updateStreamStatusDisplay(data) {
  const statusList = document.getElementById('stream-status-list');
  const previewBtn = document.getElementById('preview-marksheet-btn');
  const downloadBtn = document.getElementById('download-marksheet-btn');
  
  if (!data.streams || data.streams.length === 0) {
    statusList.innerHTML = `
      <div class="no-streams-status" style="text-align: center; padding: 2rem; color: #cb4b16;">
        <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
        <p>No streams found for the selected grade.</p>
      </div>
    `;
    return;
  }
  
  let allReady = true;
  let html = '';
  
  data.streams.forEach(stream => {
    const isReady = stream.has_marks;
    if (!isReady) allReady = false;
    
    const statusClass = isReady ? 'ready' : 'pending';
    const statusIcon = isReady ? '‚úÖ' : '‚ö†Ô∏è';
    const statusText = isReady ? 'Ready for marksheet generation' : 'Marks not yet uploaded';
    const statusColor = isReady ? '#2aa198' : '#cb4b16';
    
    html += `
      <div class="stream-status-item ${statusClass}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h5 style="margin: 0; color: #fdf6e3; font-weight: 600;">
              <i class="fas fa-stream me-2"></i>Stream ${stream.name}
            </h5>
            <p style="margin: 0.5rem 0 0 0; color: ${statusColor}; font-weight: 500;">
              ${statusIcon} ${statusText}
            </p>
          </div>
          <div class="stream-stats" style="text-align: right; color: rgba(255, 255, 255, 0.8);">
            <small>
              <i class="fas fa-users me-1"></i>${stream.student_count || 0} students<br>
              <i class="fas fa-book me-1"></i>${stream.subject_count || 0} subjects
            </small>
          </div>
        </div>
      </div>
    `;
  });
  
  // Add summary
  const readyCount = data.streams.filter(s => s.has_marks).length;
  const totalCount = data.streams.length;
  
  html += `
    <div class="status-summary" style="margin-top: 2rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(42, 161, 152, 0.2) 0%, rgba(38, 139, 210, 0.2) 100%); border-radius: 12px; border: 1px solid rgba(42, 161, 152, 0.3);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h6 style="margin: 0; color: #fdf6e3; font-weight: 600;">
            <i class="fas fa-chart-pie me-2"></i>Overall Progress
          </h6>
          <p style="margin: 0.5rem 0 0 0; color: rgba(255, 255, 255, 0.9);">
            ${readyCount} of ${totalCount} streams ready
          </p>
        </div>
        <div class="progress-circle" style="font-size: 2rem;">
          ${allReady ? 'Ìæâ' : '‚è≥'}
        </div>
      </div>
    </div>
  `;
  
  statusList.innerHTML = html;
  
  // Enable buttons if all streams are ready
  if (allReady) {
    previewBtn.disabled = false;
    downloadBtn.disabled = false;
    
    // Add success animation
    setTimeout(() => {
      previewBtn.style.animation = 'pulse 2s infinite';
      downloadBtn.style.animation = 'pulse 2s infinite';
    }, 500);
  }
}

// Add smooth animations and interactions
document.addEventListener('DOMContentLoaded', function() {
  // Enhanced form interactions
  const formSelects = document.querySelectorAll('#stream-marksheet-form select');
  
  formSelects.forEach(select => {
    select.addEventListener('change', function() {
      // Add visual feedback
      this.style.transform = 'scale(1.02)';
      setTimeout(() => {
        this.style.transform = 'scale(1)';
      }, 150);
    });
    
    select.addEventListener('focus', function() {
      this.style.transform = 'translateY(-2px)';
    });
    
    select.addEventListener('blur', function() {
      this.style.transform = 'translateY(0)';
    });
  });
  
  // Enhanced button interactions
  const actionButtons = document.querySelectorAll('#preview-marksheet-btn, #download-marksheet-btn');
  
  actionButtons.forEach(button => {
    button.addEventListener('mouseenter', function() {
      if (!this.disabled) {
        this.style.transform = 'translateY(-3px) scale(1.02)';
      }
    });
    
    button.addEventListener('mouseleave', function() {
      if (!this.disabled) {
        this.style.transform = 'translateY(0) scale(1)';
      }
    });
  });
  
  // Enhanced refresh button interaction
  const refreshBtn = document.querySelector('.refresh-status');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', function() {
      // Add spin animation
      const icon = this.querySelector('i') || this;
      icon.style.animation = 'spin 1s ease-in-out';
      
      setTimeout(() => {
        icon.style.animation = '';
      }, 1000);
    });
  }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes pulse {
    0% { box-shadow: 0 8px 25px rgba(181, 137, 0, 0.4); }
    50% { box-shadow: 0 12px 35px rgba(181, 137, 0, 0.6); }
    100% { box-shadow: 0 8px 25px rgba(181, 137, 0, 0.4); }
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .stream-status-item {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .loading-status i {
    animation: spin 1s linear infinite;
  }
`;
document.head.appendChild(style);
