#!/usr/bin/env python3
"""
Idempotent migration to ensure assessment configuration tables exist.
Creates `assessment_weights_config`, `missing_policy_config`, and includes rounding table.

Run:
  python -m new_structure.migrations.create_assessment_config_tables
or
  python new_structure/migrations/create_assessment_config_tables.py
"""
import sys
import os
from urllib.parse import quote_plus

# Ensure project root on path when executed directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
GRANDPARENT_DIR = os.path.dirname(PARENT_DIR)
sys.path.insert(0, GRANDPARENT_DIR)


def _compose_db_uri() -> str:
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', '3306') or 3306)
    user = os.environ.get('MYSQL_USER', 'root')
    pwd_raw = os.environ.get('MYSQL_PASSWORD', '')
    pwd = quote_plus(pwd_raw) if pwd_raw else ''
    dbname = os.environ.get('MYSQL_DATABASE', 'hillview_demo001')
    return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{dbname}?charset=utf8mb4"


def main() -> int:
    try:
        from flask import Flask
        from new_structure.extensions import db
        # Import only the models we need so metadata is limited
        from new_structure.models import assessment_config  # noqa: F401
        from new_structure.models import rounding_config  # noqa: F401

        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = _compose_db_uri()
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(app)
        with app.app_context():
            inspector = db.inspect(db.engine)
            existing = set(inspector.get_table_names())
            targets = {'assessment_weights_config', 'missing_policy_config', 'rounding_mode_config'}
            missing = targets - existing
            if not missing:
                print('✅ Assessment config tables already exist.')
                return 0
            print(f'🛠️ Creating missing tables: {sorted(missing)}')
            db.create_all()
            # Re-check
            new_existing = set(db.inspect(db.engine).get_table_names())
            still_missing = targets - new_existing
            if still_missing:
                print(f'❌ Failed to create tables: {sorted(still_missing)}')
                return 2
            print('✅ Assessment config tables created successfully.')
            return 0
    except Exception as e:
        print(f'❌ Migration error: {e}')
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
