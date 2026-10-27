"""Demonstrate current per-journal behavior; no batch atomicity implementation."""
import hashlib
import json
from pathlib import Path
import runpy

here = Path(__file__).resolve().parent
baseline = runpy.run_path(str(here / 'check_native_pipeline_arm.py'))
commit = baseline['commit']
load = baseline['load']
state = commit.__globals__
start = len(state['tests'])
state['mode'] = 'normal'
load('batch baseline first', 0, 1, b'A'*100)
load('batch baseline second', 2, 1, b'UNACK')
commit('batch member first committed', 0, b'NEW-FIRST', 0, 0)
state['mode'] = 'write_error'
commit('batch member second partial failure', 2, b'NEW-SECOND', 0, -1)
state['mode'] = 'normal'
load('batch recovery retains first NEW', 0, 1, b'NEW-FIRST')
load('batch recovery retains second OLD', 2, 1, b'UNACK')
report = dict(scope=__doc__, additional_cases=len(state['tests'])-start,
              baseline_cases=start, tests=state['tests'][start:],
              observed='First member remains new and second recovers old after second commit failure.',
              proves='Independent journal commits do not provide a shared batch generation.',
              limits='Own ARM code, sceIo mocked in RAM; no AppUtil semantics, commercial data or VitaOS execution.',
              elf_sha256=hashlib.sha256((here/'native-pipeline-test.elf').read_bytes()).hexdigest())
(here/'batch-gap-arm-results.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))