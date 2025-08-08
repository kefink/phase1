// Headteacher Dashboard Analytics JavaScript

// Performance Heatmap
function generatePerformanceHeatmap() {
  try {
    const performanceDataElement = document.querySelector("[data-performance]");
    let performanceData = [];

    if (performanceDataElement) {
      performanceData = JSON.parse(performanceDataElement.dataset.performance);
    } else if (typeof window.performanceData !== "undefined") {
      performanceData = window.performanceData;
    }

    if (performanceData && performanceData.length > 0) {
      updateHeatmap();
    }
  } catch (error) {
    console.error("Error generating performance heatmap:", error);
  }
}

function updateHeatmap() {
  try {
    const metricSelect = document.getElementById("heatmapMetric");
    const metric = metricSelect ? metricSelect.value : "average";

    const performanceDataElement = document.querySelector("[data-performance]");
    let performanceData = [];

    if (performanceDataElement) {
      performanceData = JSON.parse(performanceDataElement.dataset.performance);
    } else if (typeof window.performanceData !== "undefined") {
      performanceData = window.performanceData;
    }

    const container = document.getElementById("heatmapContainer");
    if (!container) return;

    container.innerHTML = "";

    if (!performanceData || performanceData.length === 0) {
      container.innerHTML =
        '<div class="drill-down-placeholder">No performance data available</div>';
      return;
    }

    performanceData.forEach((data) => {
      const cell = document.createElement("div");
      cell.className = "heatmap-cell";

      let value, color;

      switch (metric) {
        case "average":
          value = data.class_average ? data.class_average.toFixed(1) : "0.0";
          color = getHeatmapColor(data.class_average || 0, 0, 100);
          break;
        case "excellence":
          const excellenceRate = data.performance_counts
            ? ((data.performance_counts.EE1 + data.performance_counts.EE2) /
                data.total_students) *
              100
            : 0;
          value = excellenceRate.toFixed(1) + "%";
          color = getHeatmapColor(excellenceRate, 0, 100);
          break;
        case "mastery":
          const masteryRate = data.performance_counts
            ? ((data.performance_counts.ME1 + data.performance_counts.ME2) /
                data.total_students) *
              100
            : 0;
          value = masteryRate.toFixed(1) + "%";
          color = getHeatmapColor(masteryRate, 0, 100);
          break;
        default:
          value = "0";
          color = getHeatmapColor(0, 0, 100);
      }

      cell.style.background = color;
      cell.innerHTML = `
        <div class="heatmap-label">${data.grade} ${data.stream}</div>
        <div class="heatmap-value">${value}</div>
      `;

      cell.onclick = () => {
        showDrillDownAnalytics("heatmap", `${data.grade} ${data.stream}`, data);
      };

      container.appendChild(cell);
    });
  } catch (error) {
    console.error("Error updating heatmap:", error);
  }
}

function getHeatmapColor(value, min, max) {
  const ratio = Math.max(0, Math.min(1, (value - min) / (max - min)));

  if (ratio >= 0.8) return "linear-gradient(135deg, #10B981, #059669)"; // Excellent - Green
  if (ratio >= 0.6) return "linear-gradient(135deg, #3B82F6, #1D4ED8)"; // Good - Blue
  if (ratio >= 0.4) return "linear-gradient(135deg, #F59E0B, #D97706)"; // Average - Orange
  return "linear-gradient(135deg, #EF4444, #DC2626)"; // Below - Red
}

