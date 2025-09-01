# BigQuery Table Schemas - Production Data Architecture

- Generated: 2025-09-01T12:00:00 (Updated)
- Project: project-olist-470307
- Datasets: dbt_olist_dwh, dbt_olist_analytics
- Current Application Dataset: dbt_olist_dwh (Data Warehouse)
- Analytics Dataset: dbt_olist_analytics (Pre-computed metrics)

---

## Data Architecture Overview

### 1. dbt_olist_dwh (Data Warehouse)
- **Purpose**: Production data warehouse with star schema
- **Tables**: 9 tables (8 dimensions + 1 fact)
- **Use Case**: Current application queries (90% BigQuery processing)

### 2. dbt_olist_analytics (Analytics Layer)
- **Purpose**: Pre-computed optimized analytics tables
- **Tables**: 6 optimized analytics tables
- **Use Case**: Future optimization (eliminate complex SQL queries)

---

## Schema for project-olist-470307.dbt_olist_dwh.dim_customer

```text
- customer_sk (STRING, NULLABLE)
- customer_id (STRING, NULLABLE)
- customer_unique_id (STRING, NULLABLE)
- customer_zip_code_prefix (STRING, NULLABLE)
- customer_city (STRING, NULLABLE)
- customer_state (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_dwh.dim_date

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

## Schema for project-olist-470307.dbt_olist_dwh.dim_geolocation

```text
- geolocation_sk (STRING, NULLABLE)
- geolocation_zip_code_prefix (STRING, NULLABLE)
- geolocation_lat (FLOAT, NULLABLE)
- geolocation_lng (FLOAT, NULLABLE)
- geolocation_city (STRING, NULLABLE)
- geolocation_state (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_dwh.dim_order_reviews

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

## Schema for project-olist-470307.dbt_olist_dwh.dim_orders

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

## Schema for project-olist-470307.dbt_olist_dwh.dim_payment

```text
- payment_sk (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- payment_sequential (INTEGER, NULLABLE)
- payment_type (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_dwh.dim_product

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

## Schema for project-olist-470307.dbt_olist_dwh.dim_seller

```text
- seller_sk (STRING, NULLABLE)
- seller_id (STRING, NULLABLE)
- seller_zip_code_prefix (STRING, NULLABLE)
- seller_city (STRING, NULLABLE)
- seller_state (STRING, NULLABLE)
- insertion_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_dwh.fact_order_items

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

---

## Analytics Layer: project-olist-470307.dbt_olist_analytics

### Pre-computed Optimized Tables (6 tables)

## Schema for project-olist-470307.dbt_olist_analytics.customer_analytics_obt

```text
- customer_sk (STRING, NULLABLE)
- customer_id (STRING, NULLABLE)
- customer_city (STRING, NULLABLE)
- customer_state (STRING, NULLABLE)
- customer_zip_code_prefix (STRING, NULLABLE)
- total_orders (INTEGER, NULLABLE)
- total_spent (FLOAT, NULLABLE)
- total_freight_paid (FLOAT, NULLABLE)
- total_payments_made (FLOAT, NULLABLE)
- days_as_customer (INTEGER, NULLABLE)
- days_since_last_order (INTEGER, NULLABLE)
- first_order_date (DATE, NULLABLE)
- last_order_date (DATE, NULLABLE)
- avg_order_value (FLOAT, NULLABLE)
- annual_spending_rate (FLOAT, NULLABLE)
- annual_order_frequency (FLOAT, NULLABLE)
- predicted_annual_clv (FLOAT, NULLABLE)
- categories_purchased (INTEGER, NULLABLE)
- sellers_used (INTEGER, NULLABLE)
- avg_installments_used (FLOAT, NULLABLE)
- payment_methods_used (INTEGER, NULLABLE)
- category_diversity_ratio (FLOAT, NULLABLE)
- weekend_shopping_pct (FLOAT, NULLABLE)
- local_shopping_pct (FLOAT, NULLABLE)
- avg_review_score (FLOAT, NULLABLE)
- positive_reviews (INTEGER, NULLABLE)
- negative_reviews (INTEGER, NULLABLE)
- total_reviews_given (INTEGER, NULLABLE)
- satisfaction_rate_pct (FLOAT, NULLABLE)
- review_completion_rate_pct (FLOAT, NULLABLE)
- satisfaction_tier (STRING, NULLABLE)
- quarters_active (INTEGER, NULLABLE)
- months_active (INTEGER, NULLABLE)
- engagement_consistency (FLOAT, NULLABLE)
- purchase_frequency_tier (STRING, NULLABLE)
- customer_segment (STRING, NULLABLE)
- churn_risk_level (STRING, NULLABLE)
- geographic_region (STRING, NULLABLE)
- market_tier (STRING, NULLABLE)
- last_updated_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_analytics.geographic_analytics_obt

```text
- state_code (STRING, NULLABLE)
- total_cities (INTEGER, NULLABLE)
- geographic_region (STRING, NULLABLE)
- market_tier (STRING, NULLABLE)
- total_orders (INTEGER, NULLABLE)
- total_items_sold (INTEGER, NULLABLE)
- total_customers (INTEGER, NULLABLE)
- total_sellers (INTEGER, NULLABLE)
- total_products_sold (INTEGER, NULLABLE)
- total_categories_available (INTEGER, NULLABLE)
- total_revenue (FLOAT, NULLABLE)
- total_freight_revenue (FLOAT, NULLABLE)
- total_payment_received (FLOAT, NULLABLE)
- revenue_per_customer (FLOAT, NULLABLE)
- orders_per_customer (FLOAT, NULLABLE)
- average_order_value (FLOAT, NULLABLE)
- revenue_per_seller (FLOAT, NULLABLE)
- customers_per_seller (FLOAT, NULLABLE)
- daily_revenue_rate (FLOAT, NULLABLE)
- daily_order_rate (FLOAT, NULLABLE)
- market_development_tier (STRING, NULLABLE)
- market_maturity (STRING, NULLABLE)
- customers_per_city (FLOAT, NULLABLE)
- sellers_per_city (FLOAT, NULLABLE)
- revenue_per_city (FLOAT, NULLABLE)
- market_density (STRING, NULLABLE)
- avg_review_score (FLOAT, NULLABLE)
- customer_satisfaction_rate_pct (FLOAT, NULLABLE)
- avg_installments_used (FLOAT, NULLABLE)
- credit_card_usage_pct (FLOAT, NULLABLE)
- boleto_usage_pct (FLOAT, NULLABLE)
- payment_preference_profile (STRING, NULLABLE)
- local_orders (INTEGER, NULLABLE)
- cross_region_orders (INTEGER, NULLABLE)
- local_shipping_pct (FLOAT, NULLABLE)
- cross_region_shipping_pct (FLOAT, NULLABLE)
- logistics_profile (STRING, NULLABLE)
- weekend_orders (INTEGER, NULLABLE)
- weekend_activity_pct (FLOAT, NULLABLE)
- quarters_active (INTEGER, NULLABLE)
- months_active (INTEGER, NULLABLE)
- days_active (INTEGER, NULLABLE)
- first_order_date (DATE, NULLABLE)
- last_order_date (DATE, NULLABLE)
- market_activity_consistency (FLOAT, NULLABLE)
- seller_competition_level (STRING, NULLABLE)
- market_opportunity_index (FLOAT, NULLABLE)
- last_updated_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_analytics.delivery_analytics_obt

```text
- order_id (STRING, NULLABLE)
- order_item_id (INTEGER, NULLABLE)
- delivery_sk (STRING, NULLABLE)
- customer_sk (STRING, NULLABLE)
- seller_sk (STRING, NULLABLE)
- product_sk (STRING, NULLABLE)
- customer_city (STRING, NULLABLE)
- customer_state (STRING, NULLABLE)
- seller_city (STRING, NULLABLE)
- seller_state (STRING, NULLABLE)
- shipping_complexity (STRING, NULLABLE)
- order_date (DATE, NULLABLE)
- order_year (INTEGER, NULLABLE)
- order_quarter (INTEGER, NULLABLE)
- order_month (INTEGER, NULLABLE)
- total_items_in_order (INTEGER, NULLABLE)
- total_order_value (FLOAT, NULLABLE)
- product_category_english (STRING, NULLABLE)
- product_weight_category (STRING, NULLABLE)
- item_price (FLOAT, NULLABLE)
- freight_cost (FLOAT, NULLABLE)
- allocated_payment (FLOAT, NULLABLE)
- review_score (INTEGER, NULLABLE)
- satisfaction_level (STRING, NULLABLE)
- order_status (STRING, NULLABLE)
- flag_delivered (INTEGER, NULLABLE)
- flag_in_transit (INTEGER, NULLABLE)
- flag_canceled (INTEGER, NULLABLE)
- last_updated_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_analytics.payment_analytics_obt

```text
- payment_transaction_sk (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- order_item_id (INTEGER, NULLABLE)
- customer_sk (STRING, NULLABLE)
- customer_id (STRING, NULLABLE)
- product_sk (STRING, NULLABLE)
- seller_sk (STRING, NULLABLE)
- order_date (DATE, NULLABLE)
- order_year (INTEGER, NULLABLE)
- order_quarter (INTEGER, NULLABLE)
- order_month (INTEGER, NULLABLE)
- year_quarter (STRING, NULLABLE)
- year_month (STRING, NULLABLE)
- customer_city (STRING, NULLABLE)
- customer_state (STRING, NULLABLE)
- product_category_english (STRING, NULLABLE)
- product_weight_category (STRING, NULLABLE)
- payment_type (STRING, NULLABLE)
- payment_installments (INTEGER, NULLABLE)
- item_price (FLOAT, NULLABLE)
- allocated_payment (FLOAT, NULLABLE)
- freight_cost (FLOAT, NULLABLE)
- total_item_cost (FLOAT, NULLABLE)
- payment_per_installment (FLOAT, NULLABLE)
- payment_premium_pct (FLOAT, NULLABLE)
- payment_present_value (FLOAT, NULLABLE)
- purchase_value_category (STRING, NULLABLE)
- payment_risk_level (STRING, NULLABLE)
- credit_behavior_type (STRING, NULLABLE)
- installment_category (STRING, NULLABLE)
- is_credit_card (INTEGER, NULLABLE)
- is_boleto (INTEGER, NULLABLE)
- is_debit_card (INTEGER, NULLABLE)
- is_voucher (INTEGER, NULLABLE)
- affordability_index (INTEGER, NULLABLE)
- credit_utilization_level (STRING, NULLABLE)
- flag_high_installments (INTEGER, NULLABLE)
- flag_high_payment_premium (INTEGER, NULLABLE)
- flag_invalid_payment (INTEGER, NULLABLE)
- flag_invalid_installments (INTEGER, NULLABLE)
- review_score (INTEGER, NULLABLE)
- satisfaction_level (STRING, NULLABLE)
- payment_satisfaction_profile (STRING, NULLABLE)
- credit_card_usage_pct (FLOAT, NULLABLE)
- boleto_usage_pct (FLOAT, NULLABLE)
- debit_card_usage_pct (FLOAT, NULLABLE)
- voucher_usage_pct (FLOAT, NULLABLE)
- customer_avg_installments (FLOAT, NULLABLE)
- customer_max_installments (INTEGER, NULLABLE)
- customer_affordability_index (FLOAT, NULLABLE)
- customer_total_transactions (INTEGER, NULLABLE)
- customer_payment_profile (STRING, NULLABLE)
- customer_installment_behavior (STRING, NULLABLE)
- last_updated_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_analytics.revenue_analytics_obt

```text
- revenue_sk (STRING, NULLABLE)
- order_id (STRING, NULLABLE)
- order_item_id (INTEGER, NULLABLE)
- customer_sk (STRING, NULLABLE)
- product_sk (STRING, NULLABLE)
- seller_sk (STRING, NULLABLE)
- order_date (DATE, NULLABLE)
- order_year (INTEGER, NULLABLE)
- order_quarter (INTEGER, NULLABLE)
- order_month (INTEGER, NULLABLE)
- order_day_of_week (INTEGER, NULLABLE)
- is_weekend_order (BOOLEAN, NULLABLE)
- year_quarter (STRING, NULLABLE)
- year_month (STRING, NULLABLE)
- year_week (STRING, NULLABLE)
- customer_id (STRING, NULLABLE)
- customer_city (STRING, NULLABLE)
- customer_state (STRING, NULLABLE)
- customer_zip_code_prefix (STRING, NULLABLE)
- product_id (STRING, NULLABLE)
- product_category_portuguese (STRING, NULLABLE)
- product_category_english (STRING, NULLABLE)
- product_weight_g (INTEGER, NULLABLE)
- product_length_cm (INTEGER, NULLABLE)
- product_height_cm (INTEGER, NULLABLE)
- product_width_cm (INTEGER, NULLABLE)
- product_weight_category (STRING, NULLABLE)
- seller_id (STRING, NULLABLE)
- seller_city (STRING, NULLABLE)
- seller_state (STRING, NULLABLE)
- seller_zip_code_prefix (STRING, NULLABLE)
- payment_type (STRING, NULLABLE)
- payment_sequential (INTEGER, NULLABLE)
- payment_installments (INTEGER, NULLABLE)
- order_status (STRING, NULLABLE)
- review_score (INTEGER, NULLABLE)
- satisfaction_level (STRING, NULLABLE)
- item_price (FLOAT, NULLABLE)
- freight_cost (FLOAT, NULLABLE)
- allocated_payment (FLOAT, NULLABLE)
- total_item_cost (FLOAT, NULLABLE)
- payment_premium (FLOAT, NULLABLE)
- payment_markup_pct (FLOAT, NULLABLE)
- freight_to_price_ratio_pct (FLOAT, NULLABLE)
- price_per_installment (FLOAT, NULLABLE)
- payment_behavior_type (STRING, NULLABLE)
- shipping_complexity (STRING, NULLABLE)
- market_segment (STRING, NULLABLE)
- item_sequence_in_order (INTEGER, NULLABLE)
- total_items_in_order (INTEGER, NULLABLE)
- total_order_value (FLOAT, NULLABLE)
- customer_order_sequence (INTEGER, NULLABLE)
- seller_monthly_orders (INTEGER, NULLABLE)
- product_monthly_sales (INTEGER, NULLABLE)
- flag_invalid_price (INTEGER, NULLABLE)
- flag_invalid_payment (INTEGER, NULLABLE)
- flag_invalid_freight (INTEGER, NULLABLE)
- flag_invalid_installments (INTEGER, NULLABLE)
- last_updated_timestamp (DATETIME, NULLABLE)
```

## Schema for project-olist-470307.dbt_olist_analytics.seller_analytics_obt

```text
- seller_sk (STRING, NULLABLE)
- seller_id (STRING, NULLABLE)
- seller_city (STRING, NULLABLE)
- seller_state (STRING, NULLABLE)
- seller_zip_code_prefix (STRING, NULLABLE)
- total_orders (INTEGER, NULLABLE)
- total_items_sold (INTEGER, NULLABLE)
- total_revenue (FLOAT, NULLABLE)
- total_freight_revenue (FLOAT, NULLABLE)
- total_payment_received (FLOAT, NULLABLE)
- days_active (INTEGER, NULLABLE)
- days_since_last_sale (INTEGER, NULLABLE)
- first_sale_date (DATE, NULLABLE)
- last_sale_date (DATE, NULLABLE)
- revenue_per_order (FLOAT, NULLABLE)
- daily_revenue_rate (FLOAT, NULLABLE)
- daily_order_rate (FLOAT, NULLABLE)
- avg_sales_per_product (FLOAT, NULLABLE)
- product_diversity_per_order (FLOAT, NULLABLE)
- cross_state_sales_pct (FLOAT, NULLABLE)
- customer_repeat_rate (FLOAT, NULLABLE)
- unique_customers (INTEGER, NULLABLE)
- states_served (INTEGER, NULLABLE)
- cities_served (INTEGER, NULLABLE)
- cross_state_sales (INTEGER, NULLABLE)
- local_sales (INTEGER, NULLABLE)
- customer_acquisition_efficiency (FLOAT, NULLABLE)
- national_market_penetration_pct (FLOAT, NULLABLE)
- unique_products_sold (INTEGER, NULLABLE)
- categories_sold (INTEGER, NULLABLE)
- seller_category_focus (STRING, NULLABLE)
- avg_review_score (FLOAT, NULLABLE)
- positive_reviews (INTEGER, NULLABLE)
- negative_reviews (INTEGER, NULLABLE)
- total_reviews_received (INTEGER, NULLABLE)
- positive_review_rate_pct (FLOAT, NULLABLE)
- review_coverage_rate_pct (FLOAT, NULLABLE)
- quality_tier (STRING, NULLABLE)
- performance_tier (STRING, NULLABLE)
- activity_level (STRING, NULLABLE)
- business_maturity (STRING, NULLABLE)
- seller_segment (STRING, NULLABLE)
- avg_installments_offered (FLOAT, NULLABLE)
- payment_methods_accepted (INTEGER, NULLABLE)
- weekend_sales (INTEGER, NULLABLE)
- quarters_active (INTEGER, NULLABLE)
- months_active (INTEGER, NULLABLE)
- weekend_sales_pct (FLOAT, NULLABLE)
- operational_consistency (FLOAT, NULLABLE)
- seller_region (STRING, NULLABLE)
- growth_trend (STRING, NULLABLE)
- last_updated_timestamp (DATETIME, NULLABLE)
```

---

## Architecture Recommendations

### Current Setup (dbt_olist_dwh)
- ✅ **Production Ready**: Clean star schema design
- ✅ **Application Compatible**: Current dashboard works perfectly
- ✅ **Performance**: Good with BigQuery optimization
- ✅ **Maintainability**: Clear dimensional model

### Future Optimization (dbt_olist_analytics)
- 🚀 **Pre-computed Metrics**: Analytics tables have 50-80+ calculated fields each
- 🚀 **Query Simplification**: Could reduce complex SQL to simple SELECT statements
- 🚀 **Performance Boost**: No aggregation needed at query time
- ⚠️ **Data Freshness**: Need to verify update frequency
- ⚠️ **Storage Cost**: Additional storage for pre-computed data

### Migration Strategy
1. **Phase 1**: Keep current `dbt_olist_dwh` setup (✅ Working)
2. **Phase 2**: Evaluate analytics tables data quality and freshness
3. **Phase 3**: Migrate to analytics tables if they provide significant performance benefits
4. **Phase 4**: Update application code to use simplified queries
