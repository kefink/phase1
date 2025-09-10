# Classteacher Blueprint Route Index (Initial Inventory)

Legend (Category):

- CORE: Linked directly from templates / primary navigation.
- AUX: Auxiliary (AJAX / background / data endpoints used by JS or forms, not primary nav pages).
- DEV: Dev-only (now gated by `@dev_only`). Hidden in production.
- LEGACY: Candidate for removal or merge (older duplicate, debug, or superseded by another route). Some may soon be moved to DEV or deleted.

Notes:

- This is a first-pass manual inventory derived from `views/classteacher.py` and template `url_for` references.
- HTTP methods default to GET unless specified.
- Where function names are obvious (common Flask pattern), they are listed; otherwise marked `?` (can be auto-extracted in a later scripted pass).
- Follow-up: Automate extraction (AST parse) to ensure 100% accuracy, then drive pruning & modularization.

## Dev-Only (Gated) Routes (Category = DEV)

| Path                      | Function                 | Methods | Decorators | Notes                                    |
| ------------------------- | ------------------------ | ------- | ---------- | ---------------------------------------- |
| /test_components          | test_components          | GET     | dev_only   | Legacy maintenance UI                    |
| /test_debug               | test_debug               | GET     | dev_only   | Simple reachability check                |
| /debug_subjects_public    | debug_subjects_public    | GET     | dev_only   | Composite subject inspection             |
| /fix_independent_subjects | fix_independent_subjects | GET     | dev_only   | Data surgery helper                      |
| /implement_composite_fix  | implement_composite_fix  | GET     | dev_only   | Migration helper (superseded by Alembic) |
| /verify_composite_setup   | verify_composite_setup   | GET     | dev_only   | Verification now obsolete for runtime    |
| /test_component_upload    | test_component_upload    | GET     | dev_only   | Component subjects test                  |
| /create_test_marks        | create_test_marks        | GET     | dev_only   | Disabled manual fix placeholder          |
| /test_report_debug        | test_report_debug        | GET     | dev_only   | Old report calc test                     |
| /fix_kevin_assignment     | fix_kevin_assignment     | GET     | dev_only   | One-off staff fix                        |
| /upload_test              | upload_test              | GET     | dev_only   | Routing smoke test                       |
| /test-analytics           | test_analytics_dashboard | GET     | dev_only   | Mock analytics                           |

## Legacy / Duplicate / Debug (Not Yet Gated) (Category = LEGACY)

| Path                                                             | Function              | Methods | Decorators                       | Notes / Action                                             |
| ---------------------------------------------------------------- | --------------------- | ------- | -------------------------------- | ---------------------------------------------------------- |
| /debug_marks_data/<grade>/<stream>/<term>/<assessment_type>      | debug_marks_data      | GET     | classteacher_required            | Should gate or remove after verifying no template/JS usage |
| /fixed_class_report/<grade>/<stream>/<term>/<assessment_type>    | fixed_class_report    | GET     | teacher_or_classteacher_required | Superseded by enhanced_class_report; plan deprecate        |
| /enhanced_class_report/<grade>/<stream>/<term>/<assessment_type> | enhanced_class_report | GET     | teacher_or_classteacher_required | Keep (merge into unified class_report)                     |

## Core Navigation & Primary Feature Pages (Category = CORE)

