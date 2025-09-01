# Marketing Opportunity Report (3–6 Months)

Data source: project `project-olist-470307`, dataset `dbt_olist_dwh` (tables: dim_customer, dim_geolocation, dim_orders, dim_order_reviews, dim_payment, dim_product, dim_seller, fact_order_items)

This report outlines five high-impact business questions and actionable recommendations that can be executed in 3–6 months, leveraging the current BigQuery schema.

---

## 1) How do we convert One‑Time Buyers into Repeat Customers?

Why it matters: Repeat customers drive higher LTV and lower CAC. Your model includes order history and timestamps to identify one-time vs. repeat behavior.

Key data:
- fact_order_items (order_id, customer_sk, price, order_date_sk)
- dim_orders (order_status, order_purchase_timestamp)
- dim_customer (customer_unique_id, state/city)

Quick-win actions (3–6 months):
- Post‑purchase lifecycle: Send a 7/21/45‑day sequence with personalized product recommendations and a small voucher for the 2nd order.
- Cross‑sell bundles: Recommend complementary products based on last purchase category.
- Free shipping threshold: Offer limited‑time free shipping on the second order.

KPIs to monitor:
- Repeat purchase rate (RPR), time‑to‑second order, second‑order conversion rate, incremental revenue.

Example query sketch:
```sql
-- Identify one-time vs repeat customers and time-to-second order
WITH orders AS (
  SELECT c.customer_unique_id, o.order_id, o.order_purchase_timestamp
  FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
  JOIN `project-olist-470307.dbt_olist_dwh.dim_orders` o ON oi.order_sk = o.order_sk
  JOIN `project-olist-470307.dbt_olist_dwh.dim_customer` c ON oi.customer_sk = c.customer_sk
  WHERE o.order_status = 'delivered'
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY order_purchase_timestamp) rn
  FROM orders
)
SELECT customer_unique_id,
  COUNTIF(rn = 1) AS first_orders,
  COUNTIF(rn > 1) AS repeat_orders
FROM ranked
GROUP BY customer_unique_id;
```

---

## 2) Which Product Categories have high revenue but low review scores?

Why it matters: Low ratings depress conversion. Fixing a few problematic categories can lift revenue quickly.

Key data:
- fact_order_items (price, review_score, product_sk)
- dim_product (product_category_name / english)
- dim_order_reviews (review text/timestamps)

Quick-win actions (3–6 months):
- Content fixes: Improve titles/specs/photos for low‑rating, high‑revenue categories.
- Quality sweeps: Work with top sellers in those categories to address common defects/packaging.
- Review prompts: Trigger post‑delivery review requests with incentives; escalate low scores to CS.

KPIs to monitor:
- Category conversion rate, average review score, return/refund rate (if available), revenue lift by category.

Example query sketch:
```sql
SELECT p.product_category_name_english AS category,
       COUNT(*) AS items,
       SUM(oi.price) AS revenue,
       AVG(oi.review_score) AS avg_review
FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
JOIN `project-olist-470307.dbt_olist_dwh.dim_product` p ON oi.product_sk = p.product_sk
GROUP BY category
HAVING items > 100
ORDER BY revenue DESC;
```

---

## 3) Where are under‑penetrated geographies (high customers, low revenue per customer)?

Why it matters: Localized offers and shipping incentives can quickly unlock growth.

Key data:
- dim_customer (state, city, unique_id)
- dim_geolocation (lat/lng for mapping)
- fact_order_items (price by order/customer)

Quick-win actions (3–6 months):
- Geo‑targeted campaigns: Run state/city‑level promos where revenue/customer is below median.
- Shipping incentives: Test free shipping or lower freight in high‑friction locales.
- Localized merchandising: Feature top‑rated products popular in similar regions.

KPIs to monitor:
- Revenue per customer by state/city, order frequency, freight share of basket, campaign ROAS.

