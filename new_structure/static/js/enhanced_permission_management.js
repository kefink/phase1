/**
 * Enhanced Permission Management with Direct Granting and Expiration
 * Provides comprehensive permission management functionality for headteachers
 */

// Global variables
let durationOptions = {};
let allTeachers = [];
let allGrades = [];
let allStreams = {};

// Initialize enhanced permission management
document.addEventListener("DOMContentLoaded", function () {
  loadDurationOptions();
  loadTeachersAndClasses();
  loadPermissionStatistics();
  loadExpiringPermissions();
});

// ============================================================================
// DATA LOADING FUNCTIONS
// ============================================================================

async function loadDurationOptions() {
  try {
    const response = await fetch("/permission/duration_options");
    const data = await response.json();

    if (data.success) {
      durationOptions = data.duration_options;
      populateDurationSelects();
    }
  } catch (error) {
    console.error("Error loading duration options:", error);
  }
}

async function loadTeachersAndClasses() {
  try {
    // Load teachers
    const teachersResponse = await fetch("/api/teachers");
    if (teachersResponse.ok) {
      const teachersData = await teachersResponse.json();
      allTeachers = teachersData.teachers || [];
      populateTeacherSelects();
    }

    // Load grades and streams
    const gradesResponse = await fetch("/api/grades");
    if (gradesResponse.ok) {
      const gradesData = await gradesResponse.json();
      allGrades = gradesData.grades || [];
      populateGradeSelects();

      // Load streams for each grade
      for (const grade of allGrades) {
        const streamsResponse = await fetch(`/api/streams/${grade.id}`);
        if (streamsResponse.ok) {
          const streamsData = await streamsResponse.json();
          allStreams[grade.id] = streamsData.streams || [];
        }
      }
    }
  } catch (error) {
    console.error("Error loading teachers and classes:", error);
  }
}

function populateDurationSelects() {
  const selects = [
    "directGrantDuration",
    "bulkGrantDuration",
    "extendDuration",
  ];

  selects.forEach((selectId) => {
    const select = document.getElementById(selectId);
    if (select) {
      // Clear existing options except the first one
      while (select.children.length > 1) {
        select.removeChild(select.lastChild);
      }

      // Add duration options
      Object.entries(durationOptions).forEach(([key, option]) => {
        const optionElement = document.createElement("option");
        optionElement.value = key;
        optionElement.textContent = option.label;
        select.appendChild(optionElement);
      });
    }
  });
}

function populateTeacherSelects() {
  const selects = ["directGrantTeacher", "bulkGrantTeacher"];

  selects.forEach((selectId) => {
    const select = document.getElementById(selectId);
    if (select) {
      // Clear existing options except the first one
      while (select.children.length > 1) {
        select.removeChild(select.lastChild);
      }

      // Add teacher options
      allTeachers.forEach((teacher) => {
        const option = document.createElement("option");
        option.value = teacher.id;
        option.textContent = teacher.full_name || teacher.username;
        select.appendChild(option);
      });
    }
  });
}

function populateGradeSelects() {
  const selects = ["directGrantGrade"];

  selects.forEach((selectId) => {
    const select = document.getElementById(selectId);
    if (select) {
      // Clear existing options except the first one
      while (select.children.length > 1) {
        select.removeChild(select.lastChild);
      }

      // Add grade options
      allGrades.forEach((grade) => {
        const option = document.createElement("option");
        option.value = grade.id;
        option.textContent = grade.name;
        select.appendChild(option);
      });
    }
  });

  // Populate bulk grant class selection
  populateBulkClassSelection();
}

function populateBulkClassSelection() {
  const container = document.getElementById("classSelectionContainer");
  if (!container) return;

  container.innerHTML = "";

  allGrades.forEach((grade) => {
    const gradeStreams = allStreams[grade.id] || [];

    if (gradeStreams.length > 0) {
      // Grade with streams
      gradeStreams.forEach((stream) => {
        const item = document.createElement("div");
        item.className = "class-checkbox-item";
        item.innerHTML = `
                    <input type="checkbox" id="class_${grade.id}_${stream.id}" 
                           value="${grade.id}_${stream.id}" onchange="updateSelectedClassesPreview()">
                    <label for="class_${grade.id}_${stream.id}">${grade.name} - Stream ${stream.name}</label>
                `;
        container.appendChild(item);
      });
    } else {
      // Grade without streams
      const item = document.createElement("div");
      item.className = "class-checkbox-item";
      item.innerHTML = `
                <input type="checkbox" id="class_${grade.id}_" 
                       value="${grade.id}_" onchange="updateSelectedClassesPreview()">
                <label for="class_${grade.id}_">${grade.name} (All streams)</label>
            `;
      container.appendChild(item);
    }
  });
}

