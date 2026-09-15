from pathlib import Path
import json
import re
import pandas as pd
import yaml

from validator import validate_file
from processor import process_run

ROWS = [
    [1, "2026-01-01", 100.0, "A"],
    [2, "2026-01-02", 200.0, "B"],
    [3, "2026-01-03", 300.0, "C"],
    [4, "2026-01-04", 400.0, "D"],
    [5, "2026-01-05", 500.0, "A"],
]


def config():
    with open("config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    c = config_from_source()
    for key in ("input", "quarantine", "output", "logs", "audit", "manifests"):
        Path(c["paths"][key]).mkdir(parents=True, exist_ok=True)
    return c


def config_from_source():
    # Same frozen schema, with runtime paths rooted in the test directory.
    c = yaml.safe_load(Path(__file__).parents[1].joinpath("config.yaml").read_text(encoding="utf-8"))
    return c


def write_csv(path, rows=ROWS, columns=("id", "date", "amount", "category")):
    rows = [list(row) for row in rows]
    if rows is ROWS or rows == ROWS:
        match = re.search(r"file_(\d+)", Path(path).name)
        if match:
            offset = (int(match.group(1)) - 1) * len(rows)
            for row in rows:
                row[0] = row[0] + offset
    if len(columns) < len(rows[0]):
        rows = [row[:len(columns)] for row in rows]
    df = pd.DataFrame(rows, columns=columns)
    if "id" in df.columns:
        df["id"] = df["id"].astype(str)
    df.to_csv(path, index=False)


def validate(path, c):
    return {"path": str(path), "validation": validate_file(path, c)}


def run(files, c):
    return process_run(files, c, "run")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
