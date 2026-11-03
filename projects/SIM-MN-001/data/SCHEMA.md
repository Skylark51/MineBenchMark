# Synthetic data schema

These are manually authored fixtures, not quantum-chemistry outputs.

## mock_pathways.csv

- case_id: ligand/substrate case
- point_id: unique stationary-point or rejected-candidate identifier
- type: RC, TS, INT, or PC (reactant complex, transition-state candidate, intermediate, product complex)
- delta_g_kcal_mol: **synthetic** free energy relative to the **RC of the same case**; energies across distinct cases are not absolute energies
- reference: RC_same_case, always 0.0 in this fixture
- validation: simulated_pass, simulated_rejected, or simulated_not_checked
- usable_for_mock_analysis: true/false; even true does NOT mean physically validated
- source_event: the event establishing or evaluating the data
- provenance: synthetic_fixture, never real Gaussian output

A simulated_pass field reports only that the demonstration pretends the validation gate was passed. It is not evidence of a real frequency/IRC run.

## mock_jobs.csv

The job ledger exercises state tracking and failure preservation. No server job IDs, input files, or Gaussian output files exist for these entries.

## Ranking convention

For these toy pathways, the apparent activation barrier is the highest usable pathway free energy relative to the same-case RC. This simplified convention deliberately ignores competing conformers, spin crossing, pre-equilibria, concentrations, and multi-step kinetics.
