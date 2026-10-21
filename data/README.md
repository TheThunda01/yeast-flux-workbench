# Model snapshot and attribution

This repository includes the unmodified MATLAB model and aerobic medium definition from **SysBioChalmers/yeast-GEM v9.1.1**, commit `2d594ae1c4a2d550ccef120d96a58c7bbf586255`, retrieved 20 October 2026. The [machine-readable manifest](provenance.json) provides source URLs, exact bytes and SHA-256 values.

The model is 529,680 bytes and uses a MATLAB 5.0 struct readable with SciPy. Its parsed dimensions are 2,748 metabolites × 4,105 reactions, with 1,143 genes. These counts belong to this later snapshot and need not match the counts in the original Yeast9 paper. The workbench preserves the downloaded MAT and applies scenario bounds in memory.

Source: [official release](https://github.com/SysBioChalmers/yeast-GEM/releases/tag/v9.1.1). Cite Zhang et al. (2024), [Yeast9](https://doi.org/10.1038/s44320-024-00060-7), and the specific v9.1.1 release. The model and medium use **CC BY 4.0**; the full [upstream license](UPSTREAM_LICENSE.md) is retained. Original analysis code has a separate MIT license. Keep source attribution when reusing the derived reports.

`minimal_Y6.yml` is included as source documentation. The supplied MAT already has the expected minimal aerobic glucose/oxygen bounds; this program checks and retains them rather than applying an untested wholesale exchange reset. The separately inspected upstream anaerobic preset changes more than oxygen, which is why this workbench limits its scenarios to positive oxygen caps.
