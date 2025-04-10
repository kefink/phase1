document.addEventListener("DOMContentLoaded", function () {
  const uploadForm = document.getElementById("upload-form");

  if (uploadForm) {
    uploadForm.addEventListener("submit", function (e) {
      const submitBtn = e.submitter;

      // If this is the initial "Upload Marks" submission
      if (submitBtn && submitBtn.name === "upload_marks") {
        // Add console logging for debugging
        console.log("Upload Marks button clicked");

        // Validate all required fields
        const requiredFields = uploadForm.querySelectorAll("[required]");
        let isValid = true;

        requiredFields.forEach((field) => {
          console.log(`Checking field: ${field.name}, value: ${field.value}`);
          if (!field.value) {
            field.closest(".form-group").classList.add("error");
            isValid = false;
          } else {
            field.closest(".form-group").classList.remove("error");
          }
        });

        if (!isValid) {
          // Only prevent default if validation fails
          e.preventDefault();
          console.log("Form validation failed");
          return;
        }

        console.log("Form validation passed, submitting...");
        // Let the form submit naturally - DO NOT call uploadForm.submit() manually!
        // The browser will handle the submission
      } else if (submitBtn && submitBtn.name === "submit_marks") {
        console.log("Submit Marks button clicked");
        // Let the form submit naturally
      }
    });

    // Real-time validation
    const inputs = uploadForm.querySelectorAll("input, select");
    inputs.forEach((input) => {
      input.addEventListener("change", function () {
        if (this.value) {
          this.closest(".form-group").classList.remove("error");
        }
      });
    });
  }

  // Dynamic subject loading based on education level
  const educationLevelSelect = document.getElementById("education_level");
  if (educationLevelSelect) {
    educationLevelSelect.addEventListener("change", function () {
      const subjectSelect = document.getElementById("subject");
      const level = this.value;

      // Clear existing options
      subjectSelect.innerHTML = '<option value="">Select Subject</option>';

      if (level === "lower_primary") {
        addSubjects([
          "Indigenous Language",
          "Kiswahili",
          "Mathematics",
          "English",
          "Religious Education",
          "Environmental Activities",
          "Creative Activities",
        ]);
      } else if (level === "upper_primary") {
        addSubjects([
          "English",
          "Mathematics",
          "Kiswahili",
          "Religious Education",
          "Agriculture and Nutrition",
          "Social Studies",
          "Creative Arts",
          "Science and Technology",
        ]);
      } else if (level === "junior_secondary") {
        addSubjects([
          "Social Studies and Life Skills",
          "Agriculture and Home Science",
          "Integrated Science and Health Education",
          "Pre-Technical Studies",
          "Visual Arts",
          "Mathematics",
          "English",
          "Kiswahili",
          "Religious Education",
        ]);
      }

      function addSubjects(subjects) {
        subjects.forEach((subject) => {
          const option = document.createElement("option");
          option.value = subject;
          option.textContent = subject;
          subjectSelect.appendChild(option);
        });
      }
    });
  }

  // Dynamic stream loading based on grade
  const gradeSelect = document.getElementById("grade");
  if (gradeSelect) {
    gradeSelect.addEventListener("change", function () {
      const streamSelect = document.getElementById("stream");
      const grade = this.value;

      // Clear existing options
      streamSelect.innerHTML = '<option value="">Select Stream</option>';

      if (grade) {
        const streams = ["B", "G", "Y"];
        streams.forEach((stream) => {
          const option = document.createElement("option");
          option.value = `${grade}${stream}`;
          option.textContent = `${grade}${stream}`;
          streamSelect.appendChild(option);
        });
      }
    });
  }

  // Initialize global functions for form updates
  function initGlobalFormFunctions() {
    console.log("\n=== INITIALIZING GLOBAL FORM FUNCTIONS ===");

    window.updateSubjects = function () {
      console.log("\n=== UPDATING SUBJECTS ===");
      const educationLevelSelect = document.getElementById("education_level");
      const subjectSelect = document.getElementById("subject");

      if (!educationLevelSelect || !subjectSelect) {
        console.error("Required select elements not found");
        return;
      }

      const selectedEducationLevel = educationLevelSelect.value;
      console.log(`Education level changed to: ${selectedEducationLevel}`);

      subjectSelect.innerHTML = '<option value="">Select Subject</option>';
      const formGroup = subjectSelect.closest(".form-group");

      if (selectedEducationLevel) {
        let subjects = [];
        switch (selectedEducationLevel) {
          case "lower_primary":
            subjects = [
              "Indigenous Language",
              "Kiswahili",
              "Mathematics",
              "English",
              "Religious Education",
              "Environmental Activities",
              "Creative Activities",
            ];
            break;
          case "upper_primary":
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
            break;
          case "junior_secondary":
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
            break;
        }

        console.log(
          `Populating subjects for ${selectedEducationLevel}:`,
          subjects
        );
        subjects.forEach((subject) => {
          const option = document.createElement("option");
          option.value = subject;
          option.textContent = subject;
          subjectSelect.appendChild(option);
        });

        formGroup.classList.add("success");
        formGroup.classList.remove("error");
      } else {
        console.log("No education level selected - clearing subjects");
        formGroup.classList.remove("success");
      }
    };

    window.onGradeChange = function () {
      console.log("\n=== GRADE CHANGE DETECTED ===");
      const gradeSelect = document.getElementById("grade");
      const streamSelect = document.getElementById("stream");

      if (!gradeSelect || !streamSelect) {
        console.error("Grade or stream select elements not found");
        return;
      }

      const selectedGrade = gradeSelect.value;
      console.log(`Grade changed to: ${selectedGrade}`);

      streamSelect.innerHTML = '<option value="">Select Stream</option>';
      const formGroup = streamSelect.closest(".form-group");

      if (selectedGrade) {
        const streams = ["B", "G", "Y"];
        console.log(`Populating streams for grade ${selectedGrade}:`, streams);

        streams.forEach((stream) => {
          const option = document.createElement("option");
          option.value = `${selectedGrade}${stream}`;
          option.textContent = `${selectedGrade}${stream}`;
          streamSelect.appendChild(option);
        });

        formGroup.classList.add("success");
        formGroup.classList.remove("error");
      } else {
        console.log("No grade selected - clearing streams");
        formGroup.classList.remove("success");
      }
    };

    // Initialize event listeners
    if (gradeSelect) {
      console.log("Adding change listener to grade select");
      gradeSelect.addEventListener("change", window.onGradeChange);
    }

    if (educationLevelSelect) {
      console.log("Adding change listener to education level select");
      educationLevelSelect.addEventListener("change", window.updateSubjects);
    }

    // Run initial updates if values are already selected
    if (educationLevelSelect && educationLevelSelect.value) {
      console.log("Initial education level value detected - updating subjects");
      window.updateSubjects();
    }

    if (gradeSelect && gradeSelect.value) {
      console.log("Initial grade value detected - updating streams");
      window.onGradeChange();
    }

    console.log("Global form functions initialized successfully");
  }

  // Debugging helper function
  function logFormState() {
    console.log("\n=== CURRENT FORM STATE ===");
    console.log(
      "Education Level:",
      document.getElementById("education_level").value
    );
    console.log("Subject:", document.getElementById("subject").value);
    console.log("Grade:", document.getElementById("grade").value);
    console.log("Stream:", document.getElementById("stream").value);
    console.log("Term:", document.getElementById("term").value);
    console.log(
      "Assessment Type:",
      document.getElementById("assessment_type").value
    );
    console.log("Total Marks:", document.getElementById("total_marks").value);
  }

  // Add this to debug form state at any time
  window.logFormState = logFormState;

  // Initialize global functions for form updates
  initGlobalFormFunctions();
});
