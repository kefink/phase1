/**
 * Admin Dashboard Main JavaScript
 * Handles core functionality for the admin dashboard
 */

document.addEventListener("DOMContentLoaded", function () {
  initSidebar();
  initDropdowns();
  initTooltips();
  initNotifications();
  handleActiveLinks();
  enableMobileResponsiveness();
});

/**
 * Initialize sidebar functionality
 */
function initSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const sidebarClose = document.getElementById("sidebar-close");
  const menuToggle = document.getElementById("menu-toggle");

  // Create sidebar overlay for mobile
  const overlay = document.createElement("div");
  overlay.classList.add("sidebar-overlay");
  document.querySelector(".app-container").appendChild(overlay);

  // Toggle sidebar on menu button click (mobile)
  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      sidebar.classList.toggle("show");
    });
  }

  // Close sidebar when close button is clicked
  if (sidebarClose) {
    sidebarClose.addEventListener("click", function () {
      sidebar.classList.remove("show");
    });
  }

  // Close sidebar when clicking outside (on overlay)
  overlay.addEventListener("click", function () {
    sidebar.classList.remove("show");
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    if (window.innerWidth > 992 && sidebar.classList.contains("show")) {
      sidebar.classList.remove("show");
    }
  });
}

/**
 * Initialize dropdown functionality
 */
function initDropdowns() {
  const dropdownToggles = document.querySelectorAll('[data-toggle="dropdown"]');

  // For explicitly marked dropdown toggles
  dropdownToggles.forEach((toggle) => {
    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const parent = this.closest(".dropdown");
      const menu = parent.querySelector(".dropdown-menu");

      // Close all other dropdowns
      document.querySelectorAll(".dropdown-menu.show").forEach((openMenu) => {
        if (openMenu !== menu) {
          openMenu.classList.remove("show");
        }
      });

      // Toggle this dropdown
      menu.classList.toggle("show");
    });
  });

  // For notification button (special case)
  const notificationBtn = document.querySelector(".notification-btn");
  if (notificationBtn) {
    notificationBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      const menu = document.querySelector(".notification-dropdown");

      // Close all other dropdowns
      document.querySelectorAll(".dropdown-menu.show").forEach((openMenu) => {
        if (openMenu !== menu) {
          openMenu.classList.remove("show");
        }
      });

      // Toggle notification dropdown
      menu.classList.toggle("show");
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener("click", function (e) {
    const clickedElement = e.target;

    if (!clickedElement.closest(".dropdown")) {
      document.querySelectorAll(".dropdown-menu.show").forEach((menu) => {
        menu.classList.remove("show");
      });
    }
  });
}

/**
 * Initialize tooltip functionality
 */
function initTooltips() {
  const tooltipElements = document.querySelectorAll("[data-tooltip]");

  tooltipElements.forEach((element) => {
    const tooltipText = element.getAttribute("data-tooltip");

    // Create tooltip element
    const tooltip = document.createElement("div");
    tooltip.classList.add("tooltip");
    tooltip.textContent = tooltipText;

    // Add tooltip to element
    element.appendChild(tooltip);

    // Show tooltip on hover
    element.addEventListener("mouseenter", function () {
      tooltip.classList.add("show");
    });

    // Hide tooltip when mouse leaves
    element.addEventListener("mouseleave", function () {
      tooltip.classList.remove("show");
    });
  });
}

/**
 * Initialize notification functionality
 */
function initNotifications() {
  // Mark notifications as read when clicked
  const notificationItems = document.querySelectorAll(".notification-item");

  notificationItems.forEach((item) => {
    item.addEventListener("click", function () {
      this.classList.remove("unread");

      // Update unread count
      updateNotificationCount();
    });
  });
}

/**
 * Update the notification count badge
 */
function updateNotificationCount() {
  const unreadCount = document.querySelectorAll(
    ".notification-item.unread"
  ).length;
  const badge = document.querySelector(".notification-btn .badge");

  if (badge) {
    if (unreadCount > 0) {
      badge.textContent = unreadCount;
      badge.style.display = "flex";
    } else {
      badge.style.display = "none";
    }
  }
}

/**
 * Handle active link highlighting based on current URL
 */
function handleActiveLinks() {
  const currentLocation = window.location.pathname;
  const navLinks = document.querySelectorAll(".nav-link");

  navLinks.forEach((link) => {
    const href = link.getAttribute("href");

    if (
      href === currentLocation ||
      (currentLocation.includes(href) && href !== "/")
    ) {
      link.classList.add("active");
    }
  });
}

/**
 * Enable responsive functionality for mobile devices
 */
function enableMobileResponsiveness() {
  // Adjust table display for mobile
  const tables = document.querySelectorAll("table");

  tables.forEach((table) => {
    if (!table.parentElement.classList.contains("table-responsive")) {
      const wrapper = document.createElement("div");
      wrapper.classList.add("table-responsive");
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  });
}

/**
 * Initialize tab functionality
 * @param {string} tabContainerId - The ID of the tab container
 */
function initTabs(tabContainerId) {
  const tabContainer = document.getElementById(tabContainerId);
  if (!tabContainer) return;

  const tabs = tabContainer.querySelectorAll("[data-tab-target]");
  const tabContents = document.querySelectorAll("[data-tab-content]");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = document.querySelector(tab.dataset.tabTarget);

      // Hide all tab contents
      tabContents.forEach((content) => {
        content.classList.remove("active");
      });

      // Remove active class from all tabs
      tabs.forEach((t) => {
        t.classList.remove("active");
      });

      // Activate clicked tab and its content
      tab.classList.add("active");
      target.classList.add("active");
    });
  });
}

