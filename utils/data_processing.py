"""
Data processing utilities
Common data transformations and business logic
"""

import polars as pl
import streamlit as st
from typing import Dict, Any, Optional, List
from utils.database import execute_query, load_config
import logging

logger = logging.getLogger(__name__)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_customer_segments():
    """Get customer segmentation analysis"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH customer_metrics AS (
        SELECT 
            c.customer_unique_id,
            c.customer_state,
            c.customer_city,
            COUNT(DISTINCT oi.order_id) as total_orders,
            SUM(oi.price) as total_spent,
            AVG(oi.review_score) as avg_review_score,
            MIN(o.order_purchase_timestamp) as first_order_date,
            MAX(o.order_purchase_timestamp) as last_order_date,
            DATE_DIFF(DATE(MAX(o.order_purchase_timestamp)), DATE(MIN(o.order_purchase_timestamp)), DAY) as customer_lifespan_days
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c 
            ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
            ON oi.order_sk = o.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1, 2, 3
    ),
    rfm_analysis AS (
        SELECT *,
            -- Recency (based on relative timing within dataset)
            NTILE(5) OVER (ORDER BY last_order_date DESC) as recency_score,
            -- Frequency (based on order count)
            NTILE(5) OVER (ORDER BY total_orders ASC) as frequency_score,
            -- Monetary (based on total spent)
            NTILE(5) OVER (ORDER BY total_spent ASC) as monetary_score
        FROM customer_metrics
    ),
    customer_segments AS (
        SELECT *,
            CASE 
                -- High value customers (top monetary + frequency)
                WHEN monetary_score >= 4 AND frequency_score >= 4 THEN 'Champions'
                -- Good recent customers
                WHEN recency_score >= 4 AND monetary_score >= 3 THEN 'Loyal Customers'
                -- High spenders but less frequent
                WHEN monetary_score >= 4 AND frequency_score <= 2 THEN 'Big Spenders'
                -- Recent but low value
                WHEN recency_score >= 4 AND monetary_score <= 2 THEN 'New Customers'
                -- Multiple orders, medium value
                WHEN frequency_score >= 3 AND monetary_score >= 3 THEN 'Potential Loyalists'
                -- Low recent activity
                WHEN recency_score <= 2 AND frequency_score >= 2 THEN 'At Risk'
                -- Single purchase customers
                WHEN total_orders = 1 THEN 'One-Time Buyers'
                -- Default category
                ELSE 'Regular Customers'
            END as customer_segment
        FROM rfm_analysis
    )
    SELECT 
        customer_unique_id,
        customer_state,
        customer_city,
        total_orders,
        total_spent,
        avg_review_score,
        first_order_date,
        last_order_date,
        customer_segment,
        recency_score,
        frequency_score,
        monetary_score
    FROM customer_segments
    ORDER BY total_spent DESC
    """
    
    return execute_query(query, "Customer Segmentation")

@st.cache_data(ttl=1800)
def get_order_performance():
    """Get order performance metrics"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH order_metrics AS (
        SELECT 
            o.order_id,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,
            CASE 
                WHEN o.order_delivered_customer_date IS NOT NULL 
                AND o.order_delivered_customer_date != ''
                AND o.order_purchase_timestamp IS NOT NULL
                THEN DATE_DIFF(
                    DATE(CAST(o.order_delivered_customer_date AS TIMESTAMP)), 
                    DATE(o.order_purchase_timestamp), 
                    DAY
                )
                ELSE NULL
            END as actual_delivery_days,
            CASE 
                WHEN o.order_estimated_delivery_date IS NOT NULL
                AND o.order_purchase_timestamp IS NOT NULL
                THEN DATE_DIFF(
                    DATE(o.order_estimated_delivery_date), 
                    DATE(o.order_purchase_timestamp), 
                    DAY
                )
                ELSE NULL
            END as estimated_delivery_days,
            SUM(oi.price) as order_value,
            COUNT(oi.product_sk) as items_count,
            AVG(oi.review_score) as order_review_score
        FROM `{config['project_id']}.{config['dataset_id']}.dim_orders` o
        JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi 
            ON o.order_sk = oi.order_sk
        WHERE o.order_status IN ('delivered', 'shipped', 'processing')
        GROUP BY 1, 2, 3, 4, 5
    )
    SELECT *,
        CASE 
            WHEN actual_delivery_days IS NOT NULL AND estimated_delivery_days IS NOT NULL
            THEN (actual_delivery_days - estimated_delivery_days)
            ELSE NULL
        END as delivery_difference
    FROM order_metrics
    WHERE order_purchase_timestamp IS NOT NULL
    ORDER BY order_purchase_timestamp DESC
    """
    
    return execute_query(query, "Order Performance")

