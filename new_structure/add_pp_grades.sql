-- Add missing PP1 and PP2 grades to the database
-- This script should be run after checking current grades

-- Insert PP1 grade if it doesn't exist
INSERT IGNORE INTO grade (name, education_level) VALUES ('PP1', 'lower_primary');
INSERT IGNORE INTO grade (name, education_level) VALUES ('PP2', 'lower_primary');

-- Get the grade IDs for PP1 and PP2 
-- Then insert streams for each grade
INSERT IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'PP1';

INSERT IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'PP1';

INSERT IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'PP2';

INSERT IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'PP2';

-- Verify the results
SELECT 'Current grades after update:' as status;
SELECT name, education_level FROM grade ORDER BY 
  CASE 
    WHEN name = 'PP1' THEN 0
    WHEN name = 'PP2' THEN 1
    WHEN name = 'Grade 1' THEN 2
    WHEN name = 'Grade 2' THEN 3
    WHEN name = 'Grade 3' THEN 4
    WHEN name = 'Grade 4' THEN 5
    WHEN name = 'Grade 5' THEN 6
    WHEN name = 'Grade 6' THEN 7
    WHEN name = 'Grade 7' THEN 8
    WHEN name = 'Grade 8' THEN 9
    WHEN name = 'Grade 9' THEN 10
    ELSE 99
  END;