Example query sketch:
```sql
WITH cust_spend AS (
  SELECT c.customer_state, c.customer_city, c.customer_unique_id,
         SUM(oi.price) AS total_spent, COUNT(DISTINCT oi.order_id) AS orders
  FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
  JOIN `project-olist-470307.dbt_olist_dwh.dim_customer` c ON oi.customer_sk = c.customer_sk
  GROUP BY 1,2,3
)
SELECT customer_state, customer_city,
       COUNT(DISTINCT customer_unique_id) AS customers,
       SUM(total_spent) AS revenue,
       SAFE_DIVIDE(SUM(total_spent), COUNT(DISTINCT customer_unique_id)) AS revenue_per_customer
FROM cust_spend
GROUP BY 1,2
ORDER BY revenue_per_customer ASC;
```

---

## 4) Do delivery timelines impact review scores and repeat orders?

Why it matters: Late deliveries hurt ratings and repeat intent. Tightening SLAs and expectation‑setting can improve NPS fast.

Key data:
- dim_orders (purchase/approved/delivered/estimated timestamps, status)
- fact_order_items (review_score)
- dim_order_reviews (review timestamps)

Quick-win actions (3–6 months):
- ETA transparency: Show realistic delivery windows for SKUs/regions with chronic delays.
- Proactive comms: Trigger notifications when estimated vs actual gap exceeds threshold.
- Carrier/seller routing: Shift volume away from underperforming carriers/sellers for affected lanes.

KPIs to monitor:
- On‑time delivery rate, average delay days, review score distribution, repeat purchase rate after delayed deliveries.

Example query sketch:
```sql
WITH delivery AS (
  SELECT o.order_id,
         o.order_purchase_timestamp,
         o.order_delivered_customer_date,
         o.order_estimated_delivery_date,
         TIMESTAMP_DIFF(o.order_delivered_customer_date, o.order_purchase_timestamp, DAY) AS actual_days,
         TIMESTAMP_DIFF(o.order_estimated_delivery_date, o.order_purchase_timestamp, DAY) AS est_days
  FROM `project-olist-470307.dbt_olist_dwh.dim_orders` o
  WHERE o.order_delivered_customer_date IS NOT NULL
), scored AS (
  SELECT d.order_id,
         (actual_days - est_days) AS delay_days,
         AVG(oi.review_score) AS avg_review
  FROM delivery d
  JOIN `project-olist-470307.dbt_olist_dwh.fact_order_items` oi ON oi.order_id = d.order_id
  GROUP BY 1,2
)
SELECT * FROM scored ORDER BY delay_days DESC;
```

---

## 5) Which payment methods drive higher basket sizes or conversions?

Why it matters: Promoting the right payment option can quickly lift AOV/conversion.

Key data:
- dim_payment (payment_type, payment_sequential)
- fact_order_items (price, payment_value, installments)
- dim_orders (status/purchase time)

Quick-win actions (3–6 months):
- Promote top‑performing payment methods at checkout (badges/priority ordering).
- Offer limited‑time incentives for methods with higher approval and AOV.
- Reduce friction: Default to last used method for returning customers.

KPIs to monitor:
- AOV by payment method, approval rate (if available), conversion rate, refund rate.

Example query sketch:
```sql
SELECT p.payment_type,
       COUNT(DISTINCT oi.order_id) AS orders,
       SUM(oi.price) AS revenue,
       AVG(oi.price) AS avg_order_value
FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
JOIN `project-olist-470307.dbt_olist_dwh.dim_payment` p USING (payment_sk)
GROUP BY p.payment_type
ORDER BY revenue DESC;
```

---

## Execution Plan Summary (3–6 Months)
- Month 1: Build baseline dashboards for RPR, geo revenue per customer, delivery delay vs rating, AOV by payment.
- Month 2–3: Launch lifecycle journeys, category fixes, geo‑targeted offers, ETA transparency. A/B test incentives.
- Month 4–6: Scale winners; shift carrier/seller mix; institutionalize content standards for low‑rating categories.

Deliverables: Weekly KPI tracking, A/B test logs, and a roll‑up of incremental revenue and margin impact.
