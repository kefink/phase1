// Additional Classteacher JavaScript Functions
// These functions handle specialized calculations, validations and UI interactions

// Function to calculate and display proportional weights for a subject
function updateProportionalWeights(subjectId) {
  // Find all component max mark inputs for this subject
  const componentMaxInputs = document.querySelectorAll(
    `input.component-max-marks[data-subject="${subjectId}"]`
  );

  // Get the total weights of all components
  let totalWeight = 0;
  componentMaxInputs.forEach((input) => {
    totalWeight += parseInt(input.value) || 0;
  });

  // Update the proportional weight display for each component
  componentMaxInputs.forEach((input) => {
    const componentId = input.dataset.component;
    const weight = parseInt(input.value) || 0;
    const proportionalWeight =
      totalWeight > 0 ? ((weight / totalWeight) * 100).toFixed(1) : "0.0";

    // Update the display
    const weightDisplay = document.getElementById(
      `prop_weight_${subjectId}_${componentId}`
    );
    if (weightDisplay) {
      weightDisplay.textContent = `${proportionalWeight}%`;
    }
  });
}

// Function to select a class for marks upload
function selectClassForUpload(gradeName, streamName, educationLevel) {
  // Set the values in the form
  document.getElementById("education_level").value = educationLevel;

  // This will trigger the grade filter
  const educationLevelEvent = new Event("change", { bubbles: true });
  document.getElementById("education_level").dispatchEvent(educationLevelEvent);

  // Small delay to allow grade options to update
  setTimeout(() => {
    document.getElementById("grade").value = gradeName;

    // This will trigger stream loading
    const gradeEvent = new Event("change", { bubbles: true });
    document.getElementById("grade").dispatchEvent(gradeEvent);

    // Small delay to allow streams to load
    setTimeout(() => {
      // Set the stream
      document.getElementById("stream").value = streamName;

      // This will trigger any stream-dependent logic
      const streamEvent = new Event("change", { bubbles: true });
      document.getElementById("stream").dispatchEvent(streamEvent);

      // Scroll to the upload form
      const uploadForm = document.getElementById("upload-marks-form");
      if (uploadForm) {
        uploadForm.scrollIntoView({ behavior: "smooth" });
      }
    }, 300);
  }, 300);
}

// Function to validate maximum marks (should not exceed 100)
function validateMaxMarks(inputElement) {
  let value = parseInt(inputElement.value) || 0;

  // Validate minimum
  if (value < 1) {
    value = 1;
    inputElement.value = value;
  }

  // Validate maximum (usually 100, but could be higher for composite subjects)
  const maxAllowed = 100;
  if (value > maxAllowed) {
    // Determine if this is part of a composite subject with multiple components
    const isComposite =
      document.querySelectorAll(
        `input.component-max-marks[data-subject="${inputElement.dataset.subject}"]`
      ).length > 1;

    // For composite subjects, we allow individual components to exceed 100
    if (!isComposite) {
      value = maxAllowed;
      inputElement.value = value;
    }
  }

  // If this is a component max mark, update proportional weights
  if (inputElement.classList.contains("component-max-marks")) {
    const subjectId = inputElement.dataset.subject;
    updateProportionalWeights(subjectId);
  }

  // Update all student marks to reflect the new maximum
  if (inputElement.dataset.subjectIndex !== undefined) {
    const subjectId = inputElement.dataset.subject;
    const subjectIndex = inputElement.dataset.subjectIndex;
    updateAllMarksForSubject(subjectId, subjectIndex);
  }

  return value;
}

// Function to update percentage based on raw mark and total marks
function updatePercentage(inputElement) {
  // Get the mark value
  let mark = parseFloat(inputElement.value) || 0;

  // Get the maximum mark value (from the element's data attribute, or default to 100)
  const maxMark = parseFloat(inputElement.dataset.maxMark) || 100;

  // Calculate percentage
  let percentage = (mark / maxMark) * 100;

  // Ensure marks don't exceed maximum
  if (mark > maxMark) {
    mark = maxMark;
    inputElement.value = mark;
    percentage = 100;
  }

  // Find the percentage display element
  const subjectId = inputElement.dataset.subject;
  const studentId = inputElement.dataset.student;

  // The structure of the ID depends on whether this is a component mark or overall mark
  let percentageElement;

  if (inputElement.classList.contains("component-mark")) {
    // For component marks
    const componentId = inputElement.dataset.component;
    percentageElement = document.getElementById(
      `percentage_${studentId}_${subjectId}_${componentId}`
    );
  } else {
    // For overall subject marks
    percentageElement = document.getElementById(
      `percentage_${studentId}_${subjectId}`
    );
  }

  // Update the percentage display
  if (percentageElement) {
    percentageElement.textContent = `${percentage.toFixed(1)}%`;

    // Update visual performance indicator
    updatePerformanceIndicator(percentageElement, percentage);
  }

  return percentage;
}

