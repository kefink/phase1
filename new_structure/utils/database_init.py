"""MySQL-first database initialization utilities.

Replaces legacy SQLite-specific logic with pure SQLAlchemy-based
initialization so the project operates cleanly against MySQL.
"""

from __future__ import annotations

import logging
from ..extensions import db
from ..utils.constants import (
    EDUCATION_LEVELS_ORDER,
    educational_level_mapping,
    get_education_level_for_grade_name,
)

logger = logging.getLogger(__name__)


def create_all_tables() -> bool:
    """Create all tables via model metadata (idempotent)."""
    try:
        # Import models to register metadata
        from ..models import user  # noqa: F401
        from ..models import academic  # noqa: F401
        from ..models import assignment  # noqa: F401
        # Include assessment configuration models so tables are created
        from ..models import assessment_config  # noqa: F401
        try:
            from ..models import permission  # noqa: F401
        except Exception:
            pass
        try:
            from ..models import function_permission  # noqa: F401
        except Exception:
            pass
        from ..models import parent  # noqa: F401
        from ..models import report_config  # noqa: F401
        from ..models import school_setup  # noqa: F401
        # Include grading system models so tables are created
        from ..models import grading_system  # noqa: F401
        # Include rounding configuration table
        from ..models import rounding_config  # noqa: F401

        db.create_all()
        logger.info("✅ Tables ensured (SQLAlchemy metadata create_all)")
        return True
    except Exception as e:  # pragma: no cover
        logger.error("Error creating tables: %s", e)
        return False


def initialize_default_data() -> bool:
    """Seed baseline data if empty; always ensure assessment defaults exist."""
    try:
        from ..models.user import Teacher
        from ..models.assessment_config import AssessmentWeightsConfig, MissingPolicyConfig
        from ..models.grading_system import initialize_default_grading_systems
        from ..models.academic import Grade, Stream
        import json

        teacher_exists = bool(Teacher.query.first())
        if not teacher_exists:
            _create_default_users()
            _create_default_academic_structure()
            _create_default_subjects()
            _create_default_school_config()
        else:
            # Even if teachers already exist, ensure required grades/streams exist (idempotent)
            _ensure_required_grades_and_streams()

        # Seed assessment config defaults per education level to avoid 1146 queries
        levels = [lvl for lvl in EDUCATION_LEVELS_ORDER if lvl in educational_level_mapping]
        default_weights = {
            "CAT 1": 20.0,
            "CAT 2": 30.0,
            "End Term Exam": 50.0
        }
        default_policies = {
            "ABS": "exclude",
            "EXC": "exclude",
            "MED": "exclude",
            "NA": "exclude",
            "INC": "zero"
        }
        for lvl in levels:
            if not AssessmentWeightsConfig.query.filter_by(education_level=lvl, is_active=True).first():
                db.session.add(AssessmentWeightsConfig(
                    education_level=lvl,
                    weights_json=json.dumps(default_weights),
                    is_active=True
                ))
            if not MissingPolicyConfig.query.filter_by(education_level=lvl, is_active=True).first():
                db.session.add(MissingPolicyConfig(
                    education_level=lvl,
                    policies_json=json.dumps(default_policies),
                    is_active=True
                ))

        # Seed default grading systems (idempotent)
        try:
            initialize_default_grading_systems()
        except Exception as _e:
            logger.warning(f"Grading systems init skipped: {_e}")

        db.session.commit()
        if not teacher_exists:
            logger.info("🎉 Default base data seeded successfully")
        logger.info("🧮 Ensured assessment defaults exist")
        return True
    except Exception as e:  # pragma: no cover
        logger.error("Error seeding defaults: %s", e)
        db.session.rollback()
        return False


def _create_default_users() -> None:
    from ..models.user import Teacher

    default_users = [
        {"username": "headteacher", "password": "admin123", "role": "headteacher", "first_name": "Head", "last_name": "Teacher", "employee_id": "HT001"},
        {"username": "classteacher1", "password": "class123", "role": "classteacher", "first_name": "Class", "last_name": "Teacher One", "employee_id": "CT001"},
        {"username": "kevin", "password": "kev123", "role": "classteacher", "first_name": "Kevin", "last_name": "Teacher", "employee_id": "CT002"},
        {"username": "telvo", "password": "telvo123", "role": "teacher", "first_name": "Telvo", "last_name": "Subject Teacher", "employee_id": "ST001"},
    ]
    for data in default_users:
        pwd = data.pop("password")
        t = Teacher(**data)
        t.set_password(pwd)
        db.session.add(t)
    logger.info("👥 Default users added")


