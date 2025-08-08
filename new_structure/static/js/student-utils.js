// Student Dashboard - Utilities JavaScript

// Format date to a readable format
function formatDate(dateString) {
  const options = { year: "numeric", month: "long", day: "numeric" };
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", options);
}

// Format time to a readable format
function formatTime(timeString) {
  const options = { hour: "2-digit", minute: "2-digit" };
  const time = new Date(`2000-01-01T${timeString}`);
  return time.toLocaleTimeString("en-US", options);
}

// Format datetime to a readable format
function formatDateTime(dateTimeString) {
  const options = {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };
  const dateTime = new Date(dateTimeString);
  return dateTime.toLocaleString("en-US", options);
}

// Calculate days remaining until a deadline
function daysUntil(dateString) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const deadline = new Date(dateString);
  deadline.setHours(0, 0, 0, 0);

  const timeDiff = deadline.getTime() - today.getTime();
  const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));

  return daysDiff;
}

// Format days until deadline with appropriate text
function formatDaysUntil(dateString) {
  const days = daysUntil(dateString);

  if (days < 0) {
    return "Overdue";
  } else if (days === 0) {
    return "Due today";
  } else if (days === 1) {
    return "Due tomorrow";
  } else {
    return `Due in ${days} days`;
  }
}

// Get appropriate status color based on days until deadline
function getDeadlineStatusColor(dateString) {
  const days = daysUntil(dateString);

  if (days < 0) {
    return "danger"; // Overdue
  } else if (days <= 1) {
    return "warning"; // Due today or tomorrow
  } else if (days <= 3) {
    return "info"; // Due soon
  } else {
    return "success"; // Due later
  }
}

// Format file size
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Truncate text to a specific length with ellipsis
function truncateText(text, maxLength) {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

// Get initials from a name
function getInitials(name) {
  if (!name) return "";

  const parts = name.split(" ");

  if (parts.length === 1) {
    return parts[0].charAt(0).toUpperCase();
  }

  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

// Generate random color based on string
function stringToColor(str) {
  if (!str) return "#000000";

  let hash = 0;

  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }

  let color = "#";

  for (let i = 0; i < 3; i++) {
    const value = (hash >> (i * 8)) & 0xff;
    color += ("00" + value.toString(16)).substr(-2);
  }

  return color;
}

// Check if an element is in viewport
function isInViewport(element) {
  const rect = element.getBoundingClientRect();

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

// Debounce function to limit function calls
function debounce(func, wait, immediate) {
  let timeout;

  return function () {
    const context = this;
    const args = arguments;

    const later = function () {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };

    const callNow = immediate && !timeout;

    clearTimeout(timeout);
    timeout = setTimeout(later, wait);

    if (callNow) func.apply(context, args);
  };
}

// Create CSV file from array of objects
function exportToCSV(data, filename) {
  if (!data || !data.length) return;

  // Get headers from first object
  const headers = Object.keys(data[0]);

  // Create CSV content
  let csvContent = headers.join(",") + "\n";

  data.forEach(function (item) {
    const row = headers
      .map(function (header) {
        let cell = item[header] !== undefined ? item[header] : "";

        // Escape quotes and wrap in quotes if needed
        if (
          typeof cell === "string" &&
          (cell.includes(",") || cell.includes('"') || cell.includes("\n"))
        ) {
          cell = '"' + cell.replace(/"/g, '""') + '"';
        }

        return cell;
      })
      .join(",");

    csvContent += row + "\n";
  });

  // Create download link
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename || "export.csv");
  link.style.display = "none";

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Form validation
function validateForm(formElement) {
  if (!formElement) return false;

  let isValid = true;

  // Reset validation state
  formElement.querySelectorAll(".is-invalid").forEach((element) => {
    element.classList.remove("is-invalid");
  });

  // Validate required fields
  formElement.querySelectorAll("[required]").forEach((field) => {
    if (field.type === "checkbox" && !field.checked) {
      field.classList.add("is-invalid");
      isValid = false;
    } else if (field.value.trim() === "") {
      field.classList.add("is-invalid");
      isValid = false;
    }
  });

  // Validate email fields
  formElement.querySelectorAll('input[type="email"]').forEach((field) => {
    if (field.value.trim() !== "" && !isValidEmail(field.value)) {
      field.classList.add("is-invalid");
      isValid = false;
    }
  });

  // Validate number fields
  formElement.querySelectorAll('input[type="number"]').forEach((field) => {
    if (field.value.trim() !== "") {
      const min = field.getAttribute("min");
      const max = field.getAttribute("max");
      const value = parseFloat(field.value);

      if (min !== null && value < parseFloat(min)) {
        field.classList.add("is-invalid");
        isValid = false;
      }

      if (max !== null && value > parseFloat(max)) {
        field.classList.add("is-invalid");
        isValid = false;
      }
    }
  });

  return isValid;
}

// Validate email format
function isValidEmail(email) {
  const re =
    /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(email.toLowerCase());
}

// Format phone number
function formatPhoneNumber(phoneNumber) {
  // Remove all non-digit characters
  const cleaned = ("" + phoneNumber).replace(/\D/g, "");

  // Check if the input is valid
  const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);

  if (match) {
    return "(" + match[1] + ") " + match[2] + "-" + match[3];
  }

  return phoneNumber;
}

// Format currency
function formatCurrency(amount, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
  }).format(amount);
}

