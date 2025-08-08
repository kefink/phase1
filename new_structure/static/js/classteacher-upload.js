// Enhanced Class Teacher Upload Class Marks - Enhanced JavaScript

// Tab switching functionality
document.addEventListener("DOMContentLoaded", function () {
  console.log("Enhanced Class Teacher Upload JS loaded");

  // Initialize all components with premium features
  initializeTabs();
  initializeUnifiedFormFields();
  initializeFileUpload();
  initializeFormValidation();

  // Add welcome message
  setTimeout(() => {
    showToast(
      "Upload interface loaded successfully. Complete configuration to proceed.",
      "info"
    );
  }, 500);
});

// Add form validation on page load
function initializeFormValidation() {
  const uploadBtn = document.getElementById("upload-btn");
  const bulkUploadBtn = document.getElementById("bulk-upload-btn");

  // Add click handlers with validation
  if (uploadBtn) {
    uploadBtn.addEventListener("click", function (e) {
      if (!validateFormConfiguration()) {
        e.preventDefault();
        showToast(
          "Please complete all required configuration fields",
          "warning"
        );
      }
    });
  }

  if (bulkUploadBtn) {
    bulkUploadBtn.addEventListener("click", function (e) {
      if (!validateFormConfiguration()) {
        e.preventDefault();
        showToast(
          "Please complete all required configuration fields",
          "warning"
        );
        return;
      }

      const fileInput = document.getElementById("marks_file");
      if (!fileInput || !fileInput.files.length) {
        e.preventDefault();
        showToast("Please select a file to upload", "warning");

        // Highlight the drag-drop area
        const dragArea = document.querySelector(".drag-drop-area");
        if (dragArea) {
          dragArea.style.borderColor = "#dc322f";
          dragArea.style.background = "rgba(220, 50, 47, 0.1)";
          setTimeout(() => {
            dragArea.style.borderColor = "rgba(42, 161, 152, 0.3)";
            dragArea.style.background =
              "linear-gradient(135deg, rgba(42, 161, 152, 0.05) 0%, rgba(181, 137, 0, 0.05) 100%)";
          }, 2000);
        }
        return;
      }

      // Show upload progress (visual feedback)
      this.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                Uploading...
            `;
      this.disabled = true;
    });
  }
}

// Validate form configuration
function validateFormConfiguration() {
  const requiredFields = [
    "education_level",
    "term",
    "assessment_type",
    "grade",
    "stream",
  ];
  let isValid = true;

  requiredFields.forEach((fieldName) => {
    const field = document.getElementById(fieldName);
    if (!field || !field.value.trim()) {
      isValid = false;

      // Visual feedback for missing fields
      if (field) {
        field.style.borderColor = "#dc322f";
        field.style.boxShadow = "0 0 0 2px rgba(220, 50, 47, 0.1)";

        setTimeout(() => {
          field.style.borderColor = "";
          field.style.boxShadow = "";
        }, 3000);
      }
    }
  });

  return isValid;
}

// Sync form fields between tabs with enhanced error handling
function syncFormFields() {
  const sharedFields = [
    "education_level",
    "term",
    "assessment_type",
    "grade",
    "stream",
  ];
  const manualForm = document.getElementById("upload-form");
  const bulkForm = document.getElementById("bulk-upload-form");

  if (!manualForm || !bulkForm) {
    console.warn("One or both forms not found");
    return;
  }

  sharedFields.forEach((fieldName) => {
    const sourceField = document.getElementById(fieldName);
    if (!sourceField) return;

    const value = sourceField.value;

    // Update or create hidden fields in both forms
    [manualForm, bulkForm].forEach((form) => {
      let hiddenField = form.querySelector(`input[name="${fieldName}"]`);
      if (!hiddenField) {
        hiddenField = document.createElement("input");
        hiddenField.type = "hidden";
        hiddenField.name = fieldName;
        form.appendChild(hiddenField);
      }
      hiddenField.value = value;
    });
  });

  // Sync total_marks fields
  const totalMarks = document.getElementById("total_marks");
  const bulkTotalMarks = document.getElementById("bulk_total_marks");

  if (totalMarks && bulkTotalMarks) {
    bulkTotalMarks.value = totalMarks.value;
  }

  console.log("Form fields synchronized successfully");
}

// Global function to clear file selection (used by onclick handlers)
function clearFileSelection() {
  const fileInput = document.getElementById("marks_file");
  const fileList = document.getElementById("bulk-file-list");

  if (fileInput) {
    fileInput.value = "";
  }

  if (fileList) {
    fileList.style.opacity = "0";
    fileList.style.transform = "translateY(-10px)";

    setTimeout(() => {
      fileList.style.display = "none";
      fileList.innerHTML = "";
      fileList.style.opacity = "1";
      fileList.style.transform = "translateY(0)";
    }, 300);
  }

  showToast("File removed successfully", "info");
}

// Global function to handle external function calls
function updateSubjects() {
  console.log("Updating subjects...");
  // This will be handled by the main application
  if (window.updateSubjects && typeof window.updateSubjects === "function") {
    window.updateSubjects();
  }
}

function fetchStreams() {
  console.log("Fetching streams...");
  // This will be handled by the main application
  if (window.fetchStreams && typeof window.fetchStreams === "function") {
    window.fetchStreams();
  }
}

// Initialize tab switching with enhanced premium effects
function initializeTabs() {
  const tabButtons = document.querySelectorAll(".modern-tabs .tab-button");
  const tabPanes = document.querySelectorAll(".modern-tabs .tab-pane");

  tabButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const targetTab = this.getAttribute("data-tab");
      console.log("Switching to tab:", targetTab);

      // Remove active class from all buttons and panes
      tabButtons.forEach((btn) => {
        btn.classList.remove("active");
        // Reset button styling
        btn.style.background = "transparent";
        btn.style.color = "var(--text-secondary)";
        btn.style.boxShadow = "none";
        btn.style.transform = "scale(1)";
      });

      tabPanes.forEach((pane) => {
        pane.classList.remove("active");
        pane.style.opacity = "0";
        pane.style.transform = "translateY(20px)";
        pane.style.display = "none";
      });

      // Add active class to clicked button with premium styling
      this.classList.add("active");

      // Apply premium styling based on tab type
      if (targetTab === "manual-entry") {
        this.style.background =
          "linear-gradient(135deg, #268bd2 0%, #2aa198 100%)";
        this.style.color = "var(--text-white)";
        this.style.boxShadow =
          "0 4px 15px rgba(40, 139, 210, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1)";
        this.style.transform = "scale(1.02)";
      } else if (targetTab === "bulk-upload") {
        this.style.background =
          "linear-gradient(135deg, #2aa198 0%, #b58900 100%)";
        this.style.color = "var(--text-white)";
        this.style.boxShadow =
          "0 4px 15px rgba(42, 161, 152, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1)";
        this.style.transform = "scale(1.02)";
      }

      // Show target pane with smooth animation
      const targetPane = document.getElementById(targetTab);
      if (targetPane) {
        targetPane.style.display = "block";

        // Trigger animation after display change
        setTimeout(() => {
          targetPane.classList.add("active");
          targetPane.style.opacity = "1";
          targetPane.style.transform = "translateY(0)";
        }, 10);

        // Sync form fields when switching tabs
        syncFormFields();

        // Show success notification
        const tabName =
          targetTab === "manual-entry" ? "Manual Entry" : "Bulk Upload";
        showToast(`Switched to ${tabName} mode`, "success");
      }
    });

    // Add hover effects for enhanced UX
    button.addEventListener("mouseenter", function () {
      if (!this.classList.contains("active")) {
        this.style.transform = "scale(1.05)";
        this.style.background = "rgba(255, 255, 255, 0.1)";
        this.style.color = "var(--text-primary)";
      }
    });

    button.addEventListener("mouseleave", function () {
      if (!this.classList.contains("active")) {
        this.style.transform = "scale(1)";
        this.style.background = "transparent";
        this.style.color = "var(--text-secondary)";
      }
    });
  });
}

// Initialize unified form fields synchronization with enhanced validation
function initializeUnifiedFormFields() {
  const unifiedFields = document.querySelectorAll(
    ".unified-form-fields select"
  );

  unifiedFields.forEach((field) => {
    field.addEventListener("change", function () {
      const fieldName = this.getAttribute("name") || this.getAttribute("id");
      const fieldValue = this.value;

      // Enhanced visual feedback for selection
      this.style.borderColor = "#2aa198";
      this.style.boxShadow = "0 0 0 2px rgba(42, 161, 152, 0.1)";

      // Reset styling after 1 second
      setTimeout(() => {
        this.style.borderColor = "";
        this.style.boxShadow = "";
      }, 1000);

      // Sync with manual entry form
      const manualField = document.querySelector(
        `#upload-form [name="${fieldName}"]`
      );
      if (!manualField) {
        // Create hidden field in manual form
        const hiddenField = document.createElement("input");
        hiddenField.type = "hidden";
        hiddenField.name = fieldName;
        hiddenField.value = fieldValue;
        document.getElementById("upload-form").appendChild(hiddenField);
      } else if (manualField !== this) {
        manualField.value = fieldValue;
      }

      // Sync with bulk upload form
      const bulkField = document.querySelector(
        `#bulk-upload-form [name="${fieldName}"]`
      );
      if (!bulkField) {
        // Create hidden field in bulk form
        const hiddenField = document.createElement("input");
        hiddenField.type = "hidden";
        hiddenField.name = fieldName;
        hiddenField.value = fieldValue;
        document.getElementById("bulk-upload-form").appendChild(hiddenField);
      } else if (bulkField !== this) {
        bulkField.value = fieldValue;
      }

      // Update configuration status
      updateConfigurationStatus();

      // Trigger change events on synced fields
      if (manualField && manualField !== this)
        manualField.dispatchEvent(new Event("change"));
      if (bulkField && bulkField !== this)
        bulkField.dispatchEvent(new Event("change"));
    });

    // Add focus effects
    field.addEventListener("focus", function () {
      this.style.borderColor = "#268bd2";
      this.style.boxShadow = "0 0 0 3px rgba(40, 139, 210, 0.1)";
    });

    field.addEventListener("blur", function () {
      this.style.borderColor = "";
      this.style.boxShadow = "";
    });
  });
}

