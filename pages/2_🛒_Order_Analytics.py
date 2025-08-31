"""
Order Analytics Page
Detailed order trends and patterns analysis
"""

import streamlit as st
import pandas as pd
from pandas import DatetimeTZDtype
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.auth import default
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Order Analytics", page_icon="🛒", layout="wide")

@st.cache_data
def load_config():
    """Load BigQuery configuration"""
    import os
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bigquery_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

@st.cache_resource
def get_bigquery_client():
    """Initialize BigQuery client with caching"""
    config = load_config()
    credentials, _ = default()
    return bigquery.Client(credentials=credentials, project=config['project_id'])

@st.cache_data(ttl=3600)
def load_order_analytics():
    """Load comprehensive order analytics from BigQuery"""
    config = load_config()
    client = get_bigquery_client()
    
    query = f"""
    WITH order_analytics AS (
        SELECT 
            o.order_id,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_approved_at,
            o.order_delivered_customer_date,
            o.order_estimated_delivery_date,
            COUNT(oi.order_item_id) as item_count,
            SUM(oi.price) as order_value,
            SUM(oi.freight_value) as freight_cost,
            AVG(oi.review_score) as review_score,
            c.customer_state,
            c.customer_city
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o
            ON oi.order_sk = o.order_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c 
            ON oi.customer_sk = c.customer_sk
        GROUP BY 1, 2, 3, 4, 5, 6, 11, 12
    )
    SELECT * FROM order_analytics
    LIMIT 10000
    """
    
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error loading order analytics: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("🛒 Order Analytics")
    st.markdown("**Comprehensive order trends and performance analysis**")
    
    # Load data
    with st.spinner("Loading order analytics data..."):
        df = load_order_analytics()
    
    if df.empty:
        st.error("No order data available.")
        return
    
    # Convert date columns and normalize timezones
    date_columns = ['order_purchase_timestamp', 'order_approved_at', 
                   'order_delivered_customer_date', 'order_estimated_delivery_date']
    
    for col in date_columns:
        if col in df.columns:
            # Handle timezone-aware and timezone-naive datetimes consistently
            df[col] = pd.to_datetime(df[col], errors='coerce')
            # Check for timezone-aware datetimes and normalize
            if isinstance(df[col].dtype, DatetimeTZDtype):
                df[col] = df[col].dt.tz_convert('UTC').dt.tz_localize(None)
            # If already timezone-naive, leave as is
    
    # Key metrics
    st.header("📊 Key Order Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = len(df)
        st.metric("Total Orders", f"{total_orders:,}")
    
    with col2:
        total_revenue = df['order_value'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col3:
        avg_order_value = df['order_value'].mean()
        st.metric("Avg Order Value", f"${avg_order_value:.2f}")
    
    with col4:
        completion_rate = (df['order_status'] == 'delivered').mean() * 100
        st.metric("Order Completion Rate", f"{completion_rate:.1f}%")
    
    # Order trends
    st.header("📈 Order Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Orders Over Time")
        if 'order_purchase_timestamp' in df.columns:
            df['order_date'] = df['order_purchase_timestamp'].dt.date
            daily_orders = df.groupby('order_date').agg({
                'order_id': 'count',
                'order_value': 'sum'
            }).reset_index()
            
            fig = px.line(
                daily_orders,
                x='order_date',
                y='order_id',
                title="Daily Order Count",
                labels={'order_id': 'Number of Orders', 'order_date': 'Date'}
            )
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("💰 Revenue Over Time")
        if 'order_date' in locals():
            fig = px.line(
                daily_orders,
                x='order_date',
                y='order_value',
                title="Daily Revenue",
                labels={'order_value': 'Revenue ($)', 'order_date': 'Date'}
            )
            st.plotly_chart(fig, width="stretch")
    
    # Order status analysis
    st.header("📊 Order Status Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Order Status Distribution")
        status_counts = df['order_status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Order Status Breakdown"
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("⏱️ Delivery Performance")
        if 'order_delivered_customer_date' in df.columns and 'order_estimated_delivery_date' in df.columns:
            delivered_orders = df.dropna(subset=['order_delivered_customer_date', 'order_estimated_delivery_date'])
            
            delivered_orders['delivery_diff'] = (
                delivered_orders['order_delivered_customer_date'] - 
                delivered_orders['order_estimated_delivery_date']
            ).dt.days
            
            # On-time delivery rate
            on_time_rate = (delivered_orders['delivery_diff'] <= 0).mean() * 100
            st.metric("On-Time Delivery Rate", f"{on_time_rate:.1f}%")
            
            # Delivery performance histogram
            fig = px.histogram(
                delivered_orders,
                x='delivery_diff',
                nbins=50,
                title="Delivery Performance (Days vs Estimated)",
                labels={'delivery_diff': 'Days (Negative = Early)', 'count': 'Number of Orders'}
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="On Time")
            st.plotly_chart(fig, width="stretch")
    
    # Geographic analysis
    st.header("🗺️ Geographic Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Orders by State")
        state_orders = df.groupby('customer_state').agg({
            'order_id': 'count',
            'order_value': 'sum'
        }).reset_index()
        state_orders.columns = ['State', 'Order Count', 'Revenue']
        
        fig = px.bar(
            state_orders.head(15),
            x='State',
            y='Order Count',
            title="Top 15 States by Order Volume"
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("💵 Revenue by State")
        fig = px.bar(
            state_orders.head(15),
            x='State',
            y='Revenue',
            title="Top 15 States by Revenue"
        )
        st.plotly_chart(fig, width="stretch")
    
    # Order value analysis
    st.header("💰 Order Value Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Order Value Distribution")
        fig = px.histogram(
            df,
            x='order_value',
            nbins=50,
            title="Order Value Distribution",
            labels={'order_value': 'Order Value ($)', 'count': 'Number of Orders'}
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("📦 Items per Order")
        fig = px.histogram(
            df,
            x='item_count',
            nbins=20,
            title="Items per Order Distribution",
            labels={'item_count': 'Number of Items', 'count': 'Number of Orders'}
        )
        st.plotly_chart(fig, width="stretch")
    
    # Detailed data table
    st.header("📋 Order Analytics Data")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            df['order_status'].unique(),
            default=df['order_status'].unique()
        )
    
    with col2:
        min_value = st.number_input("Min Order Value ($)", min_value=0.0, value=0.0)
    
    with col3:
        state_filter = st.multiselect(
            "Filter by State",
            df['customer_state'].unique(),
            default=df['customer_state'].unique()[:10]
        )
    
    # Apply filters
    filtered_df = df[
        (df['order_status'].isin(status_filter)) &
        (df['order_value'] >= min_value) &
        (df['customer_state'].isin(state_filter))
    ]
    
    st.dataframe(filtered_df, width="stretch")

if __name__ == "__main__":
    main()
