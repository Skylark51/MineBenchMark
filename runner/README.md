# MineBenchMark Runner — installation and operation

## Important constraints

- This repository is **PUBLIC** as of setup. All committed molecular structures, requests, and parsed results will be visible. Do not submit unpublished/confidential coordinates until the repository's visibility and access policy have been reviewed.
- The runner uses the GitHub REST API. The compute server initiates only outbound HTTPS; no inbound SSH or public server port is needed.
- No Gaussian installation or real calculation is performed by the GitHub setup alone.
- Deploy the runner only to a host where your institution permits a persistent user process. **Do not run Gaussian on a login node if a scheduler (SLURM/PBS) is required.** The first runner supports local execution only; scheduler dispatch is a separate integration.
- Only repository writers you trust should be able to commit approved requests. This is a controlled-repository automation mechanism, not a multi-tenant sandbox.

## Data flow

1. The research agent writes an immutable JSON request under jobs/requests/ and, for real jobs, an input file under jobs/inputs/.
2. A trusted server worker polls main every 60 seconds.
3. The worker checks request schema, project allowlist, unique job ID, and local real-run permissions. It atomically creates jobs/claims/<id>.json before execution.
4. A smoke task generates a synthetic local receipt without running Gaussian. An approved real task runs the specified g16 binary using a trusted local profile.
5. The worker writes a runner event to projects/<project>/runner-events/<id>.md and a result JSON to jobs/results/<id>.json; the latter is published last as the completion marker.
6. The research agent separately reads the result, checks scientific validity, and writes the next numbered research event.

A crash after creating a claim leaves the job claimed; this is deliberate to prevent silent duplicate Gaussian execution. See Recovery below.

## 1. On your Linux compute host

Run only where GitHub HTTPS is reachable and user background processes are permitted.

    git clone https://github.com/Skylark51/MineBenchMark.git
    cd MineBenchMark
    bash runner/install.sh
    python3 -m unittest discover -s runner/tests -v

If the checkout already exists:

    cd MineBenchMark
    git pull --ff-only
    bash runner/install.sh

## 2. Fine-grained GitHub personal access token

Create a **fine-grained personal access token** in GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens.

- Resource owner: Skylark51
- Repository access: Only select repositories → MineBenchMark
- Repository permission: Contents → Read and write
- Limit the expiration period; keep the token secret.
- Never paste a token into ChatGPT, a committed file, a screenshot, or a shell command that enters history.

Write the token to a private file without echoing it:

    umask 077
    read -rsp "GitHub token: " GH_PAT; printf '\n'
    printf '%s' "$GH_PAT" > "$HOME/.config/minebenchmark/token"
    unset GH_PAT
    chmod 600 "$HOME/.config/minebenchmark/token"

The runner uses that private file; it never commits credentials.

## 3. First live GitHub connection: SMOKE (NO GAUSSIAN)

Initial configuration uses enable_real_gaussian=false. A single synthetic request has already been created: MB-SMOKE-001.

    python3 runner/worker.py --config ~/.config/minebenchmark/config.json --once

Expected terminal output:

    CLAIMED MB-SMOKE-001 (smoke)
    PUBLISHED MB-SMOKE-001: completed

Then inspect:
- jobs/claims/MB-SMOKE-001.json (which server claimed it)
- jobs/results/MB-SMOKE-001.json (completed synthetic result)
- projects/SIM-MN-001/runner-events/MB-SMOKE-001.md (worker receipt)

These files are created **only after the Linux host actually runs the worker successfully**. If the token, network, or permissions are wrong, report that error before proceeding.

To re-test, create a fresh uniquely named smoke JSON request; never delete or overwrite old results just to replay an ID.

## 4. Optional long-running poller

If supported by site policy, start as a user systemd service:

    systemctl --user daemon-reload
    systemctl --user enable --now minebenchmark-runner.service
    systemctl --user status minebenchmark-runner.service
    journalctl --user -u minebenchmark-runner.service -n 50 --no-pager

If the server has no systemd --user or a scheduler-only policy, do not attempt to force a daemon onto a login node. Run --once interactively for the smoke test and adapt the production worker to the scheduler policy.

## 5. Real Gaussian job (deliberately disabled initially)

Before enabling, confirm the actual Gaussian 16 profile and server policy:

    hostname
    command -v g16 || true
    command -v sbatch || command -v qsub || true
    echo "$GAUSS_SCRDIR"

Edit ~/.config/minebenchmark/config.json **on the server**:
- Set g16_profile to the real absolute path to g16/bsd/g16.profile
- Set max_cpu_index and max_memory_gb no higher than the resource allocation
- Set enable_real_gaussian=true only on an authorized execution host
- Set trusted_repo_writers_only=true only after confirming repo write access is restricted to trusted users

There is no real job currently queued. To prepare one (example H2, not a claim about Mn chemistry), run in a local repo checkout:

    python3 runner/prepare_job.py --job-id MB-G16-001 --project-id SIM-MN-001 --input runner/examples/H2_opt_freq.inp --repo-dir . --approve-real
    git add jobs/requests/MB-G16-001.json jobs/inputs/MB-G16-001.inp
    git commit -m "job: submit approved H2 Gaussian integration test"
    git push origin main

Then execute python3 runner/worker.py --once on the authorized host, or let an approved user service pick it up. The example uses 4 CPU cores and 4GB memory. Do not mix test H2 outputs into Mn-peroxo research energetics.

For scientific jobs, provide verified coordinates, charge, multiplicity, method and resources before submitting. Gaussian input is checked against limited Link0 directives, resource caps, simple relative checkpoint names, and some unsafe patterns; this check is **not a comprehensive isolation sandbox**.

## 6. Results and scientific review

A real output is retained at:

    ~/.local/share/minebenchmark/jobs/<job-id>/<job-id>.out

The GitHub result includes output_sha256, path on the compute host, termination state, SCF energy and basic frequency extraction where available. It does not upload the raw .out, and it never marks a TS/IRC as scientifically validated. The AI research agent should inspect any real raw data it needs through a separately authorized file-access mechanism before advancing the mechanism.

## 7. Recovery and debugging

- RUNNER ERROR HTTP 401: token invalid/expired.
- RUNNER ERROR HTTP 403: repository permission or API restriction.
- NO_PENDING_JOBS: all queued items have a claim/result, or no new request exists.
- SKIP invalid request: inspect schema and file name; never edit an already executed job ID.
- Status blocked: check real-run flags, trusted writers and g16_profile.
- Status failed: inspect local .out, .stderr and result.local.json.

If a claimed job has **no result** after a crash, check whether Gaussian is still executing and whether a local output exists. Do **not** blindly remove claims; this risks executing the same chemistry twice. A human must reconcile the job and publish or document recovery before requeueing under a new ID.

## Security / scaling notes

- Token is stored only under ~/.config/minebenchmark/token (mode 600).
- GitHub request files are immutable; the worker itself writes claims and results to main. Do not use untrusted pull requests as the execution queue.
- Each result and runner receipt creates a GitHub commit. This is intentional for traceability.
- GitHub Contents directory listings are limited; sharding and richer scheduling are future improvements for very large queues.
- Adding support for SLURM/PBS, server-side file streaming, multiple hosts, and agents using LLM APIs is a separate engineering step; do not mistake the worker for a fully autonomous scientist.
