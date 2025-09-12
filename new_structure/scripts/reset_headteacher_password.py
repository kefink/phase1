"""Utility to reset the headteacher password to a known value.

Run:
    python scripts/reset_headteacher_password.py

Optional custom password:
    python scripts/reset_headteacher_password.py newpassword123
"""
from __future__ import annotations
import sys, os

# Ensure package import path similar to run.py
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))  # new_structure directory
parent_dir = os.path.dirname(root_dir)
for p in (parent_dir, root_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from new_structure import create_app  # type: ignore
from new_structure.extensions import db  # type: ignore
from new_structure.models.user import Teacher  # type: ignore

RESET_USERNAME = 'headteacher'
RESET_ROLE = 'headteacher'

def reset(new_password: str = 'admin123') -> None:
    app = create_app()
    with app.app_context():
        teacher = Teacher.query.filter_by(username=RESET_USERNAME, role=RESET_ROLE).first()
        if not teacher:
            print(f"❌ No user found with username='{RESET_USERNAME}' role='{RESET_ROLE}'")
            return
        before_hash = teacher.password
        teacher.set_password(new_password)
        db.session.commit()
        after_hash = teacher.password
        changed = before_hash != after_hash
        print("✅ Password reset executed" if changed else "ℹ️ Hash unchanged (was already same value)")
        print(f"Username: {teacher.username}")
        print(f"Role: {teacher.role}")
        print(f"New password (plaintext you can log in with): {new_password}")
        print(f"Stored hash prefix: {after_hash.split(':',1)[0] if ':' in after_hash else 'plain?'}")
        print("Login test: use the normal headteacher login form with the password above.")

if __name__ == '__main__':
    pwd = sys.argv[1] if len(sys.argv) > 1 else 'admin123'
    reset(pwd)
