"""
Optimized Customer Analytics Page
Advanced customer insights and segmentation with improved performance
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database import load_config, get_bigquery_client, execute_query, normalize_datetime_columns
from utils.visualizations import (create_metric_cards, create_bar_chart, create_pie_chart, 
                                create_line_chart, display_chart, display_dataframe)
from utils.data_processing import get_customer_segments, calculate_business_metrics, format_currency

st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide")

@st.cache_data(ttl=1800)
def get_customer_cohort_analysis():
    """Get customer cohort analysis for retention insights"""
    config = load_config()
    if not config:
        return pd.DataFrame()
    
    query = f"""
    WITH first_orders AS (
        SELECT 
            c.customer_unique_id,
            DATE(DATE_TRUNC(MIN(o.order_purchase_timestamp), MONTH)) as cohort_month
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        GROUP BY 1
    ),
    cohort_data AS (
        SELECT 
            fo.cohort_month,
            DATE(DATE_TRUNC(o.order_purchase_timestamp, MONTH)) as order_month,
            COUNT(DISTINCT c.customer_unique_id) as customers
        FROM first_orders fo
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON fo.customer_unique_id = c.customer_unique_id
        JOIN `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi ON c.customer_sk = oi.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        GROUP BY 1, 2
    )
    SELECT 
        cohort_month,
        order_month,
        customers,
        DATE_DIFF(order_month, cohort_month, MONTH) as period_number
    FROM cohort_data
    ORDER BY cohort_month, period_number
    """
    
    return execute_query(query, "Customer Cohort Analysis")

@st.cache_data(ttl=1800)
def get_customer_lifetime_value():
    """Calculate customer lifetime value metrics"""
    config = load_config()
    if not config:
        return pd.DataFrame()
    
    query = f"""
    WITH customer_metrics AS (
        SELECT 
            c.customer_unique_id,
            c.customer_state,
            COUNT(DISTINCT oi.order_id) as total_orders,
            SUM(oi.price) as total_spent,
            AVG(oi.price) as avg_order_value,
            DATE_DIFF(DATE(MAX(o.order_purchase_timestamp)), DATE(MIN(o.order_purchase_timestamp)), DAY) as customer_lifespan_days,
            MIN(o.order_purchase_timestamp) as first_order,
            MAX(o.order_purchase_timestamp) as last_order
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o ON oi.order_sk = o.order_sk
        WHERE o.order_status = 'delivered'
        GROUP BY 1, 2
    )
    SELECT *,
        CASE 
            WHEN customer_lifespan_days > 0 
            THEN total_spent / (customer_lifespan_days / 30.0)  -- Monthly CLV
            ELSE total_spent 
        END as monthly_clv
    FROM customer_metrics
    ORDER BY total_spent DESC
    """
    
    return execute_query(query, "Customer Lifetime Value")

def main():
    """Main customer analytics dashboard"""
    st.title("👥 Customer Analytics")
    st.markdown("**Advanced Customer Insights & Segmentation**")
    
    # Load customer data
    with st.spinner("🔄 Loading customer analytics..."):
        customer_segments = get_customer_segments()
        cohort_data = get_customer_cohort_analysis()
        clv_data = get_customer_lifetime_value()
    
    if customer_segments.empty:
        st.error("❌ No customer data available. Please check your data connection.")
        return
    
    # Key metrics
    st.header("📊 Customer Overview")
    
    metrics = calculate_business_metrics(customer_segments)
    if metrics:
        create_metric_cards(metrics)
    
    # Customer segmentation analysis
    st.header("🎯 Customer Segmentation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'customer_segment' in customer_segments.columns:
            st.subheader("Segment Distribution")
            segment_counts = customer_segments['customer_segment'].value_counts()
            fig = create_pie_chart(
                values=segment_counts.values,
                names=segment_counts.index,
                title="Customer Segments"
            )
            display_chart(fig, key="customer_segments")
    
    with col2:
        if 'customer_segment' in customer_segments.columns and 'total_spent' in customer_segments.columns:
            st.subheader("Revenue by Segment")
            segment_revenue = customer_segments.groupby('customer_segment')['total_spent'].sum().sort_values(ascending=False)
            fig = create_bar_chart(
                data=segment_revenue.reset_index(),
                x='customer_segment',
                y='total_spent',
                title="Revenue by Customer Segment",
                labels={'customer_segment': 'Segment', 'total_spent': 'Revenue ($)'}
            )
            display_chart(fig, key="segment_revenue")
    
    # Geographic analysis
    st.header("🗺️ Geographic Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'customer_state' in customer_segments.columns:
            st.subheader("Customers by State")
            state_distribution = customer_segments['customer_state'].value_counts().head(10)
            fig = create_bar_chart(
                data=state_distribution.reset_index(),
                x='customer_state',
                y='count',
                title="Top 10 States by Customer Count",
                labels={'customer_state': 'State', 'count': 'Customers'}
            )
            display_chart(fig, key="state_distribution")
    
    with col2:
        if 'customer_state' in customer_segments.columns and 'total_spent' in customer_segments.columns:
            st.subheader("Revenue by State") 
            state_revenue = customer_segments.groupby('customer_state')['total_spent'].sum().sort_values(ascending=False).head(10)
            fig = create_bar_chart(
                data=state_revenue.reset_index(),
                x='customer_state',
                y='total_spent',
                title="Top 10 States by Revenue",
                labels={'customer_state': 'State', 'total_spent': 'Revenue ($)'}
            )
            display_chart(fig, key="state_revenue")
    
    # Customer Lifetime Value Analysis
    if not clv_data.empty:
        st.header("💰 Customer Lifetime Value")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("CLV Distribution")
            if 'total_spent' in clv_data.columns:
                # Create CLV segments
                clv_data['clv_segment'] = pd.cut(
                    clv_data['total_spent'],
                    bins=[0, 100, 500, 1000, 2000, float('inf')],
                    labels=['$0-100', '$100-500', '$500-1K', '$1K-2K', '$2K+']
                )
                
                clv_counts = clv_data['clv_segment'].value_counts()
                fig = create_pie_chart(
                    values=clv_counts.values,
                    names=clv_counts.index,
                    title="Customer Lifetime Value Distribution"
                )
                display_chart(fig, key="clv_distribution")
        
        with col2:
            st.subheader("Order Frequency vs Value")
            if 'total_orders' in clv_data.columns and 'avg_order_value' in clv_data.columns:
                fig = px.scatter(
                    clv_data,
                    x='total_orders',
                    y='avg_order_value',
                    size='total_spent',
                    color='customer_state',
                    title="Order Frequency vs Average Order Value",
                    labels={
                        'total_orders': 'Number of Orders',
                        'avg_order_value': 'Average Order Value ($)',
                        'total_spent': 'Total Spent ($)'
                    }
                )
                display_chart(fig, key="order_frequency_value")
    
    # Cohort Analysis
    if not cohort_data.empty:
        st.header("📈 Customer Retention Cohort Analysis")
        
        # Create cohort table
        cohort_table = cohort_data.pivot_table(
            index='cohort_month',
            columns='period_number', 
            values='customers',
            fill_value=0
        )
        
        if not cohort_table.empty:
            st.subheader("Cohort Retention Table")
            
            # Calculate retention rates
            cohort_sizes = cohort_data[cohort_data['period_number'] == 0].set_index('cohort_month')['customers']
            retention_table = cohort_table.divide(cohort_sizes, axis=0)
            
            # Display heatmap
            fig = px.imshow(
                retention_table,
                title="Customer Retention Rates by Cohort",
                labels={'x': 'Period Number', 'y': 'Cohort Month', 'color': 'Retention Rate'},
                color_continuous_scale='RdYlGn'
            )
            display_chart(fig, key="cohort_heatmap")
    
    # Detailed customer data
    display_dataframe(customer_segments, "📋 Customer Segmentation Data", max_rows=50)

if __name__ == "__main__":
    main()