// ============================================================================
// MODAL FUNCTIONS
// ============================================================================

function openDirectGrantModal() {
  document.getElementById("directGrantModal").style.display = "flex";
  resetDirectGrantForm();
}

function closeDirectGrantModal() {
  document.getElementById("directGrantModal").style.display = "none";
}

function openBulkDirectGrantModal() {
  document.getElementById("bulkDirectGrantModal").style.display = "flex";
  resetBulkDirectGrantForm();
}

function closeBulkDirectGrantModal() {
  document.getElementById("bulkDirectGrantModal").style.display = "none";
}

function openExtendPermissionModal(permissionId, currentInfo) {
  document.getElementById("extendPermissionModal").style.display = "flex";
  document.getElementById("extendPermissionId").value = permissionId;

  // Populate current permission info
  const infoDiv = document.getElementById("currentPermissionInfo");
  infoDiv.innerHTML = `
        <h4><i class="fas fa-info-circle"></i> Current Permission</h4>
        <p><strong>Teacher:</strong> ${currentInfo.teacher_name}</p>
        <p><strong>Class:</strong> ${currentInfo.class_info}</p>
        <p><strong>Current Expiry:</strong> ${
          currentInfo.expires_at || "Permanent"
        }</p>
        <p><strong>Status:</strong> <span class="modern-badge badge-${getStatusBadgeClass(
          currentInfo.status
        )}">${currentInfo.status}</span></p>
    `;
}

function closeExtendPermissionModal() {
  document.getElementById("extendPermissionModal").style.display = "none";
}

// ============================================================================
// FORM HANDLING FUNCTIONS
// ============================================================================

function resetDirectGrantForm() {
  document.getElementById("directGrantForm").reset();
  document.getElementById("permissionPreview").style.display = "none";
  document.getElementById("expirationPreview").style.display = "none";
}

function resetBulkDirectGrantForm() {
  document.getElementById("bulkDirectGrantForm").reset();
  document.getElementById("selectedClassesPreview").style.display = "none";
  document.getElementById("bulkExpirationPreview").style.display = "none";

  // Uncheck all class checkboxes
  const checkboxes = document.querySelectorAll(
    '#classSelectionContainer input[type="checkbox"]'
  );
  checkboxes.forEach((checkbox) => (checkbox.checked = false));
}

function loadStreamsForDirectGrant() {
  const gradeId = document.getElementById("directGrantGrade").value;
  const streamSelect = document.getElementById("directGrantStream");

  // Clear existing options except the first one
  while (streamSelect.children.length > 1) {
    streamSelect.removeChild(streamSelect.lastChild);
  }

  if (gradeId && allStreams[gradeId]) {
    allStreams[gradeId].forEach((stream) => {
      const option = document.createElement("option");
      option.value = stream.id;
      option.textContent = `Stream ${stream.name}`;
      streamSelect.appendChild(option);
    });
  }

  updatePermissionPreview();
}

function updateExpirationPreview() {
  const durationKey = document.getElementById("directGrantDuration").value;
  const previewDiv = document.getElementById("expirationPreview");
  const textSpan = document.getElementById("expirationText");

  if (durationKey && durationOptions[durationKey]) {
    const option = durationOptions[durationKey];

    if (option.days === null) {
      textSpan.innerHTML =
        '<span class="expiration-permanent">This permission will be permanent</span>';
    } else {
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + option.days);
      textSpan.innerHTML = `Permission will expire on <span class="expiration-warning">${expiryDate.toLocaleDateString()}</span>`;
    }

    previewDiv.style.display = "block";
  } else {
    previewDiv.style.display = "none";
  }

  updatePermissionPreview();
}

function updateBulkExpirationPreview() {
  const durationKey = document.getElementById("bulkGrantDuration").value;
  const previewDiv = document.getElementById("bulkExpirationPreview");
  const textSpan = document.getElementById("bulkExpirationText");

  if (durationKey && durationOptions[durationKey]) {
    const option = durationOptions[durationKey];

    if (option.days === null) {
      textSpan.innerHTML =
        '<span class="expiration-permanent">These permissions will be permanent</span>';
    } else {
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + option.days);
      textSpan.innerHTML = `Permissions will expire on <span class="expiration-warning">${expiryDate.toLocaleDateString()}</span>`;
    }

    previewDiv.style.display = "block";
  } else {
    previewDiv.style.display = "none";
  }
}

