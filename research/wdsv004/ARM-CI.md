# Reproducible synthetic ARM checks

The `WDSV004 synthetic ARM checks` workflow executes the nine existing WDSV004
ARM harnesses on Windows 2022. It does not execute the commercial client, VitaOS,
or a console. The counts overlap and must not be added as independent coverage.

Dependencies are Python 3.12.10, Unicorn 2.1.4, and VitaSDK bootstrap snapshot
`sdk-snapshot-20260825.611.1`. The SDK archive is checked against SHA256
`99c626dc6821cbc87eef3e5ce0a8447b813041e9948adae6d444b6d9b8851174`
before extraction. No compiler, game resources, or generated ELF is uploaded.

| Harness | Expected cases | Substitution boundary |
|---|---:|---|
| manifest | 208 | Own parser only |
| record_ref | 61 | Python digest callback |
| snapshot | 23 | Python digest callback |
| sha256 | 19 | Python hashlib oracle only |
| snapshot_native_sha | 23 | Native SHA, deliberate digest-failure stub |
| batch_plan | 13 | Python parity oracle |
| batch_commit | 10 | Store callbacks mocked |
| private_store | 31 | OS calls mocked |
| store_pipeline | 9 | OS calls mocked; native storage chain |

The wrapper copies tracked `.py`, `.c`, and `.h` sources from WDSV004 and the
WDSV003 storage dependency into a fresh temporary tree under `work/`. It runs
each harness sequentially with assertions enabled and a five-minute timeout.
Nonzero exit, missing/invalid evidence, or an unexpected case count fails the
run. Existing tracked JSON reports are never copied into the temporary tree.
The output directory must be empty so stale reports cannot count as success.

`summary.json` records commit, dirty-tree state, Python/emulator/compiler
versions, compiler/nm hashes, copied-source hashes, individual result status,
and report hashes. Only the explicit JSON reports and summary are uploaded,
including partial results on failure. A failed setup before wrapper execution
may leave no summary; the workflow then fails rather than inventing evidence.

Local reproduction on Windows, with Unicorn 2.1.4 installed in the selected
Python environment:

```powershell
$env:WDSV_VITASDK_BIN = 'C:\path\to\vitasdk\bin'
python research/wdsv004/run_arm_checks.py --output work/arm-results
```

The original SDK path remains the default for direct harness invocation.
The wrapper does not download dependencies. `PYTHONOPTIMIZE` and `python -O`
are rejected because these legacy harnesses use assertions for validation.
Choose a new empty output directory for each local run.

Scope: reproducibility of existing synthetic checks. No payload capacity,
storage format, hook, mount, installation, or firmware behavior is changed.
Passing this workflow does not establish isolation, power-loss durability,
authenticity of commercial inputs, or offline gameplay on real hardware.
