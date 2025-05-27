# Cross-Assessment Storage and Retrieval Guide

## How Assessment Marks Are Stored

### Database Structure

Assessment marks are stored in the `Mark` table with these key relationships:

```sql
Mark Table:
- id (Primary Key)
- student_id (Foreign Key → Student)
- subject_id (Foreign Key → Subject)  
- term_id (Foreign Key → Term)
- assessment_type_id (Foreign Key → AssessmentType)
- mark/raw_mark (The actual mark)
- percentage (Calculated percentage)
- total_marks (Maximum possible marks)
```

### Assessment Types

The system supports multiple assessment types per term:
- **Opener/Entrance** - Beginning of term assessment
- **Mid-term** - Middle of term assessment  
- **End-term** - End of term assessment

Each assessment type has its own `AssessmentType` record with a unique ID.

## How Marks Are Stored

### 1. When Teachers Upload Marks

When a teacher uploads marks for any assessment:

```python
# Example: Uploading opener exam marks
mark = Mark(
    student_id=student.id,
    subject_id=subject.id,
    term_id=term.id,
    assessment_type_id=opener_assessment_type.id,  # Specific to opener
    mark=85,
    percentage=85,
    total_marks=100
)
```

### 2. Separate Records for Each Assessment

Each assessment creates **separate records** in the database:

```
Student: John Doe, Subject: Mathematics, Term: Term 1

Record 1: assessment_type_id=1 (Opener), mark=80
Record 2: assessment_type_id=2 (Mid-term), mark=85  
Record 3: assessment_type_id=3 (End-term), mark=90
```

## How Cross-Assessment Comparison Works

### 1. Single Assessment Reports

For opener or mid-term reports, only the current assessment is shown:

```python
# Shows only opener marks
if assessment_type == 'opener':
    entrance_mark = current_mark
    mid_term_mark = 0
    end_term_mark = 0
```

### 2. End-Term Comparison Reports

For end-term reports, the system fetches marks from **all assessment types**:

```python
# Fetch marks from all assessments for comparison
if assessment_type == 'end_term':
    # Get all assessment types
    all_assessments = AssessmentType.query.all()
    
    # Fetch marks for each assessment type
    for assessment in all_assessments:
        mark_record = Mark.query.filter_by(
            student_id=student.id,
            subject_id=subject.id,
            term_id=term.id,
            assessment_type_id=assessment.id
        ).first()
        
        if mark_record:
            if assessment.name == 'opener':
                entrance_mark = mark_record.percentage
            elif assessment.name == 'mid_term':
                mid_term_mark = mark_record.percentage
            elif assessment.name == 'end_term':
                end_term_mark = mark_record.percentage
```

## Report Display Logic

### Individual Reports

**For Opener Exam:**
```
| Subjects | Opener | Subject Remarks |
| Math     | 80     | M.E            |
| English  | 75     | M.E            |
```

**For Mid-term Exam:**
```
| Subjects | Mid Term | Subject Remarks |
| Math     | 85       | E.E            |
| English  | 78       | M.E            |
```

**For End-term Exam (with comparison):**
```
| Subjects | Entrance | Mid Term | End Term | Avg. | Subject Remarks |
| Math     | 80       | 85       | 90       | 85   | E.E            |
| English  | 75       | 78       | 82       | 78   | M.E            |
```

## Data Flow Example

### Term 1 Assessment Cycle

1. **Week 2: Opener Exam**
   ```
   Teacher uploads opener marks → Stored with assessment_type_id=1
   Individual reports show only "Opener" column
   ```

2. **Week 6: Mid-term Exam**
   ```
   Teacher uploads mid-term marks → Stored with assessment_type_id=2
   Individual reports show only "Mid Term" column
   ```

3. **Week 12: End-term Exam**
   ```
   Teacher uploads end-term marks → Stored with assessment_type_id=3
   Individual reports show ALL columns for comparison:
   - Entrance (from assessment_type_id=1)
   - Mid Term (from assessment_type_id=2)  
   - End Term (from assessment_type_id=3)
   - Average (calculated from all three)
   ```

## Key Benefits

1. **Historical Data**: All assessment marks are preserved
2. **Progress Tracking**: Students can see improvement over time
3. **Flexible Reporting**: Different views for different assessment types
4. **Data Integrity**: Each assessment is stored independently
5. **Comparison Analysis**: End-term reports provide comprehensive view

## Implementation Notes

- Marks are stored as **percentages** for consistent comparison
- Missing assessments show as **0** or **"-"** in reports
- **Average calculation** only includes assessments with marks > 0
- **Composite subjects** (English/Kiswahili) work the same way
- **Component marks** are also stored separately for each assessment

This system ensures that when students reach end-term, they can see their complete academic journey for the term with all assessment comparisons in one place.
