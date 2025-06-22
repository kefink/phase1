"""
Update Composite Subjects
Mark English and Kiswahili subjects as composite in the database
"""

import pymysql
import sys

def update_composite_subjects():
    """Update subjects to mark English and Kiswahili as composite."""
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='@2494/lK',
            database='hillview_demo001'
        )
        cursor = connection.cursor()
        
        print("🔧 UPDATING COMPOSITE SUBJECTS")
        print("=" * 50)
        
        # Check if is_composite column exists in subject table
        cursor.execute("DESCRIBE subject")
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        if 'is_composite' not in column_names:
            print("➕ Adding is_composite column to subject table...")
            cursor.execute("ALTER TABLE subject ADD COLUMN is_composite BOOLEAN DEFAULT FALSE")
            print("✅ Added is_composite column")
        else:
            print("✅ is_composite column already exists")
        
        # Update English and Kiswahili subjects to be composite
        print("\n📝 Marking subjects as composite...")
        
        # Mark English subjects as composite
        cursor.execute("""
            UPDATE subject 
            SET is_composite = TRUE 
            WHERE name LIKE '%English%'
        """)
        english_updated = cursor.rowcount
        print(f"✅ Updated {english_updated} English subjects as composite")
        
        # Mark Kiswahili subjects as composite
        cursor.execute("""
            UPDATE subject 
            SET is_composite = TRUE 
            WHERE name LIKE '%Kiswahili%'
        """)
        kiswahili_updated = cursor.rowcount
        print(f"✅ Updated {kiswahili_updated} Kiswahili subjects as composite")
        
        # Commit changes
        connection.commit()
        
        # Verify the changes
        print("\n🔍 VERIFYING COMPOSITE SUBJECTS")
        print("-" * 40)
        cursor.execute("SELECT name, is_composite FROM subject ORDER BY name")
        subjects = cursor.fetchall()
        
        for subject_name, is_composite in subjects:
            status = "✅ Composite" if is_composite else "📄 Simple"
            print(f"  {status}: {subject_name}")
        
        # Show subject components
        print("\n📋 SUBJECT COMPONENTS")
        print("-" * 30)
        cursor.execute("""
            SELECT s.name, sc.name, sc.weight, sc.max_raw_mark
            FROM subject s
            JOIN subject_component sc ON s.id = sc.subject_id
            ORDER BY s.name, sc.name
        """)
        components = cursor.fetchall()
        
        if components:
            for subject_name, component_name, weight, max_mark in components:
                print(f"  {subject_name} -> {component_name} (weight: {weight}, max: {max_mark})")
        else:
            print("  No components found")
        
        connection.close()
        
        print(f"\n🎉 SUCCESS: Updated {english_updated + kiswahili_updated} subjects as composite!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating composite subjects: {e}")
        return False

if __name__ == '__main__':
    success = update_composite_subjects()
    if success:
        print("\n🚀 Composite subjects updated successfully!")
        sys.exit(0)
    else:
        print("\n💥 Failed to update composite subjects!")
        sys.exit(1)
