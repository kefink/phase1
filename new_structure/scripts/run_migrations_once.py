import os
import sys

# Ensure package is importable when running this script directly
current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.dirname(current_dir)
workspace_dir = os.path.dirname(pkg_dir)
for p in (workspace_dir, pkg_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from new_structure import create_app


def main():
    # Lightweight .env loader (sync with run.py)
    def _load_env_file():
        candidates = [
            os.path.join(pkg_dir, '.env'),
            os.path.join(pkg_dir, '.env.development'),
            os.path.join(pkg_dir, '.env.local'),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for raw in f:
                            line = raw.strip()
                            if not line or line.startswith('#'):
                                continue
                            if '=' not in line:
                                continue
                            key, val = line.split('=', 1)
                            key = key.strip()
                            val = val.strip().strip('"').strip("'")
                            if key and key not in os.environ:
                                os.environ[key] = val
                    break
                except Exception:
                    pass

    _load_env_file()

    app = create_app('development')
    with app.app_context():
        from new_structure.migrations.add_revoked_at_to_permissions import run_migration as m1
        from new_structure.migrations.add_grade_stream_to_permission_requests import run_migration as m2
        r1 = m1(app)
        r2 = m2(app)
        print({'revoked_at': r1, 'permission_requests_cols': r2})


if __name__ == '__main__':
    main()
