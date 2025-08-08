// Headteacher Dashboard Forms Handling JavaScript

// Form Submission Handlers
function initializeForms() {
  // Stream promotion form
  const streamPromotionForm = document.getElementById("streamPromotionForm");
  if (streamPromotionForm) {
    streamPromotionForm.addEventListener("submit", handleStreamPromotion);
  }

  // Message form
  const messageForm = document.getElementById("messageForm");
  if (messageForm) {
    messageForm.addEventListener("submit", handleSendMessage);
  }

  // Quick add forms
  const quickAddForms = document.querySelectorAll(".quick-add-form");
  quickAddForms.forEach((form) => {
    form.addEventListener("submit", handleQuickAdd);
  });

  // Settings form
  const settingsForm = document.getElementById("settingsForm");
  if (settingsForm) {
    settingsForm.addEventListener("submit", handleSettingsUpdate);
  }
}

// Stream Promotion Functions
function handleStreamPromotion(event) {
  event.preventDefault();

  try {
    const formData = new FormData(event.target);
    const sourceStream = formData.get("sourceStream");
    const targetStream = formData.get("targetStream");
    const criteria = formData.get("criteria");
    const minScore = formData.get("minScore");

    if (!sourceStream || !targetStream || !criteria) {
      showNotification("Please fill in all required fields", "error");
      return;
    }

    if (sourceStream === targetStream) {
      showNotification("Source and target streams cannot be the same", "error");
      return;
    }

    showProcessingIndicator("Processing stream promotion...");

    // Simulate API call
    setTimeout(() => {
      hideProcessingIndicator();
      showNotification(
        `Successfully promoted eligible students from ${sourceStream} to ${targetStream}`,
        "success"
      );
      event.target.reset();
      closeModal("streamPromotionModal");
    }, 2000);
  } catch (error) {
    console.error("Error handling stream promotion:", error);
    hideProcessingIndicator();
    showNotification("Error processing stream promotion", "error");
  }
}

function populateStreamOptions() {
  try {
    const sourceSelect = document.getElementById("sourceStream");
    const targetSelect = document.getElementById("targetStream");

    if (!sourceSelect || !targetSelect) return;

    // Get stream data from global variable or data attribute
    let streamData = [];
    const streamDataElement = document.querySelector("[data-streams]");

    if (streamDataElement) {
      streamData = JSON.parse(streamDataElement.dataset.streams);
    } else if (typeof window.streamData !== "undefined") {
      streamData = window.streamData;
    }

    if (streamData.length > 0) {
      populateStreamSelect(sourceSelect, streamData);
      populateStreamSelect(targetSelect, streamData);
    } else {
      // Fallback options
      const defaultOptions = [
        "Grade 1 A",
        "Grade 1 B",
        "Grade 1 C",
        "Grade 2 A",
        "Grade 2 B",
        "Grade 2 C",
        "Grade 3 A",
        "Grade 3 B",
        "Grade 3 C",
        "Grade 4 A",
        "Grade 4 B",
        "Grade 4 C",
        "Grade 5 A",
        "Grade 5 B",
        "Grade 5 C",
        "Grade 6 A",
        "Grade 6 B",
        "Grade 6 C",
      ];

      defaultOptions.forEach((option) => {
        sourceSelect.add(new Option(option, option));
        targetSelect.add(new Option(option, option));
      });
    }
  } catch (error) {
    console.error("Error populating stream options:", error);
  }
}

function populateStreamSelect(selectElement, streamData) {
  selectElement.innerHTML = '<option value="">Select Stream</option>';

  streamData.forEach((stream) => {
    const option = new Option(
      `${stream.grade} ${stream.stream}`,
      `${stream.grade}_${stream.stream}`
    );
    selectElement.add(option);
  });
}

// Message Handling Functions
function handleSendMessage(event) {
  event.preventDefault();

  try {
    const formData = new FormData(event.target);
    const recipients = formData.get("recipients");
    const subject = formData.get("subject");
    const message = formData.get("message");
    const priority = formData.get("priority") || "normal";

    if (!recipients || !subject || !message) {
      showNotification("Please fill in all required fields", "error");
      return;
    }

    showProcessingIndicator("Sending message...");

    // Simulate API call
    setTimeout(() => {
      hideProcessingIndicator();
      showNotification(`Message sent successfully to ${recipients}`, "success");
      event.target.reset();
      closeModal("messageModal");
    }, 1500);
  } catch (error) {
    console.error("Error sending message:", error);
    hideProcessingIndicator();
    showNotification("Error sending message", "error");
  }
}

