# SIM-MN-001 — Synthetic Mn(III)–peroxo ring-size benchmark

> **Mode: SYNTHETIC.** This is a procedural training scenario, not a report of performed Mn(III)–peroxo computations. All energetics and mock frequency/IRC outcomes were deliberately constructed.

## Goal

Explore whether changing the supporting macrocycle from 12-MTP to 14-MTP changes the apparent barrier and step sequence for oxygen insertion with two model substrates.

| Case | Ligand | Substrate |
| --- | --- | --- |
| 12-CHN | 12-MTP | cyclohexanone |
| 14-CHN | 14-MTP | cyclohexanone |
| 12-CBN | 12-MTP | cyclobutanone |
| 14-CBN | 14-MTP | cyclobutanone |

## Working hypotheses (unverified)

H1. A change in ring size may change the accessible reaction pathway, rather than only the energy of a common TS.

H2. Substrate ring strain may change the limiting free-energy barrier.

H3. Spin-state ordering and crossover may change apparent single-surface rankings. Therefore, the illustrative single-surface numbers cannot settle a real mechanism.

## Test design

- Establish atom identity, coordination, charge, structure source, and relevant spin states for each system.
- Optimize putative reactant complex (RC) and compare possible spin states.
- Explore plausible formation/oxygen-insertion coordinates with exploratory scans.
- Refine TS candidates; test frequencies and both IRC directions.
- Optimize terminal minima and perform higher-level single-point calculations.
- Combine energies consistently; identify rate-limiting maxima and mechanistic alternatives.
- Record each action, including failed paths and uncertainty.

## Benchmark scenarios

The mocked dataset creates direct pathways for the 12-MTP cases and stepwise pathways for the 14-MTP cases. This is a **testing choice**, not a claim about actual molecular chemistry. A plausible-looking 14-CHN TS candidate is intentionally invalidated when both simulated IRC directions reach the same endpoint; the agent must reject it before considering an alternative candidate.

## Completion criteria

For this synthetic trial: complete an auditable chain of goal, plan, mocked execution, rejection, retry, and appropriately qualified comparison.

For future real work: chemical identities, source structures, Gaussian output files, frequencies, IRC endpoints, energetic corrections, spin states, and independent validations must all be verified.

## Provenance

Created 2026-11-03 (Asia/Seoul) as a synthetic test fixture. The values must never be cited as computed findings.