// Function to update component percentage and calculate overall subject mark
function updateComponentPercentage(inputElement) {
  // Update the percentage for this specific component
  const percentage = updatePercentage(inputElement);

  // Get the subject and student IDs
  const subjectId = inputElement.dataset.subject;
  const studentId = inputElement.dataset.student;

  // Recalculate the overall subject mark
  calculateOverallSubjectMark(studentId, subjectId);

  return percentage;
}

// Function to calculate the overall subject mark from component marks
function calculateOverallSubjectMark(student, subject) {
  // Find all component mark inputs for this student and subject
  const componentInputs = document.querySelectorAll(
    `input.component-mark[data-student="${student}"][data-subject="${subject}"]`
  );

  // If there are no component inputs, this is not a composite subject
  if (componentInputs.length <= 1) {
    return;
  }

  // Find the overall mark display elements
  const overallMarkElement = document.getElementById(
    `overall_mark_${student}_${subject}`
  );
  const overallPercentageElement = document.getElementById(
    `overall_percentage_${student}_${subject}`
  );

  // If we can't find the display elements, we can't update
  if (!overallMarkElement || !overallPercentageElement) {
    return;
  }

  // Calculate weighted sum of component marks and total possible marks
  let weightedMarkSum = 0;
  let totalWeight = 0;

  componentInputs.forEach((input) => {
    const mark = parseFloat(input.value) || 0;
    const componentId = input.dataset.component;

    // Find the max mark for this component
    const maxMarkInput = document.querySelector(
      `input.component-max-marks[data-subject="${subject}"][data-component="${componentId}"]`
    );

    if (maxMarkInput) {
      const maxMark = parseFloat(maxMarkInput.value) || 0;
      weightedMarkSum += mark;
      totalWeight += maxMark;
    }
  });

  // Calculate the overall mark and percentage
  let overallMark = 0;
  let overallPercentage = 0;

  if (totalWeight > 0) {
    // Proportional calculation (weighted average)
    overallPercentage = (weightedMarkSum / totalWeight) * 100;
    overallMark = weightedMarkSum;
  }

  // Update the display
  overallMarkElement.textContent = overallMark.toFixed(1);
  overallPercentageElement.textContent = `${overallPercentage.toFixed(1)}%`;

  // Update visual performance indicator
  updatePerformanceIndicator(overallPercentageElement, overallPercentage);
}

// Function to update the visual performance indicator
function updatePerformanceIndicator(element, percentage) {
  // Remove existing classes
  element.classList.remove(
    "text-danger",
    "text-warning",
    "text-info",
    "text-success"
  );

  // Add appropriate class based on percentage
  if (percentage < 40) {
    element.classList.add("text-danger");
  } else if (percentage < 60) {
    element.classList.add("text-warning");
  } else if (percentage < 80) {
    element.classList.add("text-info");
  } else {
    element.classList.add("text-success");
  }
}

// Function to update component max marks for composite subjects
function updateComponentMaxMarks(subject, subjectIndex) {
  const componentRows = document.querySelectorAll(
    `.component-row[data-subject="${subject}"]`
  );

  // If we have components, this is a composite subject
  if (componentRows.length === 0) {
    return;
  }

  // Find the total marks input
  const totalMarksInput = document.getElementById(
    `total_marks_${subjectIndex}`
  );
  if (!totalMarksInput) {
    return;
  }

  // Calculate the sum of component weights
  let totalComponentWeight = 0;
  const componentMaxMarkInputs = document.querySelectorAll(
    `input.component-max-marks[data-subject="${subject}"]`
  );

  componentMaxMarkInputs.forEach((input) => {
    totalComponentWeight += parseInt(input.value) || 0;
  });

  // Update the total marks to match the sum of component weights
  totalMarksInput.value = totalComponentWeight;

  // Update all student marks for this subject
  updateAllMarksForSubject(subject);
}

// Function to update all student marks for a subject when max marks change
function updateAllStudentMarksForSubject(subject) {
  // Find all mark inputs for this subject
  const markInputs = document.querySelectorAll(
    `input[data-subject="${subject}"]`
  );

  // Update each percentage display
  markInputs.forEach((input) => {
    if (
      input.classList.contains("student-mark") ||
      input.classList.contains("component-mark")
    ) {
      updatePercentage(input);
    }
  });
}

