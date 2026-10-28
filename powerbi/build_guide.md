# Build guide: assemble the .pbix (about two hours)

No `.pbix` is committed. Power BI Desktop cannot be scripted from this pipeline, so this guide rebuilds the report by hand from
the exported tables. The HTML dashboard in `dashboard/index.html` shows the target result.

## 1. Export the data (5 min)

1. Run `make all` (or at least `make warehouse clean analysis`).
2. Run `python -m src.powerbi_export`. It writes `powerbi/export/fact_order_items.csv`, `fact_orders.csv`, `dim_date.csv`,
   `dim_customer.csv`, `dim_product.csv`, `dim_seller.csv`, `rfm_segments.csv`, `cohort_retention.csv` and `delivery_review.csv`.

## 2. Load (10 min)

1. Open Power BI Desktop > **Get data** > **Text/CSV**. Load each file from `powerbi/export/`.
2. In Power Query, check types: dates as Date, `price`, `freight_value`, `revenue` as Decimal, `is_delivered` and `is_late` as True/False.
3. **Close & Apply**.

## 3. Model (15 min)

1. **Model view**: create the relationships listed in `data_model.md` (drag key to key; many-to-one, single direction).
2. Select `dim_date` > **Table tools** > **Mark as date table** > `date_key`.
3. **Home** > **Enter data** > name it `_Measures`, load with no rows. Hide the default column.

## 4. Measures (20 min)

1. Select `_Measures` > **New measure**. Paste each block from `measures.dax` (one measure per paste).
2. Set the format string written in each comment (Measure tools > Format).
3. Check: card with `[Revenue]` and no filters must equal the README revenue; `[Orders]` must equal the README order count.

## 5. Theme (2 min)

**View** > **Themes** > **Browse for themes** > `powerbi/theme.json`.

## 6. Pages (60 min)

Follow `report_layout.md` page by page.

1. Add the three slicers to page 1; **View** > **Sync slicers** to pages 2 and 4.
2. Build visuals with the fields listed in the layout. Use **Top N** in the filter pane for the top-15 categories.
3. Page 3 uses the `rfm_segments` and `cohort_retention` tables directly; give the matrix a blue background colour scale
   (Format > Cell elements > Background color > Gradient).
4. Page 4: on the delay chart, use **Conditional formatting** on bar colour with a rule on `delay_bucket` (late buckets red).

## 7. Validate (10 min)

| Check | Expected |
|---|---|
| Revenue, no filters | Same as `reports/facts.json` > `analysis.kpi.revenue` |
| Orders | `analysis.kpi.orders` |
| Repeat Purchase Rate | `analysis.kpi.repeat_rate` |
| On-Time % | `analysis.kpi.on_time_rate` |
| Avg Review | `analysis.kpi.avg_review` |

Save as `powerbi/olist_ecommerce.pbix` (it is git-ignored by default; remove the ignore line if you want to publish it).
