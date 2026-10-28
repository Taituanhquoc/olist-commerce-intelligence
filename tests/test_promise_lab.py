"""Offline tests: require only stdlib + the checked-in published aggregate data."""
import json
from dataclasses import replace

import pytest
from src.config import ROOT
from src.promise_lab import Assumptions, allocate, build, load_state_data, scenarios, wilson_interval


def test_state_export_coverage_is_explicit_not_fabricated():
    m=load_state_data()
    c=m["coverage"]
    assert c["states_in_export"] == 21
    assert c["delivered_in_export"] == 95354
    assert c["late_in_export"] == 6483
    assert c["delivered_national"] == 96203
    assert c["late_national"] == 6531
    assert c["excluded_delivered"] == 849
    assert c["excluded_late"] == 48


def test_source_rows_match_counts_and_intervals():
    m=load_state_data()
    for r in m["rows"]:
        assert abs(r["observed_late_rate"]-r["late_orders"]/r["delivered_orders"]) < 1e-10
        assert r["wilson_95_low"] <= r["observed_late_rate"] <= r["wilson_95_high"]
        assert 0 <= r["risk_adjusted_rate"] <= 1
    assert abs(m["national_late_rate"] - 6531/96203) < 1e-10


def test_wilson_validation():
    assert wilson_interval(0,100)[0] == 0
    assert wilson_interval(100,100)[1] == 1
    for args in [(-1,10),(11,10),(0,0)]:
        with pytest.raises(ValueError): wilson_interval(*args)


def test_no_budget_overrun_or_capacity_violation():
    model=load_state_data()
    a=Assumptions()
    p=allocate(model,a)
    assert p["summary"]["modeled_program_cost_brl"] <= a.budget_brl
    assert sum(r["treated_orders"] for r in p["allocations"]) == p["summary"]["treated_orders"]
    for r in p["allocations"]:
        assert 0 <= r["treated_orders"] <= r["capacity_orders"]
        assert r["capacity_orders"] <= r["delivered_orders"]


def test_zero_budget_no_fake_returns():
    p=allocate(load_state_data(), Assumptions(budget_brl=0))
    assert p["summary"]["treated_orders"] == 0
    assert p["summary"]["modeled_net_brl"] == 0
    assert p["summary"]["break_even_value_per_avoided_late_brl"] is None


def test_monotonic_efficacy_and_no_invented_impact_when_zero():
    model=load_state_data()
    p0=allocate(model,Assumptions(relative_late_reduction=0))
    p1=allocate(model,Assumptions(relative_late_reduction=.2))
    p2=allocate(model,Assumptions(relative_late_reduction=.4))
    assert p0["summary"]["modeled_late_avoided"] == 0
    assert 0 < p1["summary"]["modeled_late_avoided"] < p2["summary"]["modeled_late_avoided"]
    assert p0["summary"]["modeled_benefit_brl"] == 0


def test_assumptions_reject_invalid_inputs():
    model=load_state_data()
    for a in [Assumptions(budget_brl=-1), Assumptions(cost_per_treated_order_brl=0),
              Assumptions(relative_late_reduction=1.2), Assumptions(max_state_coverage=-.1),
              Assumptions(value_per_avoided_late_brl=-1), Assumptions(prior_strength_orders=-1)]:
        with pytest.raises(ValueError): allocate(model,a)


def test_scenarios_and_generated_outputs(tmp_path):
    x=build(out_dir=tmp_path)
    assert len(x["sensitivity"])==3
    assert (tmp_path/"state_priority.csv").exists()
    assert (tmp_path/"intervention_plan.csv").exists()
    saved=json.loads((tmp_path/"decision_data.json").read_text(encoding="utf-8"))
    assert saved["plan"]["summary"]["treated_orders"] == x["plan"]["summary"]["treated_orders"]
    assert x["plan"]["summary"]["modeled_net_brl"] < 0   # Base assumptions intentionally not made to look profitable


def test_html_dashboard_embeds_same_data():
    html=(ROOT/"promise_lab"/"index.html").read_text(encoding="utf-8")
    assert 'id="data" type="application/json"' in html
    assert "__EMBED_DATA__" not in html
    assert "not an observed return" in html
    assert "95% Wilson" in html
