# FM P0 Proof of Concept

**Architecture:** Python proposes, FM approves, Excel presents.

## Locked scope

- FM: orchestration, governance, monitoring, approval flag
- Python: data processing, validation, transformation
- Excel/VBA: user interface and business reporting

The P0 baseline contains the locked interfaces, configuration, validation rules, nine mandatory tests, and the P0 gate.

## Run

```bash
pip install -r requirements.txt
python run_poc.py --mode dry-run
python run_poc.py --mode run --approved-by <name>
python tests/run_gate.py
```

## Gate

All nine mandatory tests must pass. The gate exits 0 only for `P0 Gate: 9/9 PASS`.
