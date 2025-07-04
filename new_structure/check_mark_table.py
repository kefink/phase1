#!/usr/bin/env python3
"""
Script to check the mark table structure in MySQL database.
"""
import sys
import os
import urllib.parse

# Add the parent directory to the path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the new_structure package
from new_structure import create_app
from new_structure.extensions import db

def check_mark_table():
    """Check the structure of the mark table using Flask app context."""
    try:
        app = create_app()

        with app.app_context():
            # Use SQLAlchemy to execute raw SQL (newer syntax)
            with db.engine.connect() as connection:
                result = connection.execute(db.text("DESCRIBE mark"))
                columns = result.fetchall()

                print('📋 Current mark table structure:')
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f"DEFAULT {col[4]}" if col[4] else ""
                    extra = col[5] if col[5] else ""
                    print(f'  - {col[0]}: {col[1]} {nullable} {default} {extra}')

                print('\n📊 Sample data from mark table:')
                result = connection.execute(db.text('SELECT COUNT(*) FROM mark'))
                count = result.fetchone()[0]
                print(f'Total records: {count}')

                if count > 0:
                    result = connection.execute(db.text('SELECT * FROM mark LIMIT 3'))
                    rows = result.fetchall()
                    print('Sample records:')
                    for row in rows:
                        print(f'  {row}')

        print('✅ Database connection successful')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_mark_table()
