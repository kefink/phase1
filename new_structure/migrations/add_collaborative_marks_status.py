"""
Database migration to add SubjectMarksStatus table for collaborative marks upload tracking.
"""
import sys
import os

# Add the parent directory to the path to import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import Flask and our app
from __init__ import app, db

def create_subject_marks_status_table():
    """Create the SubjectMarksStatus table."""
    try:
        # Create the table
        db.create_all()
        print("✅ SubjectMarksStatus table created successfully!")

        # Verify the table was created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()

        if 'subject_marks_status' in tables:
            print("✅ Table 'subject_marks_status' confirmed in database")

            # Show table structure
            columns = inspector.get_columns('subject_marks_status')
            print("\n📋 Table structure:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        else:
            print("❌ Table 'subject_marks_status' not found in database")

    except Exception as e:
        print(f"❌ Error creating SubjectMarksStatus table: {str(e)}")
        db.session.rollback()

def run_migration():
    """Run the migration."""
    print("🚀 Starting collaborative marks status migration...")

    with app.app_context():
        create_subject_marks_status_table()

    print("✅ Migration completed!")

if __name__ == "__main__":
    run_migration()