function updateExtensionPreview() {
  const durationKey = document.getElementById("extendDuration").value;
  const previewDiv = document.getElementById("extensionPreview");
  const textSpan = document.getElementById("extensionText");

  if (durationKey && durationOptions[durationKey]) {
    const option = durationOptions[durationKey];

    if (option.days === null) {
      textSpan.innerHTML =
        '<span class="expiration-permanent">Permission will become permanent</span>';
    } else {
      const extensionDate = new Date();
      extensionDate.setDate(extensionDate.getDate() + option.days);
      textSpan.innerHTML = `Permission will be extended until <span class="expiration-warning">${extensionDate.toLocaleDateString()}</span>`;
    }

    previewDiv.style.display = "block";
  } else {
    previewDiv.style.display = "none";
  }
}

function updatePermissionPreview() {
  const teacherId = document.getElementById("directGrantTeacher").value;
  const gradeId = document.getElementById("directGrantGrade").value;
  const streamId = document.getElementById("directGrantStream").value;
  const durationKey = document.getElementById("directGrantDuration").value;

  const previewDiv = document.getElementById("permissionPreview");
  const contentDiv = document.getElementById("previewContent");

  if (teacherId && gradeId && durationKey) {
    const teacher = allTeachers.find((t) => t.id == teacherId);
    const grade = allGrades.find((g) => g.id == gradeId);
    const stream = streamId
      ? allStreams[gradeId]?.find((s) => s.id == streamId)
      : null;
    const duration = durationOptions[durationKey];

    const classInfo = stream
      ? `${grade.name} - Stream ${stream.name}`
      : `${grade.name} (All streams)`;

    contentDiv.innerHTML = `
            <div class="permission-preview-item">
                <div>
                    <strong>${
                      teacher.full_name || teacher.username
                    }</strong> will get permission to manage <strong>${classInfo}</strong>
                </div>
                <div class="duration-badge">${duration.label}</div>
            </div>
        `;

    previewDiv.style.display = "block";
  } else {
    previewDiv.style.display = "none";
  }
}

function updateSelectedClassesPreview() {
  const checkboxes = document.querySelectorAll(
    '#classSelectionContainer input[type="checkbox"]:checked'
  );
  const previewDiv = document.getElementById("selectedClassesPreview");
  const listDiv = document.getElementById("selectedClassesList");

  if (checkboxes.length > 0) {
    let html = "";
    checkboxes.forEach((checkbox) => {
      const [gradeId, streamId] = checkbox.value.split("_");
      const grade = allGrades.find((g) => g.id == gradeId);
      const stream = streamId
        ? allStreams[gradeId]?.find((s) => s.id == streamId)
        : null;
      const classInfo = stream
        ? `${grade.name} - Stream ${stream.name}`
        : `${grade.name} (All streams)`;

      html += `<div class="permission-preview-item">
                <div>${classInfo}</div>
                <div class="modern-badge badge-info">Selected</div>
            </div>`;
    });

    listDiv.innerHTML = html;
    previewDiv.style.display = "block";
  } else {
    previewDiv.style.display = "none";
  }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getStatusBadgeClass(status) {
  switch (status) {
    case "active":
      return "success";
    case "permanent":
      return "primary";
    case "expiring_soon":
      return "warning";
    case "expired":
      return "danger";
    case "inactive":
      return "secondary";
    default:
      return "info";
  }
}

// ============================================================================
// SUBMISSION FUNCTIONS
// ============================================================================

async function submitDirectGrant() {
  try {
    const teacherId = document.getElementById("directGrantTeacher").value;
    const gradeId = document.getElementById("directGrantGrade").value;
    const streamId = document.getElementById("directGrantStream").value || null;
    const durationKey = document.getElementById("directGrantDuration").value;
    const notes = document.getElementById("directGrantNotes").value;

    if (!teacherId || !gradeId || !durationKey) {
      alert("Please fill in all required fields");
      return;
    }

    const response = await fetch("/permission/direct_grant", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({
        teacher_id: parseInt(teacherId),
        grade_id: parseInt(gradeId),
        stream_id: streamId ? parseInt(streamId) : null,
        duration_key: durationKey,
        notes: notes,
      }),
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ " + data.message);
      closeDirectGrantModal();
      // Refresh the page or update the permission list
      location.reload();
    } else {
      alert("❌ " + data.message);
    }
  } catch (error) {
    console.error("Error submitting direct grant:", error);
    alert("❌ Failed to grant permission. Please try again.");
  }
}

async function submitBulkDirectGrant() {
  try {
    const teacherId = document.getElementById("bulkGrantTeacher").value;
    const durationKey = document.getElementById("bulkGrantDuration").value;
    const notes = document.getElementById("bulkGrantNotes").value;

    // Get selected classes
    const checkboxes = document.querySelectorAll(
      '#classSelectionContainer input[type="checkbox"]:checked'
    );
    const classAssignments = Array.from(checkboxes).map((checkbox) => {
      const [gradeId, streamId] = checkbox.value.split("_");
      return {
        grade_id: parseInt(gradeId),
        stream_id: streamId ? parseInt(streamId) : null,
      };
    });

    if (!teacherId || !durationKey || classAssignments.length === 0) {
      alert("Please fill in all required fields and select at least one class");
      return;
    }

    const response = await fetch("/permission/bulk_direct_grant", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({
        teacher_id: parseInt(teacherId),
        class_assignments: classAssignments,
        duration_key: durationKey,
        notes: notes,
      }),
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ " + data.message);
      closeBulkDirectGrantModal();
      // Refresh the page or update the permission list
      location.reload();
    } else {
      alert("❌ " + data.message);
    }
  } catch (error) {
    console.error("Error submitting bulk direct grant:", error);
    alert("❌ Failed to grant permissions. Please try again.");
  }
}

async function submitExtendPermission() {
  try {
    const permissionId = document.getElementById("extendPermissionId").value;
    const durationKey = document.getElementById("extendDuration").value;

    if (!permissionId || !durationKey) {
      alert("Please select an extension duration");
      return;
    }

    const response = await fetch("/permission/extend_permission", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({
        permission_id: parseInt(permissionId),
        duration_key: durationKey,
      }),
    });

    const data = await response.json();

    if (data.success) {
      alert("✅ " + data.message);
      closeExtendPermissionModal();
      // Refresh the page or update the permission list
      location.reload();
    } else {
      alert("❌ " + data.message);
    }
  } catch (error) {
    console.error("Error extending permission:", error);
    alert("❌ Failed to extend permission. Please try again.");
  }
}

