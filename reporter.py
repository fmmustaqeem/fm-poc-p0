from pathlib import Path
import pandas as pd


def build_report(consolidated_rows, summary, config, run_id):
    output_dir = Path(config["paths"]["output"])
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = pd.Timestamp.now().strftime(config["output"]["timestamp_format"])
    base = config["output"]["filename_pattern"].format(run_id=run_id, timestamp=timestamp)
    output = output_dir / base
    counter = 1
    while output.exists():
        output = output_dir / f"{Path(base).stem}_{counter}{Path(base).suffix}"
        counter += 1

    columns = config["structural"]["required_columns"]
    df = pd.DataFrame(consolidated_rows)
    if not df.empty:
        for col in columns:
            if col not in df.columns:
                df[col] = None
        df = df[columns]
        if "id" in df.columns:
            df = df.sort_values("id", kind="stable").reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=columns)
    summary_df = pd.DataFrame([summary], columns=config["output"]["summary_columns"])
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=config["output"]["sheets"]["data"], index=False)
        summary_df.to_excel(writer, sheet_name=config["output"]["sheets"]["summary"], index=False)
    return str(output)
