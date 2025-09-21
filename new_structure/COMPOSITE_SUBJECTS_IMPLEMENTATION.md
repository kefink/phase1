# Composite Subjects Implementation

## Overview

This implementation adds support for flexible case-insensitive subject naming and proper composite subject display in class reports. The system now automatically groups related subjects (English Grammar + English Composition = English, Kiswahili Lugha + Kiswahili Insha = Kiswahili) and displays them with individual component scores and combined totals.

## Key Features

### 1. Case-Insensitive Subject Matching

- The system now handles subjects regardless of capitalization
- Works with: "ENGLISH GRAMMAR", "English Grammar", "english grammar", etc.
- Flexible matching for different school naming conventions

### 2. Composite Subject Grouping

- **English**: Automatically groups "English Grammar" and "English Composition"
  - Displays as: GRAM | COMP | TOTAL
- **Kiswahili**: Automatically groups "Kiswahili Lugha" and "Kiswahili Insha"
  - Displays as: LUGHA | INSHA | TOTAL
- Other subjects display normally as standalone subjects

### 3. Automatic Detection

- The system automatically detects which subjects belong to composite groups
- No manual configuration needed - works based on subject names
- Handles partial matches (e.g., "Grammar" will be grouped under English)

## Implementation Details

### Files Modified

1. **`services/class_report_builder.py`**:

   - Added `normalize_subject_name()` function for case-insensitive matching
   - Added composite grouping logic with flexible component detection
   - Modified marks processing to handle composite totals
   - Updated context to include `composite_structure` for template use

2. **`templates/preview_class_report.html`**:

   - Updated table headers to use dynamic composite structure
   - Modified student marks display to show individual components + totals
   - Updated subject averages to handle composite subjects

3. **`test_composite_subjects.py`** (new):
   - Test script to verify case-insensitive matching works correctly
   - Helper to create test subjects with different case patterns

### Subject Detection Logic

The system looks for these patterns in subject names:

**English Group**:

- "english grammar", "grammar", "english composition", "composition"

**Kiswahili Group**:

- "kiswahili lugha", "lugha", "kiswahili insha", "insha"

All matching is case-insensitive, so "ENGLISH GRAMMAR", "English Grammar", and "english grammar" all work the same way.

## Usage

### For Schools Using Independent Subjects

If your school uploads English Grammar and English Composition as separate subjects:

1. The system will automatically group them under "ENGLISH"
2. Both component marks will be displayed
3. A combined total will be calculated and shown
4. Same applies to Kiswahili subjects

### For Mixed Case Subject Names

The system handles any capitalization:

- "MATHEMATICS" ✓
- "Mathematics" ✓
- "mathematics" ✓
- "ENGLISH GRAMMAR" ✓
- "English Grammar" ✓
- "english grammar" ✓

### Class Report Display

When viewing class reports, you'll see:

```
| S/N | STUDENT NAME | ENGLISH        | MATHEMATICS | KISWAHILI      | TOTAL | AVG % | GRD | RANK |
|     |              | GRAM|COMP|TOTAL|             | LUGHA|INSHA|TOTAL|       |       |     |      |
| 1   | JOHN DOE     |  88 | 84 |  86 |     86      |   80 |  96 |  88 |  260  |  86.7 | EE2 |   1  |
```

## Testing

Run the test script to verify the implementation:

```bash
python test_composite_subjects.py
```

This will:

1. Test the case-insensitive matching logic
2. Show how different subject name variations are grouped
3. Optionally create test subjects in your database

## Troubleshooting

### If Composite Subjects Don't Appear

1. Check that both component subjects exist (e.g., both "English Grammar" AND "English Composition")
2. Verify the subject names contain the expected keywords
3. Check the education level matches between components

### If Case Matching Doesn't Work

1. The system automatically handles all case variations
2. If issues persist, check the `normalize_subject_name()` function in `class_report_builder.py`

## Compatibility

This implementation is backward compatible:

- Existing standalone subjects continue to work normally
- Schools not using composite subjects see no changes
- The template gracefully handles both composite and standalone subjects
- No database schema changes required