// Format percentage
function formatPercentage(value) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
}

// Calculate grade letter from percentage
function calculateGradeLetter(percentage) {
  if (percentage >= 90) return "A";
  if (percentage >= 80) return "B";
  if (percentage >= 70) return "C";
  if (percentage >= 60) return "D";
  return "F";
}

// Calculate GPA from grade points
function calculateGPA(gradePoints, creditHours) {
  if (
    !gradePoints.length ||
    !creditHours.length ||
    gradePoints.length !== creditHours.length
  ) {
    return 0;
  }

  let totalPoints = 0;
  let totalCredits = 0;

  for (let i = 0; i < gradePoints.length; i++) {
    totalPoints += gradePoints[i] * creditHours[i];
    totalCredits += creditHours[i];
  }

  return totalCredits > 0 ? (totalPoints / totalCredits).toFixed(2) : 0;
}

// Convert grade letter to grade points
function letterToPoints(letter) {
  const pointsMap = {
    "A+": 4.0,
    A: 4.0,
    "A-": 3.7,
    "B+": 3.3,
    B: 3.0,
    "B-": 2.7,
    "C+": 2.3,
    C: 2.0,
    "C-": 1.7,
    "D+": 1.3,
    D: 1.0,
    "D-": 0.7,
    F: 0.0,
  };

  return pointsMap[letter] || 0;
}

// Set/get cookie
function setCookie(name, value, days) {
  let expires = "";

  if (days) {
    const date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + date.toUTCString();
  }

  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
  const nameEQ = name + "=";
  const ca = document.cookie.split(";");

  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === " ") c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }

  return null;
}

function eraseCookie(name) {
  document.cookie = name + "=; Max-Age=-99999999; path=/";
}

// Get CSRF token from meta tag
function getCsrfToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  return metaTag ? metaTag.getAttribute("content") : "";
}

// Add CSRF token to fetch/axios requests
function addCsrfToken(headers = {}) {
  const csrfToken = getCsrfToken();

  if (csrfToken) {
    return {
      ...headers,
      "X-CSRFToken": csrfToken,
    };
  }

  return headers;
}

