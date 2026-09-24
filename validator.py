import re
from pathlib import Path
import pandas as pd


def _load_file(path, config):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, header=config["input"]["header_row"], encoding=config["input"]["encoding"], dtype={"id": "string"})
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path, header=config["input"]["header_row"])
    raise ValueError(f"unsupported extension: {suffix}")


def _check_value(value, dtype):
    if pd.isna(value):
        return True
    if dtype == "string":
        return isinstance(value, str)
    if dtype == "float":
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    if dtype == "date":
        try:
            pd.to_datetime(value)
            return True
        except (TypeError, ValueError):
            return False
    return False


def validate_file(path, config):
    required = config["structural"]["required_columns"]
    try:
        df = _load_file(path, config)
    except Exception as exc:
        return {"file_status":"reject","reason":f"corrupted or unreadable file: {exc}","rows_received":0,"rows_accepted":0,"rows_rejected":0,"valid_rows":[],"row_errors":[]}

    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"file_status":"reject","reason":f"missing column(s): {', '.join(missing)}","rows_received":len(df),"rows_accepted":0,"rows_rejected":len(df),"valid_rows":[],"row_errors":[]}

    dtype_map = config["structural"]["column_dtypes"]
    row_errors = []
    valid_rows = []
    unique_cols = config["business"]["unique"]
    duplicate_indexes = set()
    for col in unique_cols:
        if col in df.columns:
            duplicate_indexes.update(df.index[df[col].duplicated(keep=False)].tolist())

    for idx, row in df.iterrows():
        errors = []
        row_number = int(idx) + 2
        for col, dtype in dtype_map.items():
            if not _check_value(row[col], dtype):
                errors.append(f"{col} wrong type")
        for col in config["business"]["not_null"]:
            if pd.isna(row[col]) or str(row[col]).strip() == "":
                errors.append(f"{col} is null")
        if idx in duplicate_indexes:
            errors.extend([f"{c} is not unique" for c in unique_cols])
        for col, bounds in config["business"]["range"].items():
            if not pd.isna(row[col]):
                try:
                    value = float(row[col])
                    if value < bounds["min"] or value > bounds["max"]:
                        errors.append(f"{col} out of range")
                except (TypeError, ValueError):
                    pass
        for col, allowed in config["business"]["allowed_values"].items():
            if not pd.isna(row[col]) and row[col] not in allowed:
                errors.append(f"{col} invalid value")
        for col, pattern in config["business"]["regex"].items():
            if not pd.isna(row[col]) and re.fullmatch(pattern, str(row[col])) is None:
                errors.append(f"{col} regex mismatch")
        if errors:
            row_errors.append({"row":row_number,"errors":errors})
        else:
            valid_rows.append(row.to_dict())

    return {"file_status":"accept","reason":"","rows_received":len(df),"rows_accepted":len(valid_rows),"rows_rejected":len(row_errors),"valid_rows":valid_rows,"row_errors":row_errors}
