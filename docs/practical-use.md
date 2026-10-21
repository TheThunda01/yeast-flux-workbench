# Practical use

## Where this fits

Use the workbench to learn how environmental bounds and a growth requirement shape the feasible solution space of an existing yeast model. It can support a discussion of model assumptions or a hypothesis to compare with independent measurements. It does not estimate culture conditions from a sample or prescribe an experiment.

## Input and output contract

The input is the exact [v9.1.1 MAT snapshot](../data/README.md), plus `scenarios.json`. Each scenario has a unique alphanumeric/underscore name, a nonnegative glucose-uptake cap, a strictly positive oxygen-uptake cap, an expected status and a Boolean FVA flag. Units are model flux units: exchanges in mmol gDW⁻¹ h⁻¹ and the biomass drain in h⁻¹. Bounds are not medium concentrations. Selected reaction IDs must exist and be unique; growth fractions must be unique numbers in `(0,1]`.

Only glucose and oxygen exchange lower bounds change. The rest of the supplied aerobic medium, fixed maintenance and biomass chemistry remain. Zero oxygen is deliberately unsupported by this scenario interface because a physiological anaerobic model requires additional changes.

The run creates `analysis.json`, `scenarios.csv`, `fva.csv`, `fba_fluxes.npz`, `report.md`, two PNGs and `manifest.json`. `--no-plots` omits the PNGs and removes previous owned PNGs in that output directory. All full-model vectors are numerical arrays; load the NPZ with `allow_pickle=False`. The manifest records source/config/code hashes, solver options and versions.

Expected infeasibility is reported with a null growth value, not zero. Unexpected statuses, unknown inputs, source mismatch, or failed numerical checks exit 2 before staged output is copied. Final replacement is per file, so an interrupted write still requires verification. An existing output directory is refreshed; choose a new `--output-dir` to preserve an earlier run. Source data directories are rejected as destinations.

## Worked use case

```sh
python run.py --output-dir my_results
python verify_results.py --results-dir my_results
```

With the included configuration, five scenarios have finite optima and the no-glucose diagnostic is infeasible. The glucose cap stays at 1 while oxygen caps range from 0.25 to 1000. The large 1000 bound is a permissive modeling bound, not an oxygen concentration or a measured uptake rate.

Inspect `fva.csv` for ethanol (`r_1761`) in `oxygen_1`. Compare the 100%, 99% and 90% growth targets. The requested floor, effective floor and numerical slack appear separately. The extrema show alternatives that satisfy the same model constraints, not probabilities or confidence limits. An individual FBA vector is only one member of that set.

## Checks before relying on a result

- **Implemented:** exact model hash, input dimensions/IDs, objective handling, bounds, source fingerprints, solver statuses, mass balance and primal–dual checks.
- **Implemented:** verification of saved FBA vectors plus repeat optimum/FVA solves with a second HiGHS algorithm; CSV/JSON consistency and output hashes.
- **Operator responsibility:** confirm the chosen model version, medium, objective, numerical slack and reaction units suit the question. Do not change the fraction after inspecting results to obtain a preferred answer.
- **Operator responsibility:** inspect artificial-bound flags, source assumptions and any failure. Numerical agreement between solvers does not validate yeast physiology.

## Known limits

The model is a curated approximation with a fixed biomass objective. It has no new enzyme-capacity constraints, regulation, kinetics or dynamic adaptation. Ordinary FVA permits some internal cycles; artificial finite bounds can control a range. Its endpoints need not be simultaneously achievable. These limits follow the [model and methods literature](references.md).

This analysis does not reproduce the full upstream validation suite. It does not claim that lowering oxygen alone validates anaerobic physiology or the Crabtree effect. Runtime varies by platform. The result verifier checks computational consistency, not authorship; it does not independently regenerate figure design or prose. The source model/medium retains CC BY 4.0 terms.

## Next improvements

1. **Experimental comparison:** add a small, explicitly licensed flux/growth dataset with matching medium, normalization and strain; report all deviations without inheriting the upstream model's validation score.
2. **Loop-aware analysis:** compare selected ranges against a documented loopless method; retain the ordinary-FVA baseline and explain which mathematical constraints changed.
3. **Medium audit expansion:** inspect all relevant boundary reactions and compartments; require tests distinguishing nutrient exchanges from biomass drains before supporting new medium files.
4. **Independent implementation check:** compare the pinned cases with a versioned COBRApy/GLPK run using the identical bounds and objective; report numerical tolerances and disagreements rather than silently selecting a solver.
