#!/usr/bin/env python3
"""
Fix database issues - remove duplicate streams and ensure clean data.
"""
import sqlite3
import os

def fix_database():
    """Fix database issues."""
    db_path = 'kirima_primary.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Fixing database issues...")
        
        # 1. Remove duplicate streams
        print("📋 Removing duplicate streams...")
        
        # Get all grades
        cursor.execute('SELECT id, name FROM grade ORDER BY id')
        grades = cursor.fetchall()
        
        for grade_id, grade_name in grades:
            print(f"   Fixing streams for {grade_name}...")
            
            # Get all streams for this grade
            cursor.execute('SELECT id, name FROM stream WHERE grade_id = ? ORDER BY id', (grade_id,))
            streams = cursor.fetchall()
            
            # Keep track of stream names we've seen
            seen_names = set()
            streams_to_delete = []
            
            for stream_id, stream_name in streams:
                if stream_name in seen_names:
                    # This is a duplicate
                    streams_to_delete.append(stream_id)
                    print(f"     Marking duplicate stream {stream_name} (ID: {stream_id}) for deletion")
                else:
                    seen_names.add(stream_name)
                    print(f"     Keeping stream {stream_name} (ID: {stream_id})")
            
            # Delete duplicate streams
            for stream_id in streams_to_delete:
                cursor.execute('DELETE FROM stream WHERE id = ?', (stream_id,))
                print(f"     Deleted duplicate stream ID: {stream_id}")
        
        # 2. Ensure each grade has exactly A and B streams
        print("\n📋 Ensuring each grade has A and B streams...")
        
        for grade_id, grade_name in grades:
            # Check what streams exist
            cursor.execute('SELECT name FROM stream WHERE grade_id = ? ORDER BY name', (grade_id,))
            existing_streams = [row[0] for row in cursor.fetchall()]
            
            print(f"   {grade_name} has streams: {existing_streams}")
            
            # Ensure A and B exist
            for stream_name in ['A', 'B']:
                if stream_name not in existing_streams:
                    cursor.execute('INSERT INTO stream (name, grade_id) VALUES (?, ?)', (stream_name, grade_id))
                    print(f"     Added missing stream {stream_name}")
        
        # 3. Verify the fix
        print("\n✅ Verification:")
        cursor.execute('''
            SELECT g.name, COUNT(s.id) as stream_count
            FROM grade g
            LEFT JOIN stream s ON g.id = s.grade_id
            GROUP BY g.id, g.name
            ORDER BY g.name
        ''')
        
        results = cursor.fetchall()
        total_streams = 0
        
        for grade_name, stream_count in results:
            print(f"   {grade_name}: {stream_count} streams")
            total_streams += stream_count
            
            if stream_count != 2:
                print(f"   ⚠️  {grade_name} should have 2 streams, but has {stream_count}")
        
        print(f"\n📊 Total streams: {total_streams} (should be 18)")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        if total_streams == 18:
            print("✅ Database fixed successfully!")
            return True
        else:
            print("❌ Database still has issues!")
            return False
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False

def test_login_manually():
    """Test login manually to debug authentication issues."""
    print("\n🔐 MANUAL LOGIN TEST")
    print("=" * 50)
    
    try:
        import sys
        sys.path.append('.')
        
        # Import the authentication function
        from services.auth_service import authenticate_teacher
        
        # Test authentication directly
        teacher = authenticate_teacher('classteacher1', 'password123', 'classteacher')
        
        if teacher:
            print(f"✅ Authentication successful!")
            print(f"   Teacher ID: {teacher.id}")
            print(f"   Username: {teacher.username}")
            print(f"   Role: {teacher.role}")
            return True
        else:
            print("❌ Authentication failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing authentication: {e}")
        return False

def main():
    """Main function."""
    print("🔧 DATABASE REPAIR TOOL")
    print("=" * 50)
    
    # Fix database issues
    db_fixed = fix_database()
    
    # Test authentication
    auth_works = test_login_manually()
    
    print("\n📋 REPAIR SUMMARY")
    print("=" * 50)
    print(f"Database: {'✅ FIXED' if db_fixed else '❌ ISSUES REMAIN'}")
    print(f"Authentication: {'✅ WORKING' if auth_works else '❌ BROKEN'}")
    
    if db_fixed and auth_works:
        print("\n🎯 READY FOR TESTING!")
        print("1. Try logging in manually at: http://localhost:5000/classteacher_login")
        print("2. Use credentials: classteacher1 / password123")
        print("3. Test stream population in upload marks section")
    else:
        print("\n❌ ISSUES REMAIN - Check the errors above")

if __name__ == '__main__':
    main()
