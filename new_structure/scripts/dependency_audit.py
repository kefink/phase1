#!/usr/bin/env python
"""Lightweight dependency audit utility.

Features:
- Parses requirements.txt.
- Classifies prod vs dev sections.
- Detects loose specs (>=, >) in prod.
- Optionally runs pip-audit if installed.

Usage:
  python scripts/dependency_audit.py --summary
  python scripts/dependency_audit.py --fail-on-loose
  python scripts/dependency_audit.py --pip-audit

Exit Codes:
 0 success / no issues
 1 loose spec or vulnerabilities (depending on flags)
"""
from __future__ import annotations
import argparse, re, subprocess, shutil, sys, pathlib
from typing import List, Tuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQ = ROOT / 'requirements.txt'

PROD_SECTION_HEADERS = {
    '# Scalability and Performance Dependencies',
    '# Configuration Management',
    '# Monitoring and Logging',
    '# Security and Session Management',
    '# Background Tasks and Queue Management'
}
DEV_SECTION_HEADER = '# Development and Testing'

LOOSE_PATTERN = re.compile(r"(>=|>|<=)")
REQ_LINE_PATTERN = re.compile(r"^([A-Za-z0-9_.\-]+)([=<>!~]+.+)?$")


def parse_requirements() -> List[Tuple[str,str,bool]]:
    lines = REQ.read_text().splitlines()
    current_section = 'prod'
    results = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            if raw.strip().startswith('#'):
                if raw.strip() == DEV_SECTION_HEADER:
                    current_section = 'dev'
                elif raw.strip() in PROD_SECTION_HEADERS:
                    current_section = 'prod'
            continue
        m = REQ_LINE_PATTERN.match(line)
        if not m:
            continue
        name, spec = m.group(1), m.group(2) or ''
        is_dev = current_section == 'dev'
        results.append((name, spec, is_dev))
    return results


def find_loose_specs(deps: List[Tuple[str,str,bool]]):
    loose = []
    for name, spec, is_dev in deps:
        if is_dev:
            continue
        if not spec or '==' not in spec:
            if name.lower() == 'coverage':  # allowed range for dev but it's in dev section anyway
                continue
            if LOOSE_PATTERN.search(spec) or '==' not in spec:
                loose.append((name, spec or '(none)'))
    return loose


def run_pip_audit() -> int:
    if not shutil.which('pip-audit'):
        print('[INFO] pip-audit not installed; skipping vulnerability scan.')
        return 0
    print('[INFO] Running pip-audit...')
    proc = subprocess.run(['pip-audit', '--progress-spinner=off'], capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--summary', action='store_true')
    ap.add_argument('--fail-on-loose', action='store_true')
    ap.add_argument('--pip-audit', action='store_true')
    args = ap.parse_args()

    deps = parse_requirements()
    loose = find_loose_specs(deps)

    if args.summary:
        print('Dependency Summary:')
        for name, spec, is_dev in deps:
            print(f" - {name}{spec or ''} [{'dev' if is_dev else 'prod'}]")
        if loose:
            print('\nLoose production specs detected:')
            for name, spec in loose:
                print(f' * {name}: {spec}')
        else:
            print('\nNo loose production specs detected.')

    vuln_code = 0
    if args.pip_audit:
        vuln_code = run_pip_audit()

    if args.fail_on_loose and loose:
        print('[ERROR] Loose production dependency specifications found.')
        for name, spec in loose:
            print(f' - {name}: {spec}')
        return 1

    if vuln_code != 0:
        return vuln_code
    return 0

if __name__ == '__main__':
    sys.exit(main())
