-- Create missing tables for Hillview School Management System

-- Create subject table
CREATE TABLE IF NOT EXISTS subject (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    education_level TEXT NOT NULL,
    is_standard BOOLEAN DEFAULT 1,
    is_composite BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create grade table
CREATE TABLE IF NOT EXISTS grade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    education_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create stream table
CREATE TABLE IF NOT EXISTS stream (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    grade_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grade_id) REFERENCES grade (id)
);

-- Create student table
CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    admission_number TEXT UNIQUE,
    grade_id INTEGER NOT NULL,
    stream_id INTEGER NOT NULL,
    date_of_birth DATE,
    gender TEXT,
    parent_contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grade_id) REFERENCES grade (id),
    FOREIGN KEY (stream_id) REFERENCES stream (id)
);

-- Create term table
CREATE TABLE IF NOT EXISTS term (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    academic_year TEXT,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create assessment_type table
CREATE TABLE IF NOT EXISTS assessment_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create marks table
CREATE TABLE IF NOT EXISTS marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    assessment_type_id INTEGER NOT NULL,
    raw_mark REAL,
    percentage REAL,
    grade TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student (id),
    FOREIGN KEY (subject_id) REFERENCES subject (id),
    FOREIGN KEY (term_id) REFERENCES term (id),
    FOREIGN KEY (assessment_type_id) REFERENCES assessment_type (id)
);

-- Create teacher_subjects table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS teacher_subjects (
    teacher_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    PRIMARY KEY (teacher_id, subject_id),
    FOREIGN KEY (teacher_id) REFERENCES teacher (id),
    FOREIGN KEY (subject_id) REFERENCES subject (id)
);

-- Insert default grades
INSERT OR IGNORE INTO grade (name, education_level) VALUES
('Grade 1', 'lower_primary'),
('Grade 2', 'lower_primary'),
('Grade 3', 'lower_primary'),
('Grade 4', 'upper_primary'),
('Grade 5', 'upper_primary'),
('Grade 6', 'upper_primary'),
('Grade 7', 'junior_secondary'),
('Grade 8', 'junior_secondary'),
('Grade 9', 'junior_secondary');

-- Insert default streams for each grade
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 1';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 1';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 2';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 2';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 3';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 3';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 4';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 4';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 5';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 5';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 6';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 6';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 7';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 7';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 8';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 8';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'A', id FROM grade WHERE name = 'Grade 9';
INSERT OR IGNORE INTO stream (name, grade_id) 
SELECT 'B', id FROM grade WHERE name = 'Grade 9';

-- Insert default subjects
INSERT OR IGNORE INTO subject (name, education_level, is_standard, is_composite) VALUES
-- Lower Primary
('English', 'lower_primary', 1, 0),
('Kiswahili', 'lower_primary', 1, 0),
('Mathematics', 'lower_primary', 1, 0),
('Environmental Activities', 'lower_primary', 1, 0),
('Creative Arts', 'lower_primary', 1, 0),
('Physical Education', 'lower_primary', 1, 0),

-- Upper Primary
('English', 'upper_primary', 1, 0),
('Kiswahili', 'upper_primary', 1, 0),
('Mathematics', 'upper_primary', 1, 0),
('Science', 'upper_primary', 1, 0),
('Social Studies', 'upper_primary', 1, 0),
('Creative Arts', 'upper_primary', 1, 0),
('Physical Education', 'upper_primary', 1, 0),

-- Junior Secondary
('English', 'junior_secondary', 1, 0),
('Kiswahili', 'junior_secondary', 1, 0),
('Mathematics', 'junior_secondary', 1, 0),
('Biology', 'junior_secondary', 1, 0),
('Chemistry', 'junior_secondary', 1, 0),
('Physics', 'junior_secondary', 1, 0),
('Geography', 'junior_secondary', 1, 0),
('History', 'junior_secondary', 1, 0),
('Religious Education', 'junior_secondary', 1, 0),
('Physical Education', 'junior_secondary', 1, 0);

-- Insert default terms
INSERT OR IGNORE INTO term (name, academic_year, start_date, end_date, is_current) VALUES
('Term 1', '2024', '2024-01-15', '2024-04-12', 1),
('Term 2', '2024', '2024-05-06', '2024-08-02', 0),
('Term 3', '2024', '2024-08-26', '2024-11-22', 0);

-- Insert default assessment types
INSERT OR IGNORE INTO assessment_type (name, description, weight) VALUES
('End of Term Exam', 'Final examination for the term', 1.0),
('Mid Term Test', 'Mid-term assessment', 0.5),
('Continuous Assessment', 'Ongoing classroom assessment', 0.3);

-- Update school_configuration if it doesn't have enhanced columns
ALTER TABLE school_configuration ADD COLUMN headteacher_id INTEGER;
ALTER TABLE school_configuration ADD COLUMN deputy_headteacher_id INTEGER;

-- Insert default school configuration if it doesn't exist
INSERT OR IGNORE INTO school_configuration (
    id, school_name, school_motto, current_academic_year, current_term,
    headteacher_name, deputy_headteacher_name
) VALUES (
    1, 'Hillview School', 'Excellence in Education', '2024', 'Term 1',
    'Head Teacher', 'Deputy Head Teacher'
);
