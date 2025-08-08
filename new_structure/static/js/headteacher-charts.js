// Headteacher Dashboard Charts JavaScript

// Initialize Charts
function initializeCharts() {
  try {
    // Get performance data from global variable injected by template
    const performanceData = window.performanceData || [];

    if (!performanceData || performanceData.length === 0) {
      console.warn("No performance data available for charts");
      return;
    }

    // Calculate overall performance distribution
    const performanceDistribution = {
      EE1: 0,
      EE2: 0,
      ME1: 0,
      ME2: 0,
      AE1: 0,
      AE2: 0,
      BE1: 0,
      BE2: 0,
    };

    const classData = [];

    performanceData.forEach((data) => {
      // Aggregate performance counts
      Object.keys(performanceDistribution).forEach((key) => {
        performanceDistribution[key] += data.performance_counts[key] || 0;
      });

      // Collect class data for comparison
      classData.push({
        label: `${data.grade} ${data.stream}`,
        average: data.class_average,
        students: data.total_students,
      });
    });

    // Create Performance Distribution Donut Chart
    createPerformanceDonutChart(performanceDistribution);

    // Create Class Comparison Bar Chart
    createClassComparisonChart(classData);
  } catch (error) {
    console.error("Error initializing charts:", error);
  }
}

    // Create Class Comparison Bar Chart
    createClassComparisonChart(classData);
  } catch (error) {
    console.error("Error initializing charts:", error);
  }
}

function createPerformanceDonutChart(data) {
  try {
    const ctx = document
      .getElementById("performanceDonutChart")
      ?.getContext("2d");
    if (!ctx) {
      console.warn("Performance donut chart canvas not found");
      return;
    }

    // Destroy existing chart if it exists
    if (window.performanceChart) {
      window.performanceChart.destroy();
    }

    window.performanceChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: [
          "EE1 (≥90%)",
          "EE2 (75-89%)",
          "ME1 (58-74%)",
          "ME2 (41-57%)",
          "AE1 (31-40%)",
          "AE2 (21-30%)",
          "BE1 (11-20%)",
          "BE2 (<11%)",
        ],
        datasets: [
          {
            data: [
              data.EE1,
              data.EE2,
              data.ME1,
              data.ME2,
              data.AE1,
              data.AE2,
              data.BE1,
              data.BE2,
            ],
            backgroundColor: [
              "#10B981",
              "#34D399",
              "#60A5FA",
              "#93C5FD",
              "#FBBF24",
              "#FCD34D",
              "#F87171",
              "#FCA5A5",
            ],
            borderWidth: 3,
            borderColor: "#ffffff",
            hoverBorderWidth: 5,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              padding: 20,
              usePointStyle: true,
              font: {
                size: 11,
              },
            },
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage =
                  total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                return `${context.label}: ${context.parsed} students (${percentage}%)`;
              },
            },
          },
        },
        animation: {
          animateRotate: true,
          duration: 2000,
        },
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const elementIndex = elements[0].index;
            const performanceLevels = [
              "EE1",
              "EE2",
              "ME1",
              "ME2",
              "AE1",
              "AE2",
              "BE1",
              "BE2",
            ];
            const selectedLevel = performanceLevels[elementIndex];
            filterByPerformanceLevel(selectedLevel);

            // Show drill-down analytics
            showDrillDownAnalytics("performance", selectedLevel);
          }
        },
      },
    });
  } catch (error) {
    console.error("Error creating performance donut chart:", error);
  }
}

function createClassComparisonChart(data) {
  try {
    const ctx = document
      .getElementById("classComparisonChart")
      ?.getContext("2d");
    if (!ctx) {
      console.warn("Class comparison chart canvas not found");
      return;
    }

    // Destroy existing chart if it exists
    if (window.comparisonChart) {
      window.comparisonChart.destroy();
    }

    // Sort by average for better visualization
    data.sort((a, b) => b.average - a.average);

    window.comparisonChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.map((item) => item.label),
        datasets: [
          {
            label: "Class Average",
            data: data.map((item) => item.average),
            backgroundColor: "rgba(102, 126, 234, 0.8)",
            borderColor: "rgba(102, 126, 234, 1)",
            borderWidth: 2,
            borderRadius: 8,
            borderSkipped: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const classInfo = data[context.dataIndex];
                return [
                  `Class Average: ${context.parsed.y.toFixed(2)}`,
                  `Students: ${classInfo.students}`,
                ];
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Class Average",
            },
            grid: {
              color: "rgba(0,0,0,0.1)",
            },
          },
          x: {
            title: {
              display: true,
              text: "Classes",
            },
            grid: {
              display: false,
            },
          },
        },
        animation: {
          duration: 2000,
          easing: "easeOutQuart",
        },
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const elementIndex = elements[0].index;
            const selectedClass = data[elementIndex].label;
            const grade = selectedClass.split(" ")[0]; // Extract grade from "Grade 7 Y"
            filterByGrade(grade);

            // Show drill-down analytics
            showDrillDownAnalytics("class", selectedClass, data[elementIndex]);
          }
        },
      },
    });
  } catch (error) {
    console.error("Error creating class comparison chart:", error);
  }
}

// Filter functions
function filterByPerformanceLevel(level) {
  try {
    activeFilters.performanceLevel =
      activeFilters.performanceLevel === level ? null : level;
    applyFilters();
    updateFilterIndicators();
  } catch (error) {
    console.error("Error filtering by performance level:", error);
  }
}

