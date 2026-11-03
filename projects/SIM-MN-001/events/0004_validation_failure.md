---
event_id: "0004"
project_id: "SIM-MN-001"
timestamp: "2026-11-03T12:58:00+09:00"
actor: "research-agent-demo"
mode: "synthetic"
action: "validate"
status: "failed"
previous_event: "0003"
data_refs: ["../data/mock_pathways.csv#14CHN_TS_OI_v1", "../data/mock_jobs.csv#SIM-J003"]
---

# 0004 — Reject a false-positive transition-state candidate

## Question and available evidence
Is the provisional 14-CHN candidate at +16.4 kcal/mol a valid oxygen-insertion TS?

## Intended action and success criterion
In a real case: check one relevant imaginary mode and distinguish forward/reverse IRC endpoints. In this toy case: exercise the rejection logic with constructed observations.

## Observation
**Synthetic IRC test outcome:** the toy candidate is assigned one imaginary mode (-325.1 cm^-1, invented), but both simulated IRC directions end at the *same* reactant-like minimum rather than distinct INT and PC endpoints.

## Validation
**FAIL.** Having one imaginary mode is insufficient. The candidate does not connect the claimed elementary reaction in the synthetic scenario.

## Decision and rationale
Reject 14CHN_TS_OI_v1. Flag usable_for_mock_analysis=false in the CSV; retain its energy and job ledger entry for audit. Do not cite +16.4 as the accepted activation barrier.

## Next action
Propose another scan coordinate / TS initial guess and re-run the same validation gates in the toy scenario.
