# Interview talking points

## 60-second pitch

"I analysed 97,905 real orders from Olist, a Brazilian marketplace, to answer why growth was slowing. The YoY number looked great,
+138%, but that was ramp-up. The 2018 run-rate was flat. I built a DuckDB star schema in SQL, cohort and RFM analysis, and a
Mann-Whitney test on delivery delay versus review score. Two things came out. First, only 3.0% of customers ever order twice, so the
business is pure acquisition, and acquisition had flattened. Second, late orders average 2.27 stars against 4.29, and the
14 worst states produce 51% of late orders from 30% of deliveries. I sized three actions, a second-purchase programme, delivery fixes and cross-sell, at about R$275k
a year, with every assumption visible in an Excel model. The dashboard is live on GitHub Pages and every number in the README is generated from one facts file."

## Five hard questions

**1. Your revenue impact is only 2.5% of revenue. Why should anyone care?**
Because I sized it with conservative, explicit lifts (1.0 pp repeat rate, 2.0 pp multi-item share) instead of picking
numbers that look impressive. The point of the analysis is the diagnosis: with 97% one-time buyers, retention is the lever, and each
extra point of repeat rate is worth about R$95.1k a year. If a test shows a bigger lift, the model in the workbook updates.

**2. Late delivery and bad reviews: is that causal?**
Not proven. It is observational. The effect is large (rank-biserial -0.64) and dose-response shaped: the later the order, the worse the review
(1.70 stars at 8+ days late). Confounders are possible, such as heavy products being both slow and more often damaged. To prove it I would test
honest delivery estimates in a few states and compare review scores.

**3. Why not use a frequency quintile in RFM like the textbook?**
Because 97.0% of customers have exactly one order. `NTILE(5)` on frequency would split identical customers into different scores
by tie order. I scored frequency from the order count instead and documented it in the SQL header.

**4. How do you know your numbers are right?**
Three checks. The SQL star schema and the pandas cleaning layer are independent implementations and the tests require identical results (revenue
R$13.45M in both). The Excel workbook is recalculated by Excel and its KPI cells must match `facts.json`. And `check_numbers.py`
fails the build if any number in the README or dashboard text is not in `facts.json`.

**5. Delivery fixes barely move revenue in your model. Did you get that wrong?**
No, that was a real result I chose to report. A late first order lowers repeat rate only from 3.06% to
2.54% (p = 0.019), and repeat is rare for everyone. So delivery is a review-score and reputation problem,
worth 1,477 fewer late orders a year, not the main retention problem. Overstating it would have sent the budget to the wrong place.

## Three things I would do differently

1. **Get cost data.** Without product cost this is a revenue analysis; profit by category would change the category priorities.
2. **Use survival analysis for repeat purchase.** A time-to-second-order model would handle the late cohorts' short observation window better than cohort tables.
3. **Join reviews text.** The review comments (Portuguese) would show *why* low scores happen beyond lateness, such as wrong item or damage.
