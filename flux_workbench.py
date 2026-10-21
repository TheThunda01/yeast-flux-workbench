"""Sparse, bounded FBA and selected FVA for a pinned yeast model."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.optimize import linprog
from scipy.sparse import csc_matrix

MODEL_SHA256 = "9f985af321f9ef5e8c6041de3def9e0e95efbed7aff90c81490578f451ace524"
BALANCE_TOLERANCE = 1e-7
FVA_FLOOR_TOLERANCE = 1e-7
SOLVER_OPTIONS = {"primal_feasibility_tolerance": 1e-9,
                  "dual_feasibility_tolerance": 1e-9, "time_limit": 30}
STATUS = {0: "optimal", 1: "limit", 2: "infeasible", 3: "unbounded", 4: "solver_error"}


class ValidationError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass
class Model:
    S: csc_matrix
    lower: np.ndarray
    upper: np.ndarray
    objective: np.ndarray
    rhs: np.ndarray
    ids: tuple[str, ...]
    names: tuple[str, ...]
    gene_count: int = 0

    def __post_init__(self):
        self.S = csc_matrix(self.S, dtype=float)
        self.lower, self.upper, self.objective, self.rhs = (
            np.asarray(a, dtype=float).reshape(-1) for a in
            (self.lower, self.upper, self.objective, self.rhs))
        m, n = self.S.shape
        if any(len(a) != n for a in (self.lower, self.upper, self.objective)) or len(self.rhs) != m:
            raise ValidationError("Matrix, bounds, objective and balance dimensions disagree")
        if len(self.ids) != n or len(self.names) != n or len(set(self.ids)) != n or any(not x for x in self.ids):
            raise ValidationError("Reaction identifiers must be complete and unique")
        if (not np.isfinite(self.S.data).all() or not np.isfinite(self.rhs).all()
                or not np.isfinite(self.objective).all() or not np.any(self.objective)):
            raise ValidationError("Stoichiometry, balances and nonzero objective must be finite")
        if (np.isnan(self.lower).any() or np.isnan(self.upper).any()
                or np.isposinf(self.lower).any() or np.isneginf(self.upper).any()
                or np.any(self.lower > self.upper)):
            raise ValidationError("Invalid lower/upper bounds")

    def index(self, reaction):
        try:
            return self.ids.index(reaction)
        except ValueError as error:
            raise ValidationError(f"Unknown reaction: {reaction}") from error


def load_pinned_model(path):
    if digest(path) != MODEL_SHA256:
        raise ValidationError("Model SHA-256 does not match pinned yeast-GEM v9.1.1")
    raw = loadmat(path, simplify_cells=True)["model"]
    model = Model(raw["S"], raw["lb"], raw["ub"], raw["c"], raw["b"],
                  tuple(map(str, raw["rxns"])), tuple(map(str, raw["rxnNames"])), len(raw['genes']))
    if model.S.shape != (2748, 4105) or model.gene_count != 1143 or np.any(model.rhs != 0):
        raise ValidationError("Unexpected pinned model dimensions or balance semantics")
    if np.flatnonzero(model.objective).tolist() != [model.index("r_2111")] or model.objective[model.index("r_2111")] != 1:
        raise ValidationError("Unexpected pinned growth objective")
    # Only known exchange reactions are edited. A one-metabolite sink can be
    # biomass drainage rather than a medium exchange, so no blanket reset occurs.
    for key, bound in [("r_1714", -1), ("r_1992", -1000)]:
        i = model.index(key)
        if model.S[:, i].nnz != 1 or model.S[:, i].data[0] != -1 or model.lower[i] != bound:
            raise ValidationError(f"Unexpected uptake convention for {key}")
    i = model.index("r_4046")
    if model.lower[i] != .7 or model.upper[i] != .7:
        raise ValidationError("Pinned maintenance constraint changed")
    return model


def scenario_bounds(model, glucose, oxygen):
    if (type(glucose) not in (int, float) or type(oxygen) not in (int, float)
            or not np.isfinite([glucose, oxygen]).all() or glucose < 0 or oxygen <= 0):
        raise ValidationError("Glucose cap must be nonnegative and oxygen cap strictly positive")
    lower, upper = model.lower.copy(), model.upper.copy()
    lower[model.index("r_1714")] = -float(glucose)
    lower[model.index("r_1992")] = -float(oxygen)
    return lower, upper


def solve(model, cost, lower=None, upper=None, growth_floor=None, method="highs-ds"):
    lower = model.lower if lower is None else np.asarray(lower, dtype=float)
    upper = model.upper if upper is None else np.asarray(upper, dtype=float)
    cost = np.asarray(cost, dtype=float)
    if (cost.shape != model.objective.shape or not np.isfinite(cost).all()
            or lower.shape != model.lower.shape or upper.shape != model.upper.shape
            or np.isnan(lower).any() or np.isnan(upper).any() or np.any(lower > upper)):
        raise ValidationError("Invalid solve objective or bounds")
    if growth_floor is not None and (not np.isfinite(growth_floor) or growth_floor < 0):
        raise ValidationError("Growth floor must be finite and nonnegative")
    a_ub = None if growth_floor is None else -model.objective.reshape(1, -1)
    b_ub = None if growth_floor is None else [-growth_floor]
    result = linprog(cost, A_eq=model.S, b_eq=model.rhs, A_ub=a_ub, b_ub=b_ub,
                     bounds=list(zip(lower, upper)), method=method, options=SOLVER_OPTIONS)
    report = {"status": STATUS.get(result.status, "unknown"), "solver_status": int(result.status),
              "iterations": int(result.nit), "objective": None, "max_balance_residual": None,
              "max_bound_violation": None, "growth_floor_violation": None, "duality_gap": None}
    if not result.success:
        return report, None
    x = result.x
    balance = float(np.max(np.abs(model.S @ x - model.rhs), initial=0))
    violation = float(max(np.max(lower-x, initial=0), np.max(x-upper, initial=0)))
    floor_violation = float(max(0, growth_floor - model.objective @ x)) if growth_floor is not None else 0.0
    dual = float(model.rhs @ result.eqlin.marginals)
    if growth_floor is not None:
        dual += float(-growth_floor * result.ineqlin.marginals[0])
    for values, marginals in [(lower, result.lower.marginals), (upper, result.upper.marginals)]:
        finite = np.isfinite(values)
        dual += float(values[finite] @ marginals[finite])
    objective = float(cost @ x)
    gap = abs(objective - dual)
    if (not np.isfinite(x).all() or max(balance, violation, floor_violation) > BALANCE_TOLERANCE
            or gap > BALANCE_TOLERANCE * (1 + abs(objective))):
        raise ValidationError("Solver returned an optimum that fails residual/duality checks")
    report.update(objective=objective, max_balance_residual=balance,
                  max_bound_violation=violation, growth_floor_violation=floor_violation, duality_gap=gap)
    return report, x


def fba(model, lower=None, upper=None, method="highs-ds"):
    report, x = solve(model, -model.objective, lower, upper, method=method)
    report["growth"] = None if x is None else float(model.objective @ x)
    return report, x


def fva(model, lower, upper, optimum, reactions, fraction=.99, method="highs-ds"):
    if type(fraction) not in (int, float) or not 0 < fraction <= 1 or not np.isfinite(fraction):
        raise ValidationError("FVA growth fraction must be in (0, 1]")
    if not np.isfinite(optimum) or optimum <= 0:
        raise ValidationError("FVA requires a strictly positive optimal growth flux")
    if len(reactions) != len(set(reactions)):
        raise ValidationError("FVA reactions must be unique")
    rows = []
    slack = FVA_FLOOR_TOLERANCE * (1 + abs(optimum))
    floor = max(0., fraction*optimum - slack)
    for reaction in reactions:
        i = model.index(reaction)
        cost = np.zeros(len(model.ids)); cost[i] = 1
        lo, _ = solve(model, cost, lower, upper, floor, method)
        hi, _ = solve(model, -cost, lower, upper, floor, method)
        minimum = lo["objective"]
        maximum = None if hi["objective"] is None else -hi["objective"]
        rows.append({"reaction": reaction, "name": model.names[i], "growth_fraction": float(fraction),
                     "requested_growth_floor": float(fraction*optimum), "growth_floor": float(floor),
                     "growth_floor_slack": float(slack), "minimum": minimum, "maximum": maximum,
                     "minimum_status": lo["status"], "maximum_status": hi["status"],
                     "touches_artificial_cap": bool((minimum is not None and abs(minimum) >= 999.999)
                                                     or (maximum is not None and abs(maximum) >= 999.999)),
                     "minimum_diagnostics": lo, "maximum_diagnostics": hi})
    return rows


def read_config(path, model):
    config = json.loads(Path(path).read_text())
    if config.get("schema_version") != 1 or not isinstance(config.get("scenarios"), list) or not config["scenarios"]:
        raise ValidationError("Configuration needs schema_version 1 and scenarios")
    names = []
    for entry in config["scenarios"]:
        if set(entry) != {"name", "glucose_uptake_cap", "oxygen_uptake_cap", "expected_status", "run_fva"}:
            raise ValidationError("Unexpected scenario fields")
        name = entry["name"]
        if not isinstance(name, str) or not name or not name.replace('_','').isalnum():
            raise ValidationError("Scenario name must be nonblank alphanumeric/underscore")
        names.append(name)
        scenario_bounds(model, entry["glucose_uptake_cap"], entry["oxygen_uptake_cap"])
        if entry["expected_status"] not in {"optimal", "infeasible"} or type(entry["run_fva"]) is not bool:
            raise ValidationError("Invalid scenario expected status or FVA flag")
    if len(set(names)) != len(names):
        raise ValidationError("Scenario names must be unique")
    for fraction in config.get("growth_fractions", []):
        if type(fraction) not in (int, float) or not np.isfinite(fraction) or not 0 < fraction <= 1:
            raise ValidationError("Growth fractions must be in (0, 1]")
    if not config.get("growth_fractions") or len(set(config["growth_fractions"])) != len(config["growth_fractions"]):
        raise ValidationError("Growth fractions must be nonempty and unique")
    reactions = config.get("fva_reactions", [])
    if not reactions or len(set(reactions)) != len(reactions):
        raise ValidationError("FVA reactions must be nonempty and unique")
    for reaction in reactions:
        model.index(reaction)
    return config


def analyze(model, config, method="highs-ds"):
    scenarios, ranges, vectors = [], [], {}
    for entry in config["scenarios"]:
        lower, upper = scenario_bounds(model, entry["glucose_uptake_cap"], entry["oxygen_uptake_cap"])
        solution, x = fba(model, lower, upper, method)
        if solution["status"] != entry["expected_status"]:
            raise ValidationError(f"Unexpected status for {entry['name']}: {solution['status']}")
        scenarios.append({**entry, **solution})
        if x is not None:
            vectors[entry["name"]] = x
            if entry["run_fva"]:
                for fraction in config["growth_fractions"]:
                    for row in fva(model, lower, upper, solution["growth"], config["fva_reactions"], fraction, method):
                        if row['minimum_status']!='optimal' or row['maximum_status']!='optimal':
                            raise ValidationError(f"FVA endpoint failed: {entry['name']} / {row['reaction']}; {row['minimum_status']} / {row['maximum_status']}")
                        ranges.append({"scenario": entry["name"], **row})
    return {"scenarios": scenarios, "ranges": ranges, "vectors": vectors}
