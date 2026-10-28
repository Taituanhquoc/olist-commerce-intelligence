# Decision memo | Where should Olist test better delivery promises?

**Audience:** Operations Director, Regional Logistics Leads, Growth Analytics and Finance  
**Scope:** Historical Brazilian marketplace, Jan 2017–Aug 2018  
**Prepared as:** A portfolio case study on a public, historical dataset (not commissioned by Olist)  
**Authors' work boundaries:** New PromiseLab extension is distinguished from the attributed upstream analytics in `NOTICE.md`.

## Executive decision

**Recommendation: run a limited, randomized logistics-promise pilot before any large-scale investment.** Historical performance demonstrates a delivery experience problem, but it cannot establish either treatment efficacy or intervention profitability. The chosen *illustrative* assumptions imply **R$772 modeled net loss** from a R$15,000 pilot; the threshold for breaking even would be **about R$158 of business value per late shipment avoided**. A negative scenario is valuable evidence against overconfident rollout.

## Finding 1 — Risk percentage and operational burden are not interchangeable

- National delivered orders: **96,203**; national late deliveries: **6,531**, or **6.79%**.
- The source's state export lists **21 states / 95,354 delivered orders**, omitting **849 delivered orders and 48 late orders** in low-volume states.
- **AL**: 85 late out of 396 delivered (**21.5%**). **MA**: 125 / 713 (**17.5%**).
- **RJ**: 1,495 / 12,310 (**12.1%**), a major operational burden despite a lower percentage.
- **SP**: 1,817 / 40,399 (**4.5%**); high absolute count but *below* national percentage.

**Implication:** An intervention policy must be able to compare *expected preventable late shipments* rather than ranking on a single rate or count alone. In regions with low sample sizes, interval uncertainty and smoothing matter.

## Finding 2 — Customer experience correlations are strong, but not causal

The upstream pipeline reports average review **4.29 for on-time orders versus 2.27 for late orders**, a 2.02-star difference. Observational delivery status is correlated with other factors (distance, parcel type, carrier, geography, seller), so this alone is **not evidence** that a new delivery promise policy will increase reviews by 2.02 points.

**Next analysis with order-level data:** Fit a model adjusting for customer state, order month, basket value, shipping distance and product category, then validate sensitivity; this remains observational. Actual operational impact requires an experiment.

## Modeling logic

Let state \(s\) have late count \(L_s\) and delivery count \(N_s\). With national late rate \(p_0 = 6531 / 96203\), define a risk-adjusted state estimate

\[
\tilde p_s = \frac{L_s + 200p_0}{N_s + 200}.
\]

The 200-order prior strength is an **analyst-controlled assumption**, not a parameter fit on held-out data. Wilson 95% intervals are computed from observed state counts independently of smoothing.

For a policy treating \(T_s\) shipments in state \(s\), an assumed relative lateness-risk reduction \(e\), treatment cost \(c\) per shipment, and an assumed value \(v\) per prevented late shipment:

\[
\text{Avoided}_s = T_s \tilde p_s e,\quad \text{Net} = v \sum_s \text{Avoided}_s - c\sum_s T_s.
\]

Constraints: total treatment cost ≤ available budget; \(T_s\) ≤ floor(coverage × delivered orders in state). Greedy allocation ranks states by \(\tilde p_s\) because cost/treated shipment is assumed uniform; a future model with heterogeneous costs should instead rank marginal benefit/BRL.

## Base scenario — transparent planning assumptions

| Variable | Illustrative assumption / result |
|---|---:|
| Budget | R$15,000 |
| Cost per targeted shipment | R$5 |
| Relative late-risk reduction | 25% |
| Maximum coverage per state | 35% |
| Economic value per avoided late shipment | R$150 |
| Orders modeled as targeted | 3,000 |
| Modeled late shipments avoided | 94.9 |
| Modeled gross benefit | R$14,228 |
| Modeled program cost | R$15,000 |
| Modeled net value | **–R$772** |
| Model break-even value / avoided late order | **R$158** |

These outputs are arithmetically reproducible but **not estimated causal impact**, **not historical profit**, and **not business forecasts**.

## Proposed pilot and measurement plan

1. **Pilot definition:** Choose operations-ready lanes in selected states, not every order in the state. Avoid assigning blame to individual sellers from order-grain metrics.
2. **Random assignment:** Within participating state × carrier × calendar-week strata, randomize eligible shipments to new ETA/promise intervention vs usual process.
3. **Primary metric:** Probability of late delivery, defined against the *same contractual promise date rule* in both groups. Record promise shifts explicitly to avoid improving the KPI merely by relaxing the promise.
4. **Secondary/guardrail metrics:** Customer review scores, refund requests, complaint rate, transit time, service cost, and on-time delivery against an operationally fixed benchmark.
5. **Unit economics:** Record actual cost per eligible treated shipment; measure business value with observed refund/support/retention changes, not a guessed price per avoided late case.
6. **Analysis:** Use intention-to-treat, absolute difference with confidence interval, time-stratified adjustment and pre-registered stopping criteria. Ensure no experiment leaves customers without promised service.

## Next versions worth building

- Carrier × route × distance × product-category grain, with data-quality checks for missing promised/actual delivery timestamps.
- Compare state estimates using alternative prior strengths (0, 50, 200, 500) and expose resulting ranking stability.
- Integrate route-specific intervention costs and constrained optimization (knapsack/linear programming rather than unit-cost greedy).
- Once trial outcomes exist, estimate heterogeneous treatment effects and feed measured efficacy into the allocation engine.

## Caveats and provenance

The underlying dataset is historical and covers only a particular marketplace. Six low-volume states are omitted from the *aggregate* state export; they are not zero-risk. Original reports and broader EDA come from the upstream codebase. This memo and the PromiseLab extension were created as a learning/portfolio exercise with AI assistance; details and authorship are documented in `NOTICE.md`.