// Update configuration status with real-time feedback
function updateConfigurationStatus() {
  const requiredFields = [
    "education_level",
    "term",
    "assessment_type",
    "grade",
    "stream",
  ];
  let completedFields = 0;
  let isComplete = true;

  requiredFields.forEach((fieldName) => {
    const field = document.getElementById(fieldName);
    if (field && field.value.trim()) {
      completedFields++;
    } else {
      isComplete = false;
    }
  });

  const progress = Math.round((completedFields / requiredFields.length) * 100);

  // Find or create status indicator
  let statusIndicator = document.querySelector(".configuration-status");
  if (!statusIndicator) {
    statusIndicator = document.createElement("div");
    statusIndicator.className = "configuration-status";
    const configSection = document.querySelector(".unified-form-fields");
    if (configSection) {
      configSection.appendChild(statusIndicator);
    }
  }

  // Update status display
  if (isComplete) {
    statusIndicator.innerHTML = `
            <div style="display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); background: rgba(42, 161, 152, 0.1); border-radius: var(--radius-md); border-left: 4px solid #2aa198; margin-top: var(--space-4);">
                <i class="fas fa-check-circle" style="color: #2aa198;"></i>
                <span style="font-size: 0.9rem; color: var(--text-primary); font-weight: 600;">
                    Configuration Complete - Ready to proceed
                </span>
                <div style="margin-left: auto; background: #2aa198; color: white; padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 500;">
                    ${progress}%
                </div>
            </div>
        `;
  } else {
    statusIndicator.innerHTML = `
            <div style="display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3); background: rgba(181, 137, 0, 0.1); border-radius: var(--radius-md); border-left: 4px solid #b58900; margin-top: var(--space-4);">
                <i class="fas fa-exclamation-circle" style="color: #b58900;"></i>
                <span style="font-size: 0.9rem; color: var(--text-primary); font-weight: 500;">
                    Complete configuration to proceed (${completedFields}/${requiredFields.length} fields)
                </span>
                <div style="margin-left: auto; background: #b58900; color: white; padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.75rem; font-weight: 500;">
                    ${progress}%
                </div>
            </div>
        `;
  }

  // Enable/disable form buttons based on completion
  const uploadBtn = document.getElementById("upload-btn");
  const bulkUploadBtn = document.getElementById("bulk-upload-btn");

  if (uploadBtn) {
    uploadBtn.disabled = !isComplete;
    uploadBtn.style.opacity = isComplete ? "1" : "0.6";
    uploadBtn.style.cursor = isComplete ? "pointer" : "not-allowed";
  }

  if (bulkUploadBtn) {
    bulkUploadBtn.disabled = !isComplete;
    bulkUploadBtn.style.opacity = isComplete ? "1" : "0.6";
    bulkUploadBtn.style.cursor = isComplete ? "pointer" : "not-allowed";
  }
}

