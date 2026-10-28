"""Reproduce WDSV-004 read-only input checks and Python test evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUTS = {
    'evidence/vita/derived/rePatch-eboot.elf': '2e7d656b0862dff256c8224c6f1d52952a9d631562a9ce65e337b86994a8fb9d',
    'evidence/vita/current-ftp/rePatch-eboot.bin': 'a5dac30c97eb87c4ab0e99b272a93752501114e6b5072159c6222857e4ac3fa3',
}


def main():
    checks = []
    for path, expected in INPUTS.items():
        source = ROOT / path
        digest = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
        checks.append(dict(path=path, present=source.is_file(), sha256=digest, expected_sha256=expected, matches=digest==expected))
    suites = []
    for directory in ['research/wdsv003/storage', 'research/wdsv003/packaging', 'research/wdsv004']:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', directory, '-p', 'test_*.py'],
                                cwd=ROOT, capture_output=True, text=True)
        suites.append(dict(directory=directory, exit_code=result.returncode, output=(result.stdout+result.stderr).strip()))
    evidence = dict(scope='Local Python synthetic tests and read-only copied input hashes; no client, VitaOS or physical execution.',
                    inputs=checks, suites=suites, success=all(c['matches'] for c in checks) and all(s['exit_code']==0 for s in suites),
                    physical_execution_allowed=False,
                    limits=['Native manifest/record/snapshot readers tested under ARM with Python digest callback; no native SHA or native batch writer.', 'No client hook, isolated resource mount or AppUtil identity verified.',
                            'SELF transformation gate remains blocked.', 'No identity/Sign/Entrance/Channel integration produced in this delivery.'])
    (HERE/'validation.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())