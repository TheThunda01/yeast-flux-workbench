# Why build a yeast flux workbench?

A metabolic model can return a precise growth value without uniquely determining its reaction rates. To interpret the result, ask which assumptions permit it and which rates could change while still satisfying them.

This project explores that question with the community-maintained **yeast-GEM v9.1.1** model of *Saccharomyces cerevisiae*. It asks how declared glucose- and oxygen-uptake constraints change feasible biomass production, and how much freedom remains in selected reaction fluxes near the growth optimum. [Zhang et al. (2024)](https://doi.org/10.1038/s44320-024-00060-7) provide the resource's scientific context; the pinned release fixes the exact model used here. We retain its aerobic minimal-medium setting so that a scenario is an explicit change to a known baseline.

Flux balance analysis optimizes a chosen objective while requiring reaction rates to balance modeled metabolites and remain within their bounds. Flux variability analysis then finds alternative feasible values for selected reactions. Its intervals describe what the constrained model permits, not experimental confidence intervals. [Orth et al. (2010)](https://doi.org/10.1038/nbt.1614) and [Kenefake et al. (2022)](https://doi.org/10.1186/s12859-022-05089-9) explain that relationship.

The main themes are:

- **Biological assumptions:** nutrients, maintenance energy, biomass composition, and reaction directionality shape the answer.
- **Mathematical alternatives:** one optimum need not uniquely determine the internal fluxes.
- **Reproducibility:** a versioned model, explicit scenario definitions, solver checks, and source fingerprints make results inspectable.
- **Careful interpretation:** a feasible prediction becomes a testable hypothesis only when its conditions and limitations are clear.

Learners can follow the analysis from model input to output. Researchers can test whether a conclusion persists when the growth requirement or uptake constraint changes. Neither use establishes agreement with a new yeast experiment.

Conventional FBA omits some enzyme-capacity, regulatory, and dynamic constraints that influence living cells. [Moreno-Paz et al. (2022)](https://doi.org/10.1111/1751-7915.13995) illustrate why those distinctions matter. Adjusting oxygen alone therefore does not validate anaerobic physiology or reproduce the Crabtree effect here. The workbench makes a limited modeling argument that readers can question, reproduce, and eventually compare with independent measurements.

For definitions, see the [glossary](glossary.md); for the rationale and limits of each material choice, see the [assumptions](assumptions.md).
