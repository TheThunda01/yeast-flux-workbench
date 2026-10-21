# References and source roles

References are cited by author and year. The [reference audit](reference-audit.json) records the checked metadata, source role and exact access limits for every item below. Checks were completed on 21 October 2026 UTC as part of the review dated 20 October in the user’s local date. Earlier discovery and access records remain in the [literature review](literature-review.md). The [21 October maintenance review](review-2026-10-21.md) adds separately dated source rechecks without replacing those earlier access records.

## Model and biological context

- **Zhang C et al. (2024). Yeast9: a consensus genome-scale metabolic model for S. cerevisiae curated by the community. Molecular Systems Biology, 20(10), 1134–1150.** [DOI: 10.1038/s44320-024-00060-7](https://doi.org/10.1038/s44320-024-00060-7); [PMID 39134886](https://pubmed.ncbi.nlm.nih.gov/39134886/). Community-curated model context and limitations; central carbon pathways are represented in the reconstruction.

- **Lu H et al. (2019). A consensus S. cerevisiae metabolic model Yeast8 and its ecosystem for comprehensively probing cellular metabolism. Nature Communications, 10(1), 3586.** [DOI: 10.1038/s41467-019-11581-3](https://doi.org/10.1038/s41467-019-11581-3); [PMID 31395883](https://pubmed.ncbi.nlm.nih.gov/31395883/). Community and versioned model-development context. Abstract-level appraisal.

- **Moreno-Paz S et al. (2022). Enzyme-constrained models predict the dynamics of Saccharomyces cerevisiae growth in continuous, batch and fed-batch bioreactors. Microbial Biotechnology, 15(5), 1434–1445.** [DOI: 10.1111/1751-7915.13995](https://doi.org/10.1111/1751-7915.13995); [PMID 35048533](https://pubmed.ncbi.nlm.nih.gov/35048533/). The study adds enzyme constraints and dynamic simulation to compare growth behavior, motivating caution about conventional static FBA. Abstract-level appraisal.

## Constraint-based methods

- **Orth JD, Thiele I, Palsson BØ. (2010). What is flux balance analysis? Nature Biotechnology, 28(3), 245–248.** [DOI: 10.1038/nbt.1614](https://doi.org/10.1038/nbt.1614); [PMID 20212490](https://pubmed.ncbi.nlm.nih.gov/20212490/). Steady-state stoichiometry, flux bounds, biomass objectives, alternative optima, and limits concerning kinetics/concentrations.

- **Kenefake D et al. (2022). An improved algorithm for flux variability analysis. BMC Bioinformatics, 23(1), 550.** [DOI: 10.1186/s12859-022-05089-9](https://doi.org/10.1186/s12859-022-05089-9); [PMID 36536290](https://pubmed.ncbi.nlm.nih.gov/36536290/). FVA as separate conditional reaction minima and maxima with an objective-retention factor.

- **Schellenberger J, Lewis NE, Palsson BØ. (2011). Elimination of thermodynamically infeasible loops in steady-state metabolic models. Biophysical Journal, 100(3), 544–553.** [DOI: 10.1016/j.bpj.2010.12.3707](https://doi.org/10.1016/j.bpj.2010.12.3707); [PMID 21281568](https://pubmed.ncbi.nlm.nih.gov/21281568/). Ordinary steady-state flux formulations can admit thermodynamically infeasible internal loops. Abstract-level appraisal.

## Exact upstream material and software

- **SysBioChalmers and yeast-GEM contributors. (2026). yeast-GEM release v9.1.1.** [Official source](https://github.com/SysBioChalmers/yeast-GEM/releases/tag/v9.1.1). Version: `v9.1.1, published 2026-08-30`. Exact release identity and change history.

- **SysBioChalmers and yeast-GEM contributors. (2026). yeast-GEM.mat.** [Source](https://github.com/SysBioChalmers/yeast-GEM/blob/2d594ae1c4a2d550ccef120d96a58c7bbf586255/model/yeast-GEM.mat). Version: `2d594ae1c4a2d550ccef120d96a58c7bbf586255`. Local pinned MAT parsed: 2,748 metabolites, 4,105 reactions, 1,143 genes; r_2111 biomass drain, r_4041 assembly, r_4046 fixed ATP maintenance; selected exchange signs. Metadata/attribution-level check.

- **SysBioChalmers and yeast-GEM contributors. (2026). minimal_Y6.yml.** [Official source](https://github.com/SysBioChalmers/yeast-GEM/blob/2d594ae1c4a2d550ccef120d96a58c7bbf586255/data/conditions/minimal_Y6.yml). Version: `2d594ae1c4a2d550ccef120d96a58c7bbf586255`. The official preset declares an aerobic glucose-limited medium and exact exchange bounds/reset instructions.

- **SysBioChalmers and yeast-GEM contributors. (2026). anaerobic.yml.** [Official source](https://github.com/SysBioChalmers/yeast-GEM/blob/2d594ae1c4a2d550ccef120d96a58c7bbf586255/data/conditions/anaerobic.yml). Version: `2d594ae1c4a2d550ccef120d96a58c7bbf586255`. The official anaerobic transformation changes additional bounds and biomass/cofactor assumptions beyond oxygen.

- **SysBioChalmers and yeast-GEM contributors. (2026). yeastgem.conditions Python wrapper.** [Official source](https://github.com/SysBioChalmers/yeast-GEM/blob/2d594ae1c4a2d550ccef120d96a58c7bbf586255/code/python/yeastgem/conditions.py). Version: `2d594ae1c4a2d550ccef120d96a58c7bbf586255`. Official condition wrapper applies additional preparation and delegates generic condition handling.

- **SysBioChalmers and yeast-GEM contributors. (2026). yeast-GEM upstream license.** [Official source](https://github.com/SysBioChalmers/yeast-GEM/blob/2d594ae1c4a2d550ccef120d96a58c7bbf586255/LICENSE.md). Version: `2d594ae1c4a2d550ccef120d96a58c7bbf586255`. The upstream file states Creative Commons Attribution 4.0 International.

- **SciPy developers. (2026). SciPy 1.17.0: linprog_highs.** [Official source](https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.linprog-highs.html). Version: `1.17.0`. Linear minimization, bounds/constraints, HiGHS solver status, feasibility tolerances and marginals.

## Reuse and interpretation

The input files retain their upstream license and attribution. A software citation documents an interface; a methodological citation documents an idea. Neither demonstrates that the assumptions fit these data or that the project has been experimentally validated. See [assumptions](assumptions.md) for that distinction.

## Repository portability

- **Git project contributors. gitattributes: text and eol attributes.** [Official documentation](https://git-scm.com/docs/gitattributes), checked 21 October 2026. Explains how line-ending conversion and `-text` affect the exact bytes used by source fingerprints. The fresh-checkout validation is recorded in the [maintenance review](review-2026-10-21.md).
