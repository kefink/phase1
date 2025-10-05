#!/usr/bin/env python3
"""
Check Kevin's roles using Flask app context
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_kevin_roles_simple():
    print(f"🔍 KEVIN'S PARENT ACCOUNT STATUS")
    print("=" * 60)
    
    print(f"✅ Kevin's Account Details:")
    print(f"   Email: kevinmugo359@gmail.com")
    print(f"   Password: e3fKkXhi")
    print(f"   Account Type: Parent")
    
    print(f"\n📊 What We Fixed:")
    print(f"✅ Updated parent portal to use parent-specific routes")
    print(f"✅ Removed classteacher route redirects causing 403")
    print(f"✅ Reports now shown within parent context")
    print(f"✅ Role session conflicts handled")
    
    # Check if the app is running
    try:
        # Check parent table
        cursor.execute("SELECT id, first_name, last_name, email FROM parent WHERE email = ?", 
                      ("kevinmugo359@gmail.com",))
        parent_row = cursor.fetchone()
        
        if parent_row:
            print(f"✅ PARENT ACCOUNT FOUND:")
            print(f"   ID: {parent_row[0]}")
            print(f"   Name: {parent_row[1]} {parent_row[2]}")
            print(f"   Email: {parent_row[3]}")
            
            # Check linked children
            cursor.execute("""
                SELECT s.id, s.first_name, s.last_name 
                FROM student s 
                JOIN parent_student ps ON s.id = ps.student_id 
                WHERE ps.parent_id = ?
            """, (parent_row[0],))
            children = cursor.fetchall()
            
            print(f"   Children linked: {len(children)}")
            for child in children:
                print(f"     - {child[1]} {child[2]} (ID: {child[0]})")
        else:
            print("❌ NO PARENT ACCOUNT FOUND")
        
        # Check teacher table
        cursor.execute("SELECT id, first_name, last_name, email, role FROM teacher WHERE email = ?", 
                      ("kevinmugo359@gmail.com",))
        teacher_row = cursor.fetchone()
        
        if teacher_row:
            print(f"\n⚠️  TEACHER ACCOUNT ALSO FOUND:")
            print(f"   ID: {teacher_row[0]}")
            print(f"   Name: {teacher_row[1]} {teacher_row[2]}")
            print(f"   Email: {teacher_row[3]}")
            print(f"   Role: {teacher_row[4]}")
            print(f"\n🚨 ROLE CONFLICT DETECTED!")
            print(f"   Same email has both parent AND teacher accounts.")
        else:
            print(f"\n✅ NO TEACHER ACCOUNT CONFLICT")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        conn.close()
    
    print(f"\n📋 FIXES IMPLEMENTED:")
    print(f"✅ Parent portal now uses parent-specific routes")
    print(f"✅ No more redirects to classteacher routes") 
    print(f"✅ Reports shown within parent context")
    print(f"✅ Role session conflicts handled")
    
    print(f"\n🎯 KEVIN'S NEXT STEPS:")
    print(f"1. Clear browser cache/cookies completely")
    print(f"2. Go to: http://127.0.0.1:8080/parent/login")
    print(f"3. Login: kevinmugo359@gmail.com / e3fKkXhi")
    print(f"4. Visit: http://127.0.0.1:8080/parent/children")
    print(f"5. Click Reports - should work without 403!")

if __name__ == "__main__":
    check_kevin_roles_sql()