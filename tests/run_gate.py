import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["normal_run.py","missing_column.py","wrong_type.py","duplicate_file.py","corrupted_file.py","retry.py","reproducibility.py","audit.py","dry_run.py"]
TESTS = [ROOT / "tests" / f"test_{i:02d}_{name}" for i, name in enumerate(NAMES, 1)]


def main():
    passed = 0
    for test in TESTS:
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", str(test)], cwd=ROOT, text=True, capture_output=True)
        ok = p.returncode == 0
        print(f"[{'PASS' if ok else 'FAIL'}] {test.name}")
        if not ok:
            print(p.stdout)
            print(p.stderr)
        passed += ok
    print(f"P0 Gate: {passed}/9 {'PASS' if passed == 9 else 'FAIL'}")
    return 0 if passed == 9 else 1


if __name__ == "__main__":
    raise SystemExit(main())
