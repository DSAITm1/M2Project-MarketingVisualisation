"""
Hybrid Optimized Order Analytics Page
BigQuery SQL handles 90% of processing, Polars for 10% final formatting only
Single optimized query per dashboard section
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database import load_config, execute_query
from utils.visualizations import (create_bar_chart, create_pie_chart, 
                                create_line_chart, display_chart, display_dataframe)

st.set_page_config(page_title="Order Analytics", page_icon="🛒", layout="wide")

@st.cache_data(ttl=1800)
def get_order_overview_data():
    """Single optimized query for all order analytics - BigQuery does 90% of processing"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH order_base AS (
        SELECT 
            o.order_id,
            o.order_status,
            DATE(o.order_purchase_timestamp) as order_date,
            EXTRACT(YEAR FROM o.order_purchase_timestamp) as order_year,
            EXTRACT(MONTH FROM o.order_purchase_timestamp) as order_month,
            EXTRACT(DAYOFWEEK FROM o.order_purchase_timestamp) as order_day_of_week,
            CASE 
                WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_customer_date != ''
                THEN DATE_DIFF(o.order_delivered_customer_date, o.order_purchase_timestamp, DAY)
                ELSE NULL
            END as delivery_days,
            c.customer_state,
            COUNT(oi.product_id) as items_count,
            ROUND(SUM(oi.price), 2) as order_value,
            ROUND(AVG(oi.price), 2) as avg_item_price,
            ROUND(SUM(oi.freight_value), 2) as total_freight
        FROM `{config['project_id']}.{config['dataset_id']}.dim_orders` o
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi ON o.order_sk = oi.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        WHERE o.order_purchase_timestamp IS NOT NULL 
        AND o.order_purchase_timestamp != ''
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
    ),
    order_metrics AS (
        SELECT *,
            -- Order size categorization in SQL
            CASE 
                WHEN order_value >= 500 THEN 'High Value'
                WHEN order_value >= 200 THEN 'Medium Value'
                WHEN order_value >= 50 THEN 'Low Value'
                ELSE 'Micro'
            END as order_category,
            -- Delivery performance categorization in SQL
            CASE 
                WHEN delivery_days IS NULL THEN 'Not Delivered'
                WHEN delivery_days <= 7 THEN 'Fast (≤7 days)'
                WHEN delivery_days <= 14 THEN 'Standard (8-14 days)'
                WHEN delivery_days <= 30 THEN 'Slow (15-30 days)'
                ELSE 'Very Slow (>30 days)'
            END as delivery_category
        FROM order_base
    )
    SELECT *
    FROM order_metrics
    ORDER BY order_date DESC
    """
    
    return execute_query(query, "Order Overview Data")

@st.cache_data(ttl=1800)
def get_order_metrics():
    """Single query for all order business metrics - BigQuery aggregates everything"""
    config = load_config()
    if not config:
        return {}
    
    query = f"""
    WITH order_summary AS (
        SELECT 
            COUNT(DISTINCT o.order_id) as total_orders,
            COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN o.order_id END) as delivered_orders,
            ROUND(SUM(oi.price), 2) as total_revenue,
            ROUND(AVG(oi.price), 2) as avg_order_value,
            CASE 
                WHEN COUNT(CASE WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_customer_date != '' THEN 1 END) > 0
                THEN ROUND(AVG(CASE WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_customer_date != '' 
                                   THEN DATE_DIFF(o.order_delivered_customer_date, o.order_purchase_timestamp, DAY) END), 1)
                ELSE NULL
            END as avg_delivery_days,
            COUNT(DISTINCT c.customer_unique_id) as unique_customers,
            COUNT(DISTINCT oi.product_id) as unique_products
        FROM `{config['project_id']}.{config['dataset_id']}.dim_orders` o
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi ON o.order_sk = oi.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        WHERE o.order_purchase_timestamp IS NOT NULL 
        AND o.order_purchase_timestamp != ''
    )
    SELECT *,
        ROUND((delivered_orders * 100.0 / total_orders), 1) as delivery_rate
    FROM order_summary
    """
    
    result = execute_query(query, "Order Metrics")
    if not result.is_empty():
        return result.to_dicts()[0]
    return {}

@st.cache_data(ttl=1800)
def get_order_trends():
    """Single query for order trends analysis - BigQuery handles time-series aggregations"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH daily_orders AS (
        SELECT 
            DATE(o.order_purchase_timestamp) as order_date,
            COUNT(DISTINCT o.order_id) as daily_orders,
            ROUND(SUM(oi.price), 2) as daily_revenue,
            ROUND(AVG(oi.price), 2) as avg_daily_order_value,
            COUNT(DISTINCT c.customer_unique_id) as daily_customers
        FROM `{config['project_id']}.{config['dataset_id']}.dim_orders` o
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi ON o.order_sk = oi.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        WHERE o.order_purchase_timestamp IS NOT NULL 
        AND o.order_purchase_timestamp != ''
        GROUP BY 1
    ),
    monthly_trends AS (
        SELECT 
            DATE_TRUNC(order_date, MONTH) as month,
            SUM(daily_orders) as monthly_orders,
            ROUND(SUM(daily_revenue), 2) as monthly_revenue,
            ROUND(AVG(avg_daily_order_value), 2) as avg_monthly_order_value,
            COUNT(DISTINCT order_date) as active_days
        FROM daily_orders
        GROUP BY 1
    )
    SELECT 
        month,
        monthly_orders,
        monthly_revenue,
        avg_monthly_order_value,
        active_days,
        -- Growth rate calculation in BigQuery
        ROUND((monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY month)) * 100.0 / 
              LAG(monthly_revenue) OVER (ORDER BY month), 2) as revenue_growth_rate
    FROM monthly_trends
    ORDER BY month
    """
    
    return execute_query(query, "Order Trends")

@st.cache_data(ttl=1800)
def get_delivery_performance():
    """Single query for delivery performance analysis - BigQuery handles all calculations"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH delivery_metrics AS (
        SELECT 
            o.order_status,
            c.customer_state,
            COUNT(*) as order_count,
            CASE 
                WHEN COUNT(CASE WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_customer_date != '' THEN 1 END) > 0
                THEN ROUND(AVG(CASE WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_customer_date != '' 
                                   THEN DATE_DIFF(o.order_delivered_customer_date, o.order_purchase_timestamp, DAY) END), 1)
                ELSE NULL
            END as avg_delivery_days,
            CASE 
                WHEN COUNT(CASE WHEN o.order_estimated_delivery_date IS NOT NULL AND o.order_estimated_delivery_date != '' THEN 1 END) > 0
                THEN ROUND(AVG(CASE WHEN o.order_estimated_delivery_date IS NOT NULL AND o.order_estimated_delivery_date != '' 
                                   THEN DATE_DIFF(o.order_estimated_delivery_date, o.order_purchase_timestamp, DAY) END), 1)
                ELSE NULL
            END as avg_estimated_days,
            COUNT(CASE WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_customer_date != '' 
                       AND o.order_estimated_delivery_date IS NOT NULL AND o.order_estimated_delivery_date != ''
                       AND o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 1 END) as on_time_deliveries,
            ROUND(SUM(oi.price), 2) as total_value
        FROM `{config['project_id']}.{config['dataset_id']}.dim_orders` o
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi ON o.order_sk = oi.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        WHERE o.order_purchase_timestamp IS NOT NULL 
        AND o.order_purchase_timestamp != ''
        GROUP BY 1, 2
    )
    SELECT *,
        ROUND((on_time_deliveries * 100.0 / order_count), 1) as on_time_rate
    FROM delivery_metrics
    ORDER BY total_value DESC
    """
    
    return execute_query(query, "Delivery Performance")

def format_currency_polars(df, column_name):
    """Polars-only formatting for currency - 10% final formatting"""
    if column_name in df.columns:
        return df.with_columns(
            pl.col(column_name).map_elements(lambda x: f"${x:,.2f}" if x is not None else "N/A", return_dtype=pl.Utf8).alias(column_name)
        )
    return df

def format_percentage_polars(df, column_name):
    """Polars-only formatting for percentages - 10% final formatting"""
    if column_name in df.columns:
        return df.with_columns(
            pl.col(column_name).map_elements(lambda x: f"{x:.1f}%" if x is not None else "N/A", return_dtype=pl.Utf8).alias(column_name)
        )
    return df

def main():
    """Hybrid optimized order analytics dashboard - BigQuery 90% + Polars 10%"""
    st.title("🛒 Order Analytics")
    st.markdown("**Order Trends and Performance Analysis - Hybrid Optimized**")
    
    # Load all data with single optimized queries (BigQuery handles 90% of processing)
    with st.spinner("🔄 Loading order analytics..."):
        order_data = get_order_overview_data()
        order_metrics = get_order_metrics()
        order_trends = get_order_trends()
        delivery_data = get_delivery_performance()
    
    if order_data.is_empty():
        st.error("❌ No order data available. Please check your data connection.")
        return
    
    # Key metrics - data already aggregated by BigQuery
    st.header("📊 Order Overview")
    
    if order_metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📦 Total Orders", 
                f"{order_metrics.get('total_orders', 0):,}"
            )
            
        with col2:
            st.metric(
                "💰 Total Revenue", 
                f"${order_metrics.get('total_revenue', 0):,.2f}"
            )
            
        with col3:
            st.metric(
                "🛒 Avg Order Value", 
                f"${order_metrics.get('avg_order_value', 0):.2f}"
            )
            
        with col4:
            st.metric(
                "🚚 Delivery Rate", 
                f"{order_metrics.get('delivery_rate', 0):.1f}%"
            )
    
    # Order Status Analysis - data pre-aggregated
    st.header("📋 Order Status Analysis")
    
    if not order_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Order Status Distribution")
            status_counts = order_data.group_by('order_status').len().sort('len', descending=True)
            fig = create_pie_chart(
                data=status_counts,
                values='len',
                names='order_status',
                title="Order Status Distribution"
            )
            display_chart(fig, key="order_status")
        
        with col2:
            st.subheader("Order Value Categories")
            category_counts = order_data.group_by('order_category').len().sort('len', descending=True)
            fig = create_bar_chart(
                data=category_counts,
                x='order_category',
                y='len',
                title="Orders by Value Category",
                labels={'order_category': 'Category', 'len': 'Count'}
            )
            display_chart(fig, key="order_categories")
    
    # Delivery Performance Analysis
    if not delivery_data.is_empty():
        st.header("🚚 Delivery Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Delivery Time by State")
            # Show top 10 states by volume
            top_delivery_states = delivery_data.filter(
                pl.col('order_status') == 'delivered'
            ).sort('order_count', descending=True).limit(10)
            
            fig = create_bar_chart(
                data=top_delivery_states,
                x='customer_state',
                y='avg_delivery_days',
                title="Average Delivery Days by State",
                labels={'customer_state': 'State', 'avg_delivery_days': 'Days'}
            )
            display_chart(fig, key="delivery_performance")
        
        with col2:
            st.subheader("On-Time Delivery Rate")
            # Filter delivered orders only
            delivery_performance = delivery_data.filter(
                pl.col('order_status') == 'delivered'
            ).sort('on_time_rate', descending=True).limit(10)
            
            fig = create_bar_chart(
                data=delivery_performance,
                x='customer_state',
                y='on_time_rate',
                title="On-Time Delivery Rate by State",
                labels={'customer_state': 'State', 'on_time_rate': 'On-Time Rate (%)'}
            )
            display_chart(fig, key="ontime_delivery")
    
    # Order Trends Analysis
    if not order_trends.is_empty():
        st.header("📈 Order Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Monthly Order Volume")
            fig = create_line_chart(
                data=order_trends,
                x='month',
                y='monthly_orders',
                title="Monthly Order Count Trend",
                labels={'month': 'Month', 'monthly_orders': 'Orders'}
            )
            display_chart(fig, key="monthly_orders")
        
        with col2:
            st.subheader("Monthly Revenue Trend")
            fig = create_line_chart(
                data=order_trends,
                x='month',
                y='monthly_revenue',
                title="Monthly Revenue Trend",
                labels={'month': 'Month', 'monthly_revenue': 'Revenue ($)'}
            )
            display_chart(fig, key="monthly_revenue")
    
    # Detailed order analysis table
    st.header("📋 Order Analysis Summary")
    
    if not order_data.is_empty():
        # Create business-focused view with Polars formatting (10% processing)
        order_summary = order_data.limit(50).select([
            'order_id',
            'order_status',
            'order_date',
            'customer_state',
            'items_count',
            'order_value',
            'delivery_days',
            'order_category'
        ]).with_columns([
            # Currency formatting (Polars - 10%)
            pl.col('order_value').map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.Utf8).alias('Order Value'),
            # Date formatting (Polars - 10%)
            pl.col('order_date').dt.strftime('%Y-%m-%d').alias('Order Date'),
            # Delivery days formatting (Polars - 10%)
            pl.col('delivery_days').map_elements(lambda x: f"{x} days" if x is not None else "Pending", return_dtype=pl.Utf8).alias('Delivery Time')
        ]).select([
            pl.col('order_id').alias('Order ID'),
            pl.col('order_status').alias('Status'),
            'Order Date',
            pl.col('customer_state').alias('State'),
            pl.col('items_count').alias('Items'),
            'Order Value',
            'Delivery Time',
            pl.col('order_category').alias('Category')
        ])
        
        display_dataframe(order_summary, "📊 Recent Orders Summary")
        
        # Summary insights
        col1, col2, col3 = st.columns(3)
        with col1:
            total_orders = order_data.height
            st.metric("📦 Total Orders", f"{total_orders:,}")
        
        with col2:
            avg_order_value = order_data['order_value'].mean()
            st.metric("💰 Avg Order Value", f"${avg_order_value:,.2f}")
        
        with col3:
            delivered_orders = order_data.filter(pl.col('order_status') == 'delivered').height
            delivery_rate = (delivered_orders / total_orders) * 100 if total_orders > 0 else 0
            st.metric("🚚 Delivery Success", f"{delivery_rate:.1f}%")

if __name__ == "__main__":
    main()
