"""
Geographic Analytics Page
Location-based market intelligence and geospatial analysis
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database import get_bigquery_client
from utils.visualizations import create_metric_cards, create_bar_chart, create_pie_chart, create_line_chart

st.set_page_config(page_title="Geographic Analytics", page_icon="🗺️", layout="wide")

@st.cache_data(ttl=1800)
def get_geographic_overview_data():
    """Get geographic analytics overview data using BigQuery SQL"""
    client = get_bigquery_client()
    
    query = """
    WITH geo_analytics AS (
        SELECT 
            c.customer_state,
            c.customer_city,
            g.geolocation_lat,
            g.geolocation_lng,
            COUNT(DISTINCT c.customer_unique_id) as customer_count,
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(oi.price) as total_revenue,
            ROUND(AVG(oi.price), 2) as avg_order_value,
            ROUND(AVG(r.review_score), 2) as avg_review_score,
            COUNT(CASE WHEN o.order_status = 'delivered' THEN 1 END) as delivered_orders
        FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
        JOIN `project-olist-470307.dbt_olist_dwh.fact_orders` o
            ON oi.order_sk = o.order_sk
        JOIN `project-olist-470307.dbt_olist_dwh.dim_customer` c
            ON o.customer_sk = c.customer_sk
        LEFT JOIN `project-olist-470307.dbt_olist_dwh.dim_geolocation` g 
            ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
        LEFT JOIN `project-olist-470307.dbt_olist_dwh.dim_order_reviews` r
            ON o.order_sk = r.order_sk
        WHERE c.customer_state IS NOT NULL
        GROUP BY c.customer_state, c.customer_city, g.geolocation_lat, g.geolocation_lng
    ),
    
    geo_overview AS (
        SELECT 
            COUNT(DISTINCT customer_state) as total_states,
            COUNT(DISTINCT customer_city) as total_cities,
            SUM(customer_count) as total_customers,
            SUM(order_count) as total_orders,
            ROUND(SUM(total_revenue), 2) as total_revenue,
            ROUND(AVG(avg_order_value), 2) as avg_order_value,
            ROUND(AVG(avg_review_score), 2) as avg_review_score
        FROM geo_analytics
    ),
    
    state_summary AS (
        SELECT 
            customer_state,
            SUM(customer_count) as state_customers,
            SUM(order_count) as state_orders,
            ROUND(SUM(total_revenue), 2) as state_revenue,
            ROUND(AVG(avg_order_value), 2) as state_avg_order_value,
            ROUND(AVG(avg_review_score), 2) as state_avg_rating,
            COUNT(DISTINCT customer_city) as cities_count
        FROM geo_analytics
        GROUP BY customer_state
        ORDER BY state_revenue DESC
    ),
    
    city_summary AS (
        SELECT 
            customer_state,
            customer_city,
            customer_count as city_customers,
            order_count as city_orders,
            ROUND(total_revenue, 2) as city_revenue,
            ROUND(avg_order_value, 2) as city_avg_order_value,
            ROUND(avg_review_score, 2) as city_avg_rating,
            geolocation_lat,
            geolocation_lng
        FROM geo_analytics
        WHERE total_revenue > 1000
        ORDER BY total_revenue DESC
        LIMIT 50
    ),
    
    top_cities AS (
        SELECT 
            customer_city,
            customer_state,
            customer_count,
            order_count,
            ROUND(total_revenue, 2) as revenue,
            ROUND(avg_order_value, 2) as avg_order_value
        FROM geo_analytics
        WHERE customer_city IS NOT NULL
        ORDER BY total_revenue DESC
        LIMIT 20
    )
    
    SELECT 
        'overview' as data_type,
        NULL as customer_state, NULL as customer_city,
        total_states, total_cities, total_customers, total_orders, 
        total_revenue, avg_order_value, avg_review_score,
        NULL as state_customers, NULL as state_orders, NULL as state_revenue,
        NULL as state_avg_order_value, NULL as state_avg_rating, NULL as cities_count,
        NULL as city_customers, NULL as city_orders, NULL as city_revenue,
        NULL as city_avg_order_value, NULL as city_avg_rating,
        NULL as geolocation_lat, NULL as geolocation_lng,
        NULL as customer_count, NULL as order_count, NULL as revenue
    FROM geo_overview
    
    UNION ALL
    
    SELECT 
        'state' as data_type,
        customer_state, NULL as customer_city,
        NULL as total_states, NULL as total_cities, NULL as total_customers, NULL as total_orders,
        NULL as total_revenue, NULL as avg_order_value, NULL as avg_review_score,
        state_customers, state_orders, state_revenue,
        state_avg_order_value, state_avg_rating, cities_count,
        NULL as city_customers, NULL as city_orders, NULL as city_revenue,
        NULL as city_avg_order_value, NULL as city_avg_rating,
        NULL as geolocation_lat, NULL as geolocation_lng,
        NULL as customer_count, NULL as order_count, NULL as revenue
    FROM state_summary
    
    UNION ALL
    
    SELECT 
        'city_map' as data_type,
        customer_state, customer_city,
        NULL as total_states, NULL as total_cities, NULL as total_customers, NULL as total_orders,
        NULL as total_revenue, NULL as avg_order_value, NULL as avg_review_score,
        NULL as state_customers, NULL as state_orders, NULL as state_revenue,
        NULL as state_avg_order_value, NULL as state_avg_rating, NULL as cities_count,
        city_customers, city_orders, city_revenue,
        city_avg_order_value, city_avg_rating,
        geolocation_lat, geolocation_lng,
        NULL as customer_count, NULL as order_count, NULL as revenue
    FROM city_summary
    
    UNION ALL
    
    SELECT 
        'top_cities' as data_type,
        customer_state, customer_city,
        NULL as total_states, NULL as total_cities, NULL as total_customers, NULL as total_orders,
        NULL as total_revenue, NULL as avg_order_value, NULL as avg_review_score,
        NULL as state_customers, NULL as state_orders, NULL as state_revenue,
        NULL as state_avg_order_value, NULL as state_avg_rating, NULL as cities_count,
        NULL as city_customers, NULL as city_orders, NULL as city_revenue,
        NULL as city_avg_order_value, NULL as city_avg_rating,
        NULL as geolocation_lat, NULL as geolocation_lng,
        customer_count, order_count, revenue as revenue
    FROM top_cities
    
    ORDER BY data_type, state_revenue DESC, city_revenue DESC, revenue DESC
    """
    
    try:
        job = client.query(query)
        results = job.result()
        df = pl.from_pandas(results.to_dataframe())
        return df
    except Exception as e:
        st.error(f"Error loading geographic data: {str(e)}")
        return pl.DataFrame()

def format_currency_polars(df, col):
    """Format currency using Polars (10% processing)"""
    return df.with_columns(
        pl.col(col).map_elements(lambda x: f"${x:,.2f}" if x is not None else "$0.00", return_dtype=pl.Utf8)
    )

def display_geographic_overview(df):
    """Display geographic overview metrics"""
    overview_data = df.filter(pl.col("data_type") == "overview")
    
    if overview_data.height > 0:
        row = overview_data.row(0, named=True)
        
        # Create metric cards
        metrics = [
            ("Total States", f"{row['total_states']:,}", "🗺️"),
            ("Total Cities", f"{row['total_cities']:,}", "🏙️"),
            ("Total Customers", f"{row['total_customers']:,}", "👥"),
            ("Average Rating", f"{row['avg_review_score']:.2f}/5", "⭐")
        ]
        
        create_metric_cards(metrics)

def display_state_performance(df):
    """Display state performance analysis"""
    state_data = df.filter(pl.col("data_type") == "state").head(15)
    
    if state_data.height > 0:
        # Format currency using Polars (10% processing)
        formatted_data = format_currency_polars(state_data, "state_revenue")
        
        # Convert to pandas for visualization
        state_pd = formatted_data.to_pandas()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                state_pd,
                x='customer_state',
                y='state_orders',
                title='Orders by State (Top 15)',
                labels={'customer_state': 'State', 'state_orders': 'Number of Orders'},
                text='state_orders'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Parse currency back to float for revenue chart
            state_pd['revenue_float'] = state_pd['state_revenue'].str.replace('$', '').str.replace(',', '').astype(float)
            
            fig2 = px.bar(
                state_pd,
                x='customer_state',
                y='revenue_float',
                title='Revenue by State (Top 15)',
                labels={'customer_state': 'State', 'revenue_float': 'Revenue ($)'},
                text='state_revenue'
            )
            fig2.update_traces(textposition='outside')
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)

def display_geographic_map(df):
    """Display geographic map with city locations"""
    city_data = df.filter(pl.col("data_type") == "city_map")
    
    if city_data.height > 0:
        # Filter for cities with valid coordinates
        map_data = city_data.filter(
            (pl.col("geolocation_lat").is_not_null()) & 
            (pl.col("geolocation_lng").is_not_null())
        )
        
        if map_data.height > 0:
            # Convert to pandas for map visualization
            map_pd = map_data.to_pandas()
            
            fig = px.scatter_mapbox(
                map_pd,
                lat='geolocation_lat',
                lon='geolocation_lng',
                size='city_revenue',
                color='city_avg_rating',
                hover_name='customer_city',
                hover_data={
                    'customer_state': True,
                    'city_customers': True,
                    'city_orders': True,
                    'city_revenue': ':,.2f',
                    'geolocation_lat': False,
                    'geolocation_lng': False
                },
                mapbox_style='open-street-map',
                zoom=3,
                center={'lat': -15.7942, 'lon': -47.8822},  # Brazil center
                title='Geographic Distribution of Orders and Revenue'
            )
            fig.update_layout(height=500, margin={"r":0,"t":50,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)

def display_top_cities(df):
    """Display top performing cities"""
    city_data = df.filter(pl.col("data_type") == "top_cities")
    
    if city_data.height > 0:
        # Format currency using Polars (10% processing)
        formatted_data = format_currency_polars(city_data, "revenue")
        
        # Display top cities table
        st.subheader("Top 20 Cities by Revenue")
        display_cols = ['customer_city', 'customer_state', 'customer_count', 'order_count', 'revenue']
        city_display = formatted_data.select(display_cols)
        st.dataframe(city_display.to_pandas(), use_container_width=True)

def display_state_details(df):
    """Display detailed state analysis"""
    state_data = df.filter(pl.col("data_type") == "state")
    
    if state_data.height > 0:
        # Format currency using Polars (10% processing)
        formatted_data = format_currency_polars(state_data, "state_revenue")
        
        st.subheader("State Performance Details")
        display_cols = ['customer_state', 'state_customers', 'state_orders', 'state_revenue', 
                       'state_avg_rating', 'cities_count']
        state_display = formatted_data.select(display_cols)
        st.dataframe(state_display.to_pandas(), use_container_width=True)

def main():
    """Main function for Geographic Analytics page"""
    st.title("🗺️ Geographic Analytics")
    st.markdown("Location-based market intelligence and geospatial analysis")
    
    # Load data
    with st.spinner("Loading geographic analytics data..."):
        df = get_geographic_overview_data()
    
    if df.height == 0:
        st.warning("No geographic data available")
        return
    
    # Overview metrics
    st.header("📊 Geographic Overview")
    display_geographic_overview(df)
    
    # State performance
    st.header("🏛️ State Performance")
    display_state_performance(df)
    
    # Geographic map
    st.header("🗺️ Geographic Distribution")
    display_geographic_map(df)
    
    # Top cities
    st.header("🏙️ Top Cities")
    display_top_cities(df)
    
    # State details
    st.header("📋 State Details")
    display_state_details(df)

if __name__ == "__main__":
    main()
