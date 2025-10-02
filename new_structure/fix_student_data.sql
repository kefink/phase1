-- MANUAL SQL FIX FOR STUDENT DATA INTEGRITY ISSUES
-- Run these SQL commands to fix the grade/stream assignment problems

-- Step 1: Check current student data issues
SELECT 
    s.id,
    s.name,
    s.admission_number,
    s.grade_id,
    s.stream_id,
    g.name as grade_name,
    g.education_level,
    st.name as stream_name,
    st.grade_id as stream_grade_id
FROM students s
LEFT JOIN grades g ON s.grade_id = g.id
LEFT JOIN streams st ON s.stream_id = st.id
WHERE s.grade_id IS NULL AND s.stream_id IS NOT NULL
   OR (s.grade_id IS NOT NULL AND s.stream_id IS NOT NULL AND g.id != st.grade_id)
ORDER BY s.name;

-- Step 2: Fix students with stream but no grade
-- This will set the grade_id based on the stream's grade_id
UPDATE students 
SET grade_id = (
    SELECT grade_id 
    FROM streams 
    WHERE streams.id = students.stream_id
)
WHERE grade_id IS NULL 
  AND stream_id IS NOT NULL
  AND EXISTS (
    SELECT 1 FROM streams WHERE streams.id = students.stream_id
  );

-- Step 3: Fix students with invalid stream references (streams that don't exist)
UPDATE students 
SET stream_id = NULL
WHERE stream_id IS NOT NULL 
  AND NOT EXISTS (
    SELECT 1 FROM streams WHERE streams.id = students.stream_id
  );

-- Step 4: Verify the fixes
SELECT 
    s.id,
    s.name,
    s.admission_number,
    g.name as grade_name,
    g.education_level,
    st.name as stream_name
FROM students s
LEFT JOIN grades g ON s.grade_id = g.id
LEFT JOIN streams st ON s.stream_id = st.id
ORDER BY g.name, st.name, s.name;

-- Step 5: Show any remaining unassigned students
SELECT 
    s.id,
    s.name,
    s.admission_number,
    'No Grade/Stream Assigned' as issue
FROM students s
WHERE s.grade_id IS NULL AND s.stream_id IS NULL;