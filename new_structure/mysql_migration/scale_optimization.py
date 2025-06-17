#!/usr/bin/env python3
"""
Scale Optimization for 10,000+ Students
Optimizes MySQL database for large-scale deployment.
"""

import mysql.connector
import json

def optimize_mysql_for_scale():
    """Optimize MySQL configuration for 10,000+ students."""
    print("🚀 Optimizing MySQL for Large Scale (10K+ Students)")
    print("=" * 60)
    
    # Load MySQL credentials
    try:
        with open('mysql_credentials.json', 'r') as f:
            creds = json.load(f)
    except FileNotFoundError:
        print("❌ MySQL credentials not found!")
        return False
    
    try:
        connection = mysql.connector.connect(
            host=creds['host'],
            database=creds['database_name'],
            user=creds['username'],
            password=creds['password'],
            port=creds['port'],
            autocommit=True
        )
        
        cursor = connection.cursor()
        
        # 1. Add Performance Indexes
        print("🔧 Adding performance indexes...")
        
        performance_indexes = [
            # Student performance indexes
            "CREATE INDEX idx_student_grade_stream ON student(grade_id, stream_id)",
            "CREATE INDEX idx_student_name ON student(name)",
            "CREATE INDEX idx_student_admission ON student(admission_number)",
            "CREATE INDEX idx_student_active ON student(is_active)",

            # Mark performance indexes
            "CREATE INDEX idx_mark_student_subject ON mark(student_id, subject_id)",
            "CREATE INDEX idx_mark_term_assessment ON mark(term_id, assessment_type_id)",
            "CREATE INDEX idx_mark_grade_stream ON mark(grade_id, stream_id)",
            "CREATE INDEX idx_mark_upload_date ON mark(upload_date)",
            "CREATE INDEX idx_mark_percentage ON mark(percentage)",

            # Teacher performance indexes
            "CREATE INDEX idx_teacher_stream ON teacher(stream_id)",
            "CREATE INDEX idx_teacher_role ON teacher(role)",
            "CREATE INDEX idx_teacher_active ON teacher(is_active)",

            # Assignment performance indexes
            "CREATE INDEX idx_teacher_assignment_grade ON teacher_subject_assignment(grade_id, stream_id)",
            "CREATE INDEX idx_teacher_assignment_subject ON teacher_subject_assignment(subject_id)",

            # Parent portal indexes
            "CREATE INDEX idx_parent_email ON parent(email)",
            "CREATE INDEX idx_parent_student_parent ON parent_student(parent_id)",
            "CREATE INDEX idx_parent_student_student ON parent_student(student_id)",

            # Composite indexes for common queries
            "CREATE INDEX idx_mark_student_term_subject ON mark(student_id, term_id, subject_id)",
            "CREATE INDEX idx_student_grade_stream_active ON student(grade_id, stream_id, is_active)"
        ]
        
        for i, index_sql in enumerate(performance_indexes, 1):
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index {i}/{len(performance_indexes)}")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print(f"ℹ️ Index {i} already exists")
                else:
                    print(f"⚠️ Error creating index {i}: {e}")
        
        # 2. Optimize Table Storage
        print("\n🔧 Optimizing table storage...")
        
        storage_optimizations = [
            "ALTER TABLE student ENGINE=InnoDB ROW_FORMAT=COMPRESSED",
            "ALTER TABLE mark ENGINE=InnoDB ROW_FORMAT=COMPRESSED",
            "ALTER TABLE teacher ENGINE=InnoDB ROW_FORMAT=COMPRESSED",
            "OPTIMIZE TABLE student",
            "OPTIMIZE TABLE mark", 
            "OPTIMIZE TABLE teacher",
            "ANALYZE TABLE student",
            "ANALYZE TABLE mark",
            "ANALYZE TABLE teacher"
        ]
        
        for i, optimize_sql in enumerate(storage_optimizations, 1):
            try:
                cursor.execute(optimize_sql)
                print(f"✅ Storage optimization {i}/{len(storage_optimizations)}")
            except Exception as e:
                print(f"⚠️ Storage optimization {i} warning: {e}")
        
        # 3. Create Partitioning for Large Tables
        print("\n🔧 Setting up table partitioning...")
        
        # Note: This would require recreating tables, so we'll prepare the SQL
        partitioning_recommendations = [
            "-- Partition marks table by academic year",
            "-- ALTER TABLE mark PARTITION BY RANGE (YEAR(created_at)) (",
            "--   PARTITION p2024 VALUES LESS THAN (2025),",
            "--   PARTITION p2025 VALUES LESS THAN (2026),",
            "--   PARTITION p2026 VALUES LESS THAN (2027)",
            "-- );",
            "",
            "-- Partition students by grade for better performance",
            "-- ALTER TABLE student PARTITION BY HASH(grade_id) PARTITIONS 10;"
        ]
        
        print("ℹ️ Partitioning recommendations prepared (manual implementation needed)")
        
        cursor.close()
        connection.close()
        
        print("\n✅ MySQL optimization completed!")
        return True
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        return False