// Initialize file upload functionality with enhanced premium features
function initializeFileUpload() {
  const fileInput = document.getElementById("marks_file");
  const dragDropArea = document.querySelector(".drag-drop-area");
  const fileList = document.getElementById("bulk-file-list");

  if (!fileInput || !dragDropArea) return;

  // Enhanced file selection handler
  fileInput.addEventListener("change", function () {
    handleFileSelection(this.files);
  });

  // Enhanced drag and drop with premium visual effects
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dragDropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // Premium drag over effects
  ["dragenter", "dragover"].forEach((eventName) => {
    dragDropArea.addEventListener(eventName, function (e) {
      this.style.borderColor = "#2aa198";
      this.style.background =
        "linear-gradient(135deg, rgba(42, 161, 152, 0.15) 0%, rgba(181, 137, 0, 0.15) 100%)";
      this.style.transform = "scale(1.02)";
      this.style.boxShadow = "0 8px 30px rgba(42, 161, 152, 0.2)";

      // Add pulsing effect
      const icon = this.querySelector(".fas");
      if (icon) {
        icon.style.animation = "pulse 1s infinite";
      }
    });
  });

  // Reset drag effects
  ["dragleave", "drop"].forEach((eventName) => {
    dragDropArea.addEventListener(eventName, function (e) {
      // Only reset if leaving the drag area entirely
      if (
        eventName === "dragleave" &&
        e.relatedTarget &&
        this.contains(e.relatedTarget)
      ) {
        return;
      }

      this.style.borderColor = "rgba(42, 161, 152, 0.3)";
      this.style.background =
        "linear-gradient(135deg, rgba(42, 161, 152, 0.05) 0%, rgba(181, 137, 0, 0.05) 100%)";
      this.style.transform = "scale(1)";
      this.style.boxShadow = "none";

      // Remove pulsing effect
      const icon = this.querySelector(".fas");
      if (icon) {
        icon.style.animation = "";
      }
    });
  });

  // Handle dropped files
  dragDropArea.addEventListener("drop", function (e) {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      // Update the file input
      const dataTransfer = new DataTransfer();
      for (let file of files) {
        dataTransfer.items.add(file);
      }
      fileInput.files = dataTransfer.files;

      handleFileSelection(files);
    }
  });

  // Add click to upload functionality
  dragDropArea.addEventListener("click", function () {
    fileInput.click();
  });
}

