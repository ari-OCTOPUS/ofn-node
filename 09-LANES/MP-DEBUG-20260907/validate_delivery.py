"""Read-only validation of explicitly owned delivery files; no recursive scan.

Reuses the existing frontmatter parser/checker, never its vault-wide scan.
Prints a JSON receipt to stdout; does not write files or alter validators.
"""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

LANE = Path('F:/backup/09-LANES/MP-DEBUG-20260907')
CANDIDATE = Path('F:/wt-debug-mp-ex1-ex2-20260907')
ORIGINAL = Path('F:/wt-mp-exec-ex1-ex2-20260907')
LAB = Path('C:/Users/Armin/Desktop/اختاپوس بک لپ/OCTOPUS-LAB')
HANDOFF = LAB / '02-agent-memory-and-handoffs/MP-EXEC-DEBUG-HANDOFF-2026-09-07.md'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
checks = []

def check(name, ok, detail=None):
    checks.append({'name': name, 'passed': bool(ok), 'detail': detail})

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

names = ['SCOPE.md', 'DEBUG-REPORT.md', 'LANE-REPORT.md', 'NEXT-AGENT-PROMPT.md',
         'TEST-RECEIPT.json', 'LIVE-READBACK.json', 'live_readback.py',
         'CALIBRATION-READBACK.json', 'calibration_readback.py',
         'SOURCE-COMPARISON.json', 'NODES-READBACK.json', 'N180-READBACK.json',
         'validate_delivery.py']
files = [LANE / name for name in names] + [HANDOFF]
code_pointer = CANDIDATE / '09-LANES/MP-DEBUG-20260907/LANE-REPORT.md'
files.append(code_pointer)
objects = {}
for path in files:
    check('exists:' + path.name, path.is_file())
    if path.suffix == '.json':
        try:
            objects[path.name] = json.loads(path.read_text(encoding='utf-8'))
            check('json:' + path.name, True)
        except (OSError, ValueError) as exc:
            check('json:' + path.name, False, type(exc).__name__)

tests = objects['TEST-RECEIPT.json']
final = tests['final']
check('final_test_denominator', sum(final['suite_counts'].values()) == final['passed'] == 165)
check('no_failed_skipped_or_deselected', all(final[k] == 0 for k in ('failed', 'skipped', 'deselected', 'exit_code')))
for rel, digest in tests['candidate_raw_sha256'].items():
    path = CANDIDATE / rel
    check('candidate_sha:' + rel, sha(path) == digest)
    files.append(path)

for receipt, script in [('LIVE-READBACK.json', 'live_readback.py'),
                        ('CALIBRATION-READBACK.json', 'calibration_readback.py')]:
    check('executed_script_sha:' + script, sha(LANE / script) == objects[receipt]['probe_script_sha256'])
audit = objects['LIVE-READBACK.json']['board_probe']
check('historical_prefix_fingerprint', audit['historical_prefix']['matches_expected_sha256'])
check('audit_denom', audit['snapshot']['checks']['record_count'] == 196462)
cal = objects['CALIBRATION-READBACK.json']['board_probe']['counts']
check('calibration_kind_denominator', sum(cal['kind_counts'].values()) == cal['parsed_records'] == 4326)
check('calibration_outcome_denominator', sum(cal['outcome_status_counts_kind_outcome_only'].values()) == cal['kind_counts']['outcome'] == 2161)
check('calibration_unresolved_numeric', cal['unresolved_with_numeric_metric_kind_outcome_only'] == 2156)

original_hashes = {
    ORIGINAL / 'contracts/claim_v1.py': '30964544645dc71c3264a6665dcb58defe9814b005bc73ea1384586280e5d2ac',
    Path('F:/backup/09-LANES/MP-EXEC-EX1-EX2-20260907/LANE-REPORT.md'): '4dddce133d4897599c8695805bfe7555cfa246fb0227bbc6bee5b38a22b73141',
    Path('F:/backup/09-LANES/MP-EXEC-EX1-EX2-20260907/EX1-VERIFICATION-RECEIPT.json'): '21dbcd17d9cd5c11f8287bbca2bfdb2efffa793623dce42d9c12189e6cc18408',
}
for path, digest in original_hashes.items():
    check('preserved:' + str(path), sha(path) == digest)