| Path                                                                                                   | Function                           | Methods   | Decorators            | Notes                          |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------- | --------- | --------------------- | ------------------------------ |
| /                                                                                                      | dashboard                          | GET, POST | classteacher_required | Main hub                       |
| /class_overview                                                                                        | class_overview                     | GET       | classteacher_required | Overview & status              |
| /analytics                                                                                             | analytics_dashboard                | GET       | classteacher_required | Analytics main page            |
| /all_reports                                                                                           | all_reports                        | GET       | classteacher_required | Reports listing                |
| /preview_class_report/<grade>/<stream>/<term>/<assessment_type>                                        | preview_class_report               | GET, POST | classteacher_required | Class report preview           |
| /edit_class_marks/<grade>/<stream>/<term>/<assessment_type>                                            | edit_class_marks                   | GET       | classteacher_required | Edit marks UI                  |
| /update_class_marks/<grade>/<stream>/<term>/<assessment_type>                                          | update_class_marks                 | POST      | classteacher_required | Marks submission (class)       |
| /download_class_report/<grade>/<stream>/<term>/<assessment_type>                                       | download_class_report              | GET       | classteacher_required | PDF/Doc output                 |
| /view_student_reports/<grade>/<stream>/<term>/<assessment_type>                                        | view_student_reports               | GET       | classteacher_required | Student list view              |
| /print_individual_report/<...>                                                                         | print_individual_report            | GET       | classteacher_required | Print-ready individual         |
| /preview_individual_report/<...>                                                                       | preview_individual_report          | GET       | classteacher_required | Individual preview             |
| /subject_report/<int:grade_id>/<int:stream_id>/<int:subject_id>/<int:term_id>/<int:assessment_type_id> | subject_report                     | GET       | classteacher_required | Subject analytics/report       |
| /class_marks_status/<int:grade_id>/<int:stream_id>/<int:term_id>/<int:assessment_type_id>              | class_marks_status                 | GET       | classteacher_required | Upload workflow status         |
| /collaborative_marks_dashboard                                                                         | collaborative_marks_dashboard      | GET       | classteacher_required | Collaboration hub              |
| /grade_reports_dashboard                                                                               | grade_reports_dashboard            | GET       | classteacher_required | Grade-level reporting          |
| /grade_streams_status/<grade_name>/<term>/<assessment_type>                                            | grade_streams_status               | GET       | classteacher_required | Stream status per grade        |
| /generate_individual_stream_report/<...>                                                               | generate_individual_stream_report  | GET       | classteacher_required | Stream PDF generation          |
| /generate_consolidated_grade_report/<grade_name>/<term>/<assessment_type>                              | generate_consolidated_grade_report | GET       | classteacher_required | Consolidated grade report      |
| /generate_batch_grade_reports/<grade_name>/<term>/<assessment_type>                                    | generate_batch_grade_reports       | GET       | classteacher_required | Batch generation               |
| /generate_grade_marksheet/<grade>/<term>/<assessment_type>/<action>                                    | generate_grade_marksheet           | GET       | classteacher_required | Marksheet pipeline             |
| /preview_grade_marksheet/<grade>/<term>/<assessment_type>                                              | preview_grade_marksheet            | GET       | classteacher_required | Marksheet preview              |
| /download_grade_marksheet/<grade>/<term>/<assessment_type>                                             | download_grade_marksheet           | GET       | classteacher_required | Marksheet export               |
| /generate_all_individual_reports/<grade>/<stream>/<term>/<assessment_type>                             | generate_all_individual_reports    | GET       | classteacher_required | Bulk individual reports        |
| /manage_students                                                                                       | manage_students                    | GET, POST | classteacher_required | Student CRUD                   |
| /manage_subjects                                                                                       | manage_subjects                    | GET, POST | classteacher_required | Subject CRUD                   |
| /manage_grades_streams                                                                                 | manage_grades_streams              | GET, POST | classteacher_required | Grade & stream mgmt            |
| /manage_terms_assessments                                                                              | manage_terms_assessments           | GET, POST | classteacher_required | Term & assessment mgmt UI      |
| /manage_teacher_assignments                                                                            | manage_teacher_assignments         | GET, POST | classteacher_required | Assignment management          |
| /manage_teacher_subjects/<int:teacher_id>                                                              | manage_teacher_subjects            | GET, POST | classteacher_required | Subject assignment per teacher |
| /teacher_management_hub                                                                                | teacher_management_hub             | GET       | classteacher_required | Admin hub                      |
| /manage_teachers                                                                                       | manage_teachers                    | GET, POST | classteacher_required | Teacher CRUD                   |
| /assign_subjects                                                                                       | assign_subjects                    | GET, POST | classteacher_required | Basic assignment flow          |
| /advanced_assignments                                                                                  | advanced_assignments               | GET       | classteacher_required | Advanced assignment UI         |
| /upload (shown in file as /upload)                                                                     | upload_marks (fn name assumed)     | GET, POST | classteacher_required | Entry point for upload wizard  |
| /upload_subject_marks/<...>                                                                            | upload_subject_marks               | GET       | classteacher_required | Single subject upload UI       |
| /submit_subject_marks/<...>                                                                            | submit_subject_marks               | POST      | classteacher_required | Persist subject marks          |
| /upload_class_marks/<...>                                                                              | upload_class_marks                 | GET       | classteacher_required | Class selection step           |
| /upload_single_subject_marks/<...>                                                                     | upload_single_subject_marks        | GET       | classteacher_required | Alternate single-subject path  |
| /submit_single_subject_marks/<...>                                                                     | submit_single_subject_marks        | POST      | classteacher_required | Persist single-subject marks   |
| /download_marks_template                                                                               | download_marks_template            | GET       | classteacher_required | Template export                |
| /download_student_template                                                                             | download_student_template          | GET       | classteacher_required | Student import template        |
| /download_subject_template                                                                             | download_subject_template          | GET       | classteacher_required | Subject import template        |
| /download_class_list                                                                                   | download_class_list                | GET       | classteacher_required | Class listing export           |
| /download_individual_report/<...>                                                                      | download_individual_report         | GET       | classteacher_required | Individual PDF                 |
| /clear_cache                                                                                           | clear_cache                        | GET       | classteacher_required | Cache purge                    |
| /report_configuration                                                                                  | report_configuration               | GET, POST | classteacher_required | Report settings                |
| /database_health                                                                                       | database_health                    | GET, POST | classteacher_required | Admin health ops               |
| /permission_denied                                                                                     | permission_denied                  | GET       | (public)              | Permission notice              |

## Auxiliary / AJAX / Data Endpoints (Category = AUX)