// Copy text to clipboard
function copyToClipboard(text) {
  // Create temporary textarea
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed"; // Prevent scrolling to bottom
  document.body.appendChild(textarea);
  textarea.select();

  try {
    // Execute copy command
    const successful = document.execCommand("copy");
    const msg = successful ? "successful" : "unsuccessful";
    console.log("Copying text was " + msg);
    return successful;
  } catch (err) {
    console.error("Unable to copy", err);
    return false;
  } finally {
    // Remove temporary element
    document.body.removeChild(textarea);
  }
}

// Load image and return promise
function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
    img.src = url;
  });
}

// Convert form data to JSON object
function formToJSON(formElement) {
  const formData = new FormData(formElement);
  const json = {};

  formData.forEach((value, key) => {
    // Handle checkbox groups
    if (key.endsWith("[]")) {
      const k = key.slice(0, -2);
      if (!json[k]) json[k] = [];
      json[k].push(value);
    } else {
      json[key] = value;
    }
  });

  return json;
}

// Parse query string to object
function parseQueryString(queryString) {
  const params = {};
  const queries = queryString.substring(1).split("&");

  for (let i = 0; i < queries.length; i++) {
    const pair = queries[i].split("=");
    params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || "");
  }

  return params;
}

// Add event listener with error handling
function safeAddEventListener(element, eventType, handler) {
  if (!element) return;

  element.addEventListener(eventType, function (event) {
    try {
      handler(event);
    } catch (error) {
      console.error(`Error in ${eventType} event handler:`, error);
    }
  });
}

// Create a throttled function
function throttle(func, limit) {
  let inThrottle;

  return function () {
    const args = arguments;
    const context = this;

    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// Format text with markdown-like syntax
function simpleMarkdown(text) {
  if (!text) return "";

  // Bold: **text**
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Italic: *text*
  text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Links: [text](url)
  text = text.replace(
    /\[(.*?)\]\((.*?)\)/g,
    '<a href="$2" target="_blank">$1</a>'
  );

  // Newlines to <br>
  text = text.replace(/\n/g, "<br>");

  return text;
}

// Generate a unique ID
function generateUniqueId(prefix = "id") {
  return prefix + "-" + Math.random().toString(36).substr(2, 9);
}

// Add event listener and return removal function
function addEventListener(element, event, handler) {
  if (!element) return () => {};

  element.addEventListener(event, handler);

  return () => {
    element.removeEventListener(event, handler);
  };
}

// Initialize student utilities
document.addEventListener("DOMContentLoaded", function () {
  // Initialize form validation
  const forms = document.querySelectorAll("form");

  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      if (!validateForm(this)) {
        event.preventDefault();
        event.stopPropagation();

        // Show validation error toast
        showToast("Please check the form for errors.", "danger");

        // Scroll to first invalid field
        const firstInvalid = this.querySelector(".is-invalid");
        if (firstInvalid) {
          firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
          firstInvalid.focus();
        }
      }
    });
  });

  // Format dates
  document.querySelectorAll('[data-format="date"]').forEach((element) => {
    const dateString = element.textContent.trim();
    if (dateString) {
      element.textContent = formatDate(dateString);
    }
  });

  // Format times
  document.querySelectorAll('[data-format="time"]').forEach((element) => {
    const timeString = element.textContent.trim();
    if (timeString) {
      element.textContent = formatTime(timeString);
    }
  });

  // Format datetimes
  document.querySelectorAll('[data-format="datetime"]').forEach((element) => {
    const dateTimeString = element.textContent.trim();
    if (dateTimeString) {
      element.textContent = formatDateTime(dateTimeString);
    }
  });

  // Initialize copy buttons
  document.querySelectorAll(".copy-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const textToCopy =
        this.getAttribute("data-copy-text") ||
        this.previousElementSibling.textContent;

      if (copyToClipboard(textToCopy)) {
        // Show success message
        const originalText = this.innerHTML;
        this.innerHTML = '<i class="fas fa-check"></i> Copied!';

        setTimeout(() => {
          this.innerHTML = originalText;
        }, 2000);
      }
    });
  });
});
