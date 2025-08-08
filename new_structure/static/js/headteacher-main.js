// Headteacher Dashboard Main JavaScript

// Global variables for pagination and filtering
let currentPage = 1;
const itemsPerPage = 10;
let allPerformanceData = [];
let filteredData = [];

// Global variables for chart filtering
let performanceChart = null;
let comparisonChart = null;
let activeFilters = {
  performanceLevel: null,
  grade: null,
};

// Initialize dashboard on DOM content loaded
document.addEventListener("DOMContentLoaded", function () {
  try {
    console.log("Headteacher dashboard loading...");

    // Store all performance data for filtering and pagination
    const rows = document.querySelectorAll(".performance-row");
    allPerformanceData = Array.from(rows).map((row) => ({
      element: row,
      grade: row.dataset.grade,
      term: row.dataset.term,
      assessment: row.dataset.assessment,
    }));
    filteredData = [...allPerformanceData];

    // Initialize pagination
    if (allPerformanceData.length > 0) {
      displayPage();
      updatePaginationInfo();
    } else {
      // Hide pagination if no data
      const paginationContainer = document.getElementById(
        "pagination-container"
      );
      if (paginationContainer) {
        paginationContainer.style.display = "none";
      }
    }

    // Initialize charts and animations
    initializeCharts();
    animateCounters();

    // Initialize advanced analytics
    generatePerformanceHeatmap();
    generatePerformanceAlerts();
    initializeDrillDown();

    // Initialize Universal Access link styling
    initializeUniversalAccessLink();

    console.log("Headteacher dashboard loaded successfully");
  } catch (error) {
    console.error("Error initializing dashboard:", error);
  }
});

// Toggle filter section visibility
function toggleFilters() {
  const filterSection = document.getElementById("performance-filters");
  if (filterSection) {
    if (filterSection.style.display === "none") {
      filterSection.style.display = "block";
    } else {
      filterSection.style.display = "none";
    }
  }
}

// Filter performance data based on selected criteria
function filterPerformanceData() {
  try {
    const gradeFilter = document.getElementById("grade-filter")?.value || "";
    const termFilter = document.getElementById("term-filter")?.value || "";
    const assessmentFilter =
      document.getElementById("assessment-filter")?.value || "";

    filteredData = allPerformanceData.filter((item) => {
      return (
        (!gradeFilter || item.grade === gradeFilter) &&
        (!termFilter || item.term === termFilter) &&
        (!assessmentFilter || item.assessment === assessmentFilter)
      );
    });

    currentPage = 1;
    displayPage();
    updatePaginationInfo();
  } catch (error) {
    console.error("Error filtering performance data:", error);
  }
}

// Display current page of filtered data
function displayPage() {
  try {
    // Hide all rows first
    allPerformanceData.forEach((item) => {
      if (item.element) {
        item.element.style.display = "none";
      }
    });

    // Show rows for current page
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = filteredData.slice(startIndex, endIndex);

    pageData.forEach((item) => {
      if (item.element) {
        item.element.style.display = "";
      }
    });

    // Update pagination controls
    updatePaginationControls();
  } catch (error) {
    console.error("Error displaying page:", error);
  }
}

// Update pagination information
function updatePaginationInfo() {
  try {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const startItem =
      filteredData.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const endItem = Math.min(currentPage * itemsPerPage, filteredData.length);

    const paginationContainer = document.getElementById("pagination-container");
    const paginationInfo = document.getElementById("pagination-info");
    const pageInfo = document.getElementById("page-info");

    if (!paginationContainer) return;

    if (filteredData.length > 0) {
      paginationContainer.style.display = "flex";
      if (filteredData.length > itemsPerPage) {
        if (paginationInfo) {
          paginationInfo.textContent = `Showing ${startItem}-${endItem} of ${filteredData.length} results`;
        }
        if (pageInfo) {
          pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        }
        // Generate page numbers
        generatePageNumbers(totalPages);
      } else {
        if (paginationInfo) {
          paginationInfo.textContent = `Showing all ${filteredData.length} results`;
        }
        if (pageInfo) {
          pageInfo.textContent = `Page 1 of 1`;
        }
        // Clear page numbers for single page
        const pageNumbers = document.getElementById("page-numbers");
        if (pageNumbers) {
          pageNumbers.innerHTML = "";
        }
      }
    } else {
      paginationContainer.style.display = "none";
    }
  } catch (error) {
    console.error("Error updating pagination info:", error);
  }
}

