import argparse
import json
import logging
from pathlib import Path

import yaml

from processor import process_run
from validator import validate_file


def load_config():
    with open("config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def discover_files(config):
    root = Path(config["paths"]["input"])
    root.mkdir(parents=True, exist_ok=True)
    allowed = set(config["input"]["allowed_extensions"])
    return sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in allowed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dry-run", "run"], required=True)
    parser.add_argument("--approved-by")
    args = parser.parse_args()
    if args.mode == "run" and not args.approved_by:
        parser.error("--approved-by is required for run mode")
    config = load_config()
    validated = []
    for path in discover_files(config):
        validated.append({"path":str(path),"validation":validate_file(path, config)})

    if args.mode == "dry-run":
        files_valid = sum(x["validation"]["file_status"] == "accept" for x in validated)
        files_invalid = len(validated) - files_valid
        rows_received = sum(x["validation"]["rows_received"] for x in validated if x["validation"]["file_status"] == "accept")
        payload = {"mode":"dry-run","files_valid":files_valid,"files_invalid":files_invalid,"rows_received":rows_received}
        Path(config["paths"]["logs"]).mkdir(parents=True, exist_ok=True)
        log = Path(config["paths"]["logs"]) / "dry-run.log"
        logging.basicConfig(filename=log, level=logging.INFO, format=config["logging"]["format"], force=True)
        logging.info("dry-run: %s", json.dumps(payload, sort_keys=True))
        print(json.dumps(payload, sort_keys=True))
        return 0

    result = process_run(validated, config, "run")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
