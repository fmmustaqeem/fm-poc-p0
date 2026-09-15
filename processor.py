import hashlib
import json
import logging
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path

from reporter import build_report

CODE_VERSION = "p0-1.0.0"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _dirs(config):
    for key in ("quarantine", "output", "logs", "audit", "manifests"):
        Path(config["paths"][key]).mkdir(parents=True, exist_ok=True)


def _processed_path(config):
    return Path(config["paths"]["manifests"]) / "processed_hashes.json"


def _load_processed(config):
    p = _processed_path(config)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_processed(config, data):
    _processed_path(config).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def process_run(validated_files, config, mode):
    _dirs(config)
    start = time.time()
    run_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().isoformat(timespec="seconds")
    log_path = Path(config["paths"]["logs"]) / f"{run_id}.log"
    logging.basicConfig(level=getattr(logging, config["logging"]["level"]), format=config["logging"]["format"], force=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(config["logging"]["format"]))
    logger = logging.getLogger(f"p0-{run_id}")
    logger.handlers.clear(); logger.setLevel(logging.INFO); logger.propagate = False; logger.addHandler(handler)

    processed = _load_processed(config) if config["processing"]["idempotency"]["enabled"] else {}
    seen = set(); rows = []; hashes = {}; input_files = []
    received = accepted = rejected = files_processed = files_rejected = 0
    rejected_records = []

    for item in validated_files:
        path = Path(item["path"])
        result = item["validation"]
        file_hash = _sha256(path)
        hashes[str(path)] = file_hash
        input_files.append(str(path))
        if mode == "dry-run":
            if result["file_status"] == "reject":
                files_rejected += 1
            else:
                received += result["rows_received"]
                accepted += result["rows_accepted"]; rejected += result["rows_rejected"]
            continue
        if file_hash in seen:
            logger.info("duplicate skipped: %s", path.name)
            continue
        seen.add(file_hash)
        if file_hash in processed:
            logger.info("already processed (hash match): %s", path.name)
            continue
        received += result["rows_received"]
        if result["file_status"] == "reject":
            files_rejected += 1
            reason = result["reason"]
            rejected_records.append((path, reason))
            continue
        files_processed += 1
        accepted += result["rows_accepted"]; rejected += result["rows_rejected"]
        rows.extend(result["valid_rows"])
        processed[file_hash] = {"run_id": run_id, "path": str(path), "timestamp": timestamp}
        logger.info("processed: %s", path.name)

    output_path = ""
    if mode == "run":
        for path, reason in rejected_records:
            q = Path(config["paths"]["quarantine"]) / path.name
            shutil.copy2(path, q)
            q.with_suffix(q.suffix + ".reason.txt").write_text(reason, encoding="utf-8")
            logger.info("rejected: %s", path.name)
        if config["processing"]["idempotency"]["enabled"]:
            _save_processed(config, processed)
        status = "success" if files_rejected == 0 else "partial"
        summary = {"rows_received":received,"rows_accepted":accepted,"rows_rejected":rejected,"files_processed":files_processed,"files_rejected":files_rejected,"runtime_seconds":round(time.time()-start, 6)}
        output_path = build_report(rows, summary, config, run_id)
        manifest = {"run_id":run_id,"timestamp":timestamp,"config_version":config["version"],"code_version":CODE_VERSION,"input_files":input_files,"file_hashes":hashes,"rows_received":received,"rows_accepted":accepted,"rows_rejected":rejected,"status":status,"output_path":output_path,"audit_path":str(Path(config["paths"]["audit"])/f"{run_id}.json"),"log_path":str(log_path)}
        manifest_path = Path(config["paths"]["manifests"]) / f"{run_id}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        audit_path = Path(manifest["audit_path"])
        audit_path.write_text(json.dumps({"run_id":run_id,"status":status,"approved":True,"timestamp":timestamp}, indent=2), encoding="utf-8")
    else:
        manifest_path = Path(config["paths"]["manifests"]) / f"{run_id}.json"
        audit_path = Path(config["paths"]["audit"]) / f"{run_id}.json"
        status = "dry-run"
    logger.info("run complete: %s", run_id); handler.close()
    return {"run_id":run_id,"manifest_path":str(manifest_path),"log_path":str(log_path),"audit_path":str(audit_path),"output_path":output_path,"metrics":{"rows_received":received,"rows_accepted":accepted,"rows_rejected":rejected,"files_processed":files_processed,"files_rejected":files_rejected,"status":status}}
