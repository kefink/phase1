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
from ..services.mark_calculator_adapter import build_legends
from ..config import get_config
from ..services.mark_calculator import MarkCalculator, AssessmentEntry, CalculationInput
from ..services.mark_calculator_adapter import (
    get_default_weights, get_default_missing_policies,
    get_effective_weights, get_effective_missing_policies,
)
from ..services.grading_service import GradingService
from ..utils.constants import get_education_level_for_grade_name

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
        # Prefer server-provided code if present
        if report_data.get("education_level"):
            code = report_data["education_level"]
            mapping = {
                "pre_primary": "pre primary",
                "lower_primary": "lower primary",
                "upper_primary": "upper primary",
                "junior_secondary": "junior secondary",
                "senior_secondary": "senior secondary",
            }
            return mapping.get(code, "")
        # Fallback: use centralized helper to derive code from grade name, then map to label
        code = get_education_level_for_grade_name(grade_name)
        label_map = {
            "pre_primary": "pre primary",
            "lower_primary": "lower primary",
            "upper_primary": "upper primary",
            "junior_secondary": "junior secondary",
            "senior_secondary": "senior secondary",
        }
        return label_map.get(code, "")

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
            stream_obj = (
                Stream.query.join(Grade)
                .filter(Grade.name == grade, Stream.name == stream_letter)
                .first()
            )
            # Case-insensitive, trimmed matching for term and assessment type
            term_norm = (term or '').strip()
            assess_norm = (assessment_type or '').strip()
            term_obj = Term.query.filter(db.func.lower(Term.name) == term_norm.lower()).first()
            assessment_type_obj = AssessmentType.query.filter(db.func.lower(AssessmentType.name) == assess_norm.lower()).first()
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
        label_to_code = {
            "pre primary": "pre_primary",
            "lower primary": "lower_primary",
            "upper primary": "upper_primary",
            "junior secondary": "junior_secondary",
            "senior secondary": "senior_secondary",
        }
        education_level_code = label_to_code.get(education_level, "")

        # Students for target stream
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        student_ids = [s.id for s in students]

        # Candidate subjects for this education level (case-insensitive)
        if education_level_code:
            all_education_subjects = Subject.query.filter_by(education_level=education_level_code).all()
        else:
            all_education_subjects = Subject.query.all()
        
        # Handle case-insensitive subject matching for flexible naming
        def normalize_subject_name(name):
            """Normalize subject names for case-insensitive comparison"""
            return name.lower().strip() if name else ""

        # Filter subjects by selected ids (if provided)
        if selected_subject_ids:
            filtered_subjects = [s for s in all_education_subjects if s.id in selected_subject_ids]
        else:
            filtered_subjects = all_education_subjects

        # Group subjects for composite display (English and Kiswahili)
        grouped_subjects = {}
        standalone_subjects = []
        
        # Define composite subject groups with flexible case matching
        composite_groups = {
            'english': {
                'main_name': 'ENGLISH',
                'components': ['english grammar', 'english composition', 'grammar', 'composition', 'grammer'],
                # Per user request, show component headers as ENG GRAM and ENG COMP
                'component_display': ['ENG GRAM', 'ENG COMP']
            },
            'kiswahili': {
                'main_name': 'KISWAHILI', 
                'components': ['kiswahili lugha', 'kiswahili insha', 'lugha', 'insha'],
                'component_display': ['KIS LUGHA', 'KIS INSHA']
            }
        }
        
        # Group subjects by composite categories
        for subject in filtered_subjects:
            normalized_name = normalize_subject_name(subject.name)
            grouped = False
            
            for group_key, group_info in composite_groups.items():
                if any(comp in normalized_name for comp in group_info['components']):
                    if group_key not in grouped_subjects:
                        grouped_subjects[group_key] = {
                            'main_name': group_info['main_name'],
                            'components': [],
                            'component_display': group_info['component_display']
                        }
                    grouped_subjects[group_key]['components'].append(subject)
                    grouped = True
                    break
            
            if not grouped:
                standalone_subjects.append(subject)
        
        # Build final subject list combining composite and standalone
        final_subject_names = []
        final_abbreviated_subjects = []
        composite_structure = {}
        
        # Add composite subjects first
        for group_key, group_data in grouped_subjects.items():
            main_name = group_data['main_name']
            components = group_data['components']
            
            if len(components) >= 2:  # Only if we have multiple components
                final_subject_names.append(main_name)
                final_abbreviated_subjects.append(main_name[:3])
                composite_structure[main_name] = {
                    'components': components,
                    'component_names': [comp.name for comp in components],
                    'component_display': group_data['component_display'][:len(components)]
                }
            else:
                # If only one component found, treat as standalone
                standalone_subjects.extend(components)
        
        # If a composite exists, remove any standalone base subject with the same main name or alias
        base_aliases = {
            'ENGLISH': {'english', 'eng'},
            'KISWAHILI': {'kiswahili', 'kis', 'kisw', 'swahili'},
        }
        if composite_structure:
            composite_mains = list(composite_structure.keys())
            filtered_standalone = []
            for subject in standalone_subjects:
                n = normalize_subject_name(subject.name)
                remove = False
                for main in composite_mains:
                    aliases = base_aliases.get(main.upper(), {main.lower()})
                    if n in aliases:
                        remove = True
                        break
                if not remove:
                    filtered_standalone.append(subject)
            standalone_subjects = filtered_standalone

        # Add standalone subjects
        for subject in standalone_subjects:
            final_subject_names.append(subject.name)
            parts = subject.name.split()
            if len(parts) > 1:
                final_abbreviated_subjects.append("".join(p[0].upper() for p in parts))
            else:
                final_abbreviated_subjects.append(subject.name[:3].upper())
        
        # Deduplicate final subject names to prevent duplicate headers
        seen = set()
        subject_names = []
        abbreviated_subjects = []
        for nm, abbr in zip(final_subject_names, final_abbreviated_subjects):
            key = (nm or '').strip().lower()
            if key in seen:
                continue
            seen.add(key)
            subject_names.append(nm)
            abbreviated_subjects.append(abbr)

        # Fetch marks for all individual subjects (both composite components and standalone)
        all_subject_ids = [s.id for s in filtered_subjects]
        if all_subject_ids:
            all_marks = (
                Mark.query.filter(
                    Mark.student_id.in_(student_ids),
                    Mark.subject_id.in_(all_subject_ids),
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

        # Feature-flagged: prepare calculator data for combined assessments (OPENER/MIDTERM/ENDTERM)
        cfg = get_config()
        use_calculator: bool = getattr(cfg, 'REPORTS_USE_MARK_CALCULATOR', False)
        is_final_assessment = (assessment_type or '').strip().lower() in { 'end_term', 'endterm', 'end term', 'final', 'overall' }

        calc_marks_index: Dict[tuple, float] = {}
        at_code_by_id: Dict[int, str] = {}
        subject_by_name: Dict[str, Subject] = {s.name: s for s in all_education_subjects}
        if use_calculator and is_final_assessment and all_subject_ids:
            try:
                # Resolve assessment types by aliases
                alias_to_code = {
                    'opener': 'OPENER', 'entrance': 'OPENER',
                    'mid_term': 'MIDTERM', 'midterm': 'MIDTERM', 'mid term': 'MIDTERM',
                    'end_term': 'ENDTERM', 'endterm': 'ENDTERM', 'end term': 'ENDTERM', 'final': 'ENDTERM', 'overall': 'ENDTERM',
                }
                alias_names = list(alias_to_code.keys())
                at_candidates = AssessmentType.query.filter(db.func.lower(AssessmentType.name).in_(alias_names)).all()
                at_ids: List[int] = []
                for at in at_candidates:
                    code = alias_to_code.get(at.name.lower())
                    if code:
                        at_code_by_id[at.id] = code
                        at_ids.append(at.id)

                if at_ids:
                    calc_marks = (
                        Mark.query.filter(
                            Mark.student_id.in_(student_ids),
                            Mark.subject_id.in_(all_subject_ids),
                            Mark.term_id == term_obj.id,
                            Mark.assessment_type_id.in_(at_ids),
                        ).all()
                    )
                    for m in calc_marks:
                        # Normalize to percentage (0..100)
                        if getattr(m, 'percentage', None) is not None:
                            pct = m.percentage
                        else:
                            raw = getattr(m, 'raw_mark', None)
                            if raw is None:
                                raw = getattr(m, 'mark', 0)
                            max_raw = getattr(m, 'max_raw_mark', None)
                            if max_raw is None or max_raw <= 0:
                                max_raw = getattr(m, 'total_marks', 100) or 100
                            pct = (raw / max_raw) * 100 if max_raw else 0
                            if pct > 100:
                                pct = 100.0
                        code = at_code_by_id.get(m.assessment_type_id)
                        if code:
                            calc_marks_index[(m.student_id, m.subject_id, code)] = pct
            except Exception:
                # Non-fatal; fallback to legacy per-assessment path
                calc_marks_index = {}

        class_data = report_data.get("class_data", [])

        # Augment each student entry with processed marks (including composite totals)
        for student_record in class_data:
            stud = Student.query.filter_by(name=student_record.get("student")).first()
            if not stud:
                # Leave existing marks structure
                continue
            student_record["student_id"] = stud.id
            filtered_marks = {}
            total_val = 0.0
            counted = 0
            
            # Process each subject in our final list
            for subject_name in subject_names:
                if subject_name in composite_structure:
                    # Handle composite subject
                    comp_info = composite_structure[subject_name]
                    components = comp_info['components']
                    component_marks = []
                    
                    # Get marks for each component
                    for comp_subject in components:
                        comp_mark = marks_index.get(stud.id, {}).get(comp_subject.id, 0)
                        component_marks.append(comp_mark)
                        # Store individual component marks for template access
                        filtered_marks[comp_subject.name] = comp_mark
                    
                    # Calculate composite total (average of components)
                    if component_marks and any(mark > 0 for mark in component_marks):
                        valid_marks = [mark for mark in component_marks if mark > 0]
                        composite_total = sum(valid_marks) / len(valid_marks) if valid_marks else 0
                        filtered_marks[subject_name] = composite_total
                        total_val += composite_total
                        counted += 1
                    else:
                        filtered_marks[subject_name] = 0
                        
                else:
                    # Handle standalone subject
                    subj = next((s for s in standalone_subjects if s.name == subject_name), None)
                    if subj:
                        # If calculator is enabled for final assessment, compute combined value; else legacy value
                        if use_calculator and is_final_assessment and calc_marks_index:
                            entries: List[AssessmentEntry] = []
                            for code in ('OPENER', 'MIDTERM', 'ENDTERM'):
                                pct = calc_marks_index.get((stud.id, subj.id, code))
                                if pct is None:
                                    # Mark as not assessed -> excluded by default policy
                                    entries.append(AssessmentEntry(code, None, None, 'NA'))
                                else:
                                    entries.append(AssessmentEntry(code, pct, 100.0, None))
                            try:
                                calc = MarkCalculator()
                                ci = CalculationInput(
                                    school_id=0,
                                    subject_id=subj.id,
                                    level=education_level,
                                    rounding_mode=GradingService.get_rounding_mode_for_level(education_level_code),
                                    weights=get_effective_weights(education_level_code),
                                    grade_bands=GradingService.get_calculator_grade_bands(),
                                    missing_policies=get_effective_missing_policies(education_level_code),
                                    entries=entries,
                                )
                                out = calc.compute(ci)
                                val = float(out.final_numeric) if out.final_numeric is not None else 0.0
                            except Exception:
                                # On failure, fallback to legacy per-assessment value
                                val = marks_index.get(stud.id, {}).get(subj.id, 0)
                        else:
                            val = marks_index.get(stud.id, {}).get(subj.id, 0)
                        filtered_marks[subject_name] = val
                        if val > 0:
                            total_val += val
                            counted += 1
            
            student_record["filtered_marks"] = filtered_marks
            student_record["filtered_total"] = total_val
            per_subject_possible = report_data.get("total_marks", 100) or 100
            student_record["total_possible_marks"] = per_subject_possible * max(len(subject_names), 1)
            student_record["filtered_average"] = (
                (total_val / counted) if counted else 0
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

        # Averages per subject (including composite subjects). Also compute
        # averages for component names so footer rows can display them.
        subject_averages: Dict[str, float] = {}
        avg_targets: List[str] = list(subject_names)
        # Include component names for composite structures
        for _main, _info in composite_structure.items():
            for _comp_name in _info.get('component_names', []):
                if _comp_name not in avg_targets:
                    avg_targets.append(_comp_name)

        for name in avg_targets:
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

        # Store composite structure for template access
        ctx_composite_structure = composite_structure

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
            composite_structure=ctx_composite_structure,
            # Non-invasive: provide legends for templates (not used unless template references them)
            calculator_legends=build_legends(),
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
