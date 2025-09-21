"""
Seed script to initialize default grading systems for development/testing.
Usage:
    python -m new_structure.scripts.seed_grading_system

This version intentionally avoids the full app factory (blueprints, MySQL),
so it can run in isolation using TestingConfig (SQLite in-memory).
It also verifies that bands are resolvable and that mapping works when enabled.
"""
from flask import Flask
import os

from ..extensions import db
from ..config import TestingConfig
from ..models.grading_system import initialize_default_grading_systems


def main():
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    # Ensure flag is on for verification of mapping via utils.performance
    os.environ['REPORTS_USE_MARK_CALCULATOR'] = 'true'
    db.init_app(app)

    with app.app_context():
        # Initialize schema (SQLite in-memory)
        db.create_all()
        # Seed default grading systems
        initialize_default_grading_systems()
        print("Seeded default grading systems (TestingConfig/SQLite).")

        # Verify: fetch bands and sample mappings
        try:
            from ..services.grading_service import GradingService
            bands = GradingService.get_calculator_grade_bands()
            print("Resolved bands:")
            for b in bands:
                print(f"  {b.min_inclusive}-{b.max_inclusive}: grade={b.grade}, points={b.points}")

            from ..utils.performance import get_grade_and_points
            print("Sample mappings (using utils.performance with flag on):")
            for avg in [35, 45, 55, 65, 85, 95]:
                g, p = get_grade_and_points(avg)
                print(f"  {avg}% -> grade={g}, points={p}")
        except Exception as e:
            print(f"Verification skipped due to error: {e}")


if __name__ == "__main__":
    main()
