#!/usr/bin/env python3
"""
Seed default assessment weights and missing policies per education level if none exist.
Safe to run multiple times; it only inserts when active configs are missing.
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
        from new_structure.models.assessment_config import AssessmentWeightsConfig, MissingPolicyConfig
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = _compose_db_uri()
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        with app.app_context():
            import json
            try:
                from new_structure.utils.constants import EDUCATION_LEVELS_ORDER
                levels = [lvl for lvl in EDUCATION_LEVELS_ORDER if lvl in {'lower_primary','upper_primary','junior_secondary'}]
            except Exception:
                levels = ['lower_primary', 'upper_primary', 'junior_secondary']
            default_weights = {"CAT 1": 20.0, "CAT 2": 30.0, "End Term Exam": 50.0}
            default_policies = {"ABS": "exclude", "EXC": "exclude", "MED": "exclude", "NA": "exclude", "INC": "zero"}
            inserted = []
            for lvl in levels:
                w = AssessmentWeightsConfig.query.filter_by(education_level=lvl, is_active=True).first()
                if not w:
                    db.session.add(AssessmentWeightsConfig(education_level=lvl, weights_json=json.dumps(default_weights), is_active=True))
                    inserted.append(f"weights:{lvl}")
                p = MissingPolicyConfig.query.filter_by(education_level=lvl, is_active=True).first()
                if not p:
                    db.session.add(MissingPolicyConfig(education_level=lvl, policies_json=json.dumps(default_policies), is_active=True))
                    inserted.append(f"policies:{lvl}")
            if inserted:
                db.session.commit()
                print(f"✅ Seeded defaults: {inserted}")
            else:
                print("✅ Defaults already present; nothing to do.")
            return 0
    except Exception as e:
        print(f"❌ Seed error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
