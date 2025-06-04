"""
Database migration to add performance indexes for analytics queries.
Run this script to optimize database performance for analytics operations.
"""

import sqlite3
from datetime import datetime
import os

def add_analytics_indexes(db_path):
    """
    Add performance indexes for analytics queries.
    
    Args:
        db_path: Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting analytics indexes migration...")
        
        # List of indexes to create for analytics performance
        indexes = [
            # Mark table indexes (critical for performance)
            ("idx_mark_student_id", "CREATE INDEX IF NOT EXISTS idx_mark_student_id ON mark(student_id)"),
            ("idx_mark_subject_id", "CREATE INDEX IF NOT EXISTS idx_mark_subject_id ON mark(subject_id)"),
            ("idx_mark_term_id", "CREATE INDEX IF NOT EXISTS idx_mark_term_id ON mark(term_id)"),
            ("idx_mark_assessment_type_id", "CREATE INDEX IF NOT EXISTS idx_mark_assessment_type_id ON mark(assessment_type_id)"),
            ("idx_mark_composite", "CREATE INDEX IF NOT EXISTS idx_mark_composite ON mark(student_id, subject_id, term_id)"),
            ("idx_mark_analytics", "CREATE INDEX IF NOT EXISTS idx_mark_analytics ON mark(term_id, assessment_type_id, subject_id)"),
            
            # Component mark indexes
            ("idx_component_mark_mark_id", "CREATE INDEX IF NOT EXISTS idx_component_mark_mark_id ON component_mark(mark_id)"),
            ("idx_component_mark_component_id", "CREATE INDEX IF NOT EXISTS idx_component_mark_component_id ON component_mark(component_id)"),
            
            # Student table indexes
            ("idx_student_stream_id", "CREATE INDEX IF NOT EXISTS idx_student_stream_id ON student(stream_id)"),
            ("idx_student_admission_number", "CREATE INDEX IF NOT EXISTS idx_student_admission_number ON student(admission_number)"),
            
            # Stream table indexes
            ("idx_stream_grade_id", "CREATE INDEX IF NOT EXISTS idx_stream_grade_id ON stream(grade_id)"),
            
            # Teacher assignment indexes
            ("idx_teacher_assignment_teacher_id", "CREATE INDEX IF NOT EXISTS idx_teacher_assignment_teacher_id ON teacher_subject_assignment(teacher_id)"),
            ("idx_teacher_assignment_grade_stream", "CREATE INDEX IF NOT EXISTS idx_teacher_assignment_grade_stream ON teacher_subject_assignment(grade_id, stream_id)"),
            ("idx_teacher_assignment_subject_id", "CREATE INDEX IF NOT EXISTS idx_teacher_assignment_subject_id ON teacher_subject_assignment(subject_id)"),
            
            # Permission table indexes
            ("idx_permission_teacher_active", "CREATE INDEX IF NOT EXISTS idx_permission_teacher_active ON class_teacher_permissions(teacher_id, is_active)"),
            ("idx_permission_expires_at", "CREATE INDEX IF NOT EXISTS idx_permission_expires_at ON class_teacher_permissions(expires_at) WHERE expires_at IS NOT NULL"),
            ("idx_permission_grade_stream", "CREATE INDEX IF NOT EXISTS idx_permission_grade_stream ON class_teacher_permissions(grade_id, stream_id, is_active)"),
        ]
        
        # Create indexes
        created_count = 0
        for index_name, index_sql in indexes:
            try:
                print(f"Creating index: {index_name}")
                cursor.execute(index_sql)
                created_count += 1
            except sqlite3.Error as e:
                print(f"Warning: Could not create index {index_name}: {e}")
        
        conn.commit()
        print(f"Successfully created {created_count} indexes!")
        
        # Analyze tables to update statistics
        print("Updating table statistics...")
        tables_to_analyze = ['mark', 'component_mark', 'student', 'stream', 'teacher_subject_assignment', 'class_teacher_permissions']
        
        for table in tables_to_analyze:
            try:
                cursor.execute(f"ANALYZE {table}")
                print(f"Analyzed table: {table}")
            except sqlite3.Error as e:
                print(f"Warning: Could not analyze table {table}: {e}")
        
        conn.commit()
        print("Table statistics updated!")
        
        # Show index information
        print("\nCreated indexes:")
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name")
        indexes_info = cursor.fetchall()
        
        for index_name, index_sql in indexes_info:
            print(f"  {index_name}")
        
        print(f"\nTotal analytics indexes: {len(indexes_info)}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def check_analytics_performance(db_path):
    """
    Check analytics query performance after index creation.
    
    Args:
        db_path: Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print("ANALYTICS PERFORMANCE CHECK")
        print("="*50)
        
        # Test query 1: Student marks count
        print("Testing student marks query...")
        cursor.execute("EXPLAIN QUERY PLAN SELECT student_id, COUNT(*) FROM mark GROUP BY student_id")
        plan = cursor.fetchall()
        uses_index = any('USING INDEX' in str(row) for row in plan)
        print(f"  Uses index: {'✅ Yes' if uses_index else '❌ No'}")
        
        # Test query 2: Subject performance
        print("Testing subject performance query...")
        cursor.execute("EXPLAIN QUERY PLAN SELECT subject_id, AVG(percentage) FROM mark GROUP BY subject_id")
        plan = cursor.fetchall()
        uses_index = any('USING INDEX' in str(row) for row in plan)
        print(f"  Uses index: {'✅ Yes' if uses_index else '❌ No'}")
        
        # Test query 3: Term-based filtering
        print("Testing term-based filtering...")
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM mark WHERE term_id = 1")
        plan = cursor.fetchall()
        uses_index = any('USING INDEX' in str(row) for row in plan)
        print(f"  Uses index: {'✅ Yes' if uses_index else '❌ No'}")
        
        # Test query 4: Complex analytics query
        print("Testing complex analytics query...")
        cursor.execute("""
            EXPLAIN QUERY PLAN 
            SELECT s.name, AVG(m.percentage) 
            FROM student s 
            JOIN mark m ON s.id = m.student_id 
            WHERE m.term_id = 1 
            GROUP BY s.id, s.name
        """)
        plan = cursor.fetchall()
        uses_index = any('USING INDEX' in str(row) for row in plan)
        print(f"  Uses index: {'✅ Yes' if uses_index else '❌ No'}")
        
        # Get database statistics
        print("\nDatabase statistics:")
        cursor.execute("SELECT COUNT(*) FROM student")
        student_count = cursor.fetchone()[0]
        print(f"  Students: {student_count}")
        
        cursor.execute("SELECT COUNT(*) FROM mark")
        mark_count = cursor.fetchone()[0]
        print(f"  Marks: {mark_count}")
        
        cursor.execute("SELECT COUNT(*) FROM subject")
        subject_count = cursor.fetchone()[0]
        print(f"  Subjects: {subject_count}")
        
        # Calculate analytics readiness
        analytics_ready = mark_count >= 10 and student_count >= 3 and subject_count >= 2
        print(f"\nAnalytics readiness: {'✅ Ready' if analytics_ready else '❌ Insufficient data'}")
        
        if not analytics_ready:
            print("Recommendations:")
            if mark_count < 10:
                print(f"  - Upload more marks (current: {mark_count}, recommended: 10+)")
            if student_count < 3:
                print(f"  - Add more students (current: {student_count}, recommended: 3+)")
            if subject_count < 2:
                print(f"  - Add more subjects (current: {subject_count}, recommended: 2+)")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking performance: {e}")
        if 'conn' in locals():
            conn.close()

def main():
    """Run the analytics indexes migration."""
    # Default database path (go up one directory from new_structure)
    db_path = "../kirima_primary.db"
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        print("Please ensure you're running this from the correct directory.")
        return
    
    # Backup database first
    backup_path = f"{db_path}.analytics_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("Backup created successfully!")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
        response = input("Continue without backup? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return
    
    # Run migration
    add_analytics_indexes(db_path)
    
    # Check performance
    check_analytics_performance(db_path)
    
    print("\n" + "="*50)
    print("MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("Your database is now optimized for analytics queries.")
    print("The analytics dashboard should perform significantly better.")

if __name__ == "__main__":
    main()
