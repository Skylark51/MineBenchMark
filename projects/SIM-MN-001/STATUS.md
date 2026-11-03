# SIM-MN-001 — Current status

**Updated:** 2026-11-03, Asia/Seoul  
**Current mode:** SYNTHETIC TRAINING ONLY  
**Actual Gaussian executions:** 0  
**Workflow status:** one complete mocked decision loop; no real scientific conclusion  
**Latest event:** [0006 — toy comparison](events/0006_analysis.md)

## Simulated outcome, not an actual research result

| Case | Toy pathway | Apparent max ΔG‡ (kcal/mol, relative to same-case RC) | Confidence |
| --- | --- | ---: | --- |
| 12-CHN | direct | 18.6 | synthetic fixture only |
| 14-CHN | stepwise | 21.9 | synthetic fixture only |
| 12-CBN | direct | 14.7 | synthetic fixture only |
| 14-CBN | stepwise | 17.4 | synthetic fixture only |

A +16.4 kcal/mol 14-CHN TS attempt was rejected by simulated IRC validation: [event 0004](events/0004_validation_failure.md). The alternative was recorded separately: [event 0005](events/0005_recovery.md).

## What the agent has demonstrated

The test records a research question, planned calculations, fictitious outcomes, an explicit failure, alternative reasoning, and a qualified comparison. The data lineage is traceable to [mock_pathways.csv](data/mock_pathways.csv) and the [event history](events/0001_goal.md).

## Blockers for first real experiment

The identity/charge/multiplicity of each physical model, reliable initial atomic coordinates, and competing spin surfaces are not verified. There is no Gaussian executable, server integration, or output file connected to this repository.

## Next recommended action

**TASK-0007 (not yet executed):** establish and check an atom-mapped starting model for one system, select total charge and allowed multiplicities from explicit chemistry, and log why these choices were made. Only then launch an authentic opt/freq job through an authorized compute environment. Store resulting raw outputs outside the synthetic fixture folder and reference their hashes.

At the beginning of the next session, read AGENTS.md, this STATUS.md and event 0006, then create a new event file 0007_*.md **before** changing the scientific plan.
