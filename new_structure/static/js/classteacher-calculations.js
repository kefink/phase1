/**
 * Class Teacher Marks Calculation and Validation JavaScript
 * Advanced functions for mark calculations, performance indicators, and validation
 */

// ====================================================================
// MARKS VALIDATION FUNCTIONS
// ====================================================================

/**
 * Validate maximum marks (should not exceed 100)
 * @param {HTMLElement} inputElement - The input element to validate
 */
function validateMaxMarks(inputElement) {
  const value = parseFloat(inputElement.value) || 0;
  const maxAllowed = 100;

  if (value > maxAllowed) {
    // Cap the value at maximum allowed
    inputElement.value = maxAllowed;

    // Show visual feedback
    inputElement.style.borderColor = "#dc3545";
    inputElement.style.backgroundColor = "#fff5f5";

    // Show temporary warning message
    const warningMsg = document.createElement("div");
    warningMsg.textContent = `Maximum raw marks cannot exceed ${maxAllowed}. Value capped at ${maxAllowed}.`;
    warningMsg.style.cssText = `
            position: absolute;
            background: #dc3545;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            top: 100%;
            left: 0;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        `;

    // Position relative to input
    const inputRect = inputElement.getBoundingClientRect();
    inputElement.parentElement.style.position = "relative";
    inputElement.parentElement.appendChild(warningMsg);

    // Remove warning after 3 seconds
    setTimeout(() => {
      if (warningMsg.parentElement) {
        warningMsg.parentElement.removeChild(warningMsg);
      }
      inputElement.style.borderColor = "";
      inputElement.style.backgroundColor = "";
    }, 3000);
  }
}

// ====================================================================
// PERFORMANCE CALCULATION FUNCTIONS
// ====================================================================

/**
 * Update the visual performance indicator based on percentage
 * @param {HTMLElement} element - The element to update
 * @param {number} percentage - The performance percentage
 */
function updatePerformanceIndicator(element, percentage) {
  // Remove existing performance classes
  element.classList.remove(
    "performance-ee",
    "performance-me",
    "performance-ae",
    "performance-be"
  );

  // Add appropriate class based on percentage
  if (percentage >= 75) {
    element.classList.add("performance-ee"); // Exceeding Expectation
  } else if (percentage >= 50) {
    element.classList.add("performance-me"); // Meeting Expectation
  } else if (percentage >= 30) {
    element.classList.add("performance-ae"); // Approaching Expectation
  } else {
    element.classList.add("performance-be"); // Below Expectation
  }
}

/**
 * Update performance display with color coding and percentage bar
 * @param {HTMLElement} overallPercentageDisplay - The percentage display element
 * @param {number} roundedOverallPercentage - The rounded percentage value
 */
function updatePerformanceDisplay(
  overallPercentageDisplay,
  roundedOverallPercentage
) {
  if (!overallPercentageDisplay) return;

  // Update the percentage text and color based on performance bands
  overallPercentageDisplay.textContent = `${roundedOverallPercentage}%`;

  // Apply color coding based on performance levels
  if (roundedOverallPercentage >= 75) {
    overallPercentageDisplay.style.color = "#28a745"; // Exceeding Expectation
    overallPercentageDisplay.style.fontWeight = "bold";
  } else if (roundedOverallPercentage >= 50) {
    overallPercentageDisplay.style.color = "#17a2b8"; // Meeting Expectation
    overallPercentageDisplay.style.fontWeight = "bold";
  } else if (roundedOverallPercentage >= 30) {
    overallPercentageDisplay.style.color = "#ffc107"; // Approaching Expectation
    overallPercentageDisplay.style.fontWeight = "bold";
  } else {
    overallPercentageDisplay.style.color = "#dc3545"; // Below Expectation
    overallPercentageDisplay.style.fontWeight = "bold";
  }

  // Update the percentage bar
  const percentageFill =
    overallPercentageDisplay.nextElementSibling?.querySelector(
      ".percentage-fill"
    );
  if (percentageFill) {
    percentageFill.style.width = `${Math.min(roundedOverallPercentage, 100)}%`;

    // Set color based on performance level
    if (roundedOverallPercentage >= 75) {
      percentageFill.style.backgroundColor = "#28a745"; // Exceeding Expectation
    } else if (roundedOverallPercentage >= 50) {
      percentageFill.style.backgroundColor = "#17a2b8"; // Meeting Expectation
    } else if (roundedOverallPercentage >= 30) {
      percentageFill.style.backgroundColor = "#ffc107"; // Approaching Expectation
    } else {
      percentageFill.style.backgroundColor = "#dc3545"; // Below Expectation
    }
  }
}

// ====================================================================
// COMPOSITE SUBJECT MARKS MANAGEMENT
// ====================================================================

/**
 * Update component max marks for composite subjects
 * @param {string} subject - The subject identifier
 * @param {number} subjectIndex - The subject index
 */
