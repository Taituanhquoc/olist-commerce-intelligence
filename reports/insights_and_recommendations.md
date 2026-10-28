# Insights and recommendations

Each insight follows the same chain: finding, evidence (values from `reports/facts.json`), why it matters, the recommended action,
and an impact estimate with its assumptions. Real data: Olist public dataset, 97,905 orders, Jan 2017 to Aug 2018.

---

## 1. Year-on-year growth hides a flat 2018

- **Finding.** Revenue stopped growing in 2018 even though the YoY figure looks excellent.
- **Evidence.** Jan-Aug revenue R$3.08M (2017) vs R$7.34M (2018), +138%.
  Average MoM growth fell from 22.7% (2017) to 2.5% (2018); the fitted 2018 trend is
  -1.1% a month; May-Aug averaged R$896k vs R$939k in Jan-Apr.
- **So what.** Reporting YoY alone would tell leadership the business is healthy at the moment it stalled.
- **Action.** Report a trailing three-month run-rate and MoM next to YoY on the executive dashboard.
- **Impact.** No direct revenue; it changes which problem gets attention first.

## 2. Growth is acquisition-only: 97% of customers buy once

- **Finding.** Customers almost never return.
- **Evidence.** Repeat purchase rate 3.03%; month-1 cohort retention 0.48%;
  3.2% of customers reorder within 180 days; repeat orders are 2.9% of revenue.
- **So what.** With new customers flat at about 6,459 a month, revenue cannot grow without a retention lever.
- **Action.** Second-purchase programme: post-delivery voucher plus recommendations matched to the first purchase category.
- **Impact.** R$95.1k a year at +1.0 pp repeat rate (77,509 new customers a year x
  1.0 pp x R$122.64 per repeat order). Range R$47.5k to R$190k.

## 3. The value pool is high-value one-time buyers

- **Finding.** Two RFM segments of one-time buyers hold most of the revenue.
- **Evidence.** Promising (14,682 customers) and At-Risk (14,097) are
  30% of customers and 57% of revenue, spending about
  R$267.97 each against R$55.62 for low-value New Customers.
- **So what.** A blanket retention campaign wastes budget on low-value buyers.
- **Action.** Target insight 2's programme at Promising first (recent), then At-Risk (lapsing), with a win-back offer for At-Risk.
- **Impact.** Included in insight 2; targeting raises the value per converted customer.

## 4. Late delivery is the biggest driver of bad reviews

- **Finding.** Reviews collapse as soon as an order misses its promised date.
- **Evidence.** 2.27 vs 4.29 stars, gap 2.02 (95% CI 1.98
  to 2.06); Mann-Whitney U p < 0.001, rank-biserial -0.64.
  62% of late orders get 1-2 stars vs 9% of on-time orders.
- **So what.** Review score is public on the marketplace; every late order is a visible 1-2 star rating.
- **Action.** Recalibrate promised delivery dates by state (a promise the carrier can keep), and alert sellers before the promise is breached.
- **Impact.** See insight 5.

## 5. Lateness is concentrated: 30% of deliveries produce 51% of late orders

- **Finding.** Lateness is geographic.
- **Evidence.** AL 21.5%, MA 17.5%, SE 15.4%, PI 13.9%, CE 13.8% late
  (national 6.8%). The 14 states above the national rate receive 30% of deliveries but hold 51% of late orders;
  RJ alone has 1,495 (23%).
- **So what.** A targeted fix in a few lanes moves the national number.
- **Action.** Carrier review for North-East states and RJ; state-specific delivery estimates.
- **Impact.** Bringing these states to the national rate avoids about 1,477 late orders a year and lifts the platform review average by
  about 0.04 stars. Direct repeat revenue is small (R$945), because a late first order lowers repeat
  rate only from 3.06% to 2.54% (p = 0.019).

## 6. Baskets are single-item

- **Finding.** Customers rarely add a second item.
- **Evidence.** 9.9% of orders have more than one item; 1.14 items per order; an add-on is worth
  R$111.27 on average.
- **So what.** AOV has been flat (0.4% YoY), so basket building is the cheapest growth lever after retention.
- **Action.** "Bought together" bundles at checkout in the top five categories; free-freight threshold tests.
- **Impact.** R$179k a year at +2.0 pp multi-item share (80,295 orders x
  2.0 pp x R$111.27).

## 7. Revenue depends on a few categories and sellers

- **Finding.** Concentration risk.
- **Evidence.** Top 10 of 74 categories = 62% of revenue; top 10% of sellers = 67%;
  top 20% = 83%.
- **So what.** Losing a handful of large sellers would hurt more than any seasonal dip.
- **Action.** Key-account management for the top seller decile; seller performance SLAs on delivery time.
- **Impact.** Risk reduction; not sized.

## 8. Installments go with bigger baskets (correlation)

- **Finding.** Order value rises with the number of credit-card installments.
- **Evidence.** R$82.62 single payment vs R$301.79 at 7+ installments;
  Spearman rho 0.45. Credit card is 75% of orders.
- **So what.** Installments probably enable high-ticket purchases, but big baskets may simply choose installments; the data cannot separate the two.
- **Action.** Test showing the installment price ("10x R$...") on high-ticket product pages before investing further.
- **Impact.** Not sized: needs an experiment.

---

**Total sized impact:** R$275k a year (2.5% of annualised 2018 revenue of R$11.0M).
