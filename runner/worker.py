#!/usr/bin/env python3
"""MineBenchMark runner: GitHub queue -> local execution -> immutable GitHub receipts.

Python 3.10+, standard library only. Default mode is simulation (no Gaussian).
This script must be installed on a trusted compute host by the repository owner.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
SCF_RE = re.compile(r"SCF Done:\s+E\([^)]*\)\s*=\s*([-+]?\d+\.\d+(?:[DEde][-+]?\d+)?)")
THERMAL_RE = re.compile(r"Sum of electronic and thermal Free Energies=\s*([-+]?\d+\.\d+(?:[DEde][-+]?\d+)?)")
FREQ_RE = re.compile(r"Frequencies --\s+(.+)")
ALLOWED_LINK0 = {"cpu", "nprocshared", "mem", "chk"}
FORBIDDEN_ROUTE = re.compile(r"\b(?:external|oniom)\s*(?:=|\()", re.IGNORECASE)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def valid_id(value):
    return isinstance(value, str) and bool(ID_RE.fullmatch(value))


class GitHubAPI:
    def __init__(self, repo, token):
        parts = repo.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("repository must be owner/repo")
        self.base = "https://api.github.com/repos/" + "/".join(urllib.parse.quote(p, safe="") for p in parts)
        self.token = token

    def call(self, method, path, payload=None, missing_ok=False):
        url = self.base + path
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": "Bearer " + self.token,
            "User-Agent": "MineBenchMark-runner/0.1",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as ex:
            if missing_ok and ex.code == 404:
                return None
            # Never include credentials or request headers in exception text.
            raise RuntimeError("GitHub API HTTP " + str(ex.code) + " for " + method + " " + path) from None

    def contents(self, path, missing_ok=False):
        endpoint = "/contents/" + urllib.parse.quote(path, safe="/")
        return self.call("GET", endpoint, missing_ok=missing_ok)

    def list_names(self, folder):
        response = self.contents(folder, missing_ok=True)
        if response is None:
            return set()
        if not isinstance(response, list):
            raise RuntimeError(folder + " is not a directory")
        return {item["name"] for item in response if item.get("type") == "file"}

    def read_file(self, path):
        result = self.contents(path)
        if not isinstance(result, dict) or result.get("encoding") != "base64":
            raise RuntimeError("Unsupported GitHub file encoding: " + path)
        return base64.b64decode(result["content"])

    def create_file(self, path, content, message):
        endpoint = "/contents/" + urllib.parse.quote(path, safe="/")
        payload = {
            "message": message,
            "content": base64.b64encode(content).decode("ascii"),
            "branch": "main",
        }
        return self.call("PUT", endpoint, payload)


def read_token(config):
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        token_path = Path(os.path.expanduser(config["token_file"]))
        if not token_path.exists():
            raise RuntimeError("Missing GitHub token file: " + str(token_path))
        if token_path.stat().st_mode & 0o077:
            raise RuntimeError("Token file permissions are too broad; run chmod 600 " + str(token_path))
        token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("Empty GitHub token")
    return token


def load_config(path):
    config = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    mandatory = ("repository", "token_file", "work_dir", "poll_seconds", "enable_real_gaussian", "allowed_projects")
    for key in mandatory:
        if key not in config:
            raise ValueError("Missing configuration key: " + key)
    if config["poll_seconds"] < 15:
        raise ValueError("poll_seconds must be >= 15")
    if not isinstance(config["allowed_projects"], list) or not config["allowed_projects"]:
        raise ValueError("allowed_projects must be a non-empty list")
    config["work_dir"] = str(Path(os.path.expanduser(config["work_dir"])).resolve())
    return config


def validate_request(job, filename, config):
    if not isinstance(job, dict) or job.get("schema_version") != 1:
        raise ValueError("Unsupported request schema")
    job_id = job.get("job_id")
    project = job.get("project_id")
    if not valid_id(job_id) or filename != job_id + ".json":
        raise ValueError("Invalid job ID or request filename")
    if not valid_id(project) or project not in config["allowed_projects"]:
        raise ValueError("Project not allowlisted")
    kind = job.get("kind")
    if kind not in ("smoke", "gaussian16"):
        raise ValueError("Unknown job kind")
    if kind == "smoke" and job.get("mode") != "synthetic":
        raise ValueError("Smoke job must have mode=synthetic")
    if kind == "gaussian16":
        if job.get("mode") != "real-computation":
            raise ValueError("Gaussian job must have mode=real-computation")
        if job.get("input_path") != "jobs/inputs/" + job_id + ".inp":
            raise ValueError("Input must be in the matching jobs/inputs path")
        if not isinstance(job.get("input_sha256"), str) or not re.fullmatch("[0-9a-f]{64}", job["input_sha256"]):
            raise ValueError("Real Gaussian jobs require input_sha256")
        if job.get("approved") is not True:
            raise ValueError("Real Gaussian jobs require approved=true")
    return job_id


def validate_gaussian_input(raw, config):
    if len(raw) > 256_000:
        raise ValueError("Gaussian input exceeds 256KB")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Gaussian input must be UTF-8") from None
    if not content.strip() or "\x00" in content or "@" in content:
        raise ValueError("Input is empty or contains forbidden inclusion characters")
    if "--Link1--" in content:
        raise ValueError("Multi-job Link1 input is not supported in first runner version")
    cpu_found = False
    mem_found = False
    route_found = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("%"):
            match = re.fullmatch(r"%([A-Za-z]+)\s*=\s*(.+)", stripped)
            if not match or match.group(1).lower() not in ALLOWED_LINK0:
                raise ValueError("Unsupported Gaussian Link0 directive")
            name, value = match.group(1).lower(), match.group(2).strip()
            if name == "cpu":
                match_cpu = re.fullmatch(r"0-(\d{1,3})", value)
                if not match_cpu or int(match_cpu.group(1)) > int(config.get("max_cpu_index", 15)):
                    raise ValueError("CPU range exceeds configured maximum")
                cpu_found = True
            elif name == "nprocshared":
                count = int(value) if value.isdigit() else 0
                if not 1 <= count <= int(config.get("max_cpu_index", 15)) + 1:
                    raise ValueError("nprocshared exceeds configured maximum")
                cpu_found = True
            elif name == "mem":
                match_mem = re.fullmatch(r"(\d+)\s*(GB|MB)", value, re.IGNORECASE)
                if not match_mem:
                    raise ValueError("Memory must have GB or MB unit")
                mb = int(match_mem.group(1)) * (1024 if match_mem.group(2).upper() == "GB" else 1)
                if mb > 1024 * int(config.get("max_memory_gb", 80)):
                    raise ValueError("Memory exceeds configured maximum")
                mem_found = True
            elif name == "chk":
                if not re.fullmatch(r"[A-Za-z0-9_-]+\.chk", value):
                    raise ValueError("%chk must be a simple relative filename")
        if stripped.startswith("#"):
            route_found = True
    if not (cpu_found and mem_found and route_found):
        raise ValueError("Gaussian input requires %CPU or %nprocshared, %mem, and route (#)")
    if FORBIDDEN_ROUTE.search(content):
        raise ValueError("Unsupported external/ONIOM route")
    return content


def parse_gaussian_output(path):
    """Parse basic output fields, not a chemical validity certificate."""
    scf = None
    gibbs = None
    frequencies = []
    normal = False
    error = False
    opt_completed = False
    with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            found = SCF_RE.search(line)
            if found:
                scf = float(found.group(1).replace("D", "E").replace("d", "e"))
            found = THERMAL_RE.search(line)
            if found:
                gibbs = float(found.group(1).replace("D", "E").replace("d", "e"))
            found = FREQ_RE.search(line)
            if found:
                for value in found.group(1).split():
                    try:
                        frequencies.append(float(value))
                    except ValueError:
                        pass
            if "Optimization completed." in line or "Stationary point found." in line:
                opt_completed = True
            if "Normal termination of Gaussian" in line:
                normal = True
                error = False
            if "Error termination" in line:
                error = True
                normal = False
    return {
        "scf_energy_hartree": scf,
        "gibbs_energy_hartree": gibbs,
        "frequencies_cm_1": frequencies[:500],
        "imaginary_count_below_zero": sum(f < 0 for f in frequencies),
        "opt_completed": opt_completed,
        "normal_termination": normal and not error,
        "error_termination": error,
        "ts_irc_validated": False,
        "scientific_validation": "not_evaluated",
    }


def run_smoke(job, work_dir):
    path = work_dir / "smoke_receipt.txt"
    path.write_text("SYNTHETIC SMOKE TEST: no Gaussian process was launched.\n", encoding="utf-8")
    return {
        "status": "completed",
        "provenance": "synthetic",
        "execution": "smoke-only",
        "output_path": str(path),
        "output_sha256": sha256(path.read_bytes()),
        "gaussian": None,
        "message": "Tested GitHub request retrieval, local work directory, and result publishing.",
    }


def run_gaussian(job, config, gh, work_dir):
    if config.get("enable_real_gaussian") is not True:
        return {"status": "blocked", "provenance": "real-computation", "message": "Real Gaussian execution is disabled in local config."}
    if not config.get("trusted_repo_writers_only", False):
        return {"status": "blocked", "provenance": "real-computation", "message": "trusted_repo_writers_only must be explicitly enabled."}
    input_path = job["input_path"]
    raw = gh.read_file(input_path)
    if sha256(raw) != job["input_sha256"]:
        return {"status": "blocked", "provenance": "real-computation", "message": "Input SHA256 mismatch; no execution."}
    validate_gaussian_input(raw, config)
    local_input = work_dir / (job["job_id"] + ".inp")
    local_output = work_dir / (job["job_id"] + ".out")
    stderr_path = work_dir / (job["job_id"] + ".stderr")
    local_input.write_bytes(raw)
    profile = str(Path(os.path.expanduser(config.get("g16_profile", ""))).resolve())
    if not Path(profile).is_file():
        return {"status": "blocked", "provenance": "real-computation", "message": "g16_profile not found on server; no execution."}
    command = config.get("g16_command", "g16")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", command):
        return {"status": "blocked", "provenance": "real-computation", "message": "Invalid g16_command in local config."}
    scratch = work_dir / "scratch"
    scratch.mkdir(mode=0o700, exist_ok=True)
    env = os.environ.copy()
    env["G16_PROFILE"] = profile
    env["G16_COMMAND"] = command
    env["GAUSS_SCRDIR"] = str(scratch)
    start = now()
    timed_out = False
    exit_code = None
    with local_input.open("rb") as stdin, local_output.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            proc = subprocess.run(
                ["bash", "-c", 'source "$G16_PROFILE" && exec "$G16_COMMAND"'],
                stdin=stdin, stdout=stdout, stderr=stderr, cwd=work_dir, env=env,
                timeout=int(config.get("max_runtime_seconds", 21600)),
                check=False,
            )
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    parsed = parse_gaussian_output(local_output)
    ok = exit_code == 0 and parsed["normal_termination"] and not timed_out
    return {
        "status": "completed" if ok else "failed",
        "provenance": "real-computation",
        "execution": "gaussian16",
        "started_at": start,
        "finished_at": now(),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "input_sha256": sha256(raw),
        "output_path": str(local_output),
        "output_sha256": file_sha256(local_output),
        "stderr_path": str(stderr_path),
        "gaussian": parsed,
        "message": "Raw files remain on server. Parsed fields require scientific validation.",
    }


def receipt_markdown(job, result):
    job_id = job["job_id"]
    return ("# Runner receipt — " + job_id + "\n\n"
        + "- **Project:** " + job["project_id"] + "\n"
        + "- **Mode:** " + job["mode"] + "\n"
        + "- **Kind:** " + job["kind"] + "\n"
        + "- **Status:** " + result["status"] + "\n"
        + "- **Completed at:** " + result["recorded_at"] + "\n"
        + "- **Source request:** [request](../../../jobs/requests/" + job_id + ".json)\n"
        + "- **Structured result:** [result](../../../jobs/results/" + job_id + ".json)\n\n"
        + "## Execution observation\n\n" + result.get("message", "") + "\n\n"
        + "The runner does not assert a chemically valid stationary point or reaction mechanism. "
        + "A research agent must inspect the result and author its own next decision event.\n")


def publish_result(gh, job, result):
    job_id = job["job_id"]
    project_id = job["project_id"]
    result["job_id"] = job_id
    result["project_id"] = project_id
    result["recorded_at"] = now()
    event_path = "projects/" + project_id + "/runner-events/" + job_id + ".md"
    result_path = "jobs/results/" + job_id + ".json"
    # The result file is created last and serves as the completed publication marker.
    gh.create_file(event_path, receipt_markdown(job, result).encode("utf-8"), "log: runner receipt " + job_id)
    gh.create_file(result_path, (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                   "result: " + job_id + " " + result["status"])


def run_once(config, gh):
    requests = sorted(name for name in gh.list_names("jobs/requests") if name.endswith(".json"))
    completed = gh.list_names("jobs/results")
    claimed = gh.list_names("jobs/claims")
    for filename in requests:
        if filename in completed or filename in claimed:
            continue
        try:
            job = json.loads(gh.read_file("jobs/requests/" + filename))
            job_id = validate_request(job, filename, config)
        except (ValueError, KeyError, json.JSONDecodeError) as ex:
            print("SKIP invalid request " + filename + ": " + str(ex), flush=True)
            continue
        claim = {"job_id": job_id, "host": os.uname().nodename, "claimed_at": now()}
        try:
            gh.create_file("jobs/claims/" + filename,
                           (json.dumps(claim, indent=2) + "\n").encode("utf-8"),
                           "claim: " + job_id)
        except RuntimeError as ex:
            print("SKIP claim conflict " + filename + ": " + str(ex), flush=True)
            continue
        directory = Path(config["work_dir"]) / "jobs" / job_id
        directory.mkdir(parents=True, exist_ok=True)
        print("CLAIMED " + job_id + " (" + job["kind"] + ")", flush=True)
        try:
            if job["kind"] == "smoke":
                result = run_smoke(job, directory)
            else:
                result = run_gaussian(job, config, gh, directory)
        except Exception as ex:
            result = {"status": "failed", "provenance": job["mode"],
                      "message": "Runner failed: " + type(ex).__name__ + ": " + str(ex)[:500]}
        write_json(directory / "result.local.json", result)
        publish_result(gh, job, result)
        print("PUBLISHED " + job_id + ": " + result["status"], flush=True)
        return True
    print("NO_PENDING_JOBS", flush=True)
    return False


def main():
    parser = argparse.ArgumentParser(description="MineBenchMark compute runner")
    parser.add_argument("--config", default="~/.config/minebenchmark/config.json")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--once", action="store_true")
    choice.add_argument("--loop", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    old_umask = os.umask(0o077)
    try:
        Path(config["work_dir"]).mkdir(parents=True, exist_ok=True)
        gh = GitHubAPI(config["repository"], read_token(config))
        while True:
            try:
                run_once(config, gh)
            except (RuntimeError, OSError, urllib.error.URLError) as ex:
                print("RUNNER ERROR: " + str(ex), file=sys.stderr, flush=True)
                if args.once:
                    return 1
            if not args.loop:
                return 0
            time.sleep(config["poll_seconds"])
    finally:
        os.umask(old_umask)


if __name__ == "__main__":
    sys.exit(main())
