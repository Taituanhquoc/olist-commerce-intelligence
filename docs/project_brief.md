# Project brief: E-commerce sales, customer and delivery analytics

## Problem

Growth at the marketplace is slowing. Leadership wants to know why, which customers and categories drive revenue, and where
delivery problems hurt reviews and repeat purchases. The answer has to end in a short list of actions with a sized impact.

## Stakeholders

| Stakeholder | What they need |
|---|---|
| CEO / Head of Growth | Is growth really slowing, why, and what are the top actions |
| CRM / Retention lead | Which customers to target for a second purchase, and with what |
| Category managers | Which categories and sellers carry revenue; where the long tail sits |
| Logistics / Operations | Which states and lanes are late, and how much lateness costs in reviews |
| Finance | Payment mix and order value; impact estimates with explicit assumptions |

## Business questions

1. How are revenue, orders and average order value trending (MoM, YoY, seasonality)?
2. Which categories and sellers drive revenue, and how long is the tail?
3. What RFM customer segments exist, and what is each worth?
4. Do customers come back? Cohort retention and repeat-purchase rate.
5. Does late delivery lower review scores? Statistical test and effect size.
6. Which customer states have the worst delivery experience?
7. How does payment method relate to order value?

## KPI definitions

| KPI | Definition |
|---|---|
| Revenue | Sum of item `price` for in-scope orders (freight excluded) |
| Orders | Distinct in-scope `order_id` |
| AOV | Revenue / Orders |
| MoM % / YoY % | Revenue vs previous month / same month last year |
| Repeat purchase rate | Customers (`customer_unique_id`) with two or more orders / all customers |
| Cohort retention | Share of a first-purchase-month cohort ordering again k months later |
| Avg delivery days | Mean days from purchase to customer delivery (delivered orders) |
| On-time % | Delivered orders received on or before the promised date / delivered orders |
| Avg review | Mean of the latest review score per order |
| Running total | Cumulative revenue across months |

In-scope order: purchased between January 2017 and August 2018, status not canceled or unavailable, at least one item.

## Success criteria

- Every question answered with a number, a chart and a one-line takeaway.
- SQL, Python, Excel and dashboard agree on the headline KPIs (tested).
- The headline names what holds back growth and three actions, each with an impact estimate and stated assumptions.
- Anyone can rebuild everything with `make all` from a fresh clone.
