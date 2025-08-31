"""
Geographic Analytics Page
Location-based insights and geospatial analysis
"""

import streamlit as st
import pandas as pd
from pandas import DatetimeTZDtype
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database import load_config, get_bigquery_client, execute_query
from utils.visualizations import (create_metric_cards, create_bar_chart, create_pie_chart, 
                                create_line_chart, display_chart, display_dataframe)
from utils.data_processing import get_geographic_summary, format_currency

st.set_page_config(page_title="Geographic Analytics", page_icon="🗺️", layout="wide")

@st.cache_data(ttl=3600)
def load_geographic_analytics():
    """Load geographic analytics from BigQuery"""
    config = load_config()
    if not config:
        return pd.DataFrame()
    
    query = f"""
    WITH geo_analytics AS (
        SELECT 
            c.customer_state,
            c.customer_city,
            g.geolocation_lat,
            g.geolocation_lng,
            COUNT(DISTINCT c.customer_unique_id) as customer_count,
            COUNT(DISTINCT oi.order_id) as order_count,
            SUM(oi.price) as total_revenue,
            AVG(oi.price) as avg_order_value,
            AVG(oi.review_score) as avg_review_score,
            COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN oi.order_id END) as delivered_orders
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c
            ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_geolocation` g 
            ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
            ON oi.order_sk = o.order_sk
        WHERE g.geolocation_lat IS NOT NULL 
        AND g.geolocation_lng IS NOT NULL
        AND g.geolocation_lat BETWEEN -35 AND 10  -- Brazil bounds
        AND g.geolocation_lng BETWEEN -75 AND -30 -- Brazil bounds
        GROUP BY 1, 2, 3, 4
        HAVING customer_count > 0
    )
    SELECT * FROM geo_analytics
    LIMIT 5000
    """
    
    return execute_query(query, "geographic_analytics")

@st.cache_data(ttl=3600)
def load_state_summary():
    """Load state-level summary data"""
    config = load_config()
    if not config:
        return pd.DataFrame()
    
    query = f"""
    SELECT 
        c.customer_state,
        COUNT(DISTINCT c.customer_unique_id) as customer_count,
        COUNT(DISTINCT oi.order_id) as order_count,
        SUM(oi.price) as total_revenue,
        AVG(oi.price) as avg_order_value,
        AVG(oi.review_score) as avg_review_score,
        COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN oi.order_id END) as delivered_orders
    FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
    JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c
        ON oi.customer_sk = c.customer_sk
    JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
        ON oi.order_sk = o.order_sk
    GROUP BY 1
    HAVING customer_count > 0
    ORDER BY total_revenue DESC
    """
    
    return execute_query(query, "state_summary")

