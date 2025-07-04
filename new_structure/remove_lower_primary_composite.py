#!/usr/bin/env python3
"""
Remove lower primary composite subject configurations since they don't need composite subjects.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from config import config as app_config

def remove_lower_primary_composite():
    """Remove lower primary composite configurations."""
    conf = app_config['development']()
    
    try:
        connection = pymysql.connect(
            host=conf.MYSQL_HOST,
            user=conf.MYSQL_USER,
            password='@2494/lK',
            database=conf.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("🔍 Checking current subject configurations...")
        
        # Check current configurations
        cursor.execute("""
            SELECT id, subject_name, education_level, is_composite 
            FROM subject_configuration 
            ORDER BY education_level, subject_name
        """)
        
        configs = cursor.fetchall()
        print(f"📊 Found {len(configs)} configurations:")
        
        for config in configs:
            status = "✅ Composite" if config[3] else "❌ Simple"
            print(f"   - {config[1]} ({config[2]}): {status}")
        
        # Remove lower primary configurations
        print(f"\n🗑️ Removing lower primary composite configurations...")
        
        cursor.execute("""
            DELETE FROM subject_configuration 
            WHERE education_level = 'lower_primary'
        """)
        
        deleted_count = cursor.rowcount
        connection.commit()
        print(f"✅ Removed {deleted_count} lower primary configurations")
        
        # Verify remaining configurations
        print(f"\n🔍 Remaining configurations:")
        cursor.execute("""
            SELECT id, subject_name, education_level, is_composite 
            FROM subject_configuration 
            ORDER BY education_level, subject_name
        """)
        
        remaining_configs = cursor.fetchall()
        print(f"📊 {len(remaining_configs)} configurations remaining:")
        
        for config in remaining_configs:
            status = "✅ Composite" if config[3] else "❌ Simple"
            print(f"   - {config[1]} ({config[2]}): {status}")
        
        # Also check if we need to update any lower primary subjects to NOT be composite
        print(f"\n🔍 Checking lower primary subjects...")
        cursor.execute("""
            SELECT id, name, education_level, is_composite 
            FROM subject 
            WHERE education_level = 'lower_primary'
            AND LOWER(name) IN ('english', 'kiswahili')
        """)
        
        lower_primary_subjects = cursor.fetchall()
        
        if lower_primary_subjects:
            print(f"📚 Found {len(lower_primary_subjects)} lower primary English/Kiswahili subjects:")
            
            for subject in lower_primary_subjects:
                status = "✅ Composite" if subject[3] else "❌ Simple"
                print(f"   - {subject[1]} ({subject[2]}): {status}")
            
            # Update them to NOT be composite
            print(f"\n🔧 Updating lower primary subjects to simple (not composite)...")
            cursor.execute("""
                UPDATE subject 
                SET is_composite = FALSE 
                WHERE education_level = 'lower_primary'
                AND LOWER(name) IN ('english', 'kiswahili')
            """)
            
            updated_count = cursor.rowcount
            connection.commit()
            print(f"✅ Updated {updated_count} lower primary subjects to simple")
        else:
            print("ℹ️ No lower primary English/Kiswahili subjects found")
        
        # Final summary
        print(f"\n📋 Final Summary:")
        print(f"   - Lower Primary: Simple subjects (no composite)")
        print(f"   - Upper Primary: Composite English & Kiswahili")
        print(f"   - Junior Secondary: Composite English & Kiswahili")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_final_state():
    """Verify the final state of configurations."""
    conf = app_config['development']()
    
    try:
        connection = pymysql.connect(
            host=conf.MYSQL_HOST,
            user=conf.MYSQL_USER,
            password='@2494/lK',
            database=conf.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print(f"\n🔍 Final Verification:")
        
        # Check subject_configuration table
        cursor.execute("SELECT COUNT(*) FROM subject_configuration")
        config_count = cursor.fetchone()[0]
        print(f"📊 Subject configurations: {config_count}")
        
        cursor.execute("""
            SELECT education_level, COUNT(*) 
            FROM subject_configuration 
            GROUP BY education_level
        """)
        
        config_by_level = cursor.fetchall()
        for level, count in config_by_level:
            print(f"   - {level}: {count} configurations")
        
        # Check composite subjects
        cursor.execute("""
            SELECT education_level, COUNT(*) 
            FROM subject 
            WHERE is_composite = TRUE 
            AND LOWER(name) IN ('english', 'kiswahili')
            GROUP BY education_level
        """)
        
        composite_by_level = cursor.fetchall()
        print(f"\n📚 Composite subjects by level:")
        for level, count in composite_by_level:
            print(f"   - {level}: {count} composite subjects")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Verification Error: {e}")

if __name__ == '__main__':
    print("🚀 Removing Lower Primary Composite Configurations...")
    
    success = remove_lower_primary_composite()
    
    if success:
        verify_final_state()
        print("\n✅ Lower primary composite configurations removed!")
        print("\n📝 Now composite subjects will only appear for:")
        print("   - Upper Primary: English & Kiswahili")
        print("   - Junior Secondary: English & Kiswahili")
        print("\n🔄 Test the 'Save All Configurations' button again")
    else:
        print("\n❌ Removal failed. Please check the errors above.")
