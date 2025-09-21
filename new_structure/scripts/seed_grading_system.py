"""
Seed script to initialize default grading systems for development/testing.
Usage:
    python -m new_structure.scripts.seed_grading_system
"""
from ..models.grading_system import initialize_default_grading_systems
from ..extensions import db
from flask import Flask


def main():
    # Build a minimal Flask app context if not already created
    from .. import create_app  # assume app factory exists
    app = create_app()
    with app.app_context():
        initialize_default_grading_systems()
        print("Seeded default grading systems.")


if __name__ == "__main__":
    main()
