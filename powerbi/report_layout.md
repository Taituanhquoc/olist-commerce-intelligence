# Report layout (four pages, 16:9)

Same four pages as the HTML dashboard. Slicers sit in one row at the top of every page: Month (between), Category, Customer state.
Sync slicers across pages 1, 2 and 4 (View > Sync slicers). Page 3 has no date slicer: customer metrics need full history.

## Page 1: Executive Overview

```
+------------------------------------------------------------------------------+
| [Month slicer]  [Category slicer]  [State slicer]                            |
+-----------+-----------+-----------+-----------+-----------+------------------+
| Revenue   | Orders    | AOV       | Customers | On-Time % | Avg Review       |  <- 6 cards
+-----------+-----------+-----------+-----------+-----------+------------------+
| Line chart: Revenue by dim_date[year_month]                (full width)      |
+--------------------------------------+---------------------------------------+
| Column chart: MoM % by month         | Column chart: Orders by month         |
+--------------------------------------+---------------------------------------+
| Bar: Orders by primary_payment_type  | Bar: AOV by primary_payment_type      |
+--------------------------------------+---------------------------------------+
```

## Page 2: Product & Seller

```
+--------------------------------------+---------------------------------------+
| Bar: Revenue by category (Top N 15)  | Table: category, Revenue, Category    |
|                                      | Share %, Rank by Category             |
+--------------------------------------+---------------------------------------+
| Line: Running Total Revenue by month | Bar: Revenue by seller (Top N 20)     |
+--------------------------------------+---------------------------------------+
```

## Page 3: Customer (RFM + Cohort)

```
+------------------------------------------------------------------------------+
| Cards: Customers, Repeat Purchase Rate                                       |
+--------------------------------------+---------------------------------------+
| Clustered bar: segment, customer and | Matrix: cohort_month x months_since   |
| revenue share (from rfm_segments.csv)| (from cohort_retention.csv),          |
|                                      | conditional formatting: blue scale    |
+--------------------------------------+---------------------------------------+
```

## Page 4: Delivery & Experience

```
+-----------+-----------+-----------+-----------+------------------------------+
| On-Time % | Late      | Avg       | Avg Review|                              |
|           | Orders    | Delivery  |           |                              |
+-----------+-----------+-----------+-----------+------------------------------+
| Column: Avg Review by delay_bucket   | Bar: On-Time % by customer state      |
| (late buckets coloured red)          | (sorted ascending, red below average) |
+--------------------------------------+---------------------------------------+
```
