"""MySQL-first database initialization utilities.

Replaces legacy SQLite-specific logic with pure SQLAlchemy-based
initialization so the project operates cleanly against MySQL.
"""

from __future__ import annotations

import logging
from ..extensions import db

logger = logging.getLogger(__name__)


def create_all_tables() -> bool:
    """Create all tables via model metadata (idempotent)."""
    try:
        # Import models to register metadata
        from ..models import user  # noqa: F401
        from ..models import academic  # noqa: F401
        from ..models import assignment  # noqa: F401
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

        db.create_all()
        logger.info("✅ Tables ensured (SQLAlchemy metadata create_all)")
        return True
    except Exception as e:  # pragma: no cover
        logger.error("Error creating tables: %s", e)
        return False


def initialize_default_data() -> bool:
    """Seed baseline data only if empty."""
    try:
        from ..models.user import Teacher
        if Teacher.query.first():
            logger.info("Database already seeded; skipping defaults")
            return True

        _create_default_users()
        _create_default_academic_structure()
        _create_default_subjects()
        _create_default_school_config()
        db.session.commit()
        logger.info("🎉 Default data seeded successfully")
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

    grade_level_map = [
        ("Grade 1", "lower_primary"),
        ("Grade 2", "lower_primary"),
        ("Grade 3", "lower_primary"),
        ("Grade 4", "upper_primary"),
        ("Grade 5", "upper_primary"),
        ("Grade 6", "upper_primary"),
        ("Grade 7", "junior_secondary"),
        ("Grade 8", "junior_secondary"),
        ("Grade 9", "junior_secondary"),
    ]

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
        return {
            "tables_exist": True,
            "has_data": teacher_count > 0 and subject_count > 0,
            "teacher_count": teacher_count,
            "subject_count": subject_count,
            "grade_count": grade_count,
            "stream_count": stream_count,
            "status": "healthy" if teacher_count and subject_count else "needs_initialization",
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
