"""
Marketing Analytics Dashboard
Simple and effective dashboard for marketing directors
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.database import get_bigquery_client

# Page configuration
st.set_page_config(
    page_title="Marketing Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=1800)
def get_dashboard_overview():
    """Get dashboard overview using analytics tables"""
    client = get_bigquery_client()
    if not client:
        return None
    
    try:
        # Customer Overview
        customer_query = """
        SELECT 
            COUNT(DISTINCT customer_sk) as total_customers,
            COUNT(DISTINCT customer_state) as total_states,
            SUM(total_orders) as total_orders,
            ROUND(SUM(total_spent), 2) as total_revenue,
            ROUND(AVG(avg_order_value), 2) as avg_order_value,
            ROUND(AVG(avg_review_score), 2) as avg_rating
        FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
        WHERE total_orders > 0
        """
        
        customer_result = client.query(customer_query).result()
        customer_data = customer_result.to_dataframe().iloc[0].to_dict()
        
        # Geographic Overview
        geo_query = """
        SELECT 
            COUNT(DISTINCT state_code) as states_count,
            SUM(total_cities) as cities_count,
            ROUND(AVG(market_opportunity_index), 2) as avg_market_opportunity
        FROM `project-olist-470307.dbt_olist_analytics.geographic_analytics_obt`
        """
        
        geo_result = client.query(geo_query).result()
        geo_data = geo_result.to_dataframe().iloc[0].to_dict()
        
        # Recent Revenue Trends
        revenue_query = """
        SELECT 
            order_year,
            order_month,
            COUNT(DISTINCT order_id) as monthly_orders,
            ROUND(SUM(item_price), 2) as monthly_revenue
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
        GROUP BY order_year, order_month
        ORDER BY order_year DESC, order_month DESC
        LIMIT 12
        """
        
        revenue_result = client.query(revenue_query).result()
        revenue_trends = pl.from_pandas(revenue_result.to_dataframe())
        
        return {
            'customer_metrics': customer_data,
            'geographic_metrics': geo_data,
            'revenue_trends': revenue_trends
        }
        
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        return None

def create_metric_card(title, value, icon):
    """Create a metric card"""
    return f"""
    <div style="
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <h3 style="margin: 0; font-size: 2rem;">{icon}</h3>
        <h4 style="margin: 0.5rem 0; color: #f0f0f0;">{title}</h4>
        <h2 style="margin: 0; font-size: 1.8rem;">{value}</h2>
    </div>
    """

def main():
    """Main dashboard function"""
    # Header
    st.title("📊 Marketing Analytics Dashboard")
    st.markdown("**Data-Driven Insights for Marketing Directors**")
    
    # Load data
    with st.spinner("Loading dashboard overview..."):
        data = get_dashboard_overview()
    
    if not data:
        st.error("Unable to load dashboard data. Please check your connection.")
        return
    
    # Main Metrics
    st.header("📈 Business Performance Overview")
    
    customer_metrics = data['customer_metrics']
    geo_metrics = data['geographic_metrics']
    
    # Create metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Total Customers", 
            f"{customer_metrics['total_customers']:,}", 
            "👥"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Total Orders", 
            f"{customer_metrics['total_orders']:,}", 
            "🛒"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "Total Revenue", 
            f"${customer_metrics['total_revenue']:,.0f}", 
            "💰"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "Avg Order Value", 
            f"${customer_metrics['avg_order_value']:.2f}", 
            "💳"
        ), unsafe_allow_html=True)
    
    # Second row of metrics
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.markdown(create_metric_card(
            "Market Coverage", 
            f"{customer_metrics['total_states']} States", 
            "🗺️"
        ), unsafe_allow_html=True)
    
    with col6:
        st.markdown(create_metric_card(
            "Cities Served", 
            f"{geo_metrics['cities_count']:,}", 
            "🏙️"
        ), unsafe_allow_html=True)
    
    with col7:
        st.markdown(create_metric_card(
            "Customer Rating", 
            f"{customer_metrics['avg_rating']:.2f}/5", 
            "⭐"
        ), unsafe_allow_html=True)
    
    with col8:
        st.markdown(create_metric_card(
            "Market Opportunity", 
            f"{geo_metrics['avg_market_opportunity']:.1f}", 
            "🎯"
        ), unsafe_allow_html=True)
    
    # Revenue Trends
    st.header("📊 Revenue Trends (Last 12 Months)")
    
    revenue_trends = data['revenue_trends']
    if not revenue_trends.is_empty():
        # Convert to pandas for plotting
        trends_pd = revenue_trends.to_pandas()
        trends_pd['month_label'] = trends_pd['order_year'].astype(str) + '-' + trends_pd['order_month'].astype(str).str.zfill(2)
        trends_pd = trends_pd.sort_values(['order_year', 'order_month'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_orders = px.line(
                trends_pd,
                x='month_label',
                y='monthly_orders',
                title='Monthly Order Volume',
                labels={'monthly_orders': 'Orders', 'month_label': 'Month'}
            )
            fig_orders.update_layout(
                height=400,
                showlegend=False,
                xaxis_title="Month",
                yaxis_title="Orders"
            )
            st.plotly_chart(fig_orders, use_container_width=True)
        
        with col2:
            fig_revenue = px.line(
                trends_pd,
                x='month_label',
                y='monthly_revenue',
                title='Monthly Revenue Performance',
                labels={'monthly_revenue': 'Revenue ($)', 'month_label': 'Month'}
            )
            fig_revenue.update_layout(
                height=400,
                showlegend=False,
                xaxis_title="Month",
                yaxis_title="Revenue ($)"
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Navigation Guide
    st.header("🧭 Analytics Navigation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📋 Available Analytics Pages:**
        
        � **Customer Analytics** - Customer segmentation, lifetime value, churn analysis
        
        � **Order Analytics** - Order trends, delivery performance, growth analysis
        
        � **Geographic Analytics** - Market opportunities, regional performance
        """)
    
    with col2:
        st.success("""
        **🎯 Marketing Insights:**
        
        ✅ **Customer Segmentation** - VIP, High Value, Regular customers
        
        ✅ **Market Intelligence** - Geographic opportunities and performance
        
        ✅ **Growth Analytics** - Revenue trends and business expansion opportunities
        """)
    
    # Key Insights Summary
    st.header("� Key Marketing Insights")
    
    # Calculate some quick insights
    total_customers = customer_metrics['total_customers']
    total_revenue = customer_metrics['total_revenue']
    avg_order_value = customer_metrics['avg_order_value']
    
    insights_col1, insights_col2, insights_col3 = st.columns(3)
    
    with insights_col1:
        st.markdown("""
        **🎯 Customer Acquisition**
        - Focus on states with high market opportunity
        - Target similar demographics to VIP customers
        - Leverage positive customer ratings (4+ stars average)
        """)
    
    with insights_col2:
        st.markdown(f"""
        **💰 Revenue Optimization**
        - Current AOV: ${avg_order_value:.2f}
        - Focus on increasing order frequency
        - Cross-sell opportunities across {customer_metrics['total_states']} states
        """)
    
    with insights_col3:
        st.markdown(f"""
        **📊 Growth Opportunities**
        - {total_customers:,} customers across Brazil
        - Expand in high-opportunity markets
        - Enhance customer retention programs
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("*📊 Marketing Analytics Dashboard - Built for Strategic Decision Making*")

if __name__ == "__main__":
    main()