function updateComponentMaxMarks(subject, subjectIndex) {
  // Get all component max marks inputs for this subject
  const componentInputs = document.querySelectorAll(
    `.component-max-marks[data-subject="${subject}"]`
  );
  if (!componentInputs.length) {
    return;
  }

  // Calculate the total marks from all components
  let totalMarks = 0;
  componentInputs.forEach((input) => {
    const componentMarks = parseInt(input.value) || 0;
    totalMarks += componentMarks;
  });

  // Update the total marks display
  const totalCompositeSpan = document.getElementById(
    `total_composite_${subjectIndex}`
  );
  if (totalCompositeSpan) {
    totalCompositeSpan.textContent = totalMarks;
  }

  // Update the hidden total marks input
  const totalMarksInput = document.getElementById(
    `total_marks_${subjectIndex}`
  );
  if (totalMarksInput) {
    totalMarksInput.value = totalMarks;
  }

  // Update the subject info display in the table header
  const subjectInfoSpan = document.getElementById(
    `subject_info_${subjectIndex}`
  );
  if (subjectInfoSpan) {
    subjectInfoSpan.textContent = `Max Raw: ${totalMarks}`;
  }

  // Update all component mark inputs with their new max values
  componentInputs.forEach((input) => {
    const componentId = input.dataset.component;
    const componentMaxMarks = parseInt(input.value) || 0;

    // Find all student mark inputs for this component
    const studentComponentInputs = document.querySelectorAll(
      `.component-mark[data-subject="${subject}"][data-component="${componentId}"]`
    );

    // Update each student's component mark input
    studentComponentInputs.forEach((studentInput) => {
      studentInput.max = componentMaxMarks;
      studentInput.dataset.maxMark = componentMaxMarks;

      // If the current value exceeds the new max, cap it
      const currentValue = parseInt(studentInput.value) || 0;
      if (currentValue > componentMaxMarks) {
        studentInput.value = componentMaxMarks;
      }

      // Recalculate the overall mark for this student
      const studentName = studentInput.dataset.student;
      if (window.calculateOverallSubjectMark) {
        calculateOverallSubjectMark(studentName, subject);
      }
    });
  });
}

// ====================================================================
// UPLOAD FORM NAVIGATION FUNCTIONS
// ====================================================================

/**
 * Navigate to upload form for specific grade and stream
 * @param {string} gradeName - The grade name
 * @param {string} streamName - The stream name
 */
function navigateToUploadForm(gradeName, streamName) {
  // Set the grade dropdown
  const gradeSelect = document.getElementById("upload-grade");
  if (gradeSelect) {
    gradeSelect.value = gradeName;
    gradeSelect.dispatchEvent(new Event("change"));
  }

  // Wait for stream options to load, then set stream
  setTimeout(() => {
    const streamSelect = document.getElementById("upload-stream");
    if (streamSelect) {
      streamSelect.value = `Stream ${streamName}`;
    }

    // Scroll to the upload form
    const uploadForm = document.getElementById("upload-marks-form");
    if (uploadForm) {
      uploadForm.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // Highlight the form briefly
    const formContainer = document.querySelector(".upload-form-container");
    if (formContainer) {
      formContainer.style.border = "2px solid #007bff";
      formContainer.style.borderRadius = "8px";
      setTimeout(() => {
        formContainer.style.border = "";
        formContainer.style.borderRadius = "";
      }, 3000);
    }
  }, 500);
}

// ====================================================================
// INITIALIZATION AND EVENT HANDLERS
// ====================================================================

/**
 * Initialize marks calculation and validation functionality
 */
document.addEventListener("DOMContentLoaded", function () {
  // Initialize max marks validation
  const maxMarksInputs = document.querySelectorAll(
    'input[type="number"].component-max-marks, input[type="number"][data-max-mark]'
  );
  maxMarksInputs.forEach((input) => {
    input.addEventListener("blur", function () {
      validateMaxMarks(this);
    });

    input.addEventListener("change", function () {
      validateMaxMarks(this);
    });
  });

  // Initialize component max marks functionality
  const componentMaxInputs = document.querySelectorAll(".component-max-marks");
  componentMaxInputs.forEach((input) => {
    input.addEventListener("change", function () {
      const subject = this.dataset.subject;
      const subjectIndex = this.dataset.subjectIndex;
      if (subject && subjectIndex !== undefined) {
        updateComponentMaxMarks(subject, parseInt(subjectIndex));
      }
    });
  });

  // Initialize performance indicators
  const performanceElements = document.querySelectorAll(
    "[data-performance-percentage]"
  );
  performanceElements.forEach((element) => {
    const percentage = parseFloat(element.dataset.performancePercentage) || 0;
    updatePerformanceIndicator(element, percentage);
  });
});
