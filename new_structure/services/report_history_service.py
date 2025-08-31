"""
Report History Service: track generated subject reports per teacher with filters.

Uses a JSON file in cache/reports as the primary storage to avoid DB migrations.
If a SQLAlchemy model named SubjectReportHistory is present, will attempt to use it.
"""
from __future__ import annotations

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import url_for

HISTORY_DIR = os.path.join('cache', 'reports')
HISTORY_FILE = os.path.join(HISTORY_DIR, 'history.json')


def _ensure_history_file():
    os.makedirs(HISTORY_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)


def _read_history() -> Dict[str, List[dict]]:
    _ensure_history_file()
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


def _write_history(data: Dict[str, List[dict]]):
    _ensure_history_file()
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_subject_report(
    *,
    teacher_id: int,
    subject_id: int,
    subject_name: str,
    grade_id: int,
    grade_name: str,
    stream_id: Optional[int],
    stream_name: str,
    term_id: int,
    term_name: str,
    assessment_type_id: int,
    assessment_type_name: str,
    total_students: int,
    students_with_marks: int,
    class_average: float,
) -> dict:
    """Append a report record for a teacher.

    Returns the stored record.
    """
    # JSON/file-based persistence
    data = _read_history()
    key = f"teacher_{teacher_id}"
    entries = data.get(key, [])

    record = {
        'id': str(uuid.uuid4()),
        'teacher_id': teacher_id,
        'subject_id': subject_id,
        'subject': subject_name,
        'grade_id': grade_id,
        'grade': grade_name,
        'stream_id': stream_id,
        'stream': stream_name,
        'term_id': term_id,
        'term': term_name,
        'assessment_type_id': assessment_type_id,
        'assessment_type': assessment_type_name,
        'total_students': total_students,
        'students_with_marks': students_with_marks,
        'class_average': round(float(class_average or 0), 2),
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }

    # Deduplicate recent exact same combination (keep latest only)
    entries = [e for e in entries if not (
        e.get('subject_id') == record['subject_id'] and
        e.get('grade_id') == record['grade_id'] and
        e.get('stream_id') == record['stream_id'] and
        e.get('term_id') == record['term_id'] and
        e.get('assessment_type_id') == record['assessment_type_id']
    )]

    entries.insert(0, record)
    # Cap history per teacher to 100 entries
    entries = entries[:100]
    data[key] = entries
    _write_history(data)

    return record


def list_subject_reports(
    teacher_id: int,
    *,
    subject_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    stream_id: Optional[int] = None,
    term_id: Optional[int] = None,
    assessment_type_id: Optional[int] = None,
) -> List[dict]:
    """Return filtered report history for a teacher, newest first."""
    data = _read_history()
    entries = data.get(f"teacher_{teacher_id}", [])

    def match(e: dict) -> bool:
        return (
            (subject_id is None or e.get('subject_id') == subject_id) and
            (grade_id is None or e.get('grade_id') == grade_id) and
            (stream_id is None or e.get('stream_id') == stream_id) and
            (term_id is None or e.get('term_id') == term_id) and
            (assessment_type_id is None or e.get('assessment_type_id') == assessment_type_id)
        )

    # entries are already newest first; filter preserves order
    return [e for e in entries if match(e)]


def build_view_url(entry: dict) -> str:
    """Build a URL to view the report for a history entry."""
    return url_for(
        'teacher.generate_subject_report',
        subject=entry.get('subject'),
        grade=entry.get('grade'),
        stream=entry.get('stream'),
        term=entry.get('term'),
        assessment_type=entry.get('assessment_type')
    )