// Function to add selected subjects to the form before submission
function addSelectedSubjectsToForm() {
  const form = document.getElementById("marks-form");
  if (!form) {
    return false;
  }

  // Get all checked subject checkboxes
  const checkedSubjects = document.querySelectorAll(
    "input.subject-checkbox:checked"
  );

  // If no subjects are selected, show a warning
  if (checkedSubjects.length === 0) {
    const errorContainer = document.getElementById("form-errors");
    if (errorContainer) {
      errorContainer.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please select at least one subject to upload marks for.
                </div>
            `;
      errorContainer.style.display = "block";
    }
    return false;
  }

  // Create a hidden input with the selected subject IDs
  let selectedSubjectIds = [];
  checkedSubjects.forEach((checkbox) => {
    selectedSubjectIds.push(checkbox.value);
  });

  // Remove any existing hidden input
  const existingInput = document.getElementById("selected_subjects_input");
  if (existingInput) {
    existingInput.remove();
  }

  // Create a new hidden input with the selected subject IDs
  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.id = "selected_subjects_input";
  hiddenInput.name = "selected_subjects";
  hiddenInput.value = selectedSubjectIds.join(",");
  form.appendChild(hiddenInput);

  return true;
}

// Function to initialize selected subjects when page loads
function initializeSelectedSubjects() {
  const subjectCheckboxes = document.querySelectorAll(".subject-checkbox");

  // Initialize subject visibility based on checkbox state
  subjectCheckboxes.forEach((checkbox) => {
    if (checkbox.dataset.subjectId) {
      toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
    }
  });
}

// Initialize when page loads
document.addEventListener("DOMContentLoaded", function () {
  // Initialize subject checkboxes
  initializeSelectedSubjects();

  // Add event listeners to subject checkboxes
  document.querySelectorAll(".subject-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      if (this.dataset.subjectId) {
        toggleSubjectVisibility(this, this.dataset.subjectId);
      }
    });
  });
});

// Function to validate form before submission
function validateAndSubmitForm() {
  // Add selected subjects to the form
  const hasSelectedSubjects = addSelectedSubjectsToForm();

  // If no subjects are selected, prevent submission
  if (!hasSelectedSubjects) {
    return false;
  }

  // Submit the form
  return true;
}

// Function to show validation error
function showValidationError(message) {
  const errorContainer = document.getElementById("form-errors");
  if (errorContainer) {
    errorContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i>
                ${message}
            </div>
        `;
    errorContainer.style.display = "block";

    // Scroll to error
    errorContainer.scrollIntoView({ behavior: "smooth" });
  }
}

// Function to show confirmation dialog
function showConfirmationDialog(message, onConfirm) {
  const dialog = document.getElementById("confirmation-dialog");
  const dialogMessage = document.getElementById("confirmation-message");

  if (dialog && dialogMessage) {
    dialogMessage.textContent = message;
    dialog.style.display = "block";

    // Set the confirm action
    document.getElementById("confirm-button").onclick = function () {
      closeConfirmationDialog();
      if (typeof onConfirm === "function") {
        onConfirm();
      }
    };
  }
}

// Function to close confirmation dialog
function closeConfirmationDialog() {
  const dialog = document.getElementById("confirmation-dialog");
  if (dialog) {
    dialog.style.display = "none";
  }
}

// Function to confirm submission
function confirmSubmission() {
  // Add selected subjects to the form
  const hasSelectedSubjects = addSelectedSubjectsToForm();

  // If no subjects are selected, prevent submission
  if (!hasSelectedSubjects) {
    return false;
  }

  // Show confirmation dialog
  showConfirmationDialog(
    "Are you sure you want to submit these marks? This action cannot be undone.",
    submitMarksForm
  );

  // Prevent normal form submission
  return false;
}

// Function to submit marks form programmatically
function submitMarksForm() {
  const form = document.getElementById("marks-form");
  if (form) {
    form.submit();
  }
}

// Enhanced Navigation System Functions
function navigateToFeature(feature) {
  // Update active navigation item
  updateActiveNavigation(feature);

  // Scroll to the feature section if it exists
  const featureSection = document.getElementById(feature + "-section");
  if (featureSection) {
    featureSection.scrollIntoView({ behavior: "smooth" });
  }

  // Store the active feature in session storage
  sessionStorage.setItem("activeFeature", feature);
}

function updateActiveNavigation(activeFeature) {
  // Remove active class from all navigation items
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.remove("active");
  });

  // Add active class to current feature
  const activeItem = document.querySelector(
    `.nav-item[data-feature="${activeFeature}"]`
  );
  if (activeItem) {
    activeItem.classList.add("active");
  }
}

