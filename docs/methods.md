# Methods

## Pinned model and medium

The MATLAB 5.0 file, a structured binary data archive, is loaded with `scipy.io.loadmat`; its sparse matrix is kept sparse. The source SHA-256 is fixed in code and [provenance](../data/provenance.json). Parsing checks dimensions, unique identifiers, finite stoichiometry/objective, bounds and zero right-hand sides. The unsigned eight-bit integer (`uint8`) source objective is cast to floating point **before** negation, avoiding integer wraparound.

The snapshot contains 2,748 metabolites, 4,105 reactions, 1,143 genes and 15,463 stoichiometric nonzeros. Its sole objective is the growth drain `r_2111`. These counts describe v9.1.1; [Zhang et al. (2024)](https://doi.org/10.1038/s44320-024-00060-7) describe an earlier model state.

The deposited minimal aerobic bounds are retained. Exchanges use mmol gDW⁻¹ h⁻¹ (millimoles per gram dry cell weight per hour), while the normalized biomass drain uses h⁻¹. `r_1714` (glucose) and `r_1992` (oxygen) have single-metabolite coefficient −1; their lower bounds encode negative uptake. A cap `u` becomes lower bound `−u`, while secretion remains permitted by the original upper bound. No blanket exchange reset is used: the growth drain is itself a single-metabolite reaction and must not be mistaken for a nutrient exchange. `r_4046` remains fixed at 0.7 as the non-growth-associated maintenance constraint. The [upstream medium](../data/minimal_Y6.yml) is included for interpretation.

## FBA and FVA

Flux balance analysis (FBA) optimizes reaction rates under stoichiometric balance and bounds. Flux variability analysis (FVA) calculates selected rates’ allowed ranges. Here S is the stoichiometric matrix, v the flux vector and c the objective weights. FBA maximizes `cᵀv` subject to `Sv = 0` and `lower ≤ v ≤ upper`; SciPy receives the equivalent minimization of `−cᵀv`. This is a steady-state stoichiometric formulation, not a kinetic simulation ([Orth et al. (2010)](https://doi.org/10.1038/nbt.1614)).

For each selected reaction, FVA separately minimizes and maximizes its flux while retaining a fraction `α` of the optimal biomass flux `z`. The implemented lower-growth constraint is:

`cᵀv ≥ max(0, αz − ε(1 + |z|))`, with `ε = 10⁻⁷`.

The requested floor `αz`, effective floor and slack are all saved. This numerical relaxation avoids declaring solver-dependent failures at an exactly binding optimum to be biological infeasibility. A 100% label means a 100% **target with the declared numerical slack**, not strict equality. The 99% and 90% choices are prespecified sensitivity checks; they are not statistical confidence levels. FVA extrema need not be jointly attainable ([Kenefake et al. (2022)](https://doi.org/10.1186/s12859-022-05089-9)).

## Numerical checks and failure behavior

SciPy 1.17.0 uses HiGHS dual simplex, explicit primal/dual feasibility tolerances of 10⁻⁹ and a 30-second limit per solve. Successful solutions must have finite fluxes, maximum absolute balance residual and bound/floor violation no larger than 10⁻⁷, and a primal–dual objective gap at most `10⁻⁷(1+|objective|)`. Dual objectives are reconstructed from equality, inequality and finite-bound marginals with the minimization sign convention. All diagnostics are retained.

The configured no-glucose case is expected to be infeasible under the maintained energy requirement. Unexpected statuses, a failed FVA endpoint, or a failed residual check stop analysis with exit 2. A time limit or solver error is never renamed as infeasibility. Outputs are staged before replacement, although a filesystem failure during final multi-file replacement can leave a partial set. Use the result verifier afterward.

## Verification scope

`verify_results.py` verifies manifest hashes, checks each saved complete FBA vector directly for mass balance/bounds/objective consistency, and repeats the optimization with HiGHS interior point. Growth comparisons use relative tolerance 10⁻⁶ and absolute tolerance 10⁻⁷; FVA bounds use 10⁻⁶ and 10⁻⁵ respectively. This compares solver algorithms for the same mathematical model, not independently collected biology or a completely separate modeling implementation. One optimal flux vector can differ between algorithms, so vector equality is not required.

Scenario membership, declared caps, FVA identities, floors, bound flags and CSV-to-JSON consistency are checked. Plots and prose reports receive file-integrity checks; their scientific correctness still depends on inspection and interpretation. Reported duality diagnostics are produced by the analysis solver rather than reconstructed from a saved dual certificate.

## Limits

Ordinary FVA can include internal cycles and values bounded mainly by artificial ±1000 limits ([Schellenberger et al. (2011)](https://doi.org/10.1016/j.bpj.2010.12.3707)). A flag marks selected extrema near those limits; no loopless or thermodynamic correction is implemented. Biomass composition, maintenance and all unmodified bounds remain assumptions. Enzyme-constrained/dynamic yeast models address questions outside this scope ([Moreno-Paz et al. (2022)](https://doi.org/10.1111/1751-7915.13995)).

For definitions, see the [glossary](glossary.md); for the rationale and limits of each material choice, see the [assumptions](assumptions.md).