// Performance Alerts
function generatePerformanceAlerts() {
  try {
    const performanceDataElement = document.querySelector("[data-performance]");
    let performanceData = [];

    if (performanceDataElement) {
      performanceData = JSON.parse(performanceDataElement.dataset.performance);
    } else if (typeof window.performanceData !== "undefined") {
      performanceData = window.performanceData;
    }

    const alertsContainer = document.getElementById("performanceAlerts");
    if (!alertsContainer) return;

    const alerts = [];

    if (!performanceData || performanceData.length === 0) {
      alertsContainer.innerHTML = `
        <div class="alert-item alert-info">
          <div class="alert-header">
            <span class="alert-icon">ℹ️</span>
            <span class="alert-title">No Data Available</span>
          </div>
          <div class="alert-message">No performance data available for analysis.</div>
        </div>
      `;
      return;
    }

    performanceData.forEach((data) => {
      const classLabel = `${data.grade} ${data.stream}`;

      // Critical: Very low performance
      if (data.class_average < 30) {
        alerts.push({
          type: "critical",
          icon: "🚨",
          title: "Critical Performance Alert",
          message: `${classLabel} has a very low class average of ${data.class_average.toFixed(
            1
          )}. Immediate intervention required.`,
        });
      }

      // Warning: Low excellence rate
      if (data.performance_counts) {
        const excellenceRate =
          ((data.performance_counts.EE1 + data.performance_counts.EE2) /
            data.total_students) *
          100;
        if (excellenceRate < 20) {
          alerts.push({
            type: "warning",
            icon: "⚠️",
            title: "Low Excellence Rate",
            message: `${classLabel} has only ${excellenceRate.toFixed(
              1
            )}% of students achieving excellence (EE1/EE2).`,
          });
        }
      }

      // Info: High performance
      if (data.class_average > 80) {
        alerts.push({
          type: "info",
          icon: "🎉",
          title: "Outstanding Performance",
          message: `${classLabel} is performing exceptionally well with a class average of ${data.class_average.toFixed(
            1
          )}.`,
        });
      }

      // Warning: Large class with low performance
      if (data.total_students > 25 && data.class_average < 50) {
        alerts.push({
          type: "warning",
          icon: "👥",
          title: "Large Class Concern",
          message: `${classLabel} has ${data.total_students} students with below-average performance. Consider additional support.`,
        });
      }
    });

    // Sort alerts by priority (critical first)
    alerts.sort((a, b) => {
      const priority = { critical: 3, warning: 2, info: 1 };
      return priority[b.type] - priority[a.type];
    });

    alertsContainer.innerHTML = "";

    if (alerts.length === 0) {
      alertsContainer.innerHTML = `
        <div class="alert-item alert-info">
          <div class="alert-header">
            <span class="alert-icon">✅</span>
            <span class="alert-title">All Clear</span>
          </div>
          <div class="alert-message">No performance alerts at this time. All classes are performing within expected ranges.</div>
        </div>
      `;
    } else {
      alerts.forEach((alert) => {
        const alertElement = document.createElement("div");
        alertElement.className = `alert-item alert-${alert.type}`;
        alertElement.innerHTML = `
          <div class="alert-header">
            <span class="alert-icon">${alert.icon}</span>
            <span class="alert-title">${alert.title}</span>
          </div>
          <div class="alert-message">${alert.message}</div>
        `;
        alertsContainer.appendChild(alertElement);
      });
    }
  } catch (error) {
    console.error("Error generating performance alerts:", error);
  }
}

// Drill-down Analytics
function initializeDrillDown() {
  const container = document.getElementById("drillDownContainer");
  if (container) {
    container.innerHTML = `
      <div class="drill-down-placeholder">
        Click on any chart element above to see detailed analytics
      </div>
    `;
  }
}

function showDrillDownAnalytics(type, identifier, data = null) {
  try {
    const container = document.getElementById("drillDownContainer");
    if (!container) return;

    let content = "";

    if (type === "performance") {
      content = generatePerformanceDrillDown(identifier);
    } else if (type === "class" || type === "heatmap") {
      content = generateClassDrillDown(identifier, data);
    }

    container.innerHTML = `
      <div class="drill-down-content">
        <div class="drill-down-header">
          <div class="drill-down-title">Detailed Analytics: ${identifier}</div>
          <button class="drill-down-close" onclick="closeDrillDown()">✕ Close</button>
        </div>
        ${content}
      </div>
    `;
  } catch (error) {
    console.error("Error showing drill-down analytics:", error);
  }
}

