#!/usr/bin/env python3
"""
Fix Subject table to properly mark English and Kiswahili as composite.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from config import config

def fix_subject_table():
    """Fix the Subject table to mark English and Kiswahili as composite."""
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
        
        print("🔍 Checking current Subject table...")
        
        # Check current subjects
        cursor.execute("""
            SELECT id, name, education_level, is_composite 
            FROM subject 
            WHERE LOWER(name) LIKE '%english%' OR LOWER(name) LIKE '%kiswahili%'
            ORDER BY name, education_level
        """)
        
        subjects = cursor.fetchall()
        print(f"📊 Found {len(subjects)} English/Kiswahili subjects:")
        
        for subject in subjects:
            print(f"   ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}, Composite: {subject[3]}")
        
        if not subjects:
            print("❌ No English/Kiswahili subjects found in Subject table!")
            print("🔧 Let's check what subjects exist...")
            
            cursor.execute("SELECT id, name, education_level FROM subject LIMIT 10")
            all_subjects = cursor.fetchall()
            print("📋 Sample subjects in database:")
            for subject in all_subjects:
                print(f"   ID: {subject[0]}, Name: {subject[1]}, Level: {subject[2]}")
            
            return False
        
        # Update subjects to be composite
        print("\n🔧 Updating subjects to composite...")
        
        updated_count = 0
        for subject in subjects:
            subject_id, name, education_level, is_composite = subject
            
            if not is_composite:
                cursor.execute("""
                    UPDATE subject 
                    SET is_composite = TRUE 
                    WHERE id = %s
                """, (subject_id,))
                
                updated_count += 1
                print(f"✅ Updated {name} ({education_level}) to composite")
            else:
                print(f"ℹ️ {name} ({education_level}) already composite")
        
        connection.commit()
        print(f"\n💾 Updated {updated_count} subjects to composite")
        
        # Verify the changes
        print("\n🔍 Verifying changes...")
        cursor.execute("""
            SELECT id, name, education_level, is_composite 
            FROM subject 
            WHERE LOWER(name) LIKE '%english%' OR LOWER(name) LIKE '%kiswahili%'
            ORDER BY name, education_level
        """)
        
        updated_subjects = cursor.fetchall()
        composite_count = sum(1 for s in updated_subjects if s[3])
        
        print(f"📊 After update: {composite_count}/{len(updated_subjects)} subjects are composite")
        
        for subject in updated_subjects:
            status = "✅ Composite" if subject[3] else "❌ Not Composite"
            print(f"   {subject[1]} ({subject[2]}): {status}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_after_fix():
    """Test the save-all API after fixing the Subject table."""
    print("\n🧪 Testing save-all API after fix...")
    
    try:
        import requests
        response = requests.post("http://localhost:5000/api/subject-config/save-all",
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {data}")
            print(f"📊 Subjects updated: {data.get('subjects_updated', 0)}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ API Test Error: {e}")

if __name__ == '__main__':
    print("🚀 Starting Subject Table Fix...")
    
    success = fix_subject_table()
    
    if success:
        print("\n✅ Subject table fix completed!")
        print("\n📝 Next steps:")
        print("1. Go back to Subject Configuration page")
        print("2. Click 'Save All Configurations' button")
        print("3. Should now see 'subjects updated' > 0")
        print("4. Test marks upload with English/Kiswahili")
        
        # Test the API
        test_api_after_fix()
    else:
        print("\n❌ Fix failed. Please check the errors above.")