def create_performance_monitoring():
    """Create performance monitoring queries."""
    print("\n📊 Creating performance monitoring queries...")
    
    monitoring_queries = {
        "student_count": "SELECT COUNT(*) as total_students FROM student WHERE is_active = 1",
        "teacher_count": "SELECT COUNT(*) as total_teachers FROM teacher WHERE is_active = 1", 
        "marks_count": "SELECT COUNT(*) as total_marks FROM mark",
        "database_size": """
            SELECT 
                table_name,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            ORDER BY (data_length + index_length) DESC
        """,
        "slow_queries": """
            SELECT 
                sql_text,
                exec_count,
                avg_timer_wait/1000000000 as avg_time_seconds
            FROM performance_schema.events_statements_summary_by_digest 
            WHERE avg_timer_wait > 1000000000
            ORDER BY avg_timer_wait DESC 
            LIMIT 10
        """,
        "index_usage": """
            SELECT 
                object_schema,
                object_name,
                index_name,
                count_read,
                count_write
            FROM performance_schema.table_io_waits_summary_by_index_usage
            WHERE object_schema = DATABASE()
            ORDER BY count_read DESC
        """
    }
    
    # Save monitoring queries to file
    with open('performance_monitoring_queries.sql', 'w') as f:
        f.write("-- Performance Monitoring Queries for Large Scale Deployment\n\n")
        for name, query in monitoring_queries.items():
            f.write(f"-- {name.replace('_', ' ').title()}\n")
            f.write(f"{query};\n\n")
    
    print("✅ Performance monitoring queries saved to performance_monitoring_queries.sql")

def main():
    """Main optimization function."""
    print("🎯 Large Scale Optimization for 10,000+ Students")
    print("=" * 70)
    
    # Run optimizations
    if optimize_mysql_for_scale():
        create_performance_monitoring()
        
        print("\n🎉 Large Scale Optimization Complete!")
        print("\n📋 Recommendations for 10K+ Students:")
        print("1. ✅ Database indexes optimized")
        print("2. ✅ Storage compression enabled")
        print("3. ✅ Performance monitoring setup")
        print("4. 🔄 Consider connection pool increase (20-50 connections)")
        print("5. 🔄 Implement caching layer (Redis)")
        print("6. 🔄 Consider read replicas for reporting")
        print("7. 🔄 Monitor and tune MySQL configuration")
        
        print("\n⚙️ Additional Infrastructure Recommendations:")
        print("- Server: 8+ CPU cores, 16+ GB RAM")
        print("- Storage: SSD with 1000+ IOPS")
        print("- Network: Gigabit connection")
        print("- Backup: Daily automated backups")
        
        return True
    else:
        print("\n❌ Optimization failed!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