// Enhanced file selection handler with validation and premium display
function handleFileSelection(files) {
  const fileList = document.getElementById("bulk-file-list");
  if (!fileList || files.length === 0) return;

  const file = files[0]; // We only handle single file upload

  // Enhanced file validation
  const allowedTypes = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
    "application/vnd.ms-excel", // .xls
    "text/csv", // .csv
    "application/csv",
  ];

  const allowedExtensions = ["xlsx", "xls", "csv"];
  const fileExtension = file.name.split(".").pop().toLowerCase();

  // Validate file type
  if (
    !allowedTypes.includes(file.type) &&
    !allowedExtensions.includes(fileExtension)
  ) {
    showToast("Please select a valid Excel (.xlsx, .xls) or CSV file", "error");
    clearFileSelection();
    return;
  }

  // Validate file size (10MB limit)
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    showToast("File size must be less than 10MB", "error");
    clearFileSelection();
    return;
  }

  // Display selected file with premium styling
  displaySelectedFile(file);

  // Show success notification
  showToast(`File "${file.name}" selected successfully`, "success");
}

// Display selected file with enhanced premium styling
function displaySelectedFile(file) {
  const fileList = document.getElementById("bulk-file-list");
  if (!fileList) return;

  const fileSize = formatFileSize(file.size);
  const fileType = file.name.split(".").pop().toUpperCase();
  const fileName = file.name;

  // Get file icon based on type
  let fileIcon = "fa-file";
  let iconColor = "#268bd2";

  if (fileType === "XLSX" || fileType === "XLS") {
    fileIcon = "fa-file-excel";
    iconColor = "#2aa198";
  } else if (fileType === "CSV") {
    fileIcon = "fa-file-csv";
    iconColor = "#b58900";
  }

  fileList.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: var(--space-4); background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: var(--radius-lg); border: 1px solid rgba(42, 161, 152, 0.2); box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); animation: slideInUp 0.3s ease-out;">
            <div style="display: flex; align-items: center; gap: var(--space-3);">
                <div style="background: linear-gradient(135deg, ${iconColor} 0%, rgba(42, 161, 152, 0.8) 100%); padding: var(--space-3); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; min-width: 48px; height: 48px;">
                    <i class="fas ${fileIcon}" style="color: var(--text-white); font-size: 1.2rem;"></i>
                </div>
                <div style="flex: 1;">
                    <p style="margin: 0; font-weight: 600; color: var(--text-primary); font-size: 0.95rem; line-height: 1.4;">${fileName}</p>
                    <div style="display: flex; align-items: center; gap: var(--space-2); margin-top: var(--space-1);">
                        <span style="color: var(--text-secondary); font-size: 0.8rem;">${fileSize}</span>
                        <span style="color: var(--text-muted);">•</span>
                        <span style="background: rgba(42, 161, 152, 0.1); color: #2aa198; padding: 2px 6px; border-radius: var(--radius-full); font-size: 0.7rem; font-weight: 500;">${fileType}</span>
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <div style="display: flex; align-items: center; gap: var(--space-1);">
                    <i class="fas fa-check-circle" style="color: #2aa198; font-size: 0.9rem;"></i>
                    <span style="color: #2aa198; font-size: 0.8rem; font-weight: 500;">READY</span>
                </div>
                <button type="button" onclick="clearFileSelection()" style="background: rgba(220, 50, 47, 0.1); border: 1px solid rgba(220, 50, 47, 0.2); color: #dc322f; padding: var(--space-2); border-radius: var(--radius-md); cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center;" onmouseover="this.style.background='rgba(220, 50, 47, 0.2)'" onmouseout="this.style.background='rgba(220, 50, 47, 0.1)'">
                    <i class="fas fa-times" style="font-size: 0.9rem;"></i>
                </button>
            </div>
        </div>
    `;

  fileList.style.display = "block";
}

// Clear file selection with animation
function clearFileSelection() {
  const fileInput = document.getElementById("marks_file");
  const fileList = document.getElementById("bulk-file-list");

  if (fileInput) {
    fileInput.value = "";
  }

  if (fileList) {
    // Add fade out animation
    fileList.style.opacity = "0";
    fileList.style.transform = "translateY(-10px)";

    setTimeout(() => {
      fileList.style.display = "none";
      fileList.innerHTML = "";
      fileList.style.opacity = "1";
      fileList.style.transform = "translateY(0)";
    }, 300);
  }
}

// Format file size helper function
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Enhanced download template functionality
function downloadTemplate() {
  // Get current form values with validation
  const educationLevel = document.getElementById("education_level")?.value;
  const grade = document.getElementById("grade")?.value;
  const stream = document.getElementById("stream")?.value;
  const term = document.getElementById("term")?.value;
  const assessmentType = document.getElementById("assessment_type")?.value;

  // Validate required fields
  if (!educationLevel || !grade || !stream) {
    showToast(
      "Please complete Education Level, Grade, and Stream selection first",
      "warning"
    );

    // Highlight missing fields
    [educationLevel, grade, stream].forEach((value, index) => {
      const fieldNames = ["education_level", "grade", "stream"];
      const field = document.getElementById(fieldNames[index]);
      if (!value && field) {
        field.style.borderColor = "#dc322f";
        field.style.boxShadow = "0 0 0 2px rgba(220, 50, 47, 0.1)";
        setTimeout(() => {
          field.style.borderColor = "";
          field.style.boxShadow = "";
        }, 3000);
      }
    });
    return;
  }

  // Show loading state
  const downloadBtn = document.querySelector(
    'button[onclick="downloadTemplate()"]'
  );
  if (downloadBtn) {
    const originalContent = downloadBtn.innerHTML;
    downloadBtn.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            Generating Template...
        `;
    downloadBtn.disabled = true;
    downloadBtn.style.opacity = "0.7";

    // Reset button after 3 seconds
    setTimeout(() => {
      downloadBtn.innerHTML = originalContent;
      downloadBtn.disabled = false;
      downloadBtn.style.opacity = "1";
    }, 3000);
  }

  // Create comprehensive download URL with all parameters
  const params = new URLSearchParams({
    education_level: educationLevel,
    grade: grade,
    stream: stream,
    term: term || "",
    assessment_type: assessmentType || "",
    action: "download_template",
    format: "excel",
  });

  const downloadUrl = `/classteacher/dashboard?${params.toString()}`;

  // Create and trigger download
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = `marks_template_${grade}_${stream}_${new Date().getTime()}.xlsx`;
  link.style.display = "none";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Show success notification
  showToast(
    `Template for ${grade} Stream ${stream} downloaded successfully`,
    "success"
  );

  // Track download analytics (optional)
  console.log("Template downloaded:", {
    education_level: educationLevel,
    grade: grade,
    stream: stream,
    term: term,
    assessment_type: assessmentType,
    timestamp: new Date().toISOString(),
  });
}

