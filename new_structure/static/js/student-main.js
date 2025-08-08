// Student Dashboard - Main JavaScript

// Toggle sidebar on mobile
document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.querySelector(".sidebar");

  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", function () {
      sidebar.classList.toggle("active");
      document.body.classList.toggle("sidebar-active");
    });
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener("click", function (event) {
    if (
      sidebar &&
      sidebar.classList.contains("active") &&
      !sidebar.contains(event.target) &&
      event.target !== menuToggle
    ) {
      sidebar.classList.remove("active");
      document.body.classList.remove("sidebar-active");
    }
  });

  // Initialize tooltips
  initTooltips();

  // Initialize notifications
  initNotifications();

  // Initialize dropdowns
  initDropdowns();

  // Initialize tabs
  initTabs();
});

// Initialize tooltips
function initTooltips() {
  const tooltipElements = document.querySelectorAll("[data-tooltip]");

  tooltipElements.forEach(function (element) {
    element.addEventListener("mouseenter", function () {
      const tooltipText = this.getAttribute("data-tooltip");

      const tooltip = document.createElement("div");
      tooltip.className = "tooltip show";
      tooltip.innerHTML = `<div class="tooltip-inner">${tooltipText}</div>`;

      document.body.appendChild(tooltip);

      const rect = this.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();

      tooltip.style.top = rect.top - tooltipRect.height - 10 + "px";
      tooltip.style.left =
        rect.left + rect.width / 2 - tooltipRect.width / 2 + "px";
    });

    element.addEventListener("mouseleave", function () {
      const tooltip = document.querySelector(".tooltip");
      if (tooltip) {
        tooltip.remove();
      }
    });
  });
}

// Initialize notifications
function initNotifications() {
  const notificationBtn = document.querySelector(".notification-btn");
  const notificationDropdown = document.querySelector(".notification-dropdown");

  if (notificationBtn && notificationDropdown) {
    notificationBtn.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();

      notificationDropdown.classList.toggle("show");

      // Mark notifications as read when dropdown is opened
      const unreadNotifications = notificationDropdown.querySelectorAll(
        ".notification-item.unread"
      );
      unreadNotifications.forEach(function (notification) {
        notification.classList.remove("unread");
      });

      // Update notification count
      const notificationBadge = notificationBtn.querySelector(".badge");
      if (notificationBadge) {
        notificationBadge.textContent = "0";
        notificationBadge.style.display = "none";
      }
    });

    // Close notification dropdown when clicking outside
    document.addEventListener("click", function (event) {
      if (
        notificationDropdown.classList.contains("show") &&
        !notificationDropdown.contains(event.target) &&
        event.target !== notificationBtn
      ) {
        notificationDropdown.classList.remove("show");
      }
    });
  }
}

// Initialize dropdowns
function initDropdowns() {
  const dropdownToggleElements = document.querySelectorAll(".dropdown-toggle");

  dropdownToggleElements.forEach(function (element) {
    element.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();

      const dropdownMenu = this.nextElementSibling;

      // Close all other dropdowns
      document.querySelectorAll(".dropdown-menu.show").forEach(function (menu) {
        if (menu !== dropdownMenu) {
          menu.classList.remove("show");
        }
      });

      dropdownMenu.classList.toggle("show");
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener("click", function () {
    document.querySelectorAll(".dropdown-menu.show").forEach(function (menu) {
      menu.classList.remove("show");
    });
  });
}

// Initialize tabs
function initTabs() {
  const tabLinks = document.querySelectorAll(".nav-tabs .nav-link");

  tabLinks.forEach(function (tabLink) {
    tabLink.addEventListener("click", function (event) {
      event.preventDefault();

      // Remove active class from all tab links and content
      document.querySelectorAll(".nav-tabs .nav-link").forEach(function (link) {
        link.classList.remove("active");
      });

      document.querySelectorAll(".tab-pane").forEach(function (pane) {
        pane.classList.remove("active");
      });

      // Add active class to clicked tab link and corresponding content
      this.classList.add("active");

      const targetId = this.getAttribute("href");
      const targetPane = document.querySelector(targetId);

      if (targetPane) {
        targetPane.classList.add("active");
      }
    });
  });
}

// Show toast notification
function showToast(message, type = "info", duration = 3000) {
  // Remove existing toasts
  const existingToasts = document.querySelectorAll(".toast");
  existingToasts.forEach(function (toast) {
    toast.remove();
  });

  // Create toast element
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
        <div class="toast-body">${message}</div>
    `;

  // Add toast to document
  document.body.appendChild(toast);

  // Automatically remove toast after duration
  setTimeout(function () {
    toast.style.opacity = "0";

    setTimeout(function () {
      toast.remove();
    }, 300);
  }, duration);
}
