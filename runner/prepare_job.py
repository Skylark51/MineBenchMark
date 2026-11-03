#!/usr/bin/env python3
"""Prepare local GitHub request+input files; does not push or run Gaussian."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worker import validate_gaussian_input, valid_id

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--repo-dir", default=".", type=Path)
    parser.add_argument("--max-cpu-index", type=int, default=15)
    parser.add_argument("--max-memory-gb", type=int, default=100)
    parser.add_argument("--approve-real", action="store_true")
    args = parser.parse_args()
    if not valid_id(args.job_id) or not valid_id(args.project_id):
        parser.error("Invalid job/project id")
    raw = args.input.read_bytes()
    validate_gaussian_input(raw, {"max_cpu_index": args.max_cpu_index, "max_memory_gb": args.max_memory_gb})
    repo_dir = args.repo_dir.resolve()
    target_input = repo_dir / "jobs" / "inputs" / (args.job_id + ".inp")
    target_request = repo_dir / "jobs" / "requests" / (args.job_id + ".json")
    if target_input.exists() or target_request.exists():
        parser.error("Job already exists: never overwrite an earlier request")
    target_input.parent.mkdir(parents=True, exist_ok=True)
    target_request.parent.mkdir(parents=True, exist_ok=True)
    target_input.write_bytes(raw)
    job = {
        "schema_version": 1,
        "job_id": args.job_id,
        "project_id": args.project_id,
        "kind": "gaussian16",
        "mode": "real-computation",
        "input_path": "jobs/inputs/" + args.job_id + ".inp",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "approved": bool(args.approve_real)
    }
    target_request.write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")
    print("Created", target_input)
    print("Created", target_request)
    print("Approved for real Gaussian:", bool(args.approve_real))
    if not args.approve_real:
        print("NOTE: Runner will skip this job until a new approved request is created; requests are immutable.")
    print("Review and commit/push both files before running the server worker.")


if __name__ == "__main__":
    main()
