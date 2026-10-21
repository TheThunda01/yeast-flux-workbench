# Literature and practice review

## Question and scope

Which conclusions about a curated yeast metabolic network remain feasible under stated nutrient and growth constraints? The review supports a small, reproducible FBA/FVA analysis and its limitations. It does not review strain-design methods or validate a new biological prediction.

Primary model/method papers and official repository/solver sources were inspected on 20 October 2026. Foundational work was retained without a publication-date restriction. This is a bounded rapid review, not a complete systematic review.

## Search record

The searches below are the preserved development record, not a claim that the literature search was rerun for the editorial review. The [21 October UTC source recheck](reference-audit.json) records current metadata, inspected passages and access limits. It does not add a new systematic-search yield.

The exact queries, counts, IDs, warnings, repeat retrievals and access limits are recorded in [search-log.json](search-log.json). PubMed discovery came first, followed by official source inspection.

| Query | Order and limit | Returned / total | Use |
| --- | --- | --- | --- |
| `(Saccharomyces cerevisiae[Title/Abstract]) AND ("Yeast8"[Title/Abstract] OR "Yeast9"[Title/Abstract] OR "Yeast7"[Title/Abstract])` | Publication date; 10; no date filter | 10 / 10 | Model paper and relevant model limitations. The service warned about and omitted the Yeast7 term. Repeated once to retain metadata; duplicates counted once. |
| `("flux variability analysis"[Title] OR "What is flux balance analysis"[Title])` | Publication date; 10; no date filter | 8 / 8 | FVA method. The service warned about the FBA phrase. |
| `"What is flux balance analysis"[Title]` | Publication date; 5 | 0 / 0 | Did not retrieve the known primer; direct PMID retrieval recovered it. |
| `"thermodynamically infeasible loops"[Title/Abstract] AND Schellenberger[Author]` | Relevance; 5 | 1 / 1 | Narrow internal-loop caveat. |

The searches produced 19 distinct records; the directly retrieved FBA primer brings the scoped set to 20. Six primary papers were retained. Four had complete PMC text retrieved, with relevant methods/limitations appraised; Yeast8 and the loop paper were abstract-level appraisals. An initially misremembered PMID returned an unrelated nutrition paper and was discarded. Two over-limit full-text requests failed before returning text and were retried. The loop paper's full-text call failed internally, so no full-text appraisal is claimed.

Official material included the v9.1.1 release, license, compact MAT, medium definitions and Python condition wrapper. The model was parsed and a short LP feasibility probe was run before implementation. Web result totals were unavailable and are not added to PubMed counts.

## What the sources support

| Source | Type and access | Relevant support | Limit | Implementation consequence |
| --- | --- | --- | --- | --- |
| [Zhang et al. (2024)](https://doi.org/10.1038/s44320-024-00060-7) | Primary Yeast9 model paper; complete text | Community-curated metabolic reconstruction and demonstrated uses. | The paper version and its reported tests are not identical to the later v9.1.1 model or this workbench. | Pin the release and compute its own counts; do not inherit a published validation score. |
| [Lu et al. (2019)](https://doi.org/10.1038/s41467-019-11581-3) | Primary model resource; abstract | Versioned community model development. | Detailed derived-model predictions were not appraised or reproduced. | Retain version/commit/source hashes and distinguish model from analysis. |
| [Orth et al. (2010)](https://doi.org/10.1038/nbt.1614) | Primary FBA primer; complete text | Stoichiometric balance, flux bounds and optimization objectives. | A steady-state feasible solution is not a kinetic trajectory or an observed concentration. | Implement sparse equality/bound constraints and label variables precisely. |
| [Kenefake et al. (2022)](https://doi.org/10.1186/s12859-022-05089-9) | Primary FVA method; complete text | Conditional reaction-flux ranges when an objective-retention constraint is imposed. | Its acceleration algorithm and performance are not reproduced here. | Solve separate minima/maxima for selected reactions; expose fractions and effective floors. |
| [Moreno-Paz et al. (2022)](https://doi.org/10.1111/1751-7915.13995) | Primary enzyme-constrained/dynamic study; complete text | Additional enzyme/dynamic constraints matter for questions beyond conventional FBA. | The present static model does not inherit its predictions. | Avoid Crabtree-effect or dynamic-growth claims. |
| [Schellenberger et al. (2011)](https://doi.org/10.1016/j.bpj.2010.12.3707) | Primary loop-elimination method; abstract only | Ordinary steady-state flux models can allow thermodynamically infeasible loops. | No loopless implementation or detailed method appraisal here. | Mark ordinary FVA as such and flag ranges at artificial caps. |
| [Official release and medium](https://github.com/SysBioChalmers/yeast-GEM/tree/2d594ae1c4a2d550ccef120d96a58c7bbf586255) | Pinned source inspected; CC BY 4.0 | Exact model, signed exchanges and aerobic/anaerobic conditions. | A medium preset does not independently validate the physiological scenario. | Retain all existing bounds except two named exchanges; do not apply a blanket reset or call oxygen-only changes anaerobic modeling. |
| [SciPy 1.17.0 HiGHS interface](https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.linprog-highs.html) | Official software documentation | Minimization, linear constraints, solver statuses and tolerances. | Numerical success does not prove biology; solver methods can differ near a degenerate optimum. | Negate a float objective, validate residuals/duality, and cross-check with interior point. |

## Changes made

The workbench loads the compact pinned MAT without a commercial solver or COBRA dependency, evaluates six prespecified scenarios, and reports 36 selected FVA ranges. It exports full FBA vectors for direct feasibility checks and repeats optima/ranges with another HiGHS algorithm.

During development, an exact optimal-growth floor produced algorithm-sensitive failures on several degenerate FVA subproblems. The implementation now declares a small floor slack, records requested/effective floors per row, and requires both endpoint solves to succeed. That is numerical handling, not evidence of biological variability. Tests cover a known toy optimum/range, unsigned objective conversion, infeasible/unbounded cases, malformed inputs, the source fingerprint, full-model residuals and the result verifier.

No new experimental observations, pathway changes, gene perturbations or product-maximization objectives were added. The analysis keeps source licensing and version-specific counts explicit.

## Remaining work

Independent experimental comparison, loop-aware analysis, broader medium audits and a versioned COBRA implementation check are prioritized in [practical use](practical-use.md#next-improvements). Each requires its own acceptance checks; none is implied by the current figures.

## Limits of this review

The terms were chosen for this narrow project, not independently validated as a comprehensive search strategy. Screening was by one AI-assisted workflow, with no registered protocol, formal risk-of-bias assessment or quantitative literature synthesis. Two retained papers were abstract-only. Relevant full-text sections were appraised rather than every downstream result. Official repository descriptions and numerical smoke tests establish provenance/tractability, not external predictive validity.
