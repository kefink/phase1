#!/usr/bin/env python3
"""
Simple test to check if the enhanced top performers fix works
"""
import sqlite3
import sys
import os

def test_database_query():
    """Test the database query that was failing"""
    print("🧪 Testing Database Query for Top Performers...")
    
    try:
        # Connect to database
        db_path = os.path.join(os.path.dirname(__file__), 'kirima_primary.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 Checking database structure...")
        
        # Check if we have the required tables and data
        cursor.execute("SELECT COUNT(*) FROM student")
        student_count = cursor.fetchone()[0]
        print(f"✅ Students: {student_count}")
        
        cursor.execute("SELECT COUNT(*) FROM mark")
        mark_count = cursor.fetchone()[0]
        print(f"✅ Marks: {mark_count}")
        
        # Test the query that was causing issues
        print("🚀 Testing top performers query...")
        
        query = """
        SELECT 
            s.id,
            s.name,
            s.admission_number,
            g.name as grade_name,
            st.name as stream_name,
            AVG(m.percentage) as average_percentage,
            COUNT(m.id) as total_marks,
            MIN(m.percentage) as min_percentage,
            MAX(m.percentage) as max_percentage
        FROM student s
        JOIN mark m ON s.id = m.student_id
        JOIN grade g ON s.grade_id = g.id
        LEFT JOIN stream st ON s.stream_id = st.id
        GROUP BY s.id, s.name, s.admission_number, g.name, st.name
        HAVING COUNT(m.id) >= 3
        ORDER BY AVG(m.percentage) DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"📈 Found {len(results)} top performers")
        
        if results:
            print("🏆 Top 5 performers:")
            for i, result in enumerate(results[:5]):
                student_id, name, admission_number, grade_name, stream_name, avg_percentage, total_marks, min_percentage, max_percentage = result
                print(f"  {i+1}. {name} ({admission_number}) - Grade {grade_name} {stream_name or 'No Stream'} - {avg_percentage:.2f}%")
            
            print("✅ Query executed successfully - the fix should work!")
            return True
        else:
            print("❌ No results found - check data or query")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = test_database_query()
    if success:
        print("\n🎉 Database query test PASSED!")
        print("The enhanced top performers fix should work correctly.")
    else:
        print("\n💔 Database query test FAILED!")
        print("There may be issues with the data or query structure.")
