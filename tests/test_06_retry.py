from pathlib import Path
from _poc_helpers import setup, write_csv, validate, run, read_json


def test_retry(tmp_path, monkeypatch):
    c=setup(tmp_path,monkeypatch)
    for i in range(9): write_csv(Path("input")/f"file_{i+1:02}.csv")
    bad=Path("input/file_10_corrupt.xlsx"); bad.write_bytes(b"bad")
    files=[validate(p,c) for p in sorted(Path("input").iterdir())]
    first=run(files,c); old=read_json(first["manifest_path"]); old_output=Path(first["output_path"])
    bad.unlink(); fixed=Path("input/file_10_fixed.csv"); write_csv(fixed)
    current=[validate(p,c) for p in sorted(Path("input").iterdir())]
    second=run(current,c); m=read_json(second["manifest_path"]); log=Path(second["log_path"]).read_text()
    assert m["rows_received"]==5 and m["rows_accepted"]==5
    assert m["run_id"]!=old["run_id"] and old_output.exists() and Path(second["output_path"]).exists()
    assert log.count("already processed (hash match)")>=9
