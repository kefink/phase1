"""
Script to insert sample data into the database.
"""
import os
import sqlite3

def insert_sample_data():
    """Insert sample data into the database."""
    # Path to the database
    db_path = os.path.join('new_structure', 'hillview.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert sample subjects if they don't exist
    print("Inserting sample subjects...")
    
    # Check if subjects already exist
    cursor.execute("SELECT COUNT(*) FROM subject")
    subject_count = cursor.fetchone()[0]
    
    if subject_count == 0:
        # Junior secondary subjects
        junior_secondary_subjects = [
            ("ENGLISH", "junior_secondary"),
            ("KISWAHILI", "junior_secondary"),
            ("MATHEMATICS", "junior_secondary"),
            ("INTEGRATED SCIENCE", "junior_secondary"),
            ("HEALTH EDUCATION", "junior_secondary"),
            ("PRE-TECHNICAL STUDIES", "junior_secondary"),
            ("SOCIAL STUDIES", "junior_secondary"),
            ("RELIGIOUS EDUCATION", "junior_secondary"),
            ("BUSINESS STUDIES", "junior_secondary")
        ]
        
        cursor.executemany(
            "INSERT INTO subject (name, education_level) VALUES (?, ?)",
            junior_secondary_subjects
        )
        
        # Upper primary subjects
        upper_primary_subjects = [
            ("ENGLISH", "upper_primary"),
            ("KISWAHILI", "upper_primary"),
            ("MATHEMATICS", "upper_primary"),
            ("SCIENCE AND TECHNOLOGY", "upper_primary"),
            ("SOCIAL STUDIES", "upper_primary"),
            ("RELIGIOUS EDUCATION", "upper_primary"),
            ("CREATIVE ARTS", "upper_primary"),
            ("PHYSICAL AND HEALTH EDUCATION", "upper_primary"),
            ("AGRICULTURE", "upper_primary")
        ]
        
        cursor.executemany(
            "INSERT INTO subject (name, education_level) VALUES (?, ?)",
            upper_primary_subjects
        )
        
        # Lower primary subjects
        lower_primary_subjects = [
            ("LITERACY ACTIVITIES", "lower_primary"),
            ("KISWAHILI LANGUAGE ACTIVITIES", "lower_primary"),
            ("ENGLISH LANGUAGE ACTIVITIES", "lower_primary"),
            ("MATHEMATICAL ACTIVITIES", "lower_primary"),
            ("ENVIRONMENTAL ACTIVITIES", "lower_primary"),
            ("HYGIENE AND NUTRITION ACTIVITIES", "lower_primary"),
            ("RELIGIOUS EDUCATION ACTIVITIES", "lower_primary"),
            ("MOVEMENT AND CREATIVE ACTIVITIES", "lower_primary")
        ]
        
        cursor.executemany(
            "INSERT INTO subject (name, education_level) VALUES (?, ?)",
            lower_primary_subjects
        )
        
        print(f"Inserted {len(junior_secondary_subjects) + len(upper_primary_subjects) + len(lower_primary_subjects)} subjects")
    else:
        print(f"Found {subject_count} existing subjects, skipping insertion")
    
    # Insert sample grades if they don't exist
    print("\nInserting sample grades...")
    
    # Check if grades already exist
    cursor.execute("SELECT COUNT(*) FROM grade")
    grade_count = cursor.fetchone()[0]
    
    if grade_count == 0:
        grades = [
            ("Grade 1",),
            ("Grade 2",),
            ("Grade 3",),
            ("Grade 4",),
            ("Grade 5",),
            ("Grade 6",),
            ("Grade 7",),
            ("Grade 8",),
            ("Grade 9",)
        ]
        
        cursor.executemany(
            "INSERT INTO grade (level) VALUES (?)",
            grades
        )
        
        print(f"Inserted {len(grades)} grades")
    else:
        print(f"Found {grade_count} existing grades, skipping insertion")
    
    # Insert sample streams if they don't exist
    print("\nInserting sample streams...")
    
    # Check if streams already exist
    cursor.execute("SELECT COUNT(*) FROM stream")
    stream_count = cursor.fetchone()[0]
    
    if stream_count == 0:
        # Get grade IDs
        cursor.execute("SELECT id FROM grade")
        grade_ids = [row[0] for row in cursor.fetchall()]
        
        streams = []
        for grade_id in grade_ids:
            streams.extend([
                ("A", grade_id),
                ("B", grade_id),
                ("C", grade_id)
            ])
        
        cursor.executemany(
            "INSERT INTO stream (name, grade_id) VALUES (?, ?)",
            streams
        )
        
        print(f"Inserted {len(streams)} streams")
    else:
        print(f"Found {stream_count} existing streams, skipping insertion")
    
    # Commit changes
    conn.commit()
    
    # Close connection
    conn.close()
    
    print("\nSample data inserted successfully!")

if __name__ == "__main__":
    insert_sample_data()