// Select class for upload functionality
function selectClassForUpload(gradeName, streamName, educationLevel) {
  // Populate the unified form fields
  const educationLevelField = document.getElementById("education_level");
  const gradeField = document.getElementById("grade");
  const streamField = document.getElementById("stream");

  if (educationLevelField) {
    educationLevelField.value = educationLevel;
    educationLevelField.dispatchEvent(new Event("change"));
  }

  if (gradeField) {
    gradeField.value = gradeName;
    gradeField.dispatchEvent(new Event("change"));

    // Wait for streams to load, then select stream
    setTimeout(() => {
      if (streamField) {
        streamField.value = streamName;
        streamField.dispatchEvent(new Event("change"));
      }
    }, 500);
  }

  // Show success message
  showToast(`Selected ${gradeName} Stream ${streamName} for upload`, "success");

  // Scroll to upload form
  const uploadSection = document.querySelector(".modern-tabs");
  if (uploadSection) {
    uploadSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

// Enhanced toast notification system
function showToast(message, type = "info") {
  // Remove any existing toasts
  const existingToasts = document.querySelectorAll(".toast-notification");
  existingToasts.forEach((toast) => toast.remove());

  // Create premium toast element
  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;

  // Set premium styling based on type
  let backgroundColor, iconClass, borderColor;
  switch (type) {
    case "success":
      backgroundColor = "linear-gradient(135deg, #2aa198 0%, #268bd2 100%)";
      iconClass = "fa-check-circle";
      borderColor = "#2aa198";
      break;
    case "error":
      backgroundColor = "linear-gradient(135deg, #dc322f 0%, #b58900 100%)";
      iconClass = "fa-exclamation-circle";
      borderColor = "#dc322f";
      break;
    case "warning":
      backgroundColor = "linear-gradient(135deg, #b58900 0%, #dc322f 100%)";
      iconClass = "fa-exclamation-triangle";
      borderColor = "#b58900";
      break;
    case "info":
    default:
      backgroundColor = "linear-gradient(135deg, #268bd2 0%, #2aa198 100%)";
      iconClass = "fa-info-circle";
      borderColor = "#268bd2";
  }

  toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 320px;
        max-width: 450px;
        padding: 16px 20px;
        background: ${backgroundColor};
        border: 1px solid ${borderColor};
        border-radius: 12px;
        color: white;
        font-weight: 500;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transform: translateX(100%);
        opacity: 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 0.95rem;
        line-height: 1.4;
    `;

  toast.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <div style="flex-shrink: 0; margin-top: 2px;">
                <i class="fas ${iconClass}" style="font-size: 1.1rem; opacity: 0.9;"></i>
            </div>
            <div style="flex: 1; word-wrap: break-word;">
                ${message}
            </div>
            <button type="button" onclick="this.parentElement.parentElement.remove()" 
                    style="flex-shrink: 0; background: none; border: none; color: rgba(255, 255, 255, 0.8); font-size: 1.2rem; cursor: pointer; padding: 0; margin: 0; line-height: 1; transition: color 0.2s ease;"
                    onmouseover="this.style.color='white'"
                    onmouseout="this.style.color='rgba(255, 255, 255, 0.8)'">
                ×
            </button>
        </div>
    `;

  document.body.appendChild(toast);

  // Animate in with premium effect
  setTimeout(() => {
    toast.style.transform = "translateX(0)";
    toast.style.opacity = "1";
  }, 10);

  // Auto remove with fade out animation
  setTimeout(() => {
    toast.style.transform = "translateX(100%)";
    toast.style.opacity = "0";

    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 400);
  }, 5000);
}

// Add enhanced CSS animations and styles
const enhancedStyle = document.createElement("style");
enhancedStyle.textContent = `
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.1);
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Enhanced drag and drop styling */
    .drag-drop-area {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .drag-drop-area:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(42, 161, 152, 0.15);
    }
    
    /* Tab animation effects */
    .tab-pane {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .tab-button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .tab-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }
    
    .tab-button:hover::before {
        left: 100%;
    }
    
    /* Form field enhancements */
    .form-select, .form-control {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .form-select:focus, .form-control:focus {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(40, 139, 210, 0.15);
    }
    
    /* Button hover effects */
    .modern-btn {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .modern-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }
    
    .modern-btn:active {
        transform: translateY(0);
    }
    
    /* Loading state animations */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .fa-spinner {
        animation: spin 1s linear infinite;
    }
    
    /* Configuration status animations */
    .configuration-status {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* File list animations */
    .file-list {
        animation: slideInUp 0.4s ease-out;
    }
    
    /* Premium glassmorphism effects */
    .premium-glass {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Responsive enhancements */
    @media (max-width: 768px) {
        .toast-notification {
            right: 10px;
            left: 10px;
            min-width: auto;
            max-width: none;
        }
        
        .modern-grid.grid-cols-2 {
            grid-template-columns: 1fr;
        }
        
        .tab-button {
            font-size: 0.9rem;
            padding: var(--space-3);
        }
    }
`;
document.head.appendChild(enhancedStyle);
