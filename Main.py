"""
Marketing Analytics Dashboard
Hybrid BigQuery-Polars architecture for optimal performance
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.database import get_bigquery_client
from utils.visualizations import create_metric_cards, create_bar_chart, create_pie_chart, create_line_chart

# Page configuration
st.set_page_config(
    page_title="Marketing Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=1800)
def get_dashboard_overview_data():
    """Get dashboard overview data using BigQuery SQL"""
    client = get_bigquery_client()
    
    query = """
    WITH overview_metrics AS (
        SELECT 
            COUNT(DISTINCT c.customer_unique_id) as total_customers,
            COUNT(DISTINCT o.order_id) as total_orders,
            ROUND(SUM(oi.price), 2) as total_revenue,
            ROUND(AVG(oi.price), 2) as avg_order_value,
            COUNT(DISTINCT c.customer_state) as total_states,
            COUNT(DISTINCT c.customer_city) as total_cities,
            ROUND(AVG(r.review_score), 2) as avg_review_score,
            COUNT(DISTINCT p.product_category_name) as total_categories
        FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
        JOIN `project-olist-470307.dbt_olist_dwh.fact_orders` o
            ON oi.order_sk = o.order_sk
        JOIN `project-olist-470307.dbt_olist_dwh.dim_customer` c
            ON o.customer_sk = c.customer_sk
        LEFT JOIN `project-olist-470307.dbt_olist_dwh.dim_order_reviews` r
            ON o.order_sk = r.order_sk
        LEFT JOIN `project-olist-470307.dbt_olist_dwh.dim_product` p
            ON oi.product_sk = p.product_sk
    ),
    
    recent_activity AS (
        SELECT 
            EXTRACT(YEAR FROM o.order_purchase_timestamp) as year,
            EXTRACT(MONTH FROM o.order_purchase_timestamp) as month,
            COUNT(DISTINCT o.order_id) as monthly_orders,
            ROUND(SUM(oi.price), 2) as monthly_revenue
        FROM `project-olist-470307.dbt_olist_dwh.fact_order_items` oi
        JOIN `project-olist-470307.dbt_olist_dwh.fact_orders` o
            ON oi.order_sk = o.order_sk
        WHERE CASE 
                WHEN o.order_purchase_timestamp IS NULL 
                     OR TRIM(CAST(o.order_purchase_timestamp AS STRING)) = ''
                THEN FALSE
                ELSE TIMESTAMP(o.order_purchase_timestamp) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 MONTH)
            END
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        LIMIT 12
    )
    
    SELECT 
        'overview' as data_type,
        NULL as year, NULL as month,
        total_customers, total_orders, total_revenue, avg_order_value,
        total_states, total_cities, avg_review_score, total_categories,
        NULL as monthly_orders, NULL as monthly_revenue
    FROM overview_metrics
    
    UNION ALL
    
    SELECT 
        'monthly' as data_type,
        year, month,
        NULL as total_customers, NULL as total_orders, NULL as total_revenue, NULL as avg_order_value,
        NULL as total_states, NULL as total_cities, NULL as avg_review_score, NULL as total_categories,
        monthly_orders, monthly_revenue
    FROM recent_activity
    
    ORDER BY data_type, year DESC, month DESC
    """
    
    try:
        job = client.query(query)
        results = job.result()
        df = pl.from_pandas(results.to_dataframe())
        return df
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        return pl.DataFrame()

def format_currency_polars(value):
    """Format currency using Polars (10% processing)"""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def display_overview_metrics(df):
    """Display main dashboard overview metrics"""
    overview_data = df.filter(pl.col("data_type") == "overview")
    
    if overview_data.height > 0:
        row = overview_data.row(0, named=True)
        
        # Create metric cards
        metrics = [
            ("Total Customers", f"{row['total_customers']:,}", "👥"),
            ("Total Orders", f"{row['total_orders']:,}", "🛒"),
            ("Total Revenue", format_currency_polars(row['total_revenue']), "💰"),
            ("Avg Order Value", format_currency_polars(row['avg_order_value']), "💳"),
            ("States Covered", f"{row['total_states']:,}", "🗺️"),
            ("Cities Covered", f"{row['total_cities']:,}", "🏙️"),
            ("Avg Rating", f"{row['avg_review_score']:.2f}/5", "⭐"),
            ("Product Categories", f"{row['total_categories']:,}", "📦")
        ]
        
        create_metric_cards(metrics)

def display_recent_trends(df):
    """Display recent business activity trends"""
    monthly_data = df.filter(pl.col("data_type") == "monthly")
    
    if monthly_data.height > 0:
        # Sort data by date
        monthly_sorted = monthly_data.sort(["year", "month"])
        
        # Convert to pandas for visualization
        monthly_pd = monthly_sorted.to_pandas()
        monthly_pd['month_year'] = monthly_pd['year'].astype(str) + '-' + monthly_pd['month'].astype(str).str.zfill(2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                monthly_pd,
                x='month_year',
                y='monthly_orders',
                title='Monthly Order Trends (Last 12 Months)',
                labels={'monthly_orders': 'Orders', 'month_year': 'Month'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig2 = px.line(
                monthly_pd,
                x='month_year', 
                y='monthly_revenue',
                title='Monthly Revenue Trends (Last 12 Months)',
                labels={'monthly_revenue': 'Revenue ($)', 'month_year': 'Month'}
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)

def main():
    """Main dashboard function"""
    # Header
    st.title("📊 Marketing Analytics Dashboard")
    st.markdown("**Hybrid BigQuery-Polars Architecture** | 90% BigQuery Processing + 10% Polars Formatting")
    
    # Sidebar navigation
    st.sidebar.markdown("## 📋 Analytics Sections")
    st.sidebar.markdown("Navigate to specific analytics pages:")
    st.sidebar.markdown("- 👥 **Customer Analytics**: Segmentation & Lifetime Value")
    st.sidebar.markdown("- 🛒 **Order Analytics**: Trends & Delivery Performance") 
    st.sidebar.markdown("- ⭐ **Review Analytics**: Sentiment & Satisfaction")
    st.sidebar.markdown("- 🗺️ **Geographic Analytics**: Location Intelligence")
    
    # Load overview data
    with st.spinner("Loading dashboard overview..."):
        df = get_dashboard_overview_data()
    
    if df.height == 0:
        st.warning("No data available for dashboard overview")
        return
    
    # Overview metrics
    st.header("📊 Business Overview")
    display_overview_metrics(df)
    
    # Recent trends
    st.header("📈 Recent Activity Trends")
    display_recent_trends(df)
    
    # Architecture info
    st.header("🏗️ Architecture Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Hybrid Processing Architecture:**
        - 🔵 **BigQuery (90%)**: Aggregations, joins, filtering, time-series analysis
        - 🟡 **Polars (10%)**: Currency formatting, percentage calculations, display preparation
        - ⚡ **Performance**: 30-minute caching with @st.cache_data(ttl=1800)
        """)
    
    with col2:
        st.success("""
        **Data Sources:**
        - 📊 Dataset: `dbt_olist_dwh`
        - 🏢 Project: `project-olist-470307`
        - 📅 Data freshness cached for optimal performance
        - 🔄 Auto-refresh every 30 minutes
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit + BigQuery + Polars for optimal performance*")

if __name__ == "__main__":
    main()
