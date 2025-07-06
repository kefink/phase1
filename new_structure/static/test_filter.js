// Test script to verify educational level filtering is working
// Add this to browser console to test the filtering function

console.log("🧪 Testing Educational Level Filtering");

// Check if the required elements exist
const eduLevelSelect = document.getElementById('filter_educational_level');
const gradeSelect = document.getElementById('filter_grade');
const streamSelect = document.getElementById('filter_stream');

console.log("📋 Elements found:");
console.log("- Educational Level dropdown:", eduLevelSelect ? "✅" : "❌");
console.log("- Grade dropdown:", gradeSelect ? "✅" : "❌");
console.log("- Stream dropdown:", streamSelect ? "✅" : "❌");

// Check if the data variables exist
console.log("\n📊 Data variables:");
console.log("- allGrades:", typeof allGrades !== 'undefined' ? allGrades : "❌ Not found");
console.log("- educationalLevelMapping:", typeof educationalLevelMapping !== 'undefined' ? educationalLevelMapping : "❌ Not found");

// Check if the function exists
console.log("\n🔧 Functions:");
console.log("- updateFilterGrades:", typeof updateFilterGrades !== 'undefined' ? "✅" : "❌ Not found");

// Test the function manually
if (typeof updateFilterGrades !== 'undefined' && eduLevelSelect) {
    console.log("\n🧪 Testing function manually:");
    
    // Set to junior secondary
    eduLevelSelect.value = 'junior_secondary';
    console.log("Set educational level to: junior_secondary");
    
    // Call the function
    updateFilterGrades();
    
    // Check results
    console.log("Grade options after update:");
    for (let i = 0; i < gradeSelect.options.length; i++) {
        const option = gradeSelect.options[i];
        console.log(`  - ${option.textContent} (value: ${option.value})`);
    }
} else {
    console.log("❌ Cannot test - function or elements missing");
}

// Test event handler
if (eduLevelSelect) {
    console.log("\n🎯 Testing event handler:");
    const event = new Event('change');
    eduLevelSelect.dispatchEvent(event);
    console.log("Dispatched change event");
}