function filterByGrade(grade) {
  try {
    activeFilters.grade = activeFilters.grade === grade ? null : grade;
    applyFilters();
    updateFilterIndicators();
  } catch (error) {
    console.error("Error filtering by grade:", error);
  }
}

function applyFilters() {
  try {
    filteredData = allPerformanceData.filter((item) => {
      let matches = true;

      if (activeFilters.grade) {
        matches = matches && item.grade === activeFilters.grade;
      }

      if (activeFilters.performanceLevel) {
        // Check if this class has students in the selected performance level
        matches =
          matches &&
          item.performance_counts &&
          item.performance_counts[activeFilters.performanceLevel] > 0;
      }

      return matches;
    });

    currentPage = 1;
    if (typeof displayPage === "function") displayPage();
    if (typeof updatePaginationInfo === "function") updatePaginationInfo();
  } catch (error) {
    console.error("Error applying filters:", error);
  }
}

function resetFilters() {
  try {
    activeFilters = {
      performanceLevel: null,
      grade: null,
    };
    applyFilters();
    updateFilterIndicators();
  } catch (error) {
    console.error("Error resetting filters:", error);
  }
}

function updateFilterIndicators() {
  try {
    const resetBtn = document.querySelector('button[onclick="resetFilters()"]');
    if (resetBtn) {
      if (activeFilters.performanceLevel || activeFilters.grade) {
        resetBtn.classList.add("filter-active");
      } else {
        resetBtn.classList.remove("filter-active");
      }
    }
  } catch (error) {
    console.error("Error updating filter indicators:", error);
  }
}

// Export functionality
async function exportChartsAsPDF() {
  try {
    if (typeof window.jspdf === "undefined") {
      showNotification("PDF export library not loaded", "error");
      return;
    }

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF("landscape", "mm", "a4");

    // Add title
    pdf.setFontSize(20);
    pdf.text("Performance Overview Report", 20, 20);
    pdf.setFontSize(12);
    pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, 30);

    // Capture performance chart
    const performanceCanvas = document.getElementById("performanceDonutChart");
    if (performanceCanvas) {
      const performanceImgData = performanceCanvas.toDataURL("image/png");
      pdf.addImage(performanceImgData, "PNG", 20, 40, 120, 80);
    }

    // Capture comparison chart
    const comparisonCanvas = document.getElementById("classComparisonChart");
    if (comparisonCanvas) {
      const comparisonImgData = comparisonCanvas.toDataURL("image/png");
      pdf.addImage(comparisonImgData, "PNG", 150, 40, 120, 80);
    }

    // Add statistics
    pdf.setFontSize(14);
    pdf.text("Key Statistics:", 20, 140);
    pdf.setFontSize(10);

    const totalStudents =
      document.getElementById("total-assessed")?.textContent || "N/A";
    const bestClass =
      document.getElementById("best-class")?.textContent || "N/A";
    const schoolAverage =
      document.getElementById("school-average")?.textContent || "N/A";
    const reportsGenerated =
      document.getElementById("reports-generated")?.textContent || "N/A";

    pdf.text(`Total Students Assessed: ${totalStudents}`, 20, 150);
    pdf.text(`Best Performing Class: ${bestClass}`, 20, 160);
    pdf.text(`School Average: ${schoolAverage}`, 20, 170);
    pdf.text(`Reports Generated: ${reportsGenerated}`, 20, 180);

    // Save the PDF
    pdf.save("performance-overview.pdf");

    showNotification("Charts exported successfully!", "success");
  } catch (error) {
    console.error("Export failed:", error);
    showNotification("Export failed. Please try again.", "error");
  }
}

// Export performance data to CSV
function exportPerformanceData() {
  try {
    const headers = [
      "Grade",
      "Stream",
      "Term",
      "Assessment Type",
      "Students",
      "Class Average",
      "EE1 Count",
      "EE2 Count",
      "ME1 Count",
      "ME2 Count",
      "AE1 Count",
      "AE2 Count",
      "BE1 Count",
      "BE2 Count",
    ];
    let csvContent = headers.join(",") + "\n";

    filteredData.forEach((item) => {
      const row = item.element;
      if (!row) return;

      const cells = row.querySelectorAll("td");
      const rowData = Array.from(cells).map((cell) => {
        // Clean up the cell content
        let content = cell.textContent.trim();
        // Remove extra whitespace and newlines
        content = content.replace(/\s+/g, " ");
        // Escape commas and quotes
        if (content.includes(",") || content.includes('"')) {
          content = '"' + content.replace(/"/g, '""') + '"';
        }
        return content;
      });
      csvContent += rowData.join(",") + "\n";
    });

    // Create and download the CSV file
    const blob = new Blob([csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "performance_assessment_results.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showNotification("Data exported successfully!", "success");
  } catch (error) {
    console.error("Error exporting data:", error);
    showNotification("Export failed. Please try again.", "error");
  }
}

// Make functions globally available
window.ChartFunctions = {
  initializeCharts,
  createPerformanceDonutChart,
  createClassComparisonChart,
  filterByPerformanceLevel,
  filterByGrade,
  applyFilters,
  resetFilters,
  exportChartsAsPDF,
  exportPerformanceData,
};
