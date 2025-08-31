// Auto-wrap plain tables in a responsive container to enable horizontal scroll on small screens
// Safe, non-destructive: Only wraps tables not already inside a known responsive container
(function () {
  function isWrapped(table) {
    const parent = table.parentElement;
    if (!parent) return false;
    if (
      parent.classList.contains("table-responsive") ||
      parent.classList.contains("table-responsive-wrapper") ||
      parent.classList.contains("mobile-table-container") ||
      parent.classList.contains("mobile-table-swipe")
    ) {
      return true;
    }
    return false;
  }

  function wrapTable(table) {
    const wrapper = document.createElement("div");
    wrapper.className = "table-responsive";
    // Inline styles to avoid relying on external CSS definitions
    wrapper.style.overflowX = "auto";
    wrapper.style.webkitOverflowScrolling = "touch";
    wrapper.style.width = "100%";

    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  }

  function enhance() {
    try {
      const tables = document.querySelectorAll("table");
      tables.forEach((t) => {
        if (!isWrapped(t)) {
          wrapTable(t);
        }
      });
    } catch (e) {
      // no-op
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enhance);
  } else {
    enhance();
  }
})();
