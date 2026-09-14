from pathlib import Path
from _poc_helpers import setup, write_csv, validate, run, read_json, ROWS


def test_wrong_type(tmp_path, monkeypatch):
    c=setup(tmp_path,monkeypatch); files=[]
    for i in range(10):
        p=Path("input")/f"file_{i+1:02}.csv"; rows=[x[:] for x in ROWS]
        if i==4: rows[1][2]="abc"; rows[2][2]="xyz"
        write_csv(p,rows); files.append(validate(p,c))
    r=run(files,c); m=read_json(r["manifest_path"])
    fifth=next(x for x in files if x["path"].endswith("file_05.csv"))["validation"]
    assert m["rows_accepted"]==48 and m["rows_rejected"]==2
    assert fifth["file_status"]=="accept" and fifth["rows_accepted"]==3 and fifth["rows_rejected"]==2
    assert {e["row"] for e in fifth["row_errors"]}=={3,4}