| Path                                                      | Function                        | Methods | Decorators            | Notes                                  |
| --------------------------------------------------------- | ------------------------------- | ------- | --------------------- | -------------------------------------- |
| /api/check_stream_status/<grade>/<term>/<assessment_type> | api_check_stream_status         | GET     | classteacher_required | Status polling                         |
| /api/stream_status/<grade>/<term>/<assessment_type>       | api_stream_status               | GET     | classteacher_required | Alt status endpoint                    |
| /api/streams/<grade>                                      | api_streams                     | GET     | classteacher_required | Data feed                              |
| /api/streams_by_id/<int:grade_id>                         | api_streams_by_id               | GET     | classteacher_required | Data feed                              |
| /api/test_streams                                         | api_test_streams                | GET     | classteacher_required | Likely debug—consider DEV              |
| /api/assessment_types                                     | api_assessment_types            | GET     | classteacher_required | Dropdown data                          |
| /get_streams_by_level/<grade>                             | get_streams_by_level            | GET     | classteacher_required | JS-driven filter                       |
| /get_subjects_by_education_level/<education_level>        | get_subjects_by_education_level | GET     | classteacher_required | Subject filter                         |
| /get_streams/<grade_id>                                   | get_streams                     | GET     | classteacher_required | Form dynamic population                |
| /get_grade_streams/<int:grade_id>                         | get_grade_streams               | GET     | classteacher_required | Assignment helper                      |
| /teacher_streams/<int:grade_id>                           | teacher_streams                 | GET     | classteacher_required | Assignment helper                      |
| /get_teacher_assignments/<int:teacher_id>                 | get_teacher_assignments         | GET     | classteacher_required | Assignment summary                     |
| /class_marks_status/<...>                                 | class_marks_status              | GET     | classteacher_required | (Also CORE navigation)                 |
| /add_term_ajax                                            | add_term_ajax                   | POST    | classteacher_required | Term add                               |
| /delete_term_ajax                                         | delete_term_ajax                | POST    | classteacher_required | Term delete                            |
| /edit_term_ajax                                           | edit_term_ajax                  | POST    | classteacher_required | Term edit                              |
| /add_assessment_ajax                                      | add_assessment_ajax             | POST    | classteacher_required | Assessment add                         |
| /edit_assessment_ajax                                     | edit_assessment_ajax            | POST    | classteacher_required | Assessment edit                        |
| /delete_assessment_ajax                                   | delete_assessment_ajax          | POST    | classteacher_required | Assessment delete                      |
| /bulk_import_subjects                                     | bulk_import_subjects            | POST    | classteacher_required | Subject CSV ingest                     |
| /export_subjects                                          | export_subjects                 | GET     | classteacher_required | Subject export                         |
| /bulk_transfer_assignments                                | bulk_transfer_assignments       | POST    | classteacher_required | Teacher reassign bulk                  |
| /bulk_assign_subjects                                     | bulk_assign_subjects            | POST    | classteacher_required | Bulk assign                            |
| /enhanced_bulk_assign_subjects                            | enhanced_bulk_assign_subjects   | POST    | classteacher_required | Enhanced assign                        |
| /remove_assignment                                        | remove_assignment               | POST    | classteacher_required | Single assignment delete               |
| /reassign_class_teacher                                   | reassign_class_teacher          | POST    | classteacher_required | Class teacher swap                     |
| /reassign_subject_teacher                                 | reassign_subject_teacher        | POST    | classteacher_required | Subject teacher swap                   |
| /clear_assignment_session                                 | clear_assignment_session        | POST    | classteacher_required | Session cleanup                        |
| /download_template                                        | download_template               | GET     | classteacher_required | Generic marks template (upload wizard) |

## Summary Counts

- DEV (gated): 12
- LEGACY (needs decision): 3 (plus 1 debug AJAX: /api/test_streams)
- CORE: ~50 (user-facing navigation & primary workflows)
- AUX: ~30 (supporting AJAX/data endpoints)
- TOTAL inventoried (approx): 95 distinct logical endpoints (many parameterized).

## Immediate Recommended Actions

1. Gate remaining legacy/debug endpoints: `/debug_marks_data`, `/fixed_class_report` (or mark for merge), `/api/test_streams`.
2. Consolidate duplicate class report endpoints into one canonical `/class_report` (merge logic from fixed & enhanced).
3. Group AUX endpoints into dedicated blueprint or module segments during refactor (e.g. `reports_api`, `admin_api`).
4. Generate automated route map (script) to validate this inventory; update this file programmatically.
5. Begin moving DEV + LEGACY to separate module (`maintenance.py`) for eventual deletion.

## Automation Plan (Next Iteration)

- Write a small introspection script inside an app context to enumerate `classteacher_bp.routes`, capture endpoint, rule, methods, view_func.**name**, decorators (heuristic), and whether referenced in templates (regex scan). Use that to regenerate this markdown.

---

This file is a living document: update after each pruning/move.
