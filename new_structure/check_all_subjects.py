#!/usr/bin/env python3
"""
Check all subjects in the database and add missing English/Kiswahili subjects.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from config import config

def check_and_add_subjects():
    """Check all subjects and add missing English/Kiswahili for all education levels."""
    conf = config['development']()
    
    try:
        connection = pymysql.connect(
            host=conf.MYSQL_HOST,
            user=conf.MYSQL_USER,
            password='@2494/lK',
            database=conf.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("🔍 Checking all subjects in database...")
        
        # Check all subjects
        cursor.execute("SELECT id, name, education_level FROM subject ORDER BY education_level, name")
        all_subjects = cursor.fetchall()
        
        print(f"📊 Found {len(all_subjects)} total subjects:")
        
        # Group by education level
        by_level = {}
        for subject in all_subjects:
            level = subject[2]
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(subject)
        
        for level, subjects in by_level.items():
            print(f"\n📚 {level.upper()}:")
            for subject in subjects:
                print(f"   - {subject[1]} (ID: {subject[0]})")
        
        # Check what education levels we have
        education_levels = list(by_level.keys())
        print(f"\n🎓 Education levels found: {education_levels}")
        
        # Required subjects for each level
        required_subjects = {
            'lower_primary': ['ENGLISH', 'KISWAHILI'],
            'upper_primary': ['ENGLISH', 'KISWAHILI'],
            'junior_secondary': ['ENGLISH', 'KISWAHILI']
        }
        
        # Check and add missing subjects
        added_count = 0
        for level in ['lower_primary', 'upper_primary', 'junior_secondary']:
            if level not in by_level:
                print(f"\n⚠️ Education level '{level}' not found in database")
                continue
                
            existing_subjects = [s[1].upper() for s in by_level[level]]
            
            for required_subject in required_subjects[level]:
                if required_subject not in existing_subjects:
                    print(f"\n➕ Adding missing subject: {required_subject} for {level}")
                    
                    cursor.execute("""
                        INSERT INTO subject (name, education_level, is_composite)
                        VALUES (%s, %s, %s)
                    """, (required_subject, level, True))
                    
                    added_count += 1
                    print(f"✅ Added {required_subject} for {level}")
                else:
                    print(f"✅ {required_subject} already exists for {level}")
        
        if added_count > 0:
            connection.commit()
            print(f"\n💾 Added {added_count} new subjects")
        else:
            print(f"\n✅ All required subjects already exist")
        
        # Now update all English/Kiswahili subjects to be composite
        print(f"\n🔧 Ensuring all English/Kiswahili subjects are composite...")
        
        cursor.execute("""
            UPDATE subject 
            SET is_composite = TRUE 
            WHERE LOWER(name) IN ('english', 'kiswahili')
        """)
        
        updated_count = cursor.rowcount
        connection.commit()
        print(f"✅ Updated {updated_count} subjects to composite")
        
        # Final verification
        print(f"\n🔍 Final verification...")
        cursor.execute("""
            SELECT name, education_level, is_composite 
            FROM subject 
            WHERE LOWER(name) IN ('english', 'kiswahili')
            ORDER BY name, education_level
        """)
        
        final_subjects = cursor.fetchall()
        print(f"📊 English/Kiswahili subjects ({len(final_subjects)} total):")
        
        for subject in final_subjects:
            status = "✅ Composite" if subject[2] else "❌ Not Composite"
            print(f"   - {subject[0]} ({subject[1]}): {status}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Starting Subject Check and Fix...")
    
    success = check_and_add_subjects()
    
    if success:
        print("\n✅ Subject check and fix completed!")
        print("\n📝 Now test the Save All Configurations button again")
        print("   It should show 'subjects updated' > 0")
    else:
        print("\n❌ Fix failed. Please check the errors above.")
