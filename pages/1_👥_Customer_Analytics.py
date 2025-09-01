"""
Hybrid Optimized Customer Analytics Page
BigQuery SQL handles 90% of processing, Polars for 10% final formatting only
Single optimized query per dashboard section
"""

import streamlit as st
import polars as pl
import plotly.express as px
import sys
import os

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database import load_config, execute_query
from utils.visualizations import (create_bar_chart, create_pie_chart, 
                                display_chart, display_dataframe)

st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide")

@st.cache_data(ttl=1800)
def get_customer_overview_data():
    """Single optimized query for all customer analytics - BigQuery does 90% of processing"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH customer_base AS (
        SELECT 
            c.customer_unique_id,
            c.customer_state,
            COUNT(DISTINCT oi.order_id) as total_orders,
            ROUND(SUM(oi.price), 2) as total_spent,
            ROUND(AVG(oi.price), 2) as avg_order_value,
            ROUND(AVG(r.review_score), 1) as avg_review_score,
            MIN(o.order_purchase_timestamp) as first_order_date,
            MAX(o.order_purchase_timestamp) as last_order_date,
            DATE_DIFF(DATE(MAX(o.order_purchase_timestamp)), DATE(MIN(o.order_purchase_timestamp)), DAY) as customer_lifespan_days
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_reviews` r ON oi.order_sk = r.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1, 2
    ),
    segmented_customers AS (
        SELECT *,
            -- Customer segmentation logic in SQL
            CASE 
                WHEN total_spent >= 1000 AND total_orders >= 5 THEN 'VIP'
                WHEN total_spent >= 500 AND total_orders >= 3 THEN 'High Value'
                WHEN total_spent >= 200 AND total_orders >= 2 THEN 'Regular'
                WHEN total_spent >= 50 THEN 'Low Value'
                ELSE 'One-time'
            END as customer_segment,
            -- Monthly CLV calculation in SQL
            CASE 
                WHEN customer_lifespan_days > 0 
                THEN ROUND(total_spent / (customer_lifespan_days / 30.0), 2)
                ELSE total_spent 
            END as monthly_clv
        FROM customer_base
    )
    SELECT *,
        -- State ranking for geographic insights
        ROW_NUMBER() OVER (PARTITION BY customer_state ORDER BY total_spent DESC) as state_rank
    FROM segmented_customers
    ORDER BY total_spent DESC
    """
    
    return execute_query(query, "Customer Overview Data")

@st.cache_data(ttl=1800)
def get_business_metrics():
    """Single query for all key business metrics - BigQuery aggregates everything"""
    config = load_config()
    if not config:
        return {}
    
    query = f"""
    WITH customer_metrics AS (
        SELECT 
            COUNT(DISTINCT c.customer_unique_id) as total_customers,
            COUNT(DISTINCT c.customer_state) as total_states,
            ROUND(AVG(customer_data.total_spent), 2) as avg_customer_value,
            ROUND(AVG(customer_data.avg_order_value), 2) as avg_order_value,
            ROUND(AVG(customer_data.avg_review_score), 2) as avg_rating,
            COUNT(CASE WHEN customer_data.total_orders > 1 THEN 1 END) as repeat_customers,
            ROUND(SUM(customer_data.total_spent), 2) as total_revenue
        FROM (
            SELECT 
                c.customer_unique_id,
                c.customer_state,
                COUNT(DISTINCT oi.order_id) as total_orders,
                SUM(oi.price) as total_spent,
                AVG(oi.price) as avg_order_value,
                AVG(r.review_score) as avg_review_score
            FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
            JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
            JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
            LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_reviews` r ON oi.order_sk = r.order_sk
            WHERE o.order_status = 'delivered'
            GROUP BY 1, 2
        ) customer_data
        CROSS JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c
        WHERE c.customer_unique_id IS NOT NULL
    )
    SELECT 
        total_customers,
        total_states,
        avg_customer_value,
        avg_order_value,
        avg_rating,
        repeat_customers,
        total_revenue,
        ROUND((repeat_customers * 100.0 / total_customers), 1) as repeat_rate
    FROM customer_metrics
    """
    
    result = execute_query(query, "Business Metrics")
    if not result.is_empty():
        return result.to_dicts()[0]
    return {}

