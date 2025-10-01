"""
CLI utility: Toggle composite configuration for English/Kiswahili per education level.

Usage examples (from project root):
  - python -m new_structure.scripts.toggle_subject_composite --subject english --level upper_primary --enable
  - python -m new_structure.scripts.toggle_subject_composite --subject kiswahili --level junior_secondary --disable

This script uses the app factory to get a DB context and FlexibleSubjectService to apply changes.
"""
import argparse
import sys

from new_structure import create_app
from new_structure.services.flexible_subject_service import FlexibleSubjectService


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Toggle composite config per education level")
    p.add_argument("--subject", required=True, choices=["english", "kiswahili"], help="Subject to configure")
    p.add_argument("--level", required=True, choices=["upper_primary", "junior_secondary"], help="Education level")
    mode = p.add_mutually_exclusive_group(required=False)
    mode.add_argument("--enable", action="store_true", help="Enable composite mode")
    mode.add_argument("--disable", action="store_true", help="Disable composite mode")
    mode.add_argument("--toggle", action="store_true", help="Toggle current composite mode")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Default behavior: toggle if neither enable nor disable specified
    explicit = args.enable or args.disable

    app = create_app('development')
    with app.app_context():
        # Ensure a configuration exists (seed sane defaults for subject/level)
        cfg = FlexibleSubjectService.get_subject_configuration(args.subject, args.level)
        if not cfg:
            if args.subject == 'english':
                FlexibleSubjectService.update_subject_configuration(
                    'english', args.level, True, 'Grammar', 60.0, 'Composition', 40.0
                )
            elif args.subject == 'kiswahili':
                FlexibleSubjectService.update_subject_configuration(
                    'kiswahili', args.level, True, 'Lugha', 50.0, 'Insha', 50.0
                )
            cfg = FlexibleSubjectService.get_subject_configuration(args.subject, args.level)

        if args.toggle or not explicit:
            ok = FlexibleSubjectService.toggle_composite_mode(args.subject, args.level)
            status = FlexibleSubjectService.get_subject_configuration(args.subject, args.level)
            print(f"Toggled {args.subject} ({args.level}) -> is_composite={status['is_composite'] if status else None}")
            sys.exit(0 if ok else 1)
        else:
            # Set explicitly
            is_comp = True if args.enable else False
            ok = FlexibleSubjectService.update_subject_configuration(
                args.subject,
                args.level,
                is_comp,
                cfg['component_1_name'] if cfg else ('Grammar' if args.subject=='english' else 'Lugha'),
                cfg['component_1_weight'] if cfg else (60.0 if args.subject=='english' else 50.0),
                cfg['component_2_name'] if cfg else ('Composition' if args.subject=='english' else 'Insha'),
                cfg['component_2_weight'] if cfg else (40.0 if args.subject=='english' else 50.0),
            )
            print(f"Set {args.subject} ({args.level}) is_composite={is_comp} -> {'OK' if ok else 'FAILED'}")
            sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