canonical = lambda data: data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
check('f1_source_preserved', canonical((CANDIDATE / 'contracts/runtime_truth_v1.py').read_bytes()) == canonical((ORIGINAL / 'contracts/runtime_truth_v1.py').read_bytes()))
check('f1_lock_line_preserved', (CANDIDATE / 'contracts/FROZEN.lock').read_text().splitlines()[0] == (ORIGINAL / 'contracts/FROZEN.lock').read_text().splitlines()[0])

validator = Path('F:/backup/04 - Architect System/scripts/validate_frontmatter.py')
spec = importlib.util.spec_from_file_location('delivery_frontmatter', validator)
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)
notes = [LANE / name for name in ('SCOPE.md', 'DEBUG-REPORT.md', 'LANE-REPORT.md', 'NEXT-AGENT-PROMPT.md')] + [HANDOFF]
for path in notes:
    errors = fm.check_note(path.name, fm.parse_frontmatter(path.read_text(encoding='utf-8')))
    check('frontmatter:' + path.name, not errors, errors)

link_count = 0
for path in notes + [code_pointer]:
    for match in re.finditer(r'\[[^\]]+\]\((?:<([^>]+)>|([^\s)]+))\)', path.read_text(encoding='utf-8')):
        target = match.group(1) or match.group(2)
        if target.startswith(('http:', 'https:')):
            continue
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = path.parent / target_path
        link_count += 1
        check('link:' + target, target_path.exists())
for name in ('README.md', '00-LIVE-ENGINEERING-NAVIGATOR.md'):
    path = LAB / name
    files.append(path)
    first_lines = '\n'.join(path.read_text(encoding='utf-8').splitlines()[:8])
    check('latest_pointer:' + name, HANDOFF.name in first_lines and HANDOFF.exists())

owned_code = list(tests['candidate_raw_sha256'])
def git_check(label, root, args, require_empty=False):
    try:
        result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-C', str(root), *args],
                                capture_output=True, text=True, timeout=60)
        check(label, result.returncode == 0 and (not require_empty or not result.stdout.strip()),
              {'exit_code': result.returncode, 'scope': 'five reviewed code paths'})
    except subprocess.TimeoutExpired:
        check(label, False, {'status': 'NOT_COLLECTED_TIMEOUT', 'timeout_s': 60})
git_check('git_diff_check_owned_paths', CANDIDATE, ['diff', '--check', '--', *owned_code])
git_check('original_reviewed_paths_clean', ORIGINAL,
          ['status', '--porcelain', '--untracked-files=no', '--', *owned_code], require_empty=True)
out = {
    'schema': 'octopus.debug.delivery_verification.v1', 'started_at_utc': started,
    'ended_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Explicit delivery files only; no whole-vault scan, network call, runtime test or validator modification.',
    'frontmatter_method': 'Existing validate_frontmatter.py parse_frontmatter/check_note only, not scan/main.',
    'frontmatter_validator_sha256': sha(validator),
    'frontmatter_schema_source': fm.SCHEMA_SOURCE,
    'notes_checked': len(notes), 'local_markdown_links_checked': link_count,
    'checks_passed': sum(c['passed'] for c in checks),
    'checks_failed': sum(not c['passed'] for c in checks), 'checks': checks,
    'manifest': [{'path': str(p), 'bytes': p.stat().st_size, 'raw_sha256': sha(p)} for p in files],
    'excluded': ['Global vault validation', 'live node182', 'source loaded in RAM', 'production completion'],
    'earlier_validation_attempts': [{'result': 'FAILED_INFRASTRUCTURE', 'exit_code': 1,
        'reason': 'Unbounded-path git diff --check timed out after20seconds; no pass claimed. Retried with fsmonitor disabled, explicit five owned paths and60second timeout; no validator rules relaxed.'}],
}
print(json.dumps(out, ensure_ascii=True, indent=2))
raise SystemExit(1 if out['checks_failed'] else 0)
