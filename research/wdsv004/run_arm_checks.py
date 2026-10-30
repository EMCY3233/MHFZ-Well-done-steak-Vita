"""Run existing synthetic ARM harnesses in a disposable source-only tree."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from arm_tools import sdk_bin

ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    ('manifest', 'manifest-reader', 208),
    ('record_ref', 'record-ref', 61),
    ('snapshot', 'snapshot-reader', 23),
    ('sha256', 'sha256', 19),
    ('snapshot_native_sha', 'snapshot-native-sha', 23),
    ('batch_plan', 'batch-plan', 13),
    ('batch_commit', 'batch-commit', 10),
    ('private_store', 'private-store', 31),
    ('store_pipeline', 'store-pipeline', 9),
    ('text_handoff', 'text-handoff', 40),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/arm-results')
    args = parser.parse_args()
    output = args.output.resolve()
    # Never reuse old reports as evidence of this invocation.
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error('output directory must be empty')
    report = dict(scope='Synthetic ARM emulation only; no client, VitaOS, console or durability proof',
                  status='failed', checks=[], source_sha256={})
    try:
        if os.name != 'nt':
            raise RuntimeError('The existing harnesses require Windows')
        if not __debug__ or os.environ.get('PYTHONOPTIMIZE'):
            raise RuntimeError('Assertions must be enabled')
        version = importlib.metadata.version('unicorn')
        if version != '2.1.4':
            raise RuntimeError('unicorn==2.1.4 is required')
        sdk = sdk_bin()
        env = dict(os.environ, WDSV_VITASDK_BIN=str(sdk))
        report.update(python=platform.python_version(), unicorn=version,
                      commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      working_tree_dirty=bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
                      compiler=subprocess.check_output([str(sdk / 'arm-vita-eabi-gcc.exe'), '--version'], text=True).splitlines()[0],
                      tool_sha256={name: hashlib.sha256((sdk / name).read_bytes()).hexdigest()
                                   for name in ('arm-vita-eabi-gcc.exe', 'arm-vita-eabi-nm.exe')})
        scratch = ROOT / 'work'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='wdsv-arm-', dir=scratch) as temporary:
            tree = Path(temporary)
            # Copy only tracked own source, never commercial inputs or old JSON evidence.
            tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
            sources = {Path(p) for p in tracked if Path(p).suffix in ('.py', '.c', '.h')
                       and (p.startswith('research/wdsv004/') or p.startswith('research/wdsv003/storage/'))}
            sources.update(p.relative_to(ROOT) for p in Path(__file__).parent.glob('*.py')
                           if p.name in ('arm_tools.py', 'run_arm_checks.py'))
            for relative in sorted(sources):
                source = ROOT / relative
                destination = tree / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                report['source_sha256'][relative.as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
            for name, prefix, expected in CHECKS:
                print('Running ' + name, flush=True)
                result = subprocess.run([sys.executable, '-B', str(tree / 'research/wdsv004' / ('check_' + name + '_arm.py'))],
                                        env=env, capture_output=True, text=True, timeout=300)
                check = dict(name=name, returncode=result.returncode, status='failed')
                report['checks'].append(check)
                if result.returncode:
                    print(result.stdout, end='')
                    print(result.stderr, file=sys.stderr, end='')
                    raise RuntimeError(name + ' harness failed')
                filename = prefix + '-arm-results.json'
                evidence = tree / 'research/wdsv004' / filename
                data = json.loads(evidence.read_text())
                if data.get('passed') != expected:
                    raise RuntimeError(name + ' unexpected case count')
                shutil.copyfile(evidence, output / filename)
                check.update(status='passed', cases=data['passed'], report=filename,
                             report_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest())
                print(result.stdout, end='')
        report['status'] = 'passed'
    except Exception as error:
        report['error_type'] = type(error).__name__
        print(str(error), file=sys.stderr)
    finally:
        (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
