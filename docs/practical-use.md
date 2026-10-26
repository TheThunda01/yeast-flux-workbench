# Practical use

## Where this fits

Use the workbench to learn how environmental bounds and a growth requirement limit the fluxes an existing yeast model permits. The results can help examine model assumptions or formulate a hypothesis to compare with independent measurements. They do not estimate culture conditions from a sample or prescribe an experiment.

## Input and output contract

The input is the exact [v9.1.1 MAT snapshot](../data/README.md), plus `scenarios.json`. Each scenario has a unique alphanumeric/underscore name, a nonnegative glucose-uptake cap, a strictly positive oxygen-uptake cap, an expected status and a Boolean FVA flag. Units are model flux units: exchanges in mmol gDW⁻¹ h⁻¹ (millimoles per gram dry cell weight per hour) and the biomass drain in h⁻¹. Bounds are not medium concentrations. Selected reaction IDs must exist and be unique; growth fractions must be unique numbers in `(0,1]`.

Only glucose and oxygen exchange lower bounds change. The rest of the supplied aerobic medium, fixed maintenance and biomass chemistry remain. Zero oxygen is deliberately unsupported by this scenario interface because a physiological anaerobic model requires additional changes.

Here FBA means flux balance analysis, the constrained optimization of reaction rates; FVA means flux variability analysis, the allowed range for a selected rate at a growth requirement.

The run creates `analysis.json`, `scenarios.csv`, `fva.csv`, `fba_fluxes.npz`, `report.md`, two PNGs and `manifest.json`. `--no-plots` omits the PNGs and removes previous owned PNGs in that output directory. All full-model vectors are numerical arrays; load the NPZ with `allow_pickle=False`. The manifest records source/config/code hashes, solver options and versions.

The program reports expected infeasibility with a null growth value, not zero. Unexpected statuses, unknown inputs, source mismatch, or failed numerical checks cause exit 2 before it copies the staged output.

The program replaces output one file at a time, so an interrupted write requires verification. Choose a new `--output-dir` to preserve an earlier run; otherwise, the program refreshes the existing directory. It rejects source data directories as destinations.

## Worked use case

```sh
python run.py --output-dir my_results
python verify_results.py --results-dir my_results
```

With the included configuration, five scenarios have finite optima and the no-glucose diagnostic is infeasible. The glucose cap stays at 1 while oxygen caps range from 0.25 to 1000. The large 1000 bound is a permissive modeling bound, not an oxygen concentration or a measured uptake rate.

Inspect `fva.csv` for ethanol (`r_1761`) in `oxygen_1` and compare the 100%, 99% and 90% growth targets. The table separates the requested floor, effective floor and numerical slack. Each range describes alternatives that satisfy its stated model constraints, not probabilities or confidence limits. An individual FBA vector represents only one feasible solution.

## Checks before relying on a result

- **Implemented:** exact model hash, input dimensions/IDs, objective handling, bounds, source fingerprints, solver statuses, mass balance and primal–dual checks.
- **Implemented:** verification of saved FBA vectors plus repeat optimum/FVA solves with a second HiGHS algorithm; CSV/JSON consistency and output hashes.
- **Operator responsibility:** confirm the chosen model version, medium, objective, numerical slack and reaction units suit the question. Do not change the fraction after inspecting results to obtain a preferred answer.
- **Operator responsibility:** inspect artificial-bound flags, source assumptions and any failure. Numerical agreement between solvers does not validate yeast physiology.

## Known limits

The model is a curated approximation with a fixed biomass objective. It has no new enzyme-capacity constraints, regulation, kinetics or dynamic adaptation. Ordinary FVA permits some internal cycles; artificial finite bounds can control a range. Its endpoints need not be simultaneously achievable. These limits follow the [model and methods literature](references.md).

This analysis does not reproduce the full upstream validation suite. Lowering oxygen alone does not validate anaerobic physiology or the Crabtree effect.

The result verifier checks computational consistency, not authorship; it does not independently regenerate figure design or prose. Runtime varies by platform. The source model/medium retains CC BY 4.0 terms.

## Next improvements

1. **Experimental comparison:** add a small, explicitly licensed flux/growth dataset with matching medium, normalization and strain; report all deviations without inheriting the upstream model's validation score.
2. **Loop-aware analysis:** compare selected ranges against a documented loopless method; retain the ordinary-FVA baseline and explain which mathematical constraints changed.
3. **Medium audit expansion:** inspect all relevant boundary reactions and compartments; require tests distinguishing nutrient exchanges from biomass drains before supporting new medium files.
4. **Independent implementation check:** compare the pinned cases with a versioned COBRApy/GLPK run using the identical bounds and objective; report numerical tolerances and disagreements rather than silently selecting a solver.

For definitions, see the [glossary](glossary.md); for the rationale and limits of each material choice, see the [assumptions](assumptions.md).