function updateRecipientCount() {
  try {
    const recipientSelect = document.getElementById("recipients");
    const countDisplay = document.getElementById("recipientCount");

    if (recipientSelect && countDisplay) {
      const selectedOptions = Array.from(recipientSelect.selectedOptions);
      const count = selectedOptions.length;
      countDisplay.textContent =
        count > 0 ? `${count} recipient${count !== 1 ? "s" : ""} selected` : "";
    }
  } catch (error) {
    console.error("Error updating recipient count:", error);
  }
}

// Quick Add Functions
function handleQuickAdd(event) {
  event.preventDefault();

  try {
    const form = event.target;
    const formType = form.dataset.type;
    const formData = new FormData(form);

    // Basic validation
    const requiredFields = form.querySelectorAll("[required]");
    let isValid = true;

    requiredFields.forEach((field) => {
      if (!field.value.trim()) {
        field.classList.add("error");
        isValid = false;
      } else {
        field.classList.remove("error");
      }
    });

    if (!isValid) {
      showNotification("Please fill in all required fields", "error");
      return;
    }

    showProcessingIndicator(`Adding new ${formType}...`);

    // Simulate API call
    setTimeout(() => {
      hideProcessingIndicator();
      showNotification(`New ${formType} added successfully`, "success");
      form.reset();

      // Close modal if exists
      const modal = form.closest(".modal");
      if (modal) {
        closeModal(modal.id);
      }

      // Refresh relevant sections
      if (formType === "student") {
        refreshStudentData();
      } else if (formType === "teacher") {
        refreshTeacherData();
      }
    }, 1500);
  } catch (error) {
    console.error("Error handling quick add:", error);
    hideProcessingIndicator();
    showNotification("Error adding new record", "error");
  }
}

// Settings Functions
function handleSettingsUpdate(event) {
  event.preventDefault();

  try {
    const formData = new FormData(event.target);
    const settings = {};

    // Collect all form data
    for (let [key, value] of formData.entries()) {
      settings[key] = value;
    }

    // Collect checkbox values
    const checkboxes = event.target.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach((checkbox) => {
      settings[checkbox.name] = checkbox.checked;
    });

    showProcessingIndicator("Updating settings...");

    // Simulate API call
    setTimeout(() => {
      hideProcessingIndicator();
      showNotification("Settings updated successfully", "success");
      closeModal("settingsModal");
    }, 1000);
  } catch (error) {
    console.error("Error updating settings:", error);
    hideProcessingIndicator();
    showNotification("Error updating settings", "error");
  }
}

// Utility Functions
function showProcessingIndicator(message = "Processing...") {
  try {
    let indicator = document.getElementById("processingIndicator");

    if (!indicator) {
      indicator = document.createElement("div");
      indicator.id = "processingIndicator";
      indicator.className = "processing-indicator";
      document.body.appendChild(indicator);
    }

    indicator.innerHTML = `
      <div class="processing-content">
        <div class="spinner"></div>
        <div class="processing-message">${message}</div>
      </div>
    `;

    indicator.style.display = "flex";
  } catch (error) {
    console.error("Error showing processing indicator:", error);
  }
}

function hideProcessingIndicator() {
  try {
    const indicator = document.getElementById("processingIndicator");
    if (indicator) {
      indicator.style.display = "none";
    }
  } catch (error) {
    console.error("Error hiding processing indicator:", error);
  }
}

function refreshStudentData() {
  try {
    // Trigger refresh of student statistics
    const studentCards = document.querySelectorAll(".student-stat-card");
    studentCards.forEach((card) => {
      card.style.opacity = "0.6";
    });

    setTimeout(() => {
      studentCards.forEach((card) => {
        card.style.opacity = "1";
      });
    }, 500);
  } catch (error) {
    console.error("Error refreshing student data:", error);
  }
}

