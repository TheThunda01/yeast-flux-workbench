# Why build a yeast flux workbench?

A metabolic model may return a precise growth value and thousands of reaction rates. The useful question is what makes those numbers possible—and which numbers could change without violating the same assumptions.

This project explores that question with the community-maintained **yeast-GEM v9.1.1** model of *Saccharomyces cerevisiae*. It asks how declared glucose- and oxygen-uptake constraints change feasible biomass production, and how much freedom remains in selected reaction fluxes near the growth optimum. [Zhang et al. (2024)](https://doi.org/10.1038/s44320-024-00060-7) provide the resource's scientific context; the pinned release fixes the exact model used here. We retain its aerobic minimal-medium setting so that a scenario is an explicit change to a known baseline.

The central calculation is flux balance analysis: reactions must balance their modeled metabolites, remain within their bounds, and satisfy a chosen objective. Flux variability analysis then examines alternative feasible values for selected reactions. Its intervals describe what the constrained model permits, not experimental confidence intervals. [Orth et al. (2010)](https://doi.org/10.1038/nbt.1614) and [Kenefake et al. (2022)](https://doi.org/10.1186/s12859-022-05089-9) explain that relationship.

The main themes are:

- **Biological assumptions:** nutrients, maintenance energy, biomass composition, and reaction directionality shape the answer.
- **Mathematical alternatives:** one optimum need not uniquely determine the internal fluxes.
- **Reproducibility:** a versioned model, explicit scenario definitions, solver checks, and source fingerprints make results inspectable.
- **Careful interpretation:** a feasible prediction becomes a testable hypothesis only when its conditions and limitations are clear.

Someone learning constraint-based modeling can use the workbench to follow a compact analysis from model input to interpretable output. A researcher can inspect whether a conclusion persists when the growth requirement or uptake constraint changes. Neither use establishes agreement with a new yeast experiment.

Conventional FBA does not include all the enzyme-capacity, regulatory, and dynamic constraints that influence living cells. [Moreno-Paz et al. (2022)](https://doi.org/10.1111/1751-7915.13995) illustrate why those distinctions matter. We therefore make no claim to reproduce the Crabtree effect or validate anaerobic physiology by adjusting oxygen alone. The aim is to make a bounded modeling argument understandable enough to question, reproduce, and eventually compare with independent measurements.

For definitions, see the [glossary](glossary.md); for the rationale and limits of each material choice, see the [assumptions](assumptions.md).
