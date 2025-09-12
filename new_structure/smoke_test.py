import os, sys

# Ensure parent directory (containing the new_structure package) is on path when executed directly
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from new_structure import create_app  # type: ignore
from new_structure.extensions import db  # type: ignore

# Simple smoke test to validate app context, DB connectivity, and a basic table exists.
# Usage: python smoke_test.py

def main():
    app = create_app()
    with app.app_context():
        # Basic DB check: list first 3 tables
        insp = db.inspect(db.engine)
        tables = insp.get_table_names()[:3]
        print("Smoke OK - sample tables:", tables)

if __name__ == "__main__":
    main()
