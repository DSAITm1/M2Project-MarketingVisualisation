# BigQuery Table Schemas

- Generated: 2025-08-31T19:10:56
- Project: project-olist-470307
- Dataset: dbt_olist_stg
- Tables: dim_customer, dim_date, dim_geolocation, dim_order_reviews, dim_orders, dim_payment, dim_product, dim_seller, fact_order_items

---

## Schema for project-olist-470307.dbt_olist_stg.dim_customer

```text
- customer_sk (STRING, NULLABLE)
- customer_id (STRING, NULLABLE)
- customer_unique_id (STRING, NULLABLE)
- customer_zip_code_prefix (STRING, NULLABLE)
- customer_city (STRING, NULLABLE)
- customer_state (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_date

```text
- date_sk (INTEGER, NULLABLE)
- date_value (DATE, NULLABLE)
- year (INTEGER, NULLABLE)
- quarter (INTEGER, NULLABLE)
- month (INTEGER, NULLABLE)
- day_of_month (INTEGER, NULLABLE)
- day_of_week (INTEGER, NULLABLE)
- is_weekend (BOOLEAN, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_geolocation

```text
- geolocation_sk (STRING, NULLABLE)
- geolocation_zip_code_prefix (STRING, NULLABLE)
- geolocation_lat (FLOAT, NULLABLE)
- geolocation_lng (FLOAT, NULLABLE)
- geolocation_city (STRING, NULLABLE)
- geolocation_state (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_order_reviews

```text
- review_sk (STRING, NULLABLE)
- review_id (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- review_comment_title (STRING, NULLABLE)
- review_comment_message (STRING, NULLABLE)
- review_creation_date (TIMESTAMP, NULLABLE)
- review_answer_timestamp (TIMESTAMP, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_orders

```text
- order_sk (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- order_status (STRING, NULLABLE)
- order_purchase_timestamp (TIMESTAMP, NULLABLE)
- order_approved_at (STRING, NULLABLE)
- order_delivered_carrier_date (STRING, NULLABLE)
- order_delivered_customer_date (STRING, NULLABLE)
- order_estimated_delivery_date (TIMESTAMP, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_payment

```text
- payment_sk (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- payment_sequential (INTEGER, NULLABLE)
- payment_type (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_product

```text
- product_sk (STRING, NULLABLE)
- product_id (STRING, NULLABLE)
- product_category_name (STRING, NULLABLE)
- product_name_length (INTEGER, NULLABLE)
- product_description_length (INTEGER, NULLABLE)
- product_photos_qty (INTEGER, NULLABLE)
- product_weight_g (INTEGER, NULLABLE)
- product_length_cm (INTEGER, NULLABLE)
- product_height_cm (INTEGER, NULLABLE)
- product_width_cm (INTEGER, NULLABLE)
- product_category_name_english (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.dim_seller

```text
- seller_sk (STRING, NULLABLE)
- seller_id (STRING, NULLABLE)
- seller_zip_code_prefix (STRING, NULLABLE)
- seller_city (STRING, NULLABLE)
- seller_state (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_stg.fact_order_items

```text
- order_item_sk (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- order_item_id (INTEGER, NULLABLE)
- order_sk (STRING, NULLABLE)
- customer_sk (STRING, NULLABLE)
- product_sk (STRING, NULLABLE)
- seller_sk (STRING, NULLABLE)
- payment_sk (STRING, NULLABLE)
- review_sk (STRING, NULLABLE)
- order_date_sk (INTEGER, NULLABLE)
- shipping_limit_date_sk (INTEGER, NULLABLE)
- customer_geography_sk (STRING, NULLABLE)
- seller_geography_sk (STRING, NULLABLE)
- price (FLOAT, NULLABLE)
- freight_value (FLOAT, NULLABLE)
- payment_value (FLOAT, NULLABLE)
- payment_installments (INTEGER, NULLABLE)
- review_score (INTEGER, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```
