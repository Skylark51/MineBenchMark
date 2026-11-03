# Research agent operating instructions

## Mission

An agent is not a batch-script generator. It should choose a scientifically motivated next action, request/perform an authorized computation, read its output, check whether the result answers the intended question, and revise the plan as necessary.

The investigator's methods are the default policy. The agent may propose alternatives but should log the rationale and seek approval before altering the scientific protocol.

## Before every action

1. Read README.md, the target PROJECT.md, METHOD.md, STATUS.md, and the last chronological event.
2. State the current scientific question, available verified evidence, uncertainty, and success criterion.
3. Check prerequisites: structure source, chemical identity, atom mapping, total charge, multiplicity, method, solvent, and reference energy.
4. Assign an event identifier and record the planned action before reporting results.

## Recording contract — append-only history

- Record one new Markdown file in projects/<project-id>/events/ for each meaningful action (planning, submission, inspection, failure, retry, scientific decision).
- Use 0001, 0002, ... sequential IDs; never silently overwrite or delete an earlier event.
- Required fields: timestamp (with timezone), event_id, actor, mode, action, input references, observation, validation, decision, rationale, next_action.
- Git commit history provides an audit trail; a new event file is the source of truth for what happened, and STATUS.md is only the current derived summary.
- Update machine-readable files separately and link their rows from the event. A failed job remains in the ledger.
- A proposed job is not a completed job. Mark status as planned/submitted/running/finished/failed/cancelled explicitly.

## Scientific validity gates

- Never infer a transition state from a scan maximum or an optimizer's normal termination alone.
- A TS requires the intended imaginary mode and convincing IRC connections to verified, chemically distinct endpoints; check for structural/spin changes and endpoint identity.
- Confirm minima by frequency analysis. Review spin contamination, spin density, coordination changes, and competing multiplicities where relevant.
- Compare energy differences only after checking the same chemical composition, reference state, consistent standard state, solvent, and Gibbs correction procedure.
- If any critical gate fails, quarantine that result, diagnose, record alternatives, and then retry. Do not silently report a barrier from a failed candidate.
- Use explicit 'unknown' for an unverified condition instead of inventing data.

## Data provenance

Every numeric dataset has a mode:
- synthetic: manually constructed fixtures, no quantum-chemistry output, useful only for testing agent decisions
- real-computation: actual output with software/version, input file, output file, server/job ID, checksum or commit reference
- external-source: citation and precisely mapped extracted observation

Never mix synthetic values into real scientific comparisons. All files under SIM-MN-001/data/mock_* are synthetic.

## Research loop

Goal → hypotheses → planned jobs → outputs → independent checks → accept/reject → update working model → next jobs.

Success is correct scientific decision-making and reproducible provenance, not simply the number of completed calculations.

## Tool/compute boundary

This GitHub-only demonstration documents simulated calculations. It does not connect to a compute cluster or execute Gaussian. Do not claim otherwise. Actual server submissions, expensive jobs, destructive file operations, or publication of confidential structures require an appropriately configured environment and authorization.

## Compute-server handoff (version 0.1)

- The Linux worker is defined in [runner/README.md](runner/README.md). Do not assume this chat has SSH access to the server.
- For every request, create a new immutable jobs/requests/<job-id>.json; for real Gaussian jobs, also create the matching jobs/inputs/<job-id>.inp and calculate input_sha256.
- The worker claims jobs before executing and writes machine-readable jobs/results/<job-id>.json and a runner-events/<job-id>.md receipt.
- A worker receipt means an execution attempt was recorded, **not** that a reaction mechanism is validated. After receiving results, author a fresh scientific event documenting a separate critical assessment.
- Initially use only the synthetic MB-SMOKE-001 test. Actual Gaussian requires authorized local config, verified structure, approval and site-compliant execution resources.
- Treat output_path in a receipt as a path on the remote server; raw outputs are not accessible to the GitHub-based agent unless an additional file-transfer mechanism is configured.
