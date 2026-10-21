"""Build a model-bookkeeping diagram, not a biochemical reaction map."""
from __future__ import annotations

import hashlib
from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
INK, TEAL, BLUE, AMBER, MUTED, PALE = "#203449", "#007F7B", "#386CB0", "#B87824", "#596773", "#EEF3F6"


def text(x: int, y: int, lines: list[str], size: int = 18, color: str = INK,
         weight: str = "normal", anchor: str = "middle") -> str:
    return "".join(f'<text x="{x}" y="{y + 25*i}" font-size="{size}" fill="{color}" '
                   f'font-weight="{weight}" text-anchor="{anchor}">{escape(line)}</text>' for i, line in enumerate(lines))


def box(x: int, y: int, w: int, h: int, title: str, lines: list[str], color: str) -> str:
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="white" stroke="{color}" stroke-width="2"/>'
            + text(x+w//2, y+30, [title], 20, color, "bold")
            + text(x+w//2, y+62, lines, 17))


def arrow(x1: int, y1: int, x2: int, y2: int, color: str = MUTED) -> str:
    return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#arrow)"/>'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="750" viewBox="0 0 960 750" role="img">',
             '<title>How the yeast model turns declared constraints into conditional flux results</title>',
             '<desc>Glucose and oxygen bounds constrain a balanced reaction network alongside fixed maintenance and other medium assumptions. Biomass assembly r_4041 feeds the biomass drain r_2111. FBA optimizes the drain; FVA calculates selected individual ranges. Arrows are modeling relationships, not individual biochemical reactions.</desc>',
             f'<rect width="960" height="750" fill="white"/><g font-family="DejaVu Sans, sans-serif">',
             f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="{MUTED}"/></marker></defs>',
             text(480, 36, ["From model constraints to conditional results"], 26, INK, "bold"),
             text(480, 66, ["Bookkeeping schematic — not a reaction-by-reaction pathway map"], 17, MUTED),
             box(55, 100, 360, 125, "Exchange bounds", ["Glucose r_1714; oxygen r_1992", "Negative flux denotes uptake", "Caps are rates, not concentrations"], BLUE),
             box(545, 100, 360, 125, "Other retained constraints", ["Deposited medium and bounds", "Maintenance r_4046 = 0.7", "Model assumptions remain active"], AMBER),
             arrow(235,225,350,270), arrow(725,225,610,270),
             box(220, 270, 520, 100, "Balanced reaction network", ["S v = 0; lower ≤ v ≤ upper", "Many feasible flux distributions can remain"], TEAL),
             arrow(480,370,480,404),
             box(220, 405, 520, 95, "Biomass assembly → biomass drain", ["r_4041 assembles biomass requirements", "r_2111 is the optimized growth drain"], TEAL),
             arrow(360,500,235,550), arrow(600,500,725,550),
             box(55, 550, 360, 125, "FBA result", ["Maximum modeled growth", "One optimal flux vector", "Numerical feasibility checks"], BLUE),
             box(545, 550, 360, 125, "FVA results", ["Selected individual minima/maxima", "Declared growth floor and slack", "Endpoints need not coexist"], AMBER),
             text(480, 720, ["Feasible fluxes are model results, not measured rates or confidence intervals."], 17, MUTED),
             '</g></svg>']
    path = OUT / "model-bookkeeping.svg"
    path.write_text("\n".join(parts) + "\n")
    ET.parse(path)
    sources = [ROOT / "scenarios.json", ROOT / "docs" / "methods.md", ROOT / "data" / "provenance.json"]
    manifest = {"kind": "conceptual model-bookkeeping diagram", "arrows": "relationships between modeling steps; not biochemical reaction edges",
                "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                "output_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}
    (OUT / "figure-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
