"""Delivery Promise Lab: an independently reproducible decision-support extension.

Uses the original project's published SQL aggregate export. No customer-level data is
needed, and the original project's metrics, notebooks, and code remain unchanged.

All economic and efficacy parameters are USER ASSUMPTIONS, not measured treatment
impacts or evidence of a causal relationship between delays and review ratings.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from src.config import ROOT

BASE = ROOT / "reports" / "sql_outputs" / "state_logistics.csv"
FACTS = ROOT / "reports" / "facts.json"
OUTPUT = ROOT / "reports" / "promise_lab"
NATIONAL_PRIOR_STRENGTH = 200.0  # Assumption: shrink small state samples toward national baseline


@dataclass(frozen=True)
class Assumptions:
    budget_brl: float = 15000.0
    cost_per_treated_order_brl: float = 5.0
    relative_late_reduction: float = 0.25
    value_per_avoided_late_brl: float = 150.0
    max_state_coverage: float = 0.35
    prior_strength_orders: float = NATIONAL_PRIOR_STRENGTH

    def validate(self):
        if self.budget_brl < 0 or self.cost_per_treated_order_brl <= 0:
            raise ValueError("Budget must be nonnegative and cost per treated order must be > 0")
        if not (0 <= self.relative_late_reduction <= 1):
            raise ValueError("Relative risk reduction must be in [0,1]")
        if not (0 <= self.max_state_coverage <= 1):
            raise ValueError("Maximum state coverage must be in [0,1]")
        if self.value_per_avoided_late_brl < 0 or self.prior_strength_orders < 0:
            raise ValueError("Value and prior strength must be nonnegative")


def wilson_interval(late: int, n: int, z: float = 1.95996398454) -> tuple[float, float]:
    """95% binomial Wilson interval; for descriptive risk, not causal effects."""
    if n <= 0 or late < 0 or late > n:
        raise ValueError("Invalid count")
    p = late / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    spread = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return max(0.0, center-spread), min(1.0, center+spread)


def load_state_data(csv_path: Path = BASE, facts_path: Path = FACTS, strength: float = NATIONAL_PRIOR_STRENGTH) -> dict:
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    national = facts["analysis"]["kpi"]
    national_delivered = int(national["delivered_orders"])
    national_late = int(national["late_orders"])
    national_rate = national_late/national_delivered
    if strength < 0:
        raise ValueError("Prior strength must be nonnegative")
    rows = []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"customer_state", "delivered_orders", "late_orders", "late_rate", "avg_review", "revenue"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("State export missing columns: " + str(required - set(reader.fieldnames or [])))
        for r in reader:
            state = r["customer_state"]
            n = int(r["delivered_orders"])
            late_raw = float(r["late_orders"])
            if not late_raw.is_integer():
                raise ValueError(f"Nonintegral late orders in {state}")
            late = int(late_raw)
            if n <= 0 or late < 0 or late > n:
                raise ValueError(f"Invalid late/delivered for {state}")
            if abs(late/n - float(r["late_rate"])) > 1e-8:
                raise ValueError(f"Late rate mismatch for {state}")
            low, high = wilson_interval(late, n)
            posterior = (late + national_rate*strength)/(n+strength)
            rows.append({
                "state": state, "delivered_orders": n, "late_orders": late,
                "observed_late_rate": late/n, "risk_adjusted_rate": posterior,
                "wilson_95_low": low, "wilson_95_high": high,
                "excess_late_vs_national_observed": max(0.0, late-n*national_rate),
                "avg_review": float(r["avg_review"]), "revenue_brl": float(r["revenue"]),
                "above_national_wilson": low > national_rate,
            })
    if len({r["state"] for r in rows}) != len(rows):
        raise ValueError("Duplicate state in aggregate")
    rows.sort(key=lambda r: (-r["risk_adjusted_rate"], -r["delivered_orders"], r["state"]))
    covered_orders = sum(r["delivered_orders"] for r in rows)
    covered_late = sum(r["late_orders"] for r in rows)
    if covered_orders > national_delivered or covered_late > national_late:
        raise ValueError("State export has more orders than national total: inconsistent scope")
    return {
        "dataset": "Olist Brazilian E-Commerce, Jan 2017–Aug 2018 (historical)",
        "coverage": {"states_in_export": len(rows), "delivered_in_export": covered_orders,
                     "late_in_export": covered_late, "delivered_national": national_delivered,
                     "late_national": national_late,
                     "excluded_delivered": national_delivered-covered_orders,
                     "excluded_late": national_late-covered_late,
                     "coverage_rate": covered_orders/national_delivered,
                     "note": "Original state_logistics export contains only states meeting its minimum-volume filter; excluded states are NOT treated as zero risk."},
        "national_late_rate": national_rate,
        "rows": rows,
    }


def allocate(model: dict, assumptions: Assumptions) -> dict:
    """Constrained greedy allocation by expected delayed orders avoided per BRL.

    Unit costs are uniform across states: risk-adjusted rate gives the ordering.
    The maximum volume targeted in each state is a scenario assumption, not an
    operationally verified capacity constraint.
    """
    assumptions.validate()
    remaining = int(math.floor(assumptions.budget_brl / assumptions.cost_per_treated_order_brl + 1e-10))
    allocations = []
    for row in sorted(model["rows"], key=lambda r: (-r["risk_adjusted_rate"], r["state"])):
        capacity = int(math.floor(row["delivered_orders"] * assumptions.max_state_coverage))
        treated = max(0, min(remaining, capacity))
        remaining -= treated
        averted = treated * row["risk_adjusted_rate"] * assumptions.relative_late_reduction
        cost = treated * assumptions.cost_per_treated_order_brl
        benefit = averted * assumptions.value_per_avoided_late_brl
        allocations.append({
            "state": row["state"], "delivered_orders": row["delivered_orders"],
            "observed_late_rate": row["observed_late_rate"],
            "risk_adjusted_rate": row["risk_adjusted_rate"],
            "wilson_95_low": row["wilson_95_low"],
            "wilson_95_high": row["wilson_95_high"],
            "above_national_wilson": row["above_national_wilson"],
            "capacity_orders": capacity, "treated_orders": treated,
            "modeled_late_avoided": averted, "modeled_benefit_brl": benefit,
            "modeled_cost_brl": cost, "modeled_net_brl": benefit-cost,
        })
    treated = sum(r["treated_orders"] for r in allocations)
    avoided = sum(r["modeled_late_avoided"] for r in allocations)
    cost = sum(r["modeled_cost_brl"] for r in allocations)
    benefit = avoided*assumptions.value_per_avoided_late_brl
    return {
        "assumptions": asdict(assumptions),
        "summary": {"treated_orders": treated, "modeled_late_avoided": avoided,
                    "modeled_program_cost_brl": cost, "modeled_benefit_brl": benefit,
                    "modeled_net_brl": benefit-cost,
                    "break_even_value_per_avoided_late_brl": (cost/avoided if avoided > 0 else None),
                    "unused_budget_brl": assumptions.budget_brl-cost},
        "allocations": allocations,
        "disclaimer": "Scenario, not prediction: efficacy, costs and business value are assumed; selected states are associated with historical late-delivery risk, not a measured treatment response.",
    }


def scenarios(model: dict, base: Assumptions) -> list[dict]:
    """Sensitivity changes efficacy and value, holding budget and unit cost fixed."""
    values = [("Conservative", 0.10, 75.0), ("Base case", base.relative_late_reduction, base.value_per_avoided_late_brl), ("Optimistic", 0.40, 225.0)]
    output=[]
    for name, efficacy, value in values:
        p = Assumptions(base.budget_brl, base.cost_per_treated_order_brl, efficacy,
                        value, base.max_state_coverage, base.prior_strength_orders)
        run = allocate(model,p)
        output.append({"scenario":name, **run["summary"], "efficacy":efficacy, "value_per_avoided_late_brl":value})
    return output


def build(out_dir: Path=OUTPUT, csv_path: Path=BASE, facts_path: Path=FACTS, assumptions: Assumptions=Assumptions()) -> dict:
    model=load_state_data(csv_path, facts_path, assumptions.prior_strength_orders)
    result={"model":model,"plan":allocate(model,assumptions),"sensitivity":scenarios(model,assumptions)}
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"decision_data.json").write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    with (out_dir/"state_priority.csv").open("w",newline="",encoding="utf-8") as f:
        keys=["state","delivered_orders","late_orders","observed_late_rate","risk_adjusted_rate","wilson_95_low","wilson_95_high","excess_late_vs_national_observed","above_national_wilson"]
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore");writer.writeheader();writer.writerows(model["rows"])
    with (out_dir/"intervention_plan.csv").open("w",newline="",encoding="utf-8") as f:
        keys=["state","delivered_orders","observed_late_rate","risk_adjusted_rate","capacity_orders","treated_orders","modeled_late_avoided","modeled_program_cost_brl","modeled_benefit_brl","modeled_net_brl"]
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore");writer.writeheader();writer.writerows(result["plan"]["allocations"])
    return result


def main():
    ap=argparse.ArgumentParser(description="Generate an honest, assumption-driven delivery promise prioritization.")
    ap.add_argument("--budget",type=float,default=15000.0)
    ap.add_argument("--unit-cost",type=float,default=5.0)
    ap.add_argument("--efficacy",type=float,default=.25)
    ap.add_argument("--value",type=float,default=150.0)
    ap.add_argument("--coverage",type=float,default=.35)
    ap.add_argument("--prior",type=float,default=200.0)
    args=ap.parse_args()
    p=Assumptions(args.budget,args.unit_cost,args.efficacy,args.value,args.coverage,args.prior)
    result=build(assumptions=p)
    print(json.dumps({"coverage":result["model"]["coverage"],"plan":result["plan"]["summary"]},indent=2))

if __name__=="__main__": main()
