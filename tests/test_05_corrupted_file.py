from pathlib import Path
from _poc_helpers import setup, write_csv, validate, run, read_json


def test_corrupted_file(tmp_path, monkeypatch):
    c=setup(tmp_path,monkeypatch); files=[]
    for i in range(9):
        p=Path("input")/f"file_{i+1:02}.csv"; write_csv(p); files.append(validate(p,c))
    bad=Path("input/file_10_corrupt.xlsx"); bad.write_bytes(b"not an excel file"); files.append(validate(bad,c))
    r=run(files,c); m=read_json(r["manifest_path"])
    assert m["status"]=="partial" and m["rows_accepted"]==45 and m["files_rejected"]==1
    assert (Path("quarantine")/bad.name).exists()
    assert (Path("quarantine")/(bad.name+".reason.txt")).exists()
