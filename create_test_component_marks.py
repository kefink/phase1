#!/usr/bin/env python3
"""
Create Test Component Marks Script
Creates realistic component marks based on existing marks in the database.
"""

import sqlite3
import os
import random

def create_test_component_marks():
    """Create test component marks for English and Kiswahili subjects."""
    
    # Connect to the database
    db_path = 'hillview.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=== Creating Test Component Marks ===")
        
        # 1. Check existing marks for English and Kiswahili
        print("1. Finding existing marks for composite subjects...")
        cursor.execute('''
        SELECT id, grade, stream, student_name, subject, mark 
        FROM marks 
        WHERE subject IN ('English', 'ENGLISH', 'Kiswahili', 'KISWAHILI')
        ORDER BY subject, student_name
        ''')
        marks = cursor.fetchall()
        
        if not marks:
            print("   No existing marks found for English or Kiswahili!")
            print("   Creating sample marks first...")
            
            # Create some sample marks
            sample_marks = [
                ('Grade 6', 'A', 'John Doe', 'ENGLISH', 69),
                ('Grade 6', 'A', 'Jane Smith', 'ENGLISH', 75),
                ('Grade 6', 'A', 'Bob Wilson', 'ENGLISH', 82),
                ('Grade 6', 'A', 'John Doe', 'KISWAHILI', 77),
                ('Grade 6', 'A', 'Jane Smith', 'KISWAHILI', 68),
                ('Grade 6', 'A', 'Bob Wilson', 'KISWAHILI', 85),
            ]
            
            for mark_data in sample_marks:
                cursor.execute('''
                INSERT INTO marks (grade, stream, student_name, subject, mark)
                VALUES (?, ?, ?, ?, ?)
                ''', mark_data)
            
            print(f"   Created {len(sample_marks)} sample marks")
            
            # Re-fetch the marks
            cursor.execute('''
            SELECT id, grade, stream, student_name, subject, mark 
            FROM marks 
            WHERE subject IN ('English', 'ENGLISH', 'Kiswahili', 'KISWAHILI')
            ORDER BY subject, student_name
            ''')
            marks = cursor.fetchall()
        
        print(f"   Found {len(marks)} marks for composite subjects")
        
        # 2. Get component definitions
        print("2. Getting component definitions...")
        cursor.execute('SELECT id, subject_id, name, weight, max_raw_mark FROM subject_component')
        components = cursor.fetchall()
        
        if not components:
            print("   No components found! Please run setup_component_tables.py first.")
            return False
        
        print(f"   Found {len(components)} components:")
        for comp in components:
            print(f"      ID {comp[0]}: {comp[2]} (Subject {comp[1]}, {comp[4]} marks)")
        
        # 3. Create component marks for each main subject mark
        print("3. Creating component marks...")
        created_count = 0
        
        for mark in marks:
            mark_id, grade, stream, student_name, subject, total_mark = mark
            
            # Determine which components to use based on subject
            if subject.upper() == 'ENGLISH':
                subject_id = 1  # English
                relevant_components = [comp for comp in components if comp[1] == subject_id]
            elif subject.upper() == 'KISWAHILI':
                subject_id = 2  # Kiswahili
                relevant_components = [comp for comp in components if comp[1] == subject_id]
            else:
                continue
            
            print(f"   Processing {student_name} - {subject} (Total: {total_mark})")
            
            # Create component marks for this student
            for component in relevant_components:
                comp_id, comp_subject_id, comp_name, weight, max_raw_mark = component
                
                # Calculate component raw mark based on weight and some variation
                # For example: if total is 69 and Grammar weight is 0.7, Grammar gets ~48 marks
                base_component_mark = int(total_mark * weight)
                
                # Add some realistic variation (±5 marks)
                variation = random.randint(-5, 5)
                component_raw_mark = max(0, min(max_raw_mark, base_component_mark + variation))
                
                # Calculate percentage
                percentage = (component_raw_mark / max_raw_mark) * 100
                
                # Check if component mark already exists
                cursor.execute('''
                SELECT id FROM component_mark 
                WHERE mark_id = ? AND component_id = ?
                ''', (mark_id, comp_id))
                
                existing = cursor.fetchone()
                if existing:
                    # Update existing
                    cursor.execute('''
                    UPDATE component_mark 
                    SET raw_mark = ?, max_raw_mark = ?, percentage = ?
                    WHERE mark_id = ? AND component_id = ?
                    ''', (component_raw_mark, max_raw_mark, percentage, mark_id, comp_id))
                    print(f"      Updated {comp_name}: {component_raw_mark}/{max_raw_mark} ({percentage:.1f}%)")
                else:
                    # Create new
                    cursor.execute('''
                    INSERT INTO component_mark (mark_id, component_id, raw_mark, max_raw_mark, percentage)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (mark_id, comp_id, component_raw_mark, max_raw_mark, percentage))
                    print(f"      Created {comp_name}: {component_raw_mark}/{max_raw_mark} ({percentage:.1f}%)")
                    created_count += 1
        
        # Commit the changes
        conn.commit()
        print(f"\n✅ Created/updated {created_count} component marks!")
        
        # 4. Verify the results
        print("\n=== Verification ===")
        cursor.execute('''
        SELECT cm.raw_mark, cm.max_raw_mark, cm.percentage, sc.name, m.student_name, m.subject
        FROM component_mark cm
        JOIN subject_component sc ON cm.component_id = sc.id
        JOIN marks m ON cm.mark_id = m.id
        ORDER BY m.subject, m.student_name, sc.name
        ''')
        
        results = cursor.fetchall()
        print(f"Total component marks in database: {len(results)}")
        
        # Show sample results
        print("\nSample component marks:")
        for i, result in enumerate(results[:10]):  # Show first 10
            raw_mark, max_raw_mark, percentage, comp_name, student_name, subject = result
            print(f"   {student_name} - {subject} - {comp_name}: {raw_mark}/{max_raw_mark} ({percentage:.1f}%)")
        
        if len(results) > 10:
            print(f"   ... and {len(results) - 10} more")
        
        return True
        
    except Exception as e:
        print(f"Error creating component marks: {str(e)}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    success = create_test_component_marks()
    if success:
        print("\n🎉 Test component marks created! You can now test the individual reports.")
    else:
        print("\n❌ Failed to create component marks. Please check the errors above.")
