"""
Quick DB connectivity check using SQLAlchemy and the app's configuration.

Usage:
  python scripts/db_ping.py

Reads DATABASE_URL from environment (or Config fallbacks) and attempts a simple
SELECT 1; prints success or the error encountered.
"""
import os
import sys


def _load_env_file():
    # Try to load ../.env similar to run.py
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    env_path = os.path.join(root, '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    k = k.strip(); v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


def main():
    # Ensure project root on sys.path
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    sys.path.insert(0, root)
    sys.path.insert(0, os.path.dirname(root))

    _load_env_file()

    from new_structure import create_app
    from new_structure.extensions import db
    from sqlalchemy import text

    app = create_app('development')
    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    print(f"Using SQLALCHEMY_DATABASE_URI=\n  {uri}")

    with app.app_context():
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text('SELECT 1'))
                row = result.scalar_one()
                print(f"✅ DB ping successful (SELECT 1 -> {row})")
        except Exception as e:
            print("❌ DB ping failed:", e)
            raise


if __name__ == '__main__':
    main()
