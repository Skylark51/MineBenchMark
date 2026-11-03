# MineBenchMark

**Autonomous Computational Chemistry Research Agent — Event-Sourced Benchmark**

> [!IMPORTANT]
> This repository currently contains **synthetic demonstration data only**. No Gaussian calculations were executed for the mock records. Numerical results are fixtures, not scientific evidence.

## Purpose

Train and evaluate an agent that performs computational chemistry research by repeatedly applying a researcher-defined method:

**goal → hypothesis → calculation plan → job request → result inspection → validation → scientific decision → next action**

Every meaningful action is captured in an immutable Markdown event (events/) and a Git commit. The agent must distinguish a completed computation from a simulated result, a successful optimizer termination from a valid transition state, and an attractive hypothesis from a verified mechanism.

## Starter benchmark

[SIM-MN-001 — Mn(III)–peroxo ring-size effect](projects/SIM-MN-001/PROJECT.md)

The synthetic test compares 12-MTP and 14-MTP complexes with cyclohexanone and cyclobutanone. It includes a deliberately invalid transition-state candidate, a simulated recovery, and a first-pass comparison.

## Navigate

| File | Purpose |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Decision rules and append-only logging contract |
| [Project overview](projects/SIM-MN-001/PROJECT.md) | Research question, hypotheses, scope |
| [Method](projects/SIM-MN-001/METHOD.md) | Computational protocol and verification gates |
| [Status](projects/SIM-MN-001/STATUS.md) | Current state, next action |
| [Synthetic pathway data](projects/SIM-MN-001/data/mock_pathways.csv) | Machine-readable mock free energies |
| [First event](projects/SIM-MN-001/events/0001_goal.md) | Start of immutable decision trail |
| [Event template](templates/event.md) | Structure for future agent actions |

## Operating contract

1. Read AGENTS.md, the current project STATUS.md, and the latest event before taking action.
2. Create a **new** sequential event file for every material action or decision; do not rewrite earlier events to conceal failures.
3. Store numerical results in CSV/JSON with units, source, simulation flag, and validation state.
4. Update STATUS.md as a derived summary, retaining links to the event records.
5. New results must be marked synthetic, real-computation, or external-source with provenance.
6. Do not represent a test fixture as a Gaussian output, a verified TS, or a publishable energetic result.

Future real jobs can reuse the same schema and gatekeeping, while keeping mock and actual results in separate datasets.