// Enhanced Floating Action Button Functions
function toggleEnhancedFab() {
  const fabMenu = document.getElementById("fab-menu");
  const fabIcon = document.getElementById("fab-icon");
  const fabMain = document.getElementById("fab-main-btn");

  if (fabMenu.classList.contains("active")) {
    fabIcon.className = "fas fa-plus";
  } else {
    fabIcon.className = "fas fa-times";
  }

  fabMenu.classList.toggle("active");
  fabMain.classList.toggle("active");
}

function initializeEnhancedNavigation() {
  // Close FAB menu when clicking outside
  document.addEventListener("click", function (event) {
    const fabMenu = document.getElementById("fab-menu");
    const fabButton = document.getElementById("fab-main-btn");

    if (
      fabMenu &&
      fabMenu.classList.contains("active") &&
      !event.target.closest("#fab-menu") &&
      !event.target.closest("#fab-main-btn")
    ) {
      toggleEnhancedFab();
    }
  });

  // Initialize active navigation based on current tab
  const activeTab = sessionStorage.getItem("activeTab") || "recent-reports";
  updateActiveNavigation(activeTab);
}

// Smooth scrolling function
function scrollToSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }
}

// Function to select all subjects
function selectAllSubjects() {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = true;
    toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
  });
}

// Function to deselect all subjects
function deselectAllSubjects() {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = false;
    toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
  });
}

// Function to update all marks for a subject when the total marks change
function updateAllMarksForSubject(subject, subjectIndex) {
  // Get the new total marks value
  const totalMarksInput = document.getElementById(
    `total_marks_${subjectIndex}`
  );
  let totalMarks = parseFloat(totalMarksInput.value) || 100;

  // Enforce reasonable limits on total marks (maximum 100)
  if (totalMarks < 1) {
    totalMarks = 1;
    totalMarksInput.value = totalMarks;
  } else if (totalMarks > 100) {
    // Check if this is a composite subject with multiple components
    const isComposite =
      document.querySelectorAll(`.component-row[data-subject="${subject}"]`)
        .length > 0;

    // For non-composite subjects, cap at 100
    if (!isComposite) {
      totalMarks = 100;
      totalMarksInput.value = totalMarks;
    }
  }

  // Update the subject info display
  const subjectInfoSpan = document.getElementById(
    `subject_info_${subjectIndex}`
  );
  if (subjectInfoSpan) {
    subjectInfoSpan.textContent = `(Max: ${totalMarks})`;
  }

  // Get all mark inputs for this subject
  const markInputs = document.querySelectorAll(
    `.student-mark[data-subject="${subject}"]`
  );

  // Update each mark's max attribute and data-max-mark attribute
  markInputs.forEach((input) => {
    input.max = totalMarks;
    input.dataset.maxMark = totalMarks;

    // If current value exceeds new max, cap it
    const currentValue = parseFloat(input.value) || 0;
    if (currentValue > totalMarks) {
      input.value = totalMarks;
    }

    updatePercentage(input);
  });
}

// Function to toggle subject visibility in the table (CORRECTED VERSION)
function toggleSubjectVisibility(checkbox, subjectId) {
  // Get the correct table cells and headers for this subject
  const subjectHeaders = document.querySelectorAll(
    `th[data-subject-id="${subjectId}"]`
  );
  const subjectCells = document.querySelectorAll(
    `td[data-subject-id="${subjectId}"]`
  );
  const subjectItem = checkbox.closest(".subject-mark-item");

  if (checkbox.checked) {
    // Show the subject
    subjectHeaders.forEach((header) => {
      header.style.display = "";
    });

    subjectCells.forEach((cell) => {
      cell.style.display = "";
    });

    if (subjectItem) {
      subjectItem.classList.remove("disabled");
    }
  } else {
    // Hide the subject
    subjectHeaders.forEach((header) => {
      header.style.display = "none";
    });

    subjectCells.forEach((cell) => {
      cell.style.display = "none";
    });

    if (subjectItem) {
      subjectItem.classList.add("disabled");
    }
  }
}

// Function to select or deselect all subjects
function selectAllSubjects(select = true) {
  const checkboxes = document.querySelectorAll(".subject-checkbox");
  checkboxes.forEach((checkbox) => {
    checkbox.checked = select;
    if (checkbox.dataset.subjectId) {
      toggleSubjectVisibility(checkbox, checkbox.dataset.subjectId);
    }
  });
}

// Function to deselect all subjects
function deselectAllSubjects() {
  selectAllSubjects(false);
}
