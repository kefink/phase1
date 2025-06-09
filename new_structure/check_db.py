#!/usr/bin/env python3
"""
Simple script to check database contents for debugging stream population issue.
"""
import sqlite3
import os

def check_database():
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    print(f"✅ Database found at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📊 Available tables ({len(tables)}): {', '.join(tables)}")

        if 'grade' not in tables:
            print("❌ Grade table not found!")
            print("🔧 Available tables suggest database needs initialization")
            return

        if 'stream' not in tables:
            print("❌ Stream table not found!")
            print("🔧 Available tables suggest database needs initialization")
            return
        
        print('\n=== GRADES ===')
        cursor.execute('SELECT id, name, education_level FROM grade ORDER BY id')
        grades = cursor.fetchall()
        if not grades:
            print("❌ No grades found in database!")
        else:
            for grade in grades:
                print(f'ID: {grade[0]}, Name: "{grade[1]}", Education Level: "{grade[2]}"')
        
        print('\n=== STREAMS ===')
        cursor.execute('SELECT id, name, grade_id FROM stream ORDER BY grade_id, name')
        streams = cursor.fetchall()
        if not streams:
            print("❌ No streams found in database!")
        else:
            for stream in streams:
                print(f'ID: {stream[0]}, Name: "{stream[1]}", Grade ID: {stream[2]}')
                
        print('\n=== GRADE-STREAM RELATIONSHIPS ===')
        cursor.execute('''
            SELECT g.id, g.name as grade_name, s.id as stream_id, s.name as stream_name
            FROM grade g
            LEFT JOIN stream s ON g.id = s.grade_id
            ORDER BY g.id, s.name
        ''')
        relationships = cursor.fetchall()
        
        if not relationships:
            print("❌ No grade-stream relationships found!")
        else:
            current_grade_id = None
            for rel in relationships:
                grade_id, grade_name, stream_id, stream_name = rel
                if grade_id != current_grade_id:
                    current_grade_id = grade_id
                    print(f'\nGrade {grade_name} (ID: {grade_id}):')
                if stream_name:
                    print(f'  - Stream {stream_name} (ID: {stream_id})')
                else:
                    print('  - No streams found')
        
        # Test the specific query used by the API
        print('\n=== TESTING API QUERY ===')
        test_grades = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'Grade 1', 'Grade 2']
        
        for test_grade in test_grades:
            # Test both formats
            grade_name = f"Grade {test_grade}" if test_grade.isdigit() else test_grade
            
            cursor.execute('SELECT id, name FROM grade WHERE name = ?', (grade_name,))
            grade_result = cursor.fetchone()
            
            if grade_result:
                grade_id, found_name = grade_result
                cursor.execute('SELECT id, name FROM stream WHERE grade_id = ?', (grade_id,))
                stream_results = cursor.fetchall()
                
                print(f'✅ Grade "{test_grade}" -> Found "{found_name}" (ID: {grade_id}) -> {len(stream_results)} streams')
                for stream in stream_results:
                    print(f'    - Stream {stream[1]} (ID: {stream[0]})')
            else:
                print(f'❌ Grade "{test_grade}" -> Not found')
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_database()