def _create_default_academic_structure() -> None:
    from ..models.academic import Grade, Stream, Term, AssessmentType

    # Build grades from canonical mapping (pre_primary through senior_secondary)
    grade_level_map = []
    for lvl in EDUCATION_LEVELS_ORDER:
        for gname in educational_level_mapping.get(lvl, []):
            grade_level_map.append((gname, lvl))

    grades = []
    for name, level in grade_level_map:
        g = Grade(name=name, education_level=level)
        db.session.add(g)
        grades.append(g)

    # Streams (A,B) per grade
    db.session.flush()  # ensure IDs
    for g in grades:
        for stream_name in ("A", "B"):
            db.session.add(Stream(name=stream_name, grade_id=g.id))

    terms = [
        {"name": "Term 1", "academic_year": "2024", "is_current": True},
        {"name": "Term 2", "academic_year": "2024", "is_current": False},
        {"name": "Term 3", "academic_year": "2024", "is_current": False},
    ]
    for t in terms:
        db.session.add(Term(**t))

    assessments = [
        {"name": "CAT 1"},
        {"name": "CAT 2"},
        {"name": "End Term Exam"},
        {"name": "Assignment"},
        {"name": "Project"},
    ]
    for a in assessments:
        db.session.add(AssessmentType(**a))

    logger.info("🏗️ Academic structure seeded")


def _ensure_required_grades_and_streams() -> None:
    """Ensure PP1, PP2, and Grades 1–9 exist with default streams A,B (idempotent)."""
    try:
        from ..models.academic import Grade, Stream
        required = []
        for lvl in EDUCATION_LEVELS_ORDER:
            for gname in educational_level_mapping.get(lvl, []):
                required.append((gname, lvl))
        existing = {g.name: g for g in Grade.query.all()}
        created = []
        for name, level in required:
            g = existing.get(name)
            if not g:
                g = Grade(name=name, education_level=level)
                db.session.add(g)
                db.session.flush()
                created.append(name)
            # Ensure streams A,B exist for this grade
            try:
                # Fetch streams lazily via relationship if available
                existing_streams = {s.name for s in getattr(g, 'streams', [])}
            except Exception:
                existing_streams = set()
            for sname in ("A", "B"):
                if sname not in existing_streams:
                    db.session.add(Stream(name=sname, grade_id=g.id))
        if created:
            logger.info("➕ Created missing grades: %s", ", ".join(created))
    except Exception as e:
        logger.warning("Ensure required grades skipped: %s", e)


def _create_default_subjects() -> None:
    from ..models.academic import Subject

    subjects = [
        # Lower Primary
        ("English", "lower_primary", True),
        ("Kiswahili", "lower_primary", True),
        ("Mathematics", "lower_primary", False),
        ("Environmental Activities", "lower_primary", False),
        # Upper Primary
        ("English", "upper_primary", True),
        ("Kiswahili", "upper_primary", True),
        ("Mathematics", "upper_primary", False),
        ("Science & Technology", "upper_primary", False),
        # Junior Secondary
        ("English", "junior_secondary", True),
        ("Kiswahili", "junior_secondary", True),
        ("Mathematics", "junior_secondary", False),
        ("Integrated Science", "junior_secondary", False),
    ]
    for name, level, composite in subjects:
        db.session.add(Subject(name=name, education_level=level, is_composite=composite))
    logger.info("📚 Subjects seeded")


def _create_default_school_config() -> None:
    from ..models.academic import SchoolConfiguration
    cfg = SchoolConfiguration(
        school_name="Hillview School",
        school_motto="Excellence in Education",
        current_academic_year="2024",
        current_term="Term 1",
        headteacher_name="Head Teacher",
    )
    db.session.add(cfg)
    logger.info("🏫 School configuration created")


def check_database_integrity() -> dict:
    """Return lightweight integrity snapshot."""
    try:
        from ..models.user import Teacher
        from ..models.academic import Subject, Grade, Stream
        teacher_count = Teacher.query.count()
        subject_count = Subject.query.count()
        grade_count = Grade.query.count()
        stream_count = Stream.query.count()
        # Verify required grade names exist
        required_names = set()
        for lvl in EDUCATION_LEVELS_ORDER:
            required_names.update(educational_level_mapping.get(lvl, []))
        existing_names = {g.name for g in Grade.query.all()}
        required_ok = required_names.issubset(existing_names)
        status = "healthy" if (teacher_count and subject_count and required_ok) else "needs_initialization"
        return {
            "tables_exist": True,
            "has_data": teacher_count > 0 and subject_count > 0,
            "teacher_count": teacher_count,
            "subject_count": subject_count,
            "grade_count": grade_count,
            "stream_count": stream_count,
            "required_grades_ok": required_ok,
            "status": status,
        }
    except Exception as e:  # pragma: no cover
        return {"tables_exist": False, "has_data": False, "error": str(e), "status": "error"}


def initialize_database_completely() -> dict:
    logger.info("🚀 Starting database initialization (MySQL mode)")
    if not create_all_tables():
        return {"success": False, "error": "Failed to create tables"}
    if not initialize_default_data():
        return {"success": False, "error": "Failed to seed default data"}
    status = check_database_integrity()
    if status.get("status") == "healthy":
        return {"success": True, "status": status}
    return {"success": False, "status": status, "error": "Integrity check failed"}


def repair_database() -> dict:
    logger.info("🔧 Repair requested")
    before = check_database_integrity()
    if before.get("status") != "healthy":
        create_all_tables()
        initialize_default_data()
    after = check_database_integrity()
    return {"success": after.get("status") == "healthy", "before": before, "after": after}


if __name__ == "__main__":  # Manual diagnostic
    snap = check_database_integrity()
    print("Integrity:", snap)
    if snap.get("status") != "healthy":
        print(initialize_database_completely())
    else:
        print("Already healthy")
