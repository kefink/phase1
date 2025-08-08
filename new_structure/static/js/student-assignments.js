// Student Dashboard - Assignments JavaScript

// Function to filter assignments by status
function filterAssignments(status) {
  const assignmentCards = document.querySelectorAll(".assignment-card");

  assignmentCards.forEach(function (card) {
    const cardStatus = card.getAttribute("data-status");

    if (status === "all" || cardStatus === status) {
      card.style.display = "block";
    } else {
      card.style.display = "none";
    }
  });

  // Update active filter button
  const filterButtons = document.querySelectorAll(".assignment-filter-btn");
  filterButtons.forEach(function (btn) {
    if (btn.getAttribute("data-filter") === status) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Update empty state message
  updateEmptyState(status);
}

// Update empty state message
function updateEmptyState(status) {
  const visibleCards = document.querySelectorAll(
    '.assignment-card[style="display: block;"]'
  );
  const emptyState = document.querySelector(".assignments-empty-state");

  if (emptyState) {
    if (visibleCards.length === 0) {
      emptyState.style.display = "block";

      // Update empty state message based on filter
      const emptyStateMessage = emptyState.querySelector(
        ".empty-state-message"
      );
      if (emptyStateMessage) {
        switch (status) {
          case "pending":
            emptyStateMessage.textContent = "You have no pending assignments.";
            break;
          case "submitted":
            emptyStateMessage.textContent =
              "You have not submitted any assignments yet.";
            break;
          case "graded":
            emptyStateMessage.textContent =
              "You have no graded assignments yet.";
            break;
          case "late":
            emptyStateMessage.textContent =
              "You have no late assignments. Great job!";
            break;
          default:
            emptyStateMessage.textContent = "You have no assignments.";
        }
      }
    } else {
      emptyState.style.display = "none";
    }
  }
}

// Sort assignments by date or priority
function sortAssignments(sortBy) {
  const assignmentList = document.querySelector(".assignment-list");

  if (!assignmentList) {
    return;
  }

  const assignments = Array.from(
    assignmentList.querySelectorAll(".assignment-card")
  );

  assignments.sort(function (a, b) {
    if (sortBy === "date") {
      const dateA = new Date(a.getAttribute("data-due-date"));
      const dateB = new Date(b.getAttribute("data-due-date"));
      return dateA - dateB;
    } else if (sortBy === "priority") {
      const priorityA = parseInt(a.getAttribute("data-priority"));
      const priorityB = parseInt(b.getAttribute("data-priority"));
      return priorityB - priorityA;
    }

    return 0;
  });

  // Remove existing assignments
  assignments.forEach(function (assignment) {
    assignment.remove();
  });

  // Re-append sorted assignments
  assignments.forEach(function (assignment) {
    assignmentList.appendChild(assignment);
  });

  // Update active sort button
  const sortButtons = document.querySelectorAll(".assignment-sort-btn");
  sortButtons.forEach(function (btn) {
    if (btn.getAttribute("data-sort") === sortBy) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

// Open assignment details
function openAssignmentDetails(id) {
  // Show assignment details modal or navigate to assignment page
  window.location.href = `/student/assignment/${id}`;
}

// Submit assignment
function submitAssignment(formElement) {
  // Validate form before submission
  if (!validateAssignmentForm(formElement)) {
    return false;
  }

  // Get form data
  const formData = new FormData(formElement);

  // Show loading indicator
  const submitButton = formElement.querySelector('button[type="submit"]');
  const originalButtonText = submitButton.innerHTML;
  submitButton.disabled = true;
  submitButton.innerHTML =
    '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';

  // Submit form via AJAX
  fetch(formElement.action, {
    method: "POST",
    body: formData,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      // Reset form
      formElement.reset();

      // Reset file input
      const fileInput = formElement.querySelector('input[type="file"]');
      if (fileInput) {
        fileInput.value = "";
        const fileLabel = formElement.querySelector(".custom-file-label");
        if (fileLabel) {
          fileLabel.textContent = "Choose file";
        }
      }

      // Show success message
      showToast(
        data.message || "Assignment submitted successfully!",
        "success"
      );

      // Redirect if needed
      if (data.redirect) {
        setTimeout(() => {
          window.location.href = data.redirect;
        }, 1500);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showToast(
        "An error occurred while submitting the assignment. Please try again.",
        "danger"
      );
    })
    .finally(() => {
      // Restore submit button
      submitButton.disabled = false;
      submitButton.innerHTML = originalButtonText;
    });

  return false;
}

// Validate assignment submission form
function validateAssignmentForm(formElement) {
  let isValid = true;

  // Reset validation state
  formElement.querySelectorAll(".is-invalid").forEach((element) => {
    element.classList.remove("is-invalid");
  });

  // Validate required fields
  formElement.querySelectorAll("[required]").forEach((field) => {
    if (!field.value.trim()) {
      field.classList.add("is-invalid");
      isValid = false;

      // Show error message
      const feedbackElement = field.nextElementSibling;
      if (
        feedbackElement &&
        feedbackElement.classList.contains("invalid-feedback")
      ) {
        feedbackElement.textContent = "This field is required.";
      }
    }
  });

  // Validate file input if present
  const fileInput = formElement.querySelector('input[type="file"]');
  if (fileInput && fileInput.hasAttribute("required")) {
    if (!fileInput.files.length) {
      fileInput.classList.add("is-invalid");
      isValid = false;

      // Show error message
      const feedbackElement = fileInput.nextElementSibling;
      if (
        feedbackElement &&
        feedbackElement.classList.contains("invalid-feedback")
      ) {
        feedbackElement.textContent = "Please select a file to upload.";
      }
    } else {
      // Validate file type if restrictions exist
      const acceptAttr = fileInput.getAttribute("accept");
      if (acceptAttr) {
        const acceptedTypes = acceptAttr.split(",");
        const fileName = fileInput.files[0].name;
        const fileExtension = "." + fileName.split(".").pop().toLowerCase();

        let fileTypeValid = false;
        for (let i = 0; i < acceptedTypes.length; i++) {
          const type = acceptedTypes[i].trim().toLowerCase();
          if (type === fileExtension || type === ".*") {
            fileTypeValid = true;
            break;
          }
        }

        if (!fileTypeValid) {
          fileInput.classList.add("is-invalid");
          isValid = false;

          // Show error message
          const feedbackElement = fileInput.nextElementSibling;
          if (
            feedbackElement &&
            feedbackElement.classList.contains("invalid-feedback")
          ) {
            feedbackElement.textContent =
              "Invalid file type. Accepted types: " + acceptAttr;
          }
        }
      }

      // Validate file size if max size is specified
      const maxSize = parseInt(fileInput.getAttribute("data-max-size") || "0");
      if (maxSize > 0 && fileInput.files[0].size > maxSize) {
        fileInput.classList.add("is-invalid");
        isValid = false;

        // Show error message
        const feedbackElement = fileInput.nextElementSibling;
        if (
          feedbackElement &&
          feedbackElement.classList.contains("invalid-feedback")
        ) {
          feedbackElement.textContent =
            "File is too large. Maximum size: " + formatFileSize(maxSize);
        }
      }
    }
  }

  return isValid;
}

// Format file size
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Handle file selection for assignment submission
function handleFileSelect(fileInput) {
  const fileName = fileInput.files.length
    ? fileInput.files[0].name
    : "Choose file";

  const fileLabel = fileInput.nextElementSibling;
  if (fileLabel) {
    fileLabel.textContent = fileName;
  }

  // Validate file size
  const maxSize = parseInt(fileInput.getAttribute("data-max-size") || "0");
  if (
    maxSize > 0 &&
    fileInput.files.length &&
    fileInput.files[0].size > maxSize
  ) {
    fileInput.classList.add("is-invalid");

    // Show error message
    const feedbackElement = document.createElement("div");
    feedbackElement.className = "invalid-feedback";
    feedbackElement.textContent =
      "File is too large. Maximum size: " + formatFileSize(maxSize);

    const existingFeedback =
      fileInput.parentElement.querySelector(".invalid-feedback");
    if (existingFeedback) {
      existingFeedback.textContent = feedbackElement.textContent;
    } else {
      fileInput.parentElement.appendChild(feedbackElement);
    }
  } else {
    fileInput.classList.remove("is-invalid");

    // Remove error message
    const existingFeedback =
      fileInput.parentElement.querySelector(".invalid-feedback");
    if (existingFeedback) {
      existingFeedback.textContent = "";
    }
  }
}

// Initialize drag and drop file upload
function initDragAndDrop() {
  const dragDropAreas = document.querySelectorAll(".drag-drop-area");

  dragDropAreas.forEach(function (area) {
    const fileInput = document.getElementById(
      area.getAttribute("data-file-input")
    );

    if (!fileInput) {
      return;
    }

    // Prevent default drag behaviors
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      area.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    // Highlight drop area when item is dragged over it
    ["dragenter", "dragover"].forEach((eventName) => {
      area.addEventListener(eventName, highlight, false);
    });

    ["dragleave", "drop"].forEach((eventName) => {
      area.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
      area.classList.add("drag-over");
    }

    function unhighlight() {
      area.classList.remove("drag-over");
    }

    // Handle dropped files
    area.addEventListener("drop", handleDrop, false);

    function handleDrop(e) {
      const dt = e.dataTransfer;
      const files = dt.files;

      fileInput.files = files;

      // Trigger change event
      const event = new Event("change", { bubbles: true });
      fileInput.dispatchEvent(event);

      // Update file label
      handleFileSelect(fileInput);
    }
  });
}

// Initialize assignments page
document.addEventListener("DOMContentLoaded", function () {
  // Initialize drag and drop
  initDragAndDrop();

  // Setup file input change handlers
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(function (input) {
    input.addEventListener("change", function () {
      handleFileSelect(this);
    });
  });

  // Setup assignment filter buttons
  const filterButtons = document.querySelectorAll(".assignment-filter-btn");
  filterButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filterAssignments(this.getAttribute("data-filter"));
    });
  });

  // Setup assignment sort buttons
  const sortButtons = document.querySelectorAll(".assignment-sort-btn");
  sortButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      sortAssignments(this.getAttribute("data-sort"));
    });
  });

  // Setup assignment submission form
  const assignmentForm = document.getElementById("assignment-submission-form");
  if (assignmentForm) {
    assignmentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      submitAssignment(this);
    });
  }
});