// ============================================================================
// STATISTICS AND MONITORING FUNCTIONS
// ============================================================================

async function loadPermissionStatistics() {
  try {
    const response = await fetch("/permission/permission_statistics");
    const data = await response.json();

    if (data.success) {
      updateStatisticsDisplay(data.statistics);
    }
  } catch (error) {
    console.error("Error loading permission statistics:", error);
  }
}

async function loadExpiringPermissions() {
  try {
    const response = await fetch(
      "/permission/expiring_permissions?days_ahead=7"
    );
    const data = await response.json();

    if (data.success) {
      updateExpiringPermissionsDisplay(data.expiring_permissions);
    }
  } catch (error) {
    console.error("Error loading expiring permissions:", error);
  }
}

function updateStatisticsDisplay(stats) {
  // Update statistics cards if they exist on the page
  const elements = {
    "total-active-permissions": stats.total_active_permissions,
    "permanent-permissions": stats.permanent_permissions,
    "temporary-permissions": stats.temporary_permissions,
    "expiring-soon": stats.expiring_soon,
    "auto-granted": stats.auto_granted,
    "request-approved": stats.request_approved,
  };

  Object.entries(elements).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  });
}

function updateExpiringPermissionsDisplay(expiringPermissions) {
  const container = document.getElementById("expiring-permissions-list");
  if (!container) return;

  if (expiringPermissions.length === 0) {
    container.innerHTML =
      '<p class="text-muted">No permissions expiring in the next 7 days.</p>';
    return;
  }

  let html = "";
  expiringPermissions.forEach((permission) => {
    const daysText =
      permission.days_until_expiry === 1
        ? "1 day"
        : `${permission.days_until_expiry} days`;
    html += `
            <div class="expiring-permission-item" style="display: flex; justify-content: space-between; align-items: center; padding: var(--space-3); border: 1px solid var(--orange-200); border-radius: var(--radius-md); margin-bottom: var(--space-2); background: var(--orange-50);">
                <div>
                    <strong>${permission.teacher_name}</strong> - ${
      permission.class_info
    }
                    <br><small class="text-muted">Granted by ${
                      permission.granted_by_name
                    }</small>
                </div>
                <div style="text-align: right;">
                    <div class="modern-badge badge-warning">Expires in ${daysText}</div>
                    <br><button class="modern-btn btn-sm btn-outline" onclick="openExtendPermissionModal(${
                      permission.id
                    }, ${JSON.stringify(permission).replace(/"/g, "&quot;")})">
                        <i class="fas fa-clock"></i> Extend
                    </button>
                </div>
            </div>
        `;
  });

  container.innerHTML = html;
}

// Get CSRF token
function getCSRFToken() {
  return document
    .querySelector("meta[name=csrf-token]")
    .getAttribute("content");
}
