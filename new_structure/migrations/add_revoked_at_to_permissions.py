"""
Migration: Ensure class_teacher_permissions has revoked_at column.

This migration is safe to run multiple times. It checks the database schema
and only adds the column if it's missing. Uses SQLAlchemy inspector and
driver-level SQL to be compatible with SQLAlchemy 2.x.
"""

from typing import Optional


def run_migration(app=None) -> bool:
    """Run the migration using the Flask app's SQLAlchemy engine.

    Returns True if the migration succeeded or was already applied.
    """
    created_app = None
    try:
        if app is None:
            from new_structure import create_app
            created_app = create_app('development')
            app = created_app

        with app.app_context():
            from new_structure.extensions import db
            from sqlalchemy import inspect

            engine = db.engine
            table = 'class_teacher_permissions'
            column = 'revoked_at'

            insp = inspect(engine)
            try:
                cols = [c['name'].lower() for c in insp.get_columns(table)]
            except Exception:
                cols = []

            if column.lower() in cols:
                return True

            # Add column via driver SQL (works for MySQL/SQLite generically)
            with engine.connect() as conn:
                try:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} DATETIME NULL")
                    return True
                except Exception:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} TIMESTAMP NULL")
                        return True
                    except Exception:
                        return False

    except Exception as e:
        print(f"Migration add_revoked_at_to_permissions failed: {e}")
        return False
    finally:
        pass


def main():
    ok = run_migration()
    if ok:
        print("✅ Migration complete: 'revoked_at' column ensured on class_teacher_permissions.")
    else:
        print("⚠️ Migration did not complete. Check logs for details.")


if __name__ == "__main__":
    main()
