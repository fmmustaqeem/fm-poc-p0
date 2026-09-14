from pathlib import Path
from _poc_helpers import setup, write_csv, validate, run, read_json, ROWS


def test_missing_column(tmp_path, monkeypatch):
    c = setup(tmp_path, monkeypatch); files=[]
    for i in range(9):
        p=Path("input")/f"file_{i+1:02}.csv"; write_csv(p); files.append(validate(p,c))
    bad=Path("input/file_10_bad.csv"); write_csv(bad, ROWS, ("id","date","amount")); files.append(validate(bad,c))
    r=run(files,c); m=read_json(r["manifest_path"])
    assert m["status"]=="partial" and m["rows_received"]==50 and m["rows_accepted"]==45 and m["rows_rejected"]==0
    assert (Path("quarantine")/bad.name).exists()
    assert "category" in (Path("quarantine")/"file_10_bad.csv.reason.txt").read_text()
