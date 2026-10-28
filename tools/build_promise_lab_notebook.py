"""Build an inspectable analyst notebook for the distinct PromiseLab extension."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nbformat as nbf
from src.config import ROOT

n=nbf.v4.new_notebook(metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python"}})
md=lambda s:nbf.v4.new_markdown_cell(s)
code=lambda s:nbf.v4.new_code_cell(s)
n.cells=[
md("""# Delivery Promise Lab | From historical delay data to a pilot decision

**Distinct portfolio extension** to the original Olist analysis. This notebook intentionally begins from *published regional aggregate data*, not raw orders. See `NOTICE.md` for attribution.

**Decision question:** If an operations team can intervene on only a fraction of shipments, which states should enter a first pilot? What cost/value assumptions would justify one?

**Do not interpret the simulation as measured causal impact.** The source covers 2017–2018 and contains no actual intervention outcomes or verified cost-per-late-delivery figures."""),
md("""## 1 — Load and validate decision data

Reconcile the published state export against nationwide totals. The source CSV omits states with small order volumes, a source of easy but consequential denominator mistakes."""),
code("""from src.promise_lab import load_state_data, Assumptions, allocate, scenarios\nfrom pathlib import Path\nimport pandas as pd\nimport matplotlib.pyplot as plt\nmodel = load_state_data()\nprint('Coverage:', model['coverage'])\nassert model['coverage']['excluded_delivered'] == 849\nassert model['coverage']['excluded_late'] == 48\nstates = pd.DataFrame(model['rows'])\nstates.head(8)[['state','delivered_orders','late_orders','observed_late_rate','risk_adjusted_rate','above_national_wilson']]"""),
md("""## 2 — Compare both risk *rate* and absolute *volume*

Raw percentages make small states look extreme; late-order totals can make large states look worse simply because they ship more. Use both, add a 95% Wilson interval, and shrink sparse proportions toward a national prior. The prior strength of 200 is a planning choice; do not describe the resulting rate as ground truth."""),
code("""display(states.sort_values('late_orders', ascending=False).head(10)[['state','delivered_orders','late_orders','observed_late_rate','wilson_95_low','wilson_95_high']])\nfig,ax=plt.subplots(figsize=(10,5))\ntop=states.sort_values('late_orders',ascending=False).head(10).sort_values('late_orders')\nax.barh(top.state,top.late_orders,color='#208b81')\nax.set(title='Where the actual late-delivery workload accumulates',xlabel='Late orders in source data',ylabel='Customer state')\nfor i,v in enumerate(top.late_orders):ax.text(v+8,i,f'{v:,.0f}',va='center')\nax.spines[['top','right']].set_visible(False)\nfig.tight_layout();plt.show()"""),
md("""## 3 — Allocate a limited hypothetical pilot

The priority rule is **expected prevented late orders per unit cost**, given the same per-order intervention cost across states. Each state has a hypothetical maximum coverage. Assumed efficacy (relative late-rate reduction) and modeled value per avoided late case are not available in the dataset."""),
code("""base = Assumptions(budget_brl=15_000, cost_per_treated_order_brl=5, relative_late_reduction=.25, value_per_avoided_late_brl=150, max_state_coverage=.35)\nplan=allocate(model,base)\nprint('Base-case scenario summary:', plan['summary'])\ndisplay(pd.DataFrame(plan['allocations']).query('treated_orders > 0')[['state','treated_orders','risk_adjusted_rate','modeled_late_avoided','modeled_cost_brl']])"""),
md("""## 4 — Stress-test assumptions, never cherry-pick the most profitable outcome

Base case is deliberately allowed to be unprofitable. The break-even value is a decision threshold for *future validation*, not a claim of verified cost savings."""),
code("""sensitivity=pd.DataFrame(scenarios(model,base))\ndisplay(sensitivity[['scenario','efficacy','value_per_avoided_late_brl','modeled_late_avoided','modeled_program_cost_brl','modeled_net_brl']])\nfig,ax=plt.subplots(figsize=(8,4))\nax.bar(sensitivity['scenario'],sensitivity['modeled_net_brl'],color=['#ad6a5e','#217e86','#67a99d'])\nax.axhline(0,color='black',linewidth=.8)\nax.set(ylabel='Modeled net value (BRL)',title='Scenario economics: assumptions dominate the decision')\nax.spines[['top','right']].set_visible(False)\nfig.tight_layout();plt.show()"""),
md("""## 5 — Recommendation, experiment design and limits

**Recommendation:** Do *not* sign off on national rollout from this dataset. Start with a narrowly controlled pilot, validate treatment cost and actual efficacy, and then reallocate using observed uplift.

**Candidate pilot markets:** RJ provides substantial late-order volume; AL and MA offer higher observed percentages but fewer orders. Because the model uses a uniform treatment cost, it ranks by adjusted risk. If local carrier costs differ, replace this ranking with incremental preventable delays per BRL.

**Experiment design:** Randomly allocate eligible shipments (within market and time strata) to a revised delivery-promise intervention versus business-as-usual. Pre-register late-delivery rate as primary outcome; monitor complaint rate, review score, net margin, and guardrails. Use intention-to-treat analysis and track both absolute and relative risk reductions.

**Key limitations:** (i) state aggregation hides route/carrier heterogeneity, (ii) 2017–18 is not representative of current operations, (iii) historical review differences are associational, (iv) costs, efficacy and monetary value are assumptions, (v) the source's state export excludes 849 national deliveries. See `docs/portfolio/decision_memo.md`."""),
]
p=ROOT/'notebooks'/'05_delivery_promise_lab.ipynb'
nbf.write(n,p)
print('Wrote',p)
if __name__=='__main__':
    import sys
    if '--execute' in sys.argv:
        import nbclient
        client=nbclient.NotebookClient(n,timeout=90,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
        n=client.execute()
        nbf.write(n,p)
        print('Executed notebook:',len(n.cells),'cells')