@st.cache_data(ttl=1800)
def get_segment_analysis():
    """Single query for customer segment analysis - all aggregations in BigQuery"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH customer_segments AS (
        SELECT 
            c.customer_unique_id,
            c.customer_state,
            COUNT(DISTINCT oi.order_id) as total_orders,
            SUM(oi.price) as total_spent,
            AVG(oi.price) as avg_order_value,
            AVG(r.review_score) as avg_review_score,
            CASE 
                WHEN SUM(oi.price) >= 1000 AND COUNT(DISTINCT oi.order_id) >= 5 THEN 'VIP'
                WHEN SUM(oi.price) >= 500 AND COUNT(DISTINCT oi.order_id) >= 3 THEN 'High Value'
                WHEN SUM(oi.price) >= 200 AND COUNT(DISTINCT oi.order_id) >= 2 THEN 'Regular'
                WHEN SUM(oi.price) >= 50 THEN 'Low Value'
                ELSE 'One-time'
            END as customer_segment
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_reviews` r ON oi.order_sk = r.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1, 2
    )
    SELECT 
        customer_segment,
        COUNT(*) as customer_count,
        ROUND(SUM(total_spent), 2) as segment_revenue,
        ROUND(AVG(total_spent), 2) as avg_customer_value,
        ROUND(AVG(avg_order_value), 2) as avg_order_value,
        ROUND(AVG(total_orders), 1) as avg_orders_per_customer
    FROM customer_segments
    GROUP BY customer_segment
    ORDER BY segment_revenue DESC
    """
    
    return execute_query(query, "Segment Analysis")

@st.cache_data(ttl=1800)
def get_geographic_analysis():
    """Single query for geographic analysis - BigQuery handles all aggregations"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH state_metrics AS (
        SELECT 
            c.customer_state,
            COUNT(DISTINCT c.customer_unique_id) as customer_count,
            COUNT(DISTINCT oi.order_id) as total_orders,
            ROUND(SUM(oi.price), 2) as total_revenue,
            ROUND(AVG(oi.price), 2) as avg_order_value,
            ROUND(AVG(r.review_score), 2) as avg_rating
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        LEFT JOIN `{config['project_id']}.{config['dataset_id']}.dim_reviews` r ON oi.order_sk = r.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
    )
    SELECT *,
        ROUND((total_revenue / customer_count), 2) as revenue_per_customer,
        ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as revenue_rank
    FROM state_metrics
    ORDER BY total_revenue DESC
    """
    
    return execute_query(query, "Geographic Analysis")

@st.cache_data(ttl=1800)
def get_customer_cohort_analysis():
    """Optimized cohort analysis - BigQuery handles all date calculations and aggregations"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH first_orders AS (
        SELECT 
            c.customer_unique_id,
            DATE(DATE_TRUNC(MIN(o.order_purchase_timestamp), MONTH)) as cohort_month
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1
    ),
    cohort_data AS (
        SELECT 
            fo.cohort_month,
            DATE(DATE_TRUNC(o.order_purchase_timestamp, MONTH)) as order_month,
            COUNT(DISTINCT c.customer_unique_id) as customers,
            DATE_DIFF(DATE(DATE_TRUNC(o.order_purchase_timestamp, MONTH)), fo.cohort_month, MONTH) as period_number
        FROM first_orders fo
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON fo.customer_unique_id = c.customer_unique_id
        JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi ON c.customer_sk = oi.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1, 2, 4
    ),
    cohort_summary AS (
        SELECT 
            cohort_month,
            period_number,
            customers,
            -- Calculate retention rates directly in BigQuery
            ROUND(customers * 100.0 / FIRST_VALUE(customers) OVER (
                PARTITION BY cohort_month 
                ORDER BY period_number 
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ), 2) as retention_rate
        FROM cohort_data
        WHERE period_number <= 12  -- Limit to 12 months for performance
    )
    SELECT *
    FROM cohort_summary
    ORDER BY cohort_month, period_number
    """
    
    return execute_query(query, "Customer Cohort Analysis")

