from pathlib import Path
from _poc_helpers import setup, write_csv, validate, run, read_json


def test_duplicate_file(tmp_path, monkeypatch):
    c=setup(tmp_path,monkeypatch); p1=Path("input/file_01.csv"); p2=Path("input/file_01_copy.csv"); write_csv(p1); p2.write_bytes(p1.read_bytes())
    r=run([validate(p1,c),validate(p2,c)],c); m=read_json(r["manifest_path"])
    assert m["rows_received"]==5 and m["rows_accepted"]==5
    assert m["file_hashes"][str(p1)]==m["file_hashes"][str(p2)]
    assert "duplicate skipped" in Path(r["log_path"]).read_text()
