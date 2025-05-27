"""
Migration script to update the Mark model with new field names and ensure percentage is calculated.
Run this script after updating the Mark model in academic.py.
"""
from new_structure import create_app
from new_structure.models import Mark
from new_structure.extensions import db
import sqlalchemy as sa
from sqlalchemy import Column, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import os

app = create_app()

def migrate_marks():
    """
    Migrate existing marks to the new schema.
    1. Add new columns if they don't exist
    2. Copy data from old columns to new columns
    3. Calculate percentage for marks that don't have it
    """
    with app.app_context():
        # Check if we need to perform the migration
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('mark')]
        
        needs_migration = 'raw_mark' not in columns or 'max_raw_mark' not in columns
        
        if not needs_migration:
            print("Migration already completed. No action needed.")
            return
        
        print("Starting mark migration...")
        
        # Get database URI from app config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Create a direct connection to the database
        engine = create_engine(db_uri)
        Base = declarative_base()
        
        # Define a temporary class to represent the current state of the Mark table
        class OldMark(Base):
            __tablename__ = 'mark'
            id = sa.Column(sa.Integer, primary_key=True)
            mark = sa.Column(sa.Float)
            total_marks = sa.Column(sa.Float)
            percentage = sa.Column(sa.Float, nullable=True)
        
        # Create a session
        session = Session(engine)
        
        try:
            # Add new columns to the table
            with engine.connect() as conn:
                # Check if columns exist before adding them
                if 'raw_mark' not in columns:
                    conn.execute(sa.text('ALTER TABLE mark ADD COLUMN raw_mark FLOAT'))
                    print("Added raw_mark column")
                
                if 'max_raw_mark' not in columns:
                    conn.execute(sa.text('ALTER TABLE mark ADD COLUMN max_raw_mark FLOAT'))
                    print("Added max_raw_mark column")
                
                # Copy data from old columns to new columns
                conn.execute(sa.text('UPDATE mark SET raw_mark = mark WHERE raw_mark IS NULL'))
                conn.execute(sa.text('UPDATE mark SET max_raw_mark = total_marks WHERE max_raw_mark IS NULL'))
                
                # Calculate percentage for marks that don't have it
                conn.execute(sa.text('''
                    UPDATE mark 
                    SET percentage = (raw_mark / max_raw_mark) * 100 
                    WHERE percentage IS NULL AND max_raw_mark > 0
                '''))
                
                # Set percentage to 0 for marks with max_raw_mark = 0
                conn.execute(sa.text('''
                    UPDATE mark 
                    SET percentage = 0 
                    WHERE percentage IS NULL AND max_raw_mark = 0
                '''))
                
                # Make percentage column NOT NULL
                # SQLite doesn't support ALTER COLUMN, so we need to handle this differently
                if 'sqlite' in db_uri:
                    print("SQLite detected - percentage column will remain nullable but all values are set")
                else:
                    conn.execute(sa.text('ALTER TABLE mark ALTER COLUMN percentage SET NOT NULL'))
                    print("Made percentage column NOT NULL")
                
                print("Migration completed successfully!")
        
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            session.rollback()
        finally:
            session.close()

if __name__ == "__main__":
    migrate_marks()