def main():
    st.title("🗺️ Geographic Analytics")
    st.markdown("**Location-based business insights and market analysis**")
    
    # Load data
    with st.spinner("Loading geographic data..."):
        geo_df = load_geographic_analytics()
        state_df = load_state_summary()
    
    if geo_df.empty and state_df.empty:
        st.error("No geographic data available.")
        return
    
    # Key geographic metrics
    st.header("📊 Geographic Overview")
    
    if not state_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_states = len(state_df)
            st.metric("States Covered", f"{total_states}")
        
        with col2:
            if not geo_df.empty:
                total_cities = geo_df['customer_city'].nunique()
                st.metric("Cities with Data", f"{total_cities:,}")
        
        with col3:
            top_state_revenue = state_df.iloc[0]['total_revenue'] if len(state_df) > 0 else 0
            st.metric("Top State Revenue", f"${top_state_revenue:,.2f}")
        
        with col4:
            market_concentration = (state_df.head(5)['total_revenue'].sum() / 
                                  state_df['total_revenue'].sum()) * 100
            st.metric("Top 5 States Revenue %", f"{market_concentration:.1f}%")
    
    # State-level analysis
    st.header("🏛️ State-Level Performance")
    
    if not state_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Revenue by State")
            top_revenue_states = state_df.head(15)
            fig = px.bar(
                top_revenue_states,
                x='customer_state',
                y='total_revenue',
                title="Top 15 States by Revenue",
                labels={'total_revenue': 'Revenue ($)', 'customer_state': 'State'}
            )
            st.plotly_chart(fig, width="stretch")
        
        with col2:
            st.subheader("👥 Customers by State")
            top_customer_states = state_df.nlargest(15, 'customer_count')
            fig = px.bar(
                top_customer_states,
                x='customer_state',
                y='customer_count',
                title="Top 15 States by Customer Count",
                labels={'customer_count': 'Customer Count', 'customer_state': 'State'}
            )
            st.plotly_chart(fig, width="stretch")
    
    # Map visualization
    st.header("🗺️ Interactive Map")
    
    if not geo_df.empty:
        # Filter for better visualization
        map_data = geo_df[
            (geo_df['customer_count'] >= 5) &  # At least 5 customers
            (geo_df['geolocation_lat'].notna()) &
            (geo_df['geolocation_lng'].notna())
        ].copy()
        
        if not map_data.empty:
            col1, col2 = st.columns([3, 1])
            
            with col2:
                st.subheader("🎛️ Map Controls")
                
                # Map type selection
                map_type = st.selectbox(
                    "Map Visualization",
                    ["Customer Count", "Revenue", "Avg Review Score", "Order Count"]
                )
                
                # Color column mapping
                color_mapping = {
                    "Customer Count": "customer_count",
                    "Revenue": "total_revenue",
                    "Avg Review Score": "avg_review_score",
                    "Order Count": "order_count"
                }
                
                color_col = color_mapping[map_type]
                
                # Size control
                size_by = st.selectbox(
                    "Bubble Size by",
                    ["Customer Count", "Revenue", "Order Count"],
                    index=1
                )
                
                size_mapping = {
                    "Customer Count": "customer_count",
                    "Revenue": "total_revenue",
                    "Order Count": "order_count"
                }
                
                size_col = size_mapping[size_by]
            
            with col1:
                st.subheader(f"📍 Brazil Map - {map_type}")
                
                fig = px.scatter_mapbox(
                    map_data,
                    lat='geolocation_lat',
                    lon='geolocation_lng',
                    color=color_col,
                    size=size_col,
                    hover_name='customer_city',
                    hover_data={
                        'customer_state': True,
                        'customer_count': True,
                        'total_revenue': ':.2f',
                        'avg_review_score': ':.2f'
                    },
                    color_continuous_scale='Viridis',
                    mapbox_style='open-street-map',
                    zoom=3,
                    center={'lat': -15, 'lon': -50},  # Center on Brazil
                    title=f"Geographic Distribution - {map_type}"
                )
                
                fig.update_layout(height=600)
                st.plotly_chart(fig, width="stretch")
    
    # Regional comparison
    st.header("🏛️ Regional Comparison")
    
    if not state_df.empty:
        # Define Brazilian regions (simplified)
        region_mapping = {
            'SP': 'Southeast', 'RJ': 'Southeast', 'MG': 'Southeast', 'ES': 'Southeast',
            'RS': 'South', 'SC': 'South', 'PR': 'South',
            'BA': 'Northeast', 'PE': 'Northeast', 'CE': 'Northeast', 'PB': 'Northeast',
            'RN': 'Northeast', 'AL': 'Northeast', 'SE': 'Northeast', 'PI': 'Northeast', 'MA': 'Northeast',
            'GO': 'Central-West', 'MT': 'Central-West', 'MS': 'Central-West', 'DF': 'Central-West',
            'AM': 'North', 'PA': 'North', 'RO': 'North', 'AC': 'North', 'RR': 'North', 'AP': 'North', 'TO': 'North'
        }
        
        state_df['region'] = state_df['customer_state'].map(region_mapping).fillna('Other')
        
        regional_summary = state_df.groupby('region').agg({
            'customer_count': 'sum',
            'order_count': 'sum',
            'total_revenue': 'sum',
            'avg_order_value': 'mean',
            'avg_review_score': 'mean'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌎 Revenue by Region")
            fig = px.pie(
                regional_summary,
                values='total_revenue',
                names='region',
                title="Revenue Distribution by Brazilian Region"
            )
            st.plotly_chart(fig, width="stretch")
        
        with col2:
            st.subheader("⭐ Customer Satisfaction by Region")
            fig = px.bar(
                regional_summary,
                x='region',
                y='avg_review_score',
                title="Average Review Score by Region"
            )
            st.plotly_chart(fig, width="stretch")
    
    # Detailed data tables
    st.header("📋 Geographic Data")
    
    tab1, tab2 = st.tabs(["State Summary", "City Details"])
    
    with tab1:
        if not state_df.empty:
            st.subheader("🏛️ State Performance Summary")
            display_df = state_df.copy()
            display_df['delivery_rate'] = (display_df['delivered_orders'] / display_df['order_count'] * 100).round(1)
            st.dataframe(display_df, width="stretch")
    
    with tab2:
        if not geo_df.empty:
            st.subheader("🏙️ City-Level Details")
            
            # City filters
            col1, col2 = st.columns(2)
            
            with col1:
                min_customers = st.number_input("Min Customers", min_value=1, value=10)
            
            with col2:
                selected_states = st.multiselect(
                    "Filter by State",
                    geo_df['customer_state'].unique(),
                    default=geo_df['customer_state'].unique()[:10]
                )
            
            filtered_geo = geo_df[
                (geo_df['customer_count'] >= min_customers) &
                (geo_df['customer_state'].isin(selected_states))
            ]
            
            st.dataframe(filtered_geo, width="stretch")

if __name__ == "__main__":
    main()
