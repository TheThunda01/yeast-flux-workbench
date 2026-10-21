# Glossary: yeast metabolism and constrained models

These definitions explain how terms are used in this project. A software check, a model assumption and biological evidence answer different questions. See the [assumption register](assumptions.md) for the conditions behind the calculations.

## Biology and units

| Term | Meaning here |
| --- | --- |
| Saccharomyces cerevisiae; S288C | The budding-yeast species and the laboratory reference strain represented by the pinned model. A model is not an observation of a particular culture. |
| Metabolite; metabolism; metabolic network | A chemical participating in cellular reactions; the collection of those reactions; and their connected representation. |
| Enzyme; reaction; compartment | An enzyme catalyzes a reaction. A compartment identifies where a modeled metabolite occurs; the same chemical in different compartments has separate entries. |
| Glycolysis; pentose phosphate pathway; tricarboxylic acid (TCA) cycle | Connected routes involved in glucose breakdown, pentose/reducing-equivalent production, and central carbon oxidation. Listing them in a reconstruction does not measure their activity. |
| ATP; ADP; hydrolysis | Adenosine triphosphate and diphosphate are molecules involved in energy transfer. Hydrolysis uses water to break a bond; the maintenance reaction represents ATP hydrolysis. |
| Respiration; fermentation; respiro-fermentation | Respiration uses an electron-transport system; fermentation supports metabolism by other electron-balancing routes. Respiro-fermentation combines their activity. This workbench does not establish their regulation. |
| Aerobic; anaerobic; Crabtree effect | Aerobic conditions include available oxygen; anaerobic conditions lack it. The Crabtree effect concerns aerobic fermentation under particular carbon conditions. An oxygen-bound sweep alone does not validate it. |
| Biomass; pseudoreaction; growth drain | Biomass represents cellular material. A pseudoreaction summarizes its assembly requirements. In this snapshot r_4041 assembles biomass, while objective reaction r_2111 drains it. |
| Maintenance; non-growth-associated maintenance | An aggregate energy demand retained even without new biomass production. Here r_4046 is fixed at 0.7; it is not a measured single-enzyme activity. |
| Flux; mmol gDW⁻¹ h⁻¹; h⁻¹ | Flux is a reaction rate. Exchange fluxes use millimoles per gram dry cell weight per hour; biomass-drain flux uses reciprocal hours. gDW is grams of dry cell weight. A flux is not a concentration. |
| Medium; uptake; secretion | A medium describes available nutrients. Uptake enters the modeled cell; secretion leaves it. For the selected exchange reactions, negative flux means uptake. |
| Enzyme capacity; kinetic; regulatory | Capacity limits the rate supported by available enzymes; kinetics describes rate dependence on concentrations and constants; regulation changes activity. Conventional FBA does not include all these effects. |

## Mathematics and checks

| Term | Meaning here |
| --- | --- |
| Reconstruction; genome-scale model; yeast-GEM | A reconstruction collects reaction and gene knowledge; a genome-scale model organizes it for calculation. yeast-GEM is the upstream community model. |
| Stoichiometry; stoichiometric matrix S | Stoichiometry records amounts consumed and produced in each reaction. Matrix S has metabolite rows and reaction columns; negative entries mean consumption. |
| Steady state; Sv=0 | Each modeled balanced metabolite has matched production and consumption. It does not mean zero flux or an unchanged growing culture. |
| Sparse matrix; nonzero | A sparse matrix has mostly zero entries; sparse storage retains its nonzero values and their locations efficiently. Here, nonzeros are nonzero stoichiometric coefficients, not extra reactions. |
| Flux balance analysis (FBA) | Optimization of a linear combination of fluxes subject to stoichiometric balance and bounds. Here the objective is the biomass drain. |
| Linear program (LP); objective; optimum | An LP optimizes a linear objective with linear constraints. An optimum is the best permitted objective value; several flux vectors can share it. |
| Bounds; uptake cap; feasible set | Bounds are allowed ranges. An uptake cap limits the magnitude of a negative exchange. The feasible set contains all flux vectors meeting every constraint. |
| Flux variability analysis (FVA) | Separate minimizations and maximizations give each selected reaction’s feasible range at the stated growth requirement. Their endpoints need not occur together. |
| Growth fraction; floor; slack | The fraction multiplies the optimal biomass flux to request a minimum. The effective floor subtracts a declared tiny numerical slack; 99% is not a confidence level. |
| Infeasible; unbounded | Infeasible means no vector meets the constraints. Unbounded means the objective can improve without a finite limit. Neither is interchangeable with a timeout or zero growth. |
| Degeneracy; alternative optima | Degeneracy can complicate solver behavior; alternative optima are distinct feasible flux vectors with the same best objective. A single solution need not identify all reaction rates uniquely. |
| Primal; dual; marginal; duality gap | The primal is the original LP; the dual is a related bounding problem. Marginals are reported sensitivities/multipliers. Their objective gap is used as a numerical consistency check. |
| Residual; tolerance; floating point | A balance residual is the departure from Sv=0. A tolerance permits small numerical discrepancies due to approximate floating-point arithmetic. |
| HiGHS; dual simplex; interior point | HiGHS supplies LP solvers. The analysis uses its dual-simplex algorithm and the verifier uses an interior-point algorithm for the same model. |
| Internal cycle; thermodynamic constraint; loopless | An internal cycle circulates flux without net external conversion. Thermodynamic restrictions concern physically permitted reaction directions. Loopless methods add restrictions absent from ordinary FVA. |
| Artificial bound; confidence interval | A large bound such as ±1000 can be a computational convention. A confidence interval is a sampling-based statistical construct; an FVA range is not one. |

## Files and reuse

| Term | Meaning here |
| --- | --- |
| MAT; MATLAB struct; uint8 | MAT is a MATLAB data file; a struct contains named fields. uint8 is an unsigned integer type; the objective is converted to floating point before sign reversal. |
| CSV; JSON; NPZ; PNG; YAML | Text tables; structured records; a NumPy array archive; image files; and the structured text format used by the upstream medium preset. |
| CLI; dependency; CI; COBRApy; GLPK | A command-line interface, a required library, and automated integration checks. COBRApy is a constraint-based modeling library; GLPK is an alternative LP solver mentioned only as future comparison. |
| SHA-256; hash; manifest; provenance; pinned | A hash compares file bytes. A manifest records hashes and settings; provenance records origin. A pinned release/commit fixes a source revision without proving its biology. |
| MIT; CC BY 4.0 | License labels for original analysis and upstream model material. Consult the retained texts and attribution; they apply to different material. |