function refreshTeacherData() {
  try {
    // Trigger refresh of teacher statistics
    const teacherCards = document.querySelectorAll(".teacher-stat-card");
    teacherCards.forEach((card) => {
      card.style.opacity = "0.6";
    });

    setTimeout(() => {
      teacherCards.forEach((card) => {
        card.style.opacity = "1";
      });
    }, 500);
  } catch (error) {
    console.error("Error refreshing teacher data:", error);
  }
}

// Form Validation Functions
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

function validatePhone(phone) {
  const re = /^[\+]?[\d\s\-\(\)]{10,}$/;
  return re.test(phone);
}

function validateRequired(value) {
  return value && value.trim().length > 0;
}

function addFieldValidation() {
  try {
    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach((field) => {
      field.addEventListener("blur", function () {
        if (this.value && !validateEmail(this.value)) {
          this.classList.add("error");
          showFieldError(this, "Please enter a valid email address");
        } else {
          this.classList.remove("error");
          hideFieldError(this);
        }
      });
    });

    const phoneFields = document.querySelectorAll('input[type="tel"]');
    phoneFields.forEach((field) => {
      field.addEventListener("blur", function () {
        if (this.value && !validatePhone(this.value)) {
          this.classList.add("error");
          showFieldError(this, "Please enter a valid phone number");
        } else {
          this.classList.remove("error");
          hideFieldError(this);
        }
      });
    });

    const requiredFields = document.querySelectorAll("[required]");
    requiredFields.forEach((field) => {
      field.addEventListener("blur", function () {
        if (!validateRequired(this.value)) {
          this.classList.add("error");
          showFieldError(this, "This field is required");
        } else {
          this.classList.remove("error");
          hideFieldError(this);
        }
      });
    });
  } catch (error) {
    console.error("Error adding field validation:", error);
  }
}

function showFieldError(field, message) {
  try {
    let errorElement = field.parentNode.querySelector(".field-error");
    if (!errorElement) {
      errorElement = document.createElement("div");
      errorElement.className = "field-error";
      field.parentNode.appendChild(errorElement);
    }
    errorElement.textContent = message;
    errorElement.style.display = "block";
  } catch (error) {
    console.error("Error showing field error:", error);
  }
}

function hideFieldError(field) {
  try {
    const errorElement = field.parentNode.querySelector(".field-error");
    if (errorElement) {
      errorElement.style.display = "none";
    }
  } catch (error) {
    console.error("Error hiding field error:", error);
  }
}

// Auto-save Functions
function enableAutoSave(formId, interval = 30000) {
  try {
    const form = document.getElementById(formId);
    if (!form) return;

    let autoSaveTimer;
    const formFields = form.querySelectorAll("input, select, textarea");

    const saveFormData = () => {
      const formData = new FormData(form);
      const data = {};
      for (let [key, value] of formData.entries()) {
        data[key] = value;
      }
      localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
    };

    const restoreFormData = () => {
      const savedData = localStorage.getItem(`autosave_${formId}`);
      if (savedData) {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach((key) => {
          const field = form.querySelector(`[name="${key}"]`);
          if (field) {
            field.value = data[key];
          }
        });
      }
    };

    // Restore data on page load
    restoreFormData();

    // Set up auto-save
    formFields.forEach((field) => {
      field.addEventListener("input", () => {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(saveFormData, interval);
      });
    });

    // Clear saved data on successful submission
    form.addEventListener("submit", () => {
      localStorage.removeItem(`autosave_${formId}`);
    });
  } catch (error) {
    console.error("Error enabling auto-save:", error);
  }
}

// Initialize all form functionality
document.addEventListener("DOMContentLoaded", function () {
  initializeForms();
  populateStreamOptions();
  addFieldValidation();

  // Enable auto-save for long forms
  enableAutoSave("messageForm", 15000);
  enableAutoSave("settingsForm", 30000);

  // Add recipient count update
  const recipientSelect = document.getElementById("recipients");
  if (recipientSelect) {
    recipientSelect.addEventListener("change", updateRecipientCount);
  }
});

// Make functions globally available
window.FormsFunctions = {
  handleStreamPromotion,
  handleSendMessage,
  handleQuickAdd,
  handleSettingsUpdate,
  populateStreamOptions,
  updateRecipientCount,
  showProcessingIndicator,
  hideProcessingIndicator,
  refreshStudentData,
  refreshTeacherData,
  validateEmail,
  validatePhone,
  validateRequired,
  enableAutoSave,
};