@st.cache_data(ttl=1800)
def get_clv_distribution():
    """Customer Lifetime Value distribution - BigQuery calculates CLV segments"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH customer_clv AS (
        SELECT 
            c.customer_unique_id,
            c.customer_state,
            COUNT(DISTINCT oi.order_id) as total_orders,
            ROUND(SUM(oi.price), 2) as total_spent,
            ROUND(AVG(oi.price), 2) as avg_order_value,
            DATE_DIFF(DATE(MAX(o.order_purchase_timestamp)), DATE(MIN(o.order_purchase_timestamp)), DAY) as customer_lifespan_days,
            -- CLV segmentation in BigQuery
            CASE 
                WHEN SUM(oi.price) <= 100 THEN '$0-100'
                WHEN SUM(oi.price) <= 500 THEN '$100-500'
                WHEN SUM(oi.price) <= 1000 THEN '$500-1K'
                WHEN SUM(oi.price) <= 2000 THEN '$1K-2K'
                ELSE '$2K+'
            END as clv_segment
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1, 2
    )
    SELECT 
        clv_segment,
        COUNT(*) as customer_count,
        ROUND(AVG(total_spent), 2) as avg_clv,
        ROUND(AVG(total_orders), 1) as avg_orders,
        ROUND(AVG(avg_order_value), 2) as avg_order_value
    FROM customer_clv
    GROUP BY clv_segment
    ORDER BY 
        CASE clv_segment
            WHEN '$0-100' THEN 1
            WHEN '$100-500' THEN 2 
            WHEN '$500-1K' THEN 3
            WHEN '$1K-2K' THEN 4
            WHEN '$2K+' THEN 5
        END
    """
    
    return execute_query(query, "CLV Distribution")

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
    """Hybrid optimized customer analytics dashboard - BigQuery 90% + Polars 10%"""
    st.title("👥 Customer Analytics")
    st.markdown("**Advanced Customer Insights & Segmentation - Hybrid Optimized**")
    
    # Load all data with single optimized queries (BigQuery handles 90% of processing)
    with st.spinner("🔄 Loading customer analytics..."):
        customer_data = get_customer_overview_data()
        business_metrics = get_business_metrics()
        segment_data = get_segment_analysis()
        geo_data = get_geographic_analysis()
        cohort_data = get_customer_cohort_analysis()
        clv_data = get_clv_distribution()
    
    if customer_data.is_empty():
        st.error("❌ No customer data available. Please check your data connection.")
        return
    
    # Key metrics - data already aggregated by BigQuery
    st.header("📊 Customer Overview")
    
    if business_metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "👥 Total Customers", 
                f"{business_metrics.get('total_customers', 0):,}"
            )
            
        with col2:
            st.metric(
                "💰 Avg Customer Value", 
                f"${business_metrics.get('avg_customer_value', 0):,.2f}"
            )
            
        with col3:
            st.metric(
                "🔄 Repeat Rate", 
                f"{business_metrics.get('repeat_rate', 0):.1f}%"
            )
            
        with col4:
            st.metric(
                "⭐ Avg Rating", 
                f"{business_metrics.get('avg_rating', 0):.1f}/5"
            )
    
    # Customer segmentation analysis - data pre-aggregated
    st.header("🎯 Customer Segmentation")
    
    if not segment_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Segment Distribution")
            fig = create_pie_chart(
                data=segment_data,
                values='customer_count',
                names='customer_segment',
                title="Customer Segments"
            )
            display_chart(fig, key="customer_segments")
        
        with col2:
            st.subheader("Revenue by Segment")
            # Polars formatting only for currency display (10% processing)
            segment_display = format_currency_polars(segment_data.clone(), 'segment_revenue')
            
            fig = create_bar_chart(
                data=segment_data,  # Use original data for chart
                x='customer_segment',
                y='segment_revenue',
                title="Revenue by Customer Segment",
                labels={'customer_segment': 'Segment', 'segment_revenue': 'Revenue ($)'}
            )
            display_chart(fig, key="segment_revenue")
    
    # Geographic analysis - data pre-aggregated by BigQuery
    st.header("🗺️ Geographic Distribution")
    
    if not geo_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 10 States by Customer Count")
            top_states_customers = geo_data.limit(10)
            fig = create_bar_chart(
                data=top_states_customers,
                x='customer_state',
                y='customer_count',
                title="Top 10 States by Customer Count",
                labels={'customer_state': 'State', 'customer_count': 'Customers'}
            )
            display_chart(fig, key="state_distribution")
        
        with col2:
            st.subheader("Top 10 States by Revenue") 
            top_states_revenue = geo_data.limit(10)
            fig = create_bar_chart(
                data=top_states_revenue,
                x='customer_state',
                y='total_revenue',
                title="Top 10 States by Revenue",
                labels={'customer_state': 'State', 'total_revenue': 'Revenue ($)'}
            )
            display_chart(fig, key="state_revenue")
    
    # Customer Lifetime Value Analysis - data pre-segmented by BigQuery
    if not clv_data.is_empty():
        st.header("💰 Customer Lifetime Value")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("CLV Distribution")
            fig = create_pie_chart(
                data=clv_data,
                values='customer_count',
                names='clv_segment',
                title="Customer Lifetime Value Distribution"
            )
            display_chart(fig, key="clv_distribution")
        
        with col2:
            st.subheader("CLV Segment Analysis")
            # Polars formatting for currency display (10% processing)
            clv_display = format_currency_polars(clv_data.clone(), 'avg_clv')
            clv_display = format_currency_polars(clv_display, 'avg_order_value')
            
            display_dataframe(clv_display, "CLV Segment Metrics")
    
    # Cohort Analysis - retention rates pre-calculated by BigQuery
    if not cohort_data.is_empty():
        st.header("📈 Customer Retention Cohort Analysis")
        
        # Get retention summary using Polars for final aggregation (10% processing)
        retention_summary = cohort_data.filter(
            pl.col('period_number').is_in([0, 1, 3, 6])
        ).group_by('cohort_month').agg([
            pl.col('retention_rate').filter(pl.col('period_number') == 0).first().alias('month_0'),
            pl.col('retention_rate').filter(pl.col('period_number') == 1).first().alias('month_1'),
            pl.col('retention_rate').filter(pl.col('period_number') == 3).first().alias('month_3'),
            pl.col('retention_rate').filter(pl.col('period_number') == 6).first().alias('month_6')
        ]).sort('cohort_month')
        
        if retention_summary.height > 0:
            st.subheader("🎯 Key Retention Metrics")
            
            # Average retention rates
            avg_1m = retention_summary['month_1'].mean()
            avg_3m = retention_summary['month_3'].mean()  
            avg_6m = retention_summary['month_6'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("1-Month Retention", f"{avg_1m:.1f}%")
            with col2:
                st.metric("3-Month Retention", f"{avg_3m:.1f}%")
            with col3:
                st.metric("6-Month Retention", f"{avg_6m:.1f}%")
            
            # Cohort heatmap visualization
            st.subheader("Retention Rate Heatmap")
            cohort_pivot = cohort_data.pivot(
                index='cohort_month',
                on='period_number',
                values='retention_rate',
                aggregate_function='first'
            ).fill_null(0)
            
            if not cohort_pivot.is_empty():
                # Create heatmap using plotly
                import plotly.graph_objects as go
                
                # Convert to lists for plotly (minimal Polars processing)
                cohort_months = cohort_pivot.select('cohort_month').to_series().to_list()
                period_columns = [col for col in cohort_pivot.columns if col != 'cohort_month']
                
                z_data = []
                for _, row in cohort_pivot.iter_rows(named=True):
                    z_data.append([row.get(col, 0) for col in period_columns])
                
                fig = go.Figure(data=go.Heatmap(
                    z=z_data,
                    x=period_columns,
                    y=[str(month) for month in cohort_months],
                    colorscale='RdYlBu_r',
                    text=[[f"{val:.1f}%" for val in row] for row in z_data],
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hovertemplate='Month %{x}<br>Cohort: %{y}<br>Retention: %{z:.1f}%<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Customer Retention Heatmap (%)",
                    xaxis_title="Period (Months)",
                    yaxis_title="Cohort Month",
                    height=400
                )
                
                display_chart(fig, key="retention_heatmap")
    
    # Customer summary table - minimal Polars formatting (10% processing)
    st.header("📋 Top Customer Analysis")
    
    if not customer_data.is_empty():
        # Select top customers and format for display
        top_customers = customer_data.limit(20).select([
            'customer_unique_id',
            'customer_segment', 
            'customer_state',
            'total_orders',
            'total_spent',
            'avg_review_score'
        ]).with_columns([
            # Privacy-friendly customer ID (Polars formatting - 10%)
            pl.col('customer_unique_id').str.slice(0, 8).str.concat(pl.lit('...')).alias('Customer ID'),
            # Currency formatting (Polars formatting - 10%)
            pl.col('total_spent').map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.Utf8).alias('Total Spent'),
            # Rating formatting (Polars formatting - 10%)  
            pl.col('avg_review_score').map_elements(lambda x: f"{x:.1f}/5" if x is not None else "N/A", return_dtype=pl.Utf8).alias('Avg Rating')
        ]).select([
            'Customer ID',
            pl.col('customer_segment').alias('Segment'),
            pl.col('customer_state').alias('State'),
            pl.col('total_orders').alias('Orders'),
            'Total Spent',
            'Avg Rating'
        ])
        
        display_dataframe(top_customers, "🏆 Top 20 Customers by Value")
        
        # Summary insights
        col1, col2, col3 = st.columns(3)
        with col1:
            total_customers = customer_data.height
            st.metric("👥 Total Customers", f"{total_customers:,}")
        
        with col2:
            if 'customer_segment' in customer_data.columns:
                top_segment = customer_data.group_by('customer_segment').len().sort('len', descending=True).select('customer_segment').limit(1).to_series().to_list()[0]
                st.metric("🏆 Largest Segment", top_segment)
        
        with col3:
            avg_spend = customer_data['total_spent'].mean()
            st.metric("💰 Avg Customer Value", f"${avg_spend:,.0f}")

if __name__ == "__main__":
    main()