function generatePerformanceDrillDown(performanceLevel) {
  try {
    const performanceDataElement = document.querySelector("[data-performance]");
    let performanceData = [];

    if (performanceDataElement) {
      performanceData = JSON.parse(performanceDataElement.dataset.performance);
    } else if (typeof window.performanceData !== "undefined") {
      performanceData = window.performanceData;
    }

    // Calculate statistics for this performance level
    let totalStudents = 0;
    let classesWithStudents = 0;
    let bestClass = "";
    let bestCount = 0;

    performanceData.forEach((data) => {
      const count = data.performance_counts
        ? data.performance_counts[performanceLevel] || 0
        : 0;
      totalStudents += count;
      if (count > 0) {
        classesWithStudents++;
        if (count > bestCount) {
          bestCount = count;
          bestClass = `${data.grade} ${data.stream}`;
        }
      }
    });

    const performanceLabels = {
      EE1: "Exceeds Expectations 1 (≥90%)",
      EE2: "Exceeds Expectations 2 (75-89%)",
      ME1: "Meets Expectations 1 (58-74%)",
      ME2: "Meets Expectations 2 (41-57%)",
      AE1: "Approaches Expectations 1 (31-40%)",
      AE2: "Approaches Expectations 2 (21-30%)",
      BE1: "Below Expectations 1 (11-20%)",
      BE2: "Below Expectations 2 (<11%)",
    };

    return `
      <div class="drill-down-stats">
        <div class="drill-stat">
          <div class="drill-stat-value">${totalStudents}</div>
          <div class="drill-stat-label">Total Students</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${classesWithStudents}</div>
          <div class="drill-stat-label">Classes Affected</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${bestClass || "N/A"}</div>
          <div class="drill-stat-label">Highest Count</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${bestCount}</div>
          <div class="drill-stat-label">Students in Best Class</div>
        </div>
      </div>
      <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #333;">Performance Level: ${
          performanceLabels[performanceLevel] || performanceLevel
        }</h4>
        <p style="margin: 0; color: #666; line-height: 1.5;">
          This performance level represents students who ${getPerformanceDescription(
            performanceLevel
          )}.
          Focus on ${getRecommendation(performanceLevel)}.
        </p>
      </div>
    `;
  } catch (error) {
    console.error("Error generating performance drill down:", error);
    return "<p>Error loading performance details.</p>";
  }
}

function generateClassDrillDown(classLabel, data) {
  try {
    if (!data) {
      // Find data for this class
      const performanceDataElement =
        document.querySelector("[data-performance]");
      let performanceData = [];

      if (performanceDataElement) {
        performanceData = JSON.parse(
          performanceDataElement.dataset.performance
        );
      } else if (typeof window.performanceData !== "undefined") {
        performanceData = window.performanceData;
      }

      data = performanceData.find(
        (item) => `${item.grade} ${item.stream}` === classLabel
      );
    }

    if (!data) {
      return "<p>No data available for this class.</p>";
    }

    const excellenceRate = data.performance_counts
      ? (
          ((data.performance_counts.EE1 + data.performance_counts.EE2) /
            data.total_students) *
          100
        ).toFixed(1)
      : "0.0";
    const masteryRate = data.performance_counts
      ? (
          ((data.performance_counts.ME1 + data.performance_counts.ME2) /
            data.total_students) *
          100
        ).toFixed(1)
      : "0.0";
    const needsSupportRate = data.performance_counts
      ? (
          ((data.performance_counts.AE1 +
            data.performance_counts.AE2 +
            data.performance_counts.BE1 +
            data.performance_counts.BE2) /
            data.total_students) *
          100
        ).toFixed(1)
      : "0.0";

    return `
      <div class="drill-down-stats">
        <div class="drill-stat">
          <div class="drill-stat-value">${data.total_students}</div>
          <div class="drill-stat-label">Total Students</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${
            data.class_average ? data.class_average.toFixed(1) : "0.0"
          }</div>
          <div class="drill-stat-label">Class Average</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${excellenceRate}%</div>
          <div class="drill-stat-label">Excellence Rate</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${masteryRate}%</div>
          <div class="drill-stat-label">Mastery Rate</div>
        </div>
        <div class="drill-stat">
          <div class="drill-stat-value">${needsSupportRate}%</div>
          <div class="drill-stat-label">Needs Support</div>
        </div>
      </div>
      <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px;">
        <h4 style="margin: 0 0 15px 0; color: #333;">Performance Breakdown</h4>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 12px;">
          <div style="text-align: center; padding: 8px; background: #10B981; color: white; border-radius: 4px;">
            <div style="font-weight: bold;">${
              data.performance_counts ? data.performance_counts.EE1 : 0
            }</div>
            <div>EE1 (≥90%)</div>
          </div>
          <div style="text-align: center; padding: 8px; background: #34D399; color: white; border-radius: 4px;">
            <div style="font-weight: bold;">${
              data.performance_counts ? data.performance_counts.EE2 : 0
            }</div>
            <div>EE2 (75-89%)</div>
          </div>
          <div style="text-align: center; padding: 8px; background: #60A5FA; color: white; border-radius: 4px;">
            <div style="font-weight: bold;">${
              data.performance_counts ? data.performance_counts.ME1 : 0
            }</div>
            <div>ME1 (58-74%)</div>
          </div>
          <div style="text-align: center; padding: 8px; background: #93C5FD; color: white; border-radius: 4px;">
            <div style="font-weight: bold;">${
              data.performance_counts ? data.performance_counts.ME2 : 0
            }</div>
            <div>ME2 (41-57%)</div>
          </div>
        </div>
      </div>
    `;
  } catch (error) {
    console.error("Error generating class drill down:", error);
    return "<p>Error loading class details.</p>";
  }
}

