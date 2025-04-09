document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM loaded - initializing teacher dashboard");

  // Initialize form validation
  const uploadForm = document.getElementById("upload-form");
  if (uploadForm) {
    console.log("Found upload form, attaching event listeners");
    uploadForm.addEventListener("submit", function (event) {
      console.log("Upload form submitted");
      const requiredFields = uploadForm.querySelectorAll("[required]");
      let isValid = true;
      requiredFields.forEach((field) => {
        const formGroup = field.closest(".form-group");
        if (!field.value) {
          console.log(`Field ${field.name} is empty`);
          formGroup.classList.add("error");
          formGroup.classList.remove("success");
          isValid = false;
          if (!formGroup.querySelector(".error-message")) {
            const errorMsg = document.createElement("div");
            errorMsg.className = "validation-message error-message";
            errorMsg.textContent = "This field is required";
            formGroup.appendChild(errorMsg);
          }
        } else {
          formGroup.classList.remove("error");
          formGroup.classList.add("success");
          const errorMsg = formGroup.querySelector(".error-message");
          if (errorMsg) {
            errorMsg.remove();
          }
        }
      });

      if (!isValid) {
        console.log("Form validation failed, preventing submission");
        event.preventDefault();
      } else {
        console.log("Form validation passed, submitting form");
        // Form is valid, allow natural submission
      }
    });

    // Clear errors on input change
    const inputs = uploadForm.querySelectorAll("input, select");
    inputs.forEach((input) => {
      input.addEventListener("input", function () {
        const formGroup = this.closest(".form-group");
        if (this.value) {
          formGroup.classList.remove("error");
          const errorMsg = formGroup.querySelector(".error-message");
          if (errorMsg) {
            errorMsg.remove();
          }
        }
      });
    });
  }

  // Initialize global functions for form updates
  initGlobalFormFunctions();
});

// Define global functions for form updates
function initGlobalFormFunctions() {
  // Function to update subjects based on education level
  window.updateSubjects = function () {
    console.log("updateSubjects called");
    const educationLevelSelect = document.getElementById("education_level");
    const subjectSelect = document.getElementById("subject");

    if (!educationLevelSelect || !subjectSelect) {
      console.error("Education level or subject select elements not found");
      return;
    }

    const formGroup = subjectSelect.closest(".form-group");
    subjectSelect.innerHTML = '<option value="">Select Subject</option>';
    const selectedEducationLevel = educationLevelSelect.value;

    if (selectedEducationLevel) {
      console.log(
        `Updating subjects for education level: ${selectedEducationLevel}`
      );
      let subjects = [];
      if (selectedEducationLevel === "lower_primary") {
        subjects = [
          "Indigenous Language",
          "Kiswahili",
          "Mathematics",
          "English",
          "Religious Education",
          "Environmental Activities",
          "Creative Activities",
        ];
      } else if (selectedEducationLevel === "upper_primary") {
        subjects = [
          "English",
          "Mathematics",
          "Kiswahili",
          "Religious Education",
          "Agriculture and Nutrition",
          "Social Studies",
          "Creative Arts",
          "Science and Technology",
        ];
      } else if (selectedEducationLevel === "junior_secondary") {
        subjects = [
          "Social Studies and Life Skills",
          "Agriculture and Home Science",
          "Integrated Science and Health Education",
          "Pre-Technical Studies",
          "Visual Arts",
          "Mathematics",
          "English",
          "Kiswahili",
          "Religious Education",
        ];
      }

      subjects.forEach((subject) => {
        const option = document.createElement("option");
        option.value = subject;
        option.textContent = subject;
        subjectSelect.appendChild(option);
      });

      formGroup.classList.add("success");
      formGroup.classList.remove("error");
    } else {
      console.log("No education level selected");
      formGroup.classList.remove("success");
    }
  };

  // Function to handle grade change and update streams
  window.onGradeChange = function () {
    console.log("onGradeChange called");
    const gradeSelect = document.getElementById("grade");
    const streamSelect = document.getElementById("stream");

    if (!gradeSelect || !streamSelect) {
      console.error("Grade or stream select elements not found");
      return;
    }

    const formGroup = streamSelect.closest(".form-group");
    streamSelect.innerHTML = '<option value="">Select Stream</option>';
    const selectedGrade = gradeSelect.value;

    if (selectedGrade) {
      console.log(`Updating streams for grade: ${selectedGrade}`);
      const streams = ["B", "G", "Y"];
      streams.forEach((stream) => {
        const option = document.createElement("option");
        option.value = `${selectedGrade}${stream}`;
        option.textContent = `${selectedGrade}${stream}`;
        streamSelect.appendChild(option);
      });
      formGroup.classList.add("success");
      formGroup.classList.remove("error");
    } else {
      console.log("No grade selected");
      formGroup.classList.remove("success");
    }
  };

  // Attach onchange events to select elements if they exist
  const gradeSelect = document.getElementById("grade");
  if (gradeSelect) {
    console.log("Adding change event listener to grade select");
    gradeSelect.addEventListener("change", window.onGradeChange);
  }

  const educationLevelSelect = document.getElementById("education_level");
  if (educationLevelSelect) {
    console.log("Adding change event listener to education level select");
    educationLevelSelect.addEventListener("change", window.updateSubjects);
  }

  // Run initialization functions if needed
  if (educationLevelSelect && educationLevelSelect.value) {
    window.updateSubjects();
  }

  if (gradeSelect && gradeSelect.value) {
    window.onGradeChange();
  }

  console.log("Global form functions initialized");
}
