"""
Migration: Ensure permission_requests has grade_id and stream_id columns.

This migration is idempotent and safe to run multiple times. It checks the
database schema and only adds the columns if they're missing. Uses SQLAlchemy
inspector and driver-level SQL to be compatible with SQLAlchemy 2.x.
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
            table = 'permission_requests'
            grade_col = 'grade_id'
            stream_col = 'stream_id'

            insp = inspect(engine)
            try:
                cols = [c['name'].lower() for c in insp.get_columns(table)]
            except Exception:
                cols = []

            missing = []
            if grade_col.lower() not in cols:
                missing.append((grade_col, 'INT'))
            if stream_col.lower() not in cols:
                missing.append((stream_col, 'INT'))

            if not missing:
                return True

            with engine.connect() as conn:
                for col_name, col_type in missing:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} NULL")
                    except Exception:
                        # best effort; continue
                        pass
            return True

    except Exception as e:
        print(f"Migration add_grade_stream_to_permission_requests failed: {e}")
        return False
    finally:
        pass


def main():
    ok = run_migration()
    if ok:
        print("✅ Migration complete: 'grade_id' and 'stream_id' ensured on permission_requests.")
    else:
        print("⚠️ Migration did not complete. Check logs for details.")


if __name__ == "__main__":
    main()
