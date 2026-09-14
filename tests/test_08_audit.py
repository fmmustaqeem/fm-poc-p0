from pathlib import Path
from _poc_helpers import setup, write_csv, validate, run, read_json


def test_audit(tmp_path, monkeypatch):
    c=setup(tmp_path,monkeypatch); p=Path("input/file_01.csv"); write_csv(p); r=run([validate(p,c)],c)
    m=read_json(r["manifest_path"])
    required=c["manifest"]["include_fields"]
    assert all(m.get(k) not in (None, "") for k in required)
    log=Path(r["log_path"]).read_text(); assert log and " | INFO | " in log
    assert Path(r["audit_path"]).exists()