/**
 * Format number with commas
 * @param {number} number - The number to format
 * @returns {string} Formatted number
 */
function formatNumber(number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Format date to locale string
 * @param {string|Date} date - The date to format
 * @returns {string} Formatted date
 */
function formatDate(date) {
  const dateObj = new Date(date);
  return dateObj.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Show toast notification
 * @param {string} message - The notification message
 * @param {string} type - The notification type (success, error, warning, info)
 * @param {number} duration - The duration to show the notification in ms
 */
function showToast(message, type = "info", duration = 3000) {
  // Create toast container if it doesn't exist
  let toastContainer = document.querySelector(".toast-container");

  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.classList.add("toast-container");
    document.body.appendChild(toastContainer);
  }

  // Create toast element
  const toast = document.createElement("div");
  toast.classList.add("toast", `toast-${type}`);

  // Add toast content
  toast.innerHTML = `
        <div class="toast-content">
            <i class="toast-icon fas fa-${getToastIcon(type)}"></i>
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close">&times;</button>
    `;

  // Add toast to container
  toastContainer.appendChild(toast);

  // Show toast (add animation)
  setTimeout(() => {
    toast.classList.add("show");
  }, 10);

  // Set up close button
  const closeBtn = toast.querySelector(".toast-close");
  closeBtn.addEventListener("click", () => {
    closeToast(toast);
  });

  // Auto-close after duration
  if (duration) {
    setTimeout(() => {
      closeToast(toast);
    }, duration);
  }
}

/**
 * Close toast notification
 * @param {HTMLElement} toast - The toast element to close
 */
function closeToast(toast) {
  toast.classList.remove("show");

  // Remove from DOM after animation
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 300);
}

/**
 * Get icon for toast notification type
 * @param {string} type - The notification type
 * @returns {string} Icon name
 */
function getToastIcon(type) {
  switch (type) {
    case "success":
      return "check-circle";
    case "error":
      return "exclamation-circle";
    case "warning":
      return "exclamation-triangle";
    case "info":
    default:
      return "info-circle";
  }
}

/**
 * Confirm action with dialog
 * @param {string} message - The confirmation message
 * @param {Function} onConfirm - Callback function when confirmed
 * @param {string} confirmText - Text for confirm button
 * @param {string} cancelText - Text for cancel button
 */
function confirmAction(
  message,
  onConfirm,
  confirmText = "Confirm",
  cancelText = "Cancel"
) {
  // Create overlay
  const overlay = document.createElement("div");
  overlay.classList.add("modal-overlay");

  // Create confirm dialog
  const dialog = document.createElement("div");
  dialog.classList.add("confirm-dialog");

  // Add dialog content
  dialog.innerHTML = `
        <div class="confirm-dialog-content">
            <p class="confirm-dialog-message">${message}</p>
            <div class="confirm-dialog-actions">
                <button class="btn btn-secondary cancel-btn">${cancelText}</button>
                <button class="btn btn-primary confirm-btn">${confirmText}</button>
            </div>
        </div>
    `;

  // Add to document
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);

  // Show dialog (add animation)
  setTimeout(() => {
    overlay.classList.add("show");
    dialog.classList.add("show");
  }, 10);

  // Set up button events
  const cancelBtn = dialog.querySelector(".cancel-btn");
  const confirmBtn = dialog.querySelector(".confirm-btn");

  cancelBtn.addEventListener("click", () => {
    closeDialog();
  });

  confirmBtn.addEventListener("click", () => {
    closeDialog();
    if (typeof onConfirm === "function") {
      onConfirm();
    }
  });

  // Close dialog function
  function closeDialog() {
    overlay.classList.remove("show");
    dialog.classList.remove("show");

    // Remove from DOM after animation
    setTimeout(() => {
      if (overlay.parentNode) {
        document.body.removeChild(overlay);
      }
    }, 300);
  }
}

/**
 * Toggle dark/light mode
 */
function toggleDarkMode() {
  const body = document.querySelector("body");
  const isDarkMode = body.classList.contains("dark-mode");

  if (isDarkMode) {
    body.classList.remove("dark-mode");
    localStorage.setItem("darkMode", "false");
  } else {
    body.classList.add("dark-mode");
    localStorage.setItem("darkMode", "true");
  }
}

/**
 * Load stored dark mode preference
 */
function loadDarkModePreference() {
  const savedMode = localStorage.getItem("darkMode");
  const body = document.querySelector("body");

  if (savedMode === "true") {
    body.classList.add("dark-mode");
  } else {
    body.classList.remove("dark-mode");
  }
}

// Call this when DOM loads
document.addEventListener("DOMContentLoaded", function () {
  // Load dark mode preference
  loadDarkModePreference();

  // Set up dark mode toggle if it exists
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", toggleDarkMode);
  }
});
