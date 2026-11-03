# Investigator method and validation protocol

**Protocol status:** proposed default workflow, subject to structure-specific adjustment. **Not executed in this synthetic demonstration.**

## Computational level

- Gaussian 16 (when a real execution environment is connected).
- Geometry optimization and frequencies: unrestricted B3LYP / def2-SVP when an open-shell formalism is appropriate.
- Higher-level single points: B3LYP / def2-TZVPP, with Grimme D3(BJ) dispersion.
- Solvent: CPCM, acetonitrile (MeCN).
- Relative Gibbs free energies: use a documented consistent expression such as G_est = E_TZVPP_SP + (G_SVP - E_SVP), verifying energy and correction conventions before making real comparisons.
- Example computational resources from the investigator's established workflow: %CPU=0-15; memory and queue settings are not fixed until server requirements are confirmed.

## Action sequence

1. Input audit: verified geometry and atom connectivity; compute charge and possible multiplicities, without guessing from names.
2. Reactant optimization / frequency for appropriate spin states.
3. Coordinate-guided scan to propose a TS guess.
4. Frequency analysis of a candidate, then TS optimization / TS frequency analysis.
5. Validate that there is exactly one intended imaginary mode.
6. IRC forward and reverse; optimize endpoint structures and confirm minima by frequencies.
7. Higher-level single points for all compared stationary points.
8. Spin density/contamination, key bond lengths, standard state, and reference-energy consistency checks.
9. Decide: accept path, reject path, explore competing pathway, or ask for human scientific judgment.

## Automatic stop / retry triggers

| Trigger | Decision |
| --- | --- |
| Missing charge, multiplicity, source geometry, or atom mapping | Block job; request structure audit |
| Geometry optimization fails | Diagnose convergence and geometry; preserve original attempt |
| Scan gives a maximum but no validated TS | Treat as guess only |
| Zero/multiple imaginary modes for proposed TS | Reject as confirmed TS; inspect mode |
| Imaginary mode unrelated to intended reaction | Reject candidate |
| Both IRC directions reach same minimum, or endpoints are chemically inappropriate | Quarantine candidate and explore alternative TS |
| Irreconcilable spin / composition / energy-reference mismatch | Stop comparison, audit before reporting barriers |
| A result exists only as a synthetic fixture | Label as synthetic; never cite as a Gaussian result |

## Real-run metadata requirements

A future actual job record needs input/output paths, Gaussian version, server, submitted/finished timestamps, process or scheduler ID, total charge, multiplicity, method, solvent, energies, frequencies, final coordinates, IRC endpoints, job exit status, and source checksums.

For this first exercise all those real-run fields are explicitly **not available**, rather than filled with invented identifiers.