function getPerformanceDescription(level) {
  const descriptions = {
    EE1: "demonstrate exceptional mastery of learning objectives",
    EE2: "show strong understanding and application of concepts",
    ME1: "meet most learning expectations with good comprehension",
    ME2: "meet basic learning expectations with adequate understanding",
    AE1: "are approaching expectations but need additional support",
    AE2: "require significant support to meet learning objectives",
    BE1: "need intensive intervention and remedial support",
    BE2: "require immediate and comprehensive intervention",
  };
  return descriptions[level] || "are in this performance category";
}

function getRecommendation(level) {
  const recommendations = {
    EE1: "providing enrichment and advanced challenges",
    EE2: "maintaining high standards and offering extension activities",
    ME1: "reinforcing concepts and providing practice opportunities",
    ME2: "additional practice and targeted support",
    AE1: "intensive support and differentiated instruction",
    AE2: "remedial intervention and individualized learning plans",
    BE1: "immediate intervention and specialized support programs",
    BE2: "comprehensive intervention and possible assessment for learning difficulties",
  };
  return recommendations[level] || "appropriate support strategies";
}

function closeDrillDown() {
  initializeDrillDown();
}

// Alert Management Functions
function dismissAlert(button) {
  try {
    const alertElement = button.closest(".system-alert");
    if (alertElement) {
      alertElement.style.transform = "translateX(100%)";
      alertElement.style.opacity = "0";
      setTimeout(() => {
        alertElement.remove();
        updateAlertCount();
      }, 300);
    }
  } catch (error) {
    console.error("Error dismissing alert:", error);
  }
}

function showAlertDetails(alertTitle) {
  showNotification(`Showing details for: ${alertTitle}`, "info");
}

function updateAlertCount() {
  try {
    const remainingAlerts = document.querySelectorAll(".system-alert").length;
    const alertsCount = document.querySelector(".alerts-count");
    if (alertsCount) {
      alertsCount.textContent = `${remainingAlerts} Alert${
        remainingAlerts !== 1 ? "s" : ""
      }`;

      // Hide section if no alerts remain
      if (remainingAlerts === 0) {
        const alertsSection = document
          .querySelector(".system-alerts-container")
          ?.closest("div");
        if (alertsSection) {
          alertsSection.innerHTML = `
            <div class="section-header">
              <h2>
                <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                System Status
              </h2>
            </div>
            <div class="no-alerts-container">
              <div class="no-alerts-content">
                <i class="fas fa-shield-alt"></i>
                <h3>All Systems Operational</h3>
                <p>No system alerts at this time. All systems are running smoothly.</p>
              </div>
            </div>
          `;
        }
      }
    }
  } catch (error) {
    console.error("Error updating alert count:", error);
  }
}

// Make functions globally available
window.AnalyticsFunctions = {
  generatePerformanceHeatmap,
  updateHeatmap,
  generatePerformanceAlerts,
  initializeDrillDown,
  showDrillDownAnalytics,
  closeDrillDown,
  dismissAlert,
  showAlertDetails,
  updateAlertCount,
};
