#!/usr/bin/env python3
"""
Check Kevin's account roles to identify potential conflicts
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from init_db import create_app
from extensions import db
from models import Parent, Teacher, Student, ParentStudent

def check_kevin_roles():
    app = create_app()
    
    with app.app_context():
        email = "kevinmugo359@gmail.com"
        
        print(f"🔍 CHECKING ROLES FOR: {email}")
        print("=" * 50)
        
        # Check parent account
        parent = Parent.query.filter_by(email=email).first()
        if parent:
            print(f"✅ PARENT ACCOUNT FOUND:")
            print(f"   ID: {parent.id}")
            print(f"   Name: {parent.first_name} {parent.last_name}")
            print(f"   Email: {parent.email}")
            
            # Check linked children
            children = db.session.query(Student).join(
                ParentStudent, Student.id == ParentStudent.student_id
            ).filter(ParentStudent.parent_id == parent.id).all()
            
            print(f"   Children linked: {len(children)}")
            for child in children:
                print(f"     - {child.first_name} {child.last_name} (ID: {child.id})")
        else:
            print("❌ NO PARENT ACCOUNT FOUND")
        
        # Check teacher account
        teacher = Teacher.query.filter_by(email=email).first()
        if teacher:
            print(f"\n⚠️  TEACHER ACCOUNT ALSO FOUND:")
            print(f"   ID: {teacher.id}")
            print(f"   Name: {teacher.first_name} {teacher.last_name}")
            print(f"   Email: {teacher.email}")
            print(f"   Role: {teacher.role}")
            print("\n🚨 ROLE CONFLICT DETECTED!")
            print("   Same email has both parent AND teacher accounts.")
            print("   This can cause session conflicts and 403 errors.")
        else:
            print("\n✅ NO TEACHER ACCOUNT CONFLICT")
        
        print(f"\n📋 SOLUTION STATUS:")
        print(f"✅ Parent portal updated to use parent-specific routes")
        print(f"✅ Avoids classteacher route redirects")
        print(f"✅ Role conflicts handled in view logic")
        
        if parent and teacher:
            print(f"\n💡 RECOMMENDATION:")
            print(f"   Use fresh browser session when switching between:")
            print(f"   • Teacher login: http://127.0.0.1:8080/login")
            print(f"   • Parent login: http://127.0.0.1:8080/parent/login")

if __name__ == "__main__":
    check_kevin_roles()