// Generate page number buttons
function generatePageNumbers(totalPages) {
  try {
    const pageNumbers = document.getElementById("page-numbers");
    if (!pageNumbers) return;

    pageNumbers.innerHTML = "";

    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      const pageBtn = document.createElement("button");
      pageBtn.textContent = i;
      pageBtn.className =
        i === currentPage ? "btn page-btn active" : "btn-outline page-btn";
      pageBtn.onclick = () => goToPage(i);
      pageNumbers.appendChild(pageBtn);
    }
  } catch (error) {
    console.error("Error generating page numbers:", error);
  }
}

// Go to specific page
function goToPage(page) {
  try {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
      displayPage();
      updatePaginationInfo();
    }
  } catch (error) {
    console.error("Error going to page:", error);
  }
}

// Update pagination control buttons
function updatePaginationControls() {
  try {
    const totalPages = Math.ceil(filteredData.length / itemsPerPage);
    const prevButton = document.querySelector(
      'button[onclick="previousPage()"]'
    );
    const nextButton = document.querySelector('button[onclick="nextPage()"]');

    if (prevButton) {
      prevButton.disabled = currentPage === 1;
    }
    if (nextButton) {
      nextButton.disabled = currentPage === totalPages || totalPages === 0;
    }
  } catch (error) {
    console.error("Error updating pagination controls:", error);
  }
}

// Navigate to previous page
function previousPage() {
  if (currentPage > 1) {
    currentPage--;
    displayPage();
    updatePaginationInfo();
  }
}

// Navigate to next page
function nextPage() {
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    displayPage();
    updatePaginationInfo();
  }
}

// Animate counter numbers
function animateCounters() {
  try {
    const counters = document.querySelectorAll(".stat-number");

    counters.forEach((counter) => {
      const target = parseFloat(counter.textContent.replace(/[^\d.]/g, ""));
      if (isNaN(target)) return;

      const increment = target / 50;
      let current = 0;
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }

        // Format the number appropriately
        if (counter.id === "school-average") {
          counter.textContent = current.toFixed(1) + "%";
        } else if (counter.id === "best-class") {
          // Don't animate text values
          return;
        } else {
          counter.textContent = Math.floor(current);
        }
      }, 40);
    });
  } catch (error) {
    console.error("Error animating counters:", error);
  }
}

// Enhanced Dashboard Functions
function toggleFilterPanel() {
  const panel = document.getElementById("filterPanel");
  if (panel) {
    if (panel.style.display === "none" || panel.style.display === "") {
      panel.style.display = "block";
      panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
      panel.style.display = "none";
    }
  }
}

function refreshDashboard() {
  showNotification("Refreshing dashboard data...", "info");
  setTimeout(() => {
    location.reload();
  }, 1000);
}

function generateComprehensiveReport() {
  showNotification("Generating comprehensive school report...", "info");
  setTimeout(() => {
    showNotification(
      "Report generation started. You will be notified when ready.",
      "success"
    );
  }, 1500);
}

function openAnalyticsDashboard() {
  try {
    // Navigate to analytics dashboard
    const analyticsUrl = document.querySelector('[href*="analytics"]')?.href;
    if (analyticsUrl) {
      window.location.href = analyticsUrl;
    } else {
      showNotification("Analytics dashboard not available", "error");
    }
  } catch (error) {
    console.error("Error opening analytics dashboard:", error);
    showNotification("Error opening analytics dashboard", "error");
  }
}

// Initialize Universal Access link
function initializeUniversalAccessLink() {
  setTimeout(function () {
    const universalLink = document.getElementById("universal-access-link");
    if (universalLink) {
      console.log("Universal Access link found:", universalLink);
      universalLink.style.display = "flex";
      universalLink.style.visibility = "visible";
      universalLink.style.opacity = "1";
    } else {
      console.log("Universal Access link not found, creating...");
      const navbar = document.querySelector(".navbar-nav");
      if (navbar) {
        const li = document.createElement("li");
        const link = document.createElement("a");
        link.href = "/universal/dashboard";
        link.className = "nav-link";
        link.id = "universal-access-link";
        link.innerHTML =
          '<i class="fas fa-users-cog"></i> <span>UNIVERSAL ACCESS</span>';

        li.appendChild(link);
        navbar.insertBefore(li, navbar.children[1]);
        console.log("Universal Access link created and inserted");
      }
    }
  }, 100);
}

// Add smooth scrolling for better UX
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
      });
    }
  });
});

// Export this module for use by other scripts
window.HeadteacherDashboard = {
  toggleFilters,
  filterPerformanceData,
  displayPage,
  updatePaginationInfo,
  goToPage,
  previousPage,
  nextPage,
  refreshDashboard,
  generateComprehensiveReport,
  openAnalyticsDashboard,
  toggleFilterPanel,
};