@st.cache_data(ttl=1800)
def get_review_insights():
    """Get review sentiment analysis"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH review_analysis AS (
        SELECT 
            r.review_id,
            oi.review_score,
            r.review_creation_date,
            r.review_answer_timestamp,
            o.order_purchase_timestamp,
            c.customer_state,
            p.product_category_name,
            oi.price,
            CASE 
                WHEN r.review_creation_date IS NOT NULL 
                AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_delivered_customer_date != ''
                THEN DATE_DIFF(
                    DATE(r.review_creation_date), 
                    DATE(CAST(o.order_delivered_customer_date AS TIMESTAMP)), 
                    DAY
                )
                ELSE NULL
            END as days_to_review
        FROM `{config['project_id']}.{config['dataset_id']}.dim_order_reviews` r
        JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi 
            ON r.review_sk = oi.review_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
            ON oi.order_sk = o.order_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c 
            ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_product` p 
            ON oi.product_sk = p.product_sk
        WHERE oi.review_score IS NOT NULL
    )
    SELECT * FROM review_analysis
    ORDER BY review_creation_date DESC
    """
    
    return execute_query(query, "Review Insights")

@st.cache_data(ttl=1800)
def get_geographic_summary():
    """Get geographic distribution summary"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH geo_summary AS (
        SELECT 
            c.customer_state,
            c.customer_city,
            g.geolocation_lat,
            g.geolocation_lng,
            COUNT(DISTINCT c.customer_unique_id) as customer_count,
            COUNT(DISTINCT oi.order_id) as order_count,
            SUM(oi.price) as total_revenue,
            AVG(oi.review_score) as avg_review_score
        FROM `{config['project_id']}.{config['dataset_id']}.dim_customer` c
        JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi 
            ON c.customer_sk = oi.customer_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_geolocation` g 
            ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
        GROUP BY 1, 2, 3, 4
        HAVING customer_count > 0
    )
    SELECT * FROM geo_summary
    ORDER BY total_revenue DESC
    """
    
    return execute_query(query, "Geographic Summary")

def calculate_business_metrics(df: pl.DataFrame) -> Dict[str, Any]:
    """Calculate key business metrics from order data"""
    if df.is_empty():
        return {}
    
    metrics = {}
    
    # Revenue metrics
    if 'price' in df.columns or 'total_spent' in df.columns:
        revenue_col = 'total_spent' if 'total_spent' in df.columns else 'price'
        metrics['Total Revenue'] = f"${df.select(pl.col(revenue_col).sum()).item():,.2f}"
        metrics['Average Order Value'] = f"${df.select(pl.col(revenue_col).mean()).item():,.2f}"
    
    # Customer metrics
    if 'customer_unique_id' in df.columns:
        metrics['Total Customers'] = f"{df.select(pl.col('customer_unique_id').n_unique()).item():,}"
    
    # Order metrics
    if 'order_id' in df.columns:
        metrics['Total Orders'] = f"{df.select(pl.col('order_id').n_unique()).item():,}"
    
    # Review metrics
    if 'review_score' in df.columns:
        metrics['Average Rating'] = f"{df.select(pl.col('review_score').mean()).item():.2f}/5"
    
    return metrics

def filter_data_by_date(df: pl.DataFrame, date_column: str,
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pl.DataFrame:
    """Filter dataframe by date range"""
    if df.is_empty() or date_column not in df.columns:
        return df
    
    filtered_df = df.clone()
    
    # Ensure datetime column
    if filtered_df.select(pl.col(date_column).dtype).item() != pl.Datetime:
        filtered_df = filtered_df.with_columns(
            pl.col(date_column).str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
        )
    
    # Apply filters
    if start_date:
        start_dt = pl.lit(start_date).str.strptime(pl.Datetime, "%Y-%m-%d")
        filtered_df = filtered_df.filter(pl.col(date_column) >= start_dt)
    
    if end_date:
        end_dt = pl.lit(end_date).str.strptime(pl.Datetime, "%Y-%m-%d")
        filtered_df = filtered_df.filter(pl.col(date_column) <= end_dt)
    
    return filtered_df

def get_top_n_analysis(df: pl.DataFrame, group_by: str, value_col: str,
                      n: int = 10, agg_func: str = 'sum') -> pl.DataFrame:
    """Get top N analysis for any grouping"""
    if df.is_empty() or group_by not in df.columns or value_col not in df.columns:
        return pl.DataFrame()
    
    agg_funcs = {
        'sum': pl.col(value_col).sum(),
        'mean': pl.col(value_col).mean(),
        'count': pl.col(value_col).count(),
        'max': pl.col(value_col).max(),
        'min': pl.col(value_col).min()
    }
    
    if agg_func not in agg_funcs:
        agg_func = 'sum'
    
    result = df.group_by(group_by).agg(
        agg_funcs[agg_func].alias(value_col)
    ).sort(value_col, descending=True).head(n)
    
    return result

def format_currency(amount: float) -> str:
    """Format currency values consistently"""
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.1f}K"
    else:
        return f"${amount:.2f}"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage values consistently"""
    return f"{value:.{decimals}f}%"
