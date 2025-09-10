"""Class Report Builder Service

Consolidates the logic previously embedded in `preview_class_report` view so it can
be reused, tested, and safely evolved. This is an extraction (no intentional
behavior changes) – key output keys are preserved to avoid template regressions.

Contract:
    build(grade, stream, term, assessment_type, selected_subject_ids=None) -> dict

Returned dict contains (superset of prior context variables):
    report_data, education_level, current_date, subject_names, abbreviated_subjects,
    class_data, stats, subject_averages, class_average, class_total,
    subject_components, component_marks_data, component_averages, filtered_subjects,
    staff_info, school_info, logo_url, visibility, is_aggregated

Error Handling:
    On any blocking validation issue returns {'error': 'message'}.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from flask import url_for

from ..extensions import db
from ..models.academic import (
    Grade, Stream, Term, AssessmentType, Subject, Student, Mark
)
from ..services.staff_assignment_service import StaffAssignmentService
from ..services.school_config_service import SchoolConfigService
from ..services.report_config_service import ReportConfigService

# Reuse existing helper used by original route
from ..utils.cache_utils import invalidate_cache  # type: ignore
# get_class_report_data lives in report_service exposed via services __init__
from ..services import get_class_report_data  # type: ignore


class ClassReportBuilder:
    """Builder for class report context."""

    _cache: Dict[str, Dict[str, Any]] = {}
    _CACHE_MAX = 64  # simple bound

    @staticmethod
    def _derive_education_level(grade_name: str, report_data: Dict[str, Any]) -> str:
        if report_data.get("education_level"):
            code = report_data["education_level"]
            mapping = {
                "lower_primary": "lower primary",
                "upper_primary": "upper primary",
                "junior_secondary": "junior secondary",
            }
            return mapping.get(code, "")
        try:
            grade_num = int(grade_name.split()[1]) if len(grade_name.split()) > 1 else int(grade_name)
        except Exception:
            return ""
        if 1 <= grade_num <= 3:
            return "lower primary"
        if 4 <= grade_num <= 6:
            return "upper primary"
        if 7 <= grade_num <= 9:
            return "junior secondary"
        return ""

    @staticmethod
    def build(
        grade: str,
        stream: str,
        term: str,
        assessment_type: str,
        selected_subject_ids: Optional[List[int]] = None,
        invalidate: bool = True,
    ) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {}

        cache_key = f"{grade}|{stream}|{term}|{assessment_type}|{','.join(map(str, selected_subject_ids or []))}"
        if not invalidate and cache_key in ClassReportBuilder._cache:
            return ClassReportBuilder._cache[cache_key]

        # Normalize stream letter (allow forms like "Stream B")
        if stream.startswith("Stream "):
            stream_letter = stream.replace("Stream ", "")
        else:
            stream_letter = stream[-1] if len(stream) > 1 else stream

        try:
            stream_obj = Stream.query.join(Grade).filter(Grade.name == grade, Stream.name == stream_letter).first()
            term_obj = Term.query.filter_by(name=term).first()
            assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()
        except Exception as e:
            return {"error": f"Database lookup error: {e}"}

        if not (stream_obj and term_obj and assessment_type_obj):
            return {"error": "Invalid grade, stream, term, or assessment type"}

        # Invalidate cache (retain original semantics)
        if invalidate:
            try:
                invalidate_cache(grade, stream, term, assessment_type)
            except Exception:
                pass  # Non-fatal

        # Core report data (existing helper)
        report_data = get_class_report_data(
            grade,
            stream,
            term,
            assessment_type,
            selected_subject_ids=selected_subject_ids or [],
        ) or {}
        if report_data.get("error"):
            return {"error": report_data["error"]}

        education_level = ClassReportBuilder._derive_education_level(grade, report_data)

        # Convert education level to code for subject queries
        if education_level == "lower primary":
            education_level_code = "lower_primary"
        elif education_level == "upper primary":
            education_level_code = "upper_primary"
        elif education_level == "junior secondary":
            education_level_code = "junior_secondary"
        else:
            education_level_code = ""

        # Students for target stream
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        student_ids = [s.id for s in students]

        # Candidate subjects for this education level
        if education_level_code:
            all_education_subjects = Subject.query.filter_by(education_level=education_level_code).all()
        else:
            all_education_subjects = Subject.query.all()

        # Filter subjects by selected ids (if provided)
        if selected_subject_ids:
            filtered_subjects = [s for s in all_education_subjects if s.id in selected_subject_ids]
        else:
            filtered_subjects = all_education_subjects

        subject_names = [s.name for s in filtered_subjects]

        # Fetch marks for those students/subjects in chosen term & assessment
        if subject_names:
            all_marks = (
                Mark.query.filter(
                    Mark.student_id.in_(student_ids),
                    Mark.subject_id.in_([s.id for s in filtered_subjects]),
                    Mark.term_id == term_obj.id,
                    Mark.assessment_type_id == assessment_type_obj.id,
                ).all()
            )
        else:
            all_marks = []

        # Index marks: {student_id: {subject_id: percentage}}
        marks_index: Dict[int, Dict[int, float]] = {}
        for mark in all_marks:
            if mark.student_id not in marks_index:
                marks_index[mark.student_id] = {}
            # Prefer stored percentage; else compute
            if getattr(mark, "percentage", None) is not None:
                pct = mark.percentage
            else:
                raw = getattr(mark, "raw_mark", None)
                if raw is None:
                    raw = getattr(mark, "mark", 0)
                max_raw = getattr(mark, "max_raw_mark", None)
                if max_raw is None or max_raw <= 0:
                    # Fallbacks present in Mark model
                    max_raw = getattr(mark, "total_marks", 100) or 100
                pct = (raw / max_raw) * 100 if max_raw else 0
                if pct > 100:
                    pct = 100.0
            marks_index[mark.student_id][mark.subject_id] = pct

        class_data = report_data.get("class_data", [])

        # Augment each student entry with filtered marks / totals
        for student_record in class_data:
            stud = Student.query.filter_by(name=student_record.get("student")).first()
            if not stud:
                # Leave existing marks structure
                continue
            student_record["student_id"] = stud.id
            filtered_marks = {}
            total_val = 0.0
            counted = 0
            for subj in filtered_subjects:
                val = marks_index.get(stud.id, {}).get(subj.id, 0)
                filtered_marks[subj.name] = val
                if val > 0:
                    total_val += val
                    counted += 1
            student_record["filtered_marks"] = filtered_marks
            student_record["filtered_total"] = total_val
            per_subject_possible = report_data.get("total_marks", 100) or 100
            student_record["total_possible_marks"] = per_subject_possible * max(len(subject_names), 1)
            student_record["filtered_average"] = (
                (total_val / (counted * per_subject_possible)) * 100 if counted and per_subject_possible else 0
            )

        # Sort by filtered_total desc & assign rank + performance_category
        class_data.sort(key=lambda x: x.get("filtered_total", 0), reverse=True)
        for i, student_record in enumerate(class_data, 1):
            student_record["index"] = i
            student_record["rank"] = i
            avg = student_record.get("filtered_average", 0)
            if avg >= 90:
                cat = "EE1"
            elif avg >= 75:
                cat = "EE2"
            elif avg >= 58:
                cat = "ME1"
            elif avg >= 41:
                cat = "ME2"
            elif avg >= 31:
                cat = "AE1"
            elif avg >= 21:
                cat = "AE2"
            elif avg >= 11:
                cat = "BE1"
            else:
                cat = "BE2"
            student_record["performance_category"] = cat

        # Averages per subject
        subject_averages: Dict[str, float] = {}
        for name in subject_names:
            total = 0.0
            count = 0
            for sd in class_data:
                mv = sd.get("filtered_marks", {}).get(name, 0)
                if mv > 0:
                    total += mv
                    count += 1
            subject_averages[name] = round(total / count, 2) if count else 0

        # Class average (sum of filtered totals / students with any marks)
        class_total = sum(sd.get("filtered_total", 0) for sd in class_data if sd.get("filtered_total", 0) > 0)
        students_with_marks = [sd for sd in class_data if sd.get("filtered_total", 0) > 0]
        class_average = round(class_total / len(students_with_marks), 2) if students_with_marks else 0

        # Abbreviated subject names (stable logic)
        abbreviated_subjects = []
        for subj_name in subject_names:
            parts = subj_name.split()
            if len(parts) > 1:
                abbreviated_subjects.append("".join(p[0].upper() for p in parts))
            else:
                abbreviated_subjects.append(subj_name[:3].upper())

        # Component / composite breakdown (unchanged semantics)
        subject_components = {}
        component_marks_data = {}
        component_averages = {}
        for subj in filtered_subjects:
            if getattr(subj, "is_composite", False):
                components = subj.get_components()
                subject_components[subj.name] = components
                component_averages[subj.name] = {c.name: 0 for c in components}
                component_totals = {}
                component_counts = {}
                for sd in class_data:
                    student_obj = Student.query.filter_by(name=sd.get("student")).first()
                    if not student_obj:
                        continue
                    sid = student_obj.id
                    component_marks_data.setdefault(sid, {})[subj.name] = {}
                    from ..models.academic import ComponentMark  # local import to avoid cyclical
                    for comp in components:
                        cm = (
                            ComponentMark.query.filter_by(component_id=comp.id)
                            .join(Mark, ComponentMark.mark_id == Mark.id)
                            .filter(
                                Mark.student_id == sid,
                                Mark.term_id == term_obj.id,
                                Mark.assessment_type_id == assessment_type_obj.id,
                            )
                            .first()
                        )
                        if cm:
                            raw = cm.raw_mark
                            component_marks_data[sid][subj.name][comp.name] = raw
                            component_totals.setdefault(comp.name, 0)
                            component_counts.setdefault(comp.name, 0)
                            component_totals[comp.name] += raw
                            component_counts[comp.name] += 1
                        else:
                            component_marks_data[sid][subj.name][comp.name] = 0
                for comp in components:
                    if comp.name in component_counts and component_counts[comp.name] > 0:
                        component_averages[subj.name][comp.name] = round(
                            component_totals[comp.name] / component_counts[comp.name], 1
                        )

        # Staff & school info
        staff_info = StaffAssignmentService.get_report_staff_info(grade, stream_letter)
        school_info = SchoolConfigService.get_school_info_dict()
        logo_path = SchoolConfigService.get_school_logo_path()
        logo_url = url_for('static', filename=logo_path)

        report_config_data = ReportConfigService.get_comprehensive_report_data(grade, stream_letter, term)
        if report_config_data:
            visibility = report_config_data.get('visibility', {
                'show_class_teacher': True,
                'show_headteacher': True,
                'show_deputy_headteacher': False,
                'show_principal': False,
            })
        else:
            visibility = {
                'show_class_teacher': True,
                'show_headteacher': True,
                'show_deputy_headteacher': False,
                'show_principal': False,
            }

        ctx.update(
            report_data=report_data,
            education_level=education_level,
            current_date=datetime.now().strftime("%Y-%m-%d"),
            subject_names=subject_names,
            abbreviated_subjects=abbreviated_subjects,
            class_data=class_data,
            stats=report_data.get("stats", {}),
            subject_averages=subject_averages,
            class_average=class_average,
            class_total=class_total,
            subject_components=subject_components,
            component_marks_data=component_marks_data,
            component_averages=component_averages,
            filtered_subjects=filtered_subjects,
            staff_info=staff_info,
            school_info=school_info,
            logo_url=logo_url,
            visibility=visibility,
            is_aggregated=report_data.get("is_aggregated", False),
            education_level_code=education_level_code,
        )
        # Store in cache (simple LRU eviction)
        if len(ClassReportBuilder._cache) >= ClassReportBuilder._CACHE_MAX:
            try:
                first_key = next(iter(ClassReportBuilder._cache))
                ClassReportBuilder._cache.pop(first_key, None)
            except StopIteration:
                pass
        ClassReportBuilder._cache[cache_key] = ctx
        return ctx
