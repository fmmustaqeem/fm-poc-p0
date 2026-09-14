from pathlib import Path
import subprocess
import sys
from _poc_helpers import setup, write_csv, ROWS


def test_dry_run(tmp_path, monkeypatch):
    c=setup(tmp_path,monkeypatch)
    for i in range(8): write_csv(Path("input")/f"file_{i+1:02}.csv")
    bad=Path("input/file_09_bad.csv"); write_csv(bad,ROWS,("id","date","amount"))
    corrupt=Path("input/file_10_corrupt.xlsx"); corrupt.write_bytes(b"bad")
    before={p.name:p.read_bytes() for p in Path("input").iterdir()}
    script=Path(__file__).parents[1]/"run_poc.py"
    result=subprocess.run([sys.executable,str(script),"--mode","dry-run"],text=True,capture_output=True)
    assert result.returncode==0, result.stderr
    assert '"files_invalid": 2' in result.stdout and '"files_valid": 8' in result.stdout and '"rows_received": 40' in result.stdout
    assert not list(Path("output").iterdir()) and not list(Path("quarantine").iterdir()) and not list(Path("manifests").iterdir())
    assert all(p.read_bytes()==before[p.name] for p in Path("input").iterdir())
    assert Path("logs/dry-run.log").exists()
