"""Audit Teacher password hashing state.

Reports:
 - total teachers
 - rows with NULL canonical password column
 - rows where password does not use an accepted scheme
 - sample of first 5 problematic rows (ids)

Run with application context: python -m new_structure.scripts.audit_password_hashes
"""

import os, sys
from sqlalchemy import text, inspect

# Ensure parent directory (which contains the package) is on path
PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PARENT_OF_PACKAGE = os.path.abspath(os.path.join(PACKAGE_ROOT, '..'))
for p in (PARENT_OF_PACKAGE, PACKAGE_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import new_structure  # noqa: E402
from new_structure.extensions import db  # noqa: E402

ACCEPTED_PREFIXES = ("scrypt:", "pbkdf2:")

def main():
    app = new_structure.create_app()
    with app.app_context():
        conn = db.session
        inspector = inspect(db.engine)
        cols = {c['name'] for c in inspector.get_columns('teacher')}
        pwd_col = 'password_hash' if 'password_hash' in cols else 'password'
        total = conn.execute(text("SELECT COUNT(*) FROM teacher")).scalar() or 0
        nulls = conn.execute(text(f"SELECT COUNT(*) FROM teacher WHERE {pwd_col} IS NULL")).scalar() or 0
        bad_scheme = conn.execute(text(f"SELECT COUNT(*) FROM teacher WHERE {pwd_col} IS NOT NULL AND {pwd_col} NOT LIKE 'scrypt:%' AND {pwd_col} NOT LIKE 'pbkdf2:%'" )).scalar() or 0
        plain_mismatch = 0  # after rename we no longer track mismatch legacy
        sample_ids = conn.execute(text(f"SELECT id FROM teacher WHERE {pwd_col} IS NULL OR ({pwd_col} NOT LIKE 'scrypt:%' AND {pwd_col} NOT LIKE 'pbkdf2:%') LIMIT 5")).fetchall()
        print({
            'total_teachers': total,
            'null_hashes': nulls,
            'non_accepted_scheme': bad_scheme,
            'hash_plain_mismatch': plain_mismatch,
            'sample_problem_ids': [r[0] for r in sample_ids],
            'healthy': nulls == 0 and bad_scheme == 0
        })

if __name__ == '__main__':
    main()
