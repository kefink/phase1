#!/usr/bin/env python3
"""
Simple migration script to clean up grades and fix database issues.
"""

import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, grandparent_dir)

def simple_grade_cleanup():
    """Simple grade cleanup and database fix."""
    
    try:
        from new_structure import create_app
        from new_structure.extensions import db
        from new_structure.models.academic import Grade, Stream
        
        print("🧹 Simple Grade Cleanup")
        print("=" * 30)
        
        app = create_app('development')
        
        with app.app_context():
            print("📍 Connected to database")
            
            # Step 1: Delete all existing grades and streams
            print("\n🗑️ Deleting all existing grades and streams...")
            
            try:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text

                # Delete streams first (foreign key constraint)
                db.session.execute(text("DELETE FROM stream"))
                db.session.execute(text("DELETE FROM grade"))
                db.session.commit()
                print("✅ All grades and streams deleted")

            except Exception as e:
                print(f"⚠️ Error deleting grades: {e}")
                db.session.rollback()

                # Try alternative approach - delete using ORM
                try:
                    print("   Trying ORM deletion...")
                    streams = Stream.query.all()
                    for stream in streams:
                        db.session.delete(stream)

                    grades = Grade.query.all()
                    for grade in grades:
                        db.session.delete(grade)

                    db.session.commit()
                    print("✅ All grades and streams deleted using ORM")

                except Exception as e2:
                    print(f"⚠️ ORM deletion also failed: {e2}")
                    db.session.rollback()
            
            # Step 2: Create fresh grades
            print("\n📚 Creating fresh grade system...")
            
            try:
                # Create basic grades
                basic_grades = [
                    ('Grade 1', 'lower_primary'),
                    ('Grade 2', 'lower_primary'),
                    ('Grade 3', 'lower_primary'),
                    ('Grade 4', 'upper_primary'),
                    ('Grade 5', 'upper_primary'),
                    ('Grade 6', 'upper_primary'),
                    ('Grade 7', 'junior_secondary'),
                    ('Grade 8', 'junior_secondary'),
                    ('Grade 9', 'junior_secondary')
                ]
                
                for grade_name, education_level in basic_grades:
                    grade = Grade(name=grade_name, education_level=education_level)
                    db.session.add(grade)
                
                db.session.commit()
                print(f"✅ Created {len(basic_grades)} grades")
                
                # Create some sample streams
                print("   Adding sample streams...")
                
                # Get Grade 4, 5, 6 for streams
                grade_4 = Grade.query.filter_by(name='Grade 4').first()
                grade_5 = Grade.query.filter_by(name='Grade 5').first()
                grade_6 = Grade.query.filter_by(name='Grade 6').first()
                
                if grade_4:
                    for stream_name in ['A', 'B']:
                        stream = Stream(name=stream_name, grade_id=grade_4.id)
                        db.session.add(stream)
                
                if grade_5:
                    for stream_name in ['A', 'B']:
                        stream = Stream(name=stream_name, grade_id=grade_5.id)
                        db.session.add(stream)
                
                if grade_6:
                    for stream_name in ['A', 'B', 'C']:
                        stream = Stream(name=stream_name, grade_id=grade_6.id)
                        db.session.add(stream)
                
                db.session.commit()
                print("✅ Added sample streams")
                
            except Exception as e:
                print(f"❌ Error creating grades: {e}")
                db.session.rollback()
                return False
            
            # Step 3: Show final structure
            print("\n📊 Final Grade Structure:")
            grades = Grade.query.all()
            for grade in grades:
                streams = Stream.query.filter_by(grade_id=grade.id).all()
                if streams:
                    stream_names = [s.name for s in streams]
                    print(f"   - {grade.name}: {', '.join(stream_names)}")
                else:
                    print(f"   - {grade.name}: No streams")
            
            print(f"\n🎉 Grade cleanup completed successfully!")
            print(f"✅ Total grades: {len(grades)}")
            print(f"✅ Ready for custom naming")
            
            return True
            
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Simple Grade Cleanup")
    print("=" * 25)
    
    success = simple_grade_cleanup()
    
    if success:
        print("\n" + "=" * 25)
        print("✅ CLEANUP COMPLETED!")
        print("🎓 You can now manage grades at:")
        print("   http://localhost:5000/headteacher/manage_grades_streams")
        print("=" * 25)
    else:
        print("\n" + "=" * 25)
        print("❌ CLEANUP FAILED!")
        print("=" * 25)
        sys.exit(1)
