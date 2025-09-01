"""
Geographic Analytics Page
Deep analysis of customer and order distribution by geographic location
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

from utils.database import get_bigquery_client
from utils.data_processing import safe_aggregate, safe_item

st.set_page_config(page_title="Geographic Analytics", page_icon="🗺️", layout="wide")

@st.cache_data(ttl=1800)
def get_geographic_analytics_data():
    """Get comprehensive geographic analytics data"""
    client = get_bigquery_client()
    if not client:
        return None
    
    try:
        # Geographic overview using geographic_analytics_obt
        overview_query = """
        SELECT 
            state_code,
            state_code as state_name,
            geographic_region,
            total_customers,
            total_orders,
            total_revenue,
            average_order_value,
            avg_review_score,
            market_tier,
            customers_per_city,
            revenue_per_customer,
            market_opportunity_index
        FROM `project-olist-470307.dbt_olist_analytics.geographic_analytics_obt`
        ORDER BY total_revenue DESC
        """
        
        overview_result = client.query(overview_query).result()
        overview_data = pl.from_pandas(overview_result.to_dataframe())
        
        # Regional analysis
        regional_query = """
        SELECT 
            geographic_region,
            CAST(COUNT(DISTINCT state_code) AS INT64) as states_count,
            CAST(SUM(total_customers) AS INT64) as region_customers,
            CAST(SUM(total_orders) AS INT64) as region_orders,
            ROUND(SUM(total_revenue), 2) as region_revenue,
            ROUND(AVG(average_order_value), 2) as avg_order_value,
            ROUND(AVG(avg_review_score), 2) as avg_review_score
        FROM `project-olist-470307.dbt_olist_analytics.geographic_analytics_obt`
        GROUP BY geographic_region
        ORDER BY region_revenue DESC
        """
        
        regional_result = client.query(regional_query).result()
        regional_data = pl.from_pandas(regional_result.to_dataframe())
        
        # Market tier analysis
        tier_query = """
        SELECT 
            market_tier,
            CAST(COUNT(DISTINCT state_code) AS INT64) as states_count,
            CAST(SUM(total_customers) AS INT64) as tier_customers,
            CAST(SUM(total_orders) AS INT64) as tier_orders,
            ROUND(SUM(total_revenue), 2) as tier_revenue,
            ROUND(AVG(market_opportunity_index), 2) as avg_opportunity_index
        FROM `project-olist-470307.dbt_olist_analytics.geographic_analytics_obt`
        WHERE market_tier IS NOT NULL
        GROUP BY market_tier
        ORDER BY tier_revenue DESC
        """
        
        tier_result = client.query(tier_query).result()
        tier_data = pl.from_pandas(tier_result.to_dataframe())
        
        return {
            'overview_data': overview_data,
            'regional_data': regional_data,
            'tier_data': tier_data
        }
        
    except Exception as e:
        st.error(f"Error loading geographic analytics: {str(e)}")
        return None

def create_metric_card(title, value, icon, color="primary", subtitle=""):
    """Create a metric card with enhanced styling"""
    color_schemes = {
        "primary": {
            "bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "shadow": "0 8px 25px rgba(102, 126, 234, 0.3)"
        },
        "success": {
            "bg": "linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%)",
            "shadow": "0 8px 25px rgba(86, 171, 47, 0.3)"
        },
        "warning": {
            "bg": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "shadow": "0 8px 25px rgba(240, 147, 251, 0.3)"
        },
        "info": {
            "bg": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "shadow": "0 8px 25px rgba(79, 172, 254, 0.3)"
        }
    }
    
    selected_color = color_schemes.get(color, color_schemes["primary"])
    
    return f"""
    <div style="
        background: {selected_color['bg']};
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: {selected_color['shadow']};
        transition: transform 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="
            font-size: 0.9rem; 
            color: rgba(255, 255, 255, 0.8); 
            margin-bottom: 0.3rem;
            font-weight: 500;
        ">{title}</div>
        <div style="
            font-size: 2rem; 
            font-weight: bold; 
            margin-bottom: 0.2rem;
        ">{value}</div>
        {f'<div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.7);">{subtitle}</div>' if subtitle else ''}
    </div>
    """

def main():
    """Main geographic analytics function"""
    st.title("🗺️ Geographic Analytics")
    st.markdown("**Deep Geographic Analysis for Marketing Strategy**")
    
    # Load data
    with st.spinner("Loading geographic analytics..."):
        data = get_geographic_analytics_data()
    
    if not data:
        st.error("Unable to load geographic analytics data.")
        return
    
    overview_data = data['overview_data']
    regional_data = data['regional_data']
    tier_data = data['tier_data']
    
    # Overall Geographic Metrics
    st.header("📊 Geographic Market Overview")
    st.markdown("### Core Geographic Metrics")
    
    if not overview_data.is_empty():
        total_states = overview_data.height
        total_customers = safe_aggregate(overview_data, pl.sum("total_customers"))
        total_revenue = safe_aggregate(overview_data, pl.sum("total_revenue"))
        avg_opportunity = safe_aggregate(overview_data, pl.mean("market_opportunity_index"))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Total States", 
                f"{int(total_states)}", 
                "🗺️",
                "primary",
                "Market Coverage"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Total Customers", 
                f"{int(total_customers):,}", 
                "👥",
                "success",
                "Geographic Customer Base"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Total Revenue", 
                f"${total_revenue:,.0f}", 
                "💰",
                "warning",
                "Geographic Revenue"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Avg Market Opportunity", 
                f"{avg_opportunity:.2f}", 
                "🎯",
                "info",
                "Growth Potential Index"
            ), unsafe_allow_html=True)
    
    # Regional Analysis
    st.header("🌎 Regional Performance Analysis")
    
    if not regional_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue by region
            regional_pd = regional_data.to_pandas()
            fig_regional_revenue = px.pie(
                regional_pd,
                values='region_revenue',
                names='geographic_region',
                title='Revenue Distribution by Region',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_regional_revenue.update_layout(height=400)
            st.plotly_chart(fig_regional_revenue, width="stretch")
        
        with col2:
            # Customer distribution by region
            fig_regional_customers = px.bar(
                regional_pd,
                x='geographic_region',
                y='region_customers',
                title='Customer Distribution by Region',
                color='region_customers',
                color_continuous_scale='Blues'
            )
            fig_regional_customers.update_layout(height=400)
            st.plotly_chart(fig_regional_customers, width="stretch")
    
    # State Performance Analysis
    st.header("🏛️ Top State Performance")
    
    if not overview_data.is_empty():
        # Top 15 states
        top_states = overview_data.head(15)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top states by revenue
            states_pd = top_states.to_pandas()
            fig_states_revenue = px.bar(
                states_pd,
                x='total_revenue',
                y='state_name',
                orientation='h',
                title='Top 15 States by Revenue',
                color='total_revenue',
                color_continuous_scale='Viridis'
            )
            fig_states_revenue.update_layout(height=600)
            st.plotly_chart(fig_states_revenue, width="stretch")
        
        with col2:
            # Market opportunity vs revenue scatter
            fig_opportunity = px.scatter(
                states_pd,
                x='total_revenue',
                y='market_opportunity_index',
                size='total_customers',
                color='market_tier',
                hover_data=['state_name'],
                title='Market Opportunity vs Revenue',
                labels={
                    'total_revenue': 'Total Revenue ($)',
                    'market_opportunity_index': 'Market Opportunity Index'
                }
            )
            fig_opportunity.update_layout(height=600)
            st.plotly_chart(fig_opportunity, width="stretch")
    
    # Market Tier Analysis
    st.header("🎯 Market Tier Performance")
    
    if not tier_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Market tier revenue
            tier_pd = tier_data.to_pandas()
            fig_tier_revenue = px.bar(
                tier_pd,
                x='market_tier',
                y='tier_revenue',
                title='Revenue by Market Tier',
                color='tier_revenue',
                color_continuous_scale='Plasma'
            )
            fig_tier_revenue.update_layout(height=400)
            st.plotly_chart(fig_tier_revenue, width="stretch")
        
        with col2:
            # Opportunity index by tier
            fig_tier_opportunity = px.bar(
                tier_pd,
                x='market_tier',
                y='avg_opportunity_index',
                title='Average Opportunity Index by Tier',
                color='avg_opportunity_index',
                color_continuous_scale='RdYlGn'
            )
            fig_tier_opportunity.update_layout(height=400)
            st.plotly_chart(fig_tier_opportunity, width="stretch")
    
    # State Performance Table
    st.subheader("📊 State Performance Metrics")
    
    if not overview_data.is_empty():
        state_display = overview_data.head(15).select([
            pl.col("state_name").alias("State"),
            pl.col("geographic_region").alias("Region"),
            pl.col("total_customers").alias("Customers"),
            pl.col("total_orders").alias("Orders"),
            pl.col("total_revenue").map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).alias("Revenue"),
            pl.col("average_order_value").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("AOV"),
            pl.col("market_tier").alias("Market Tier"),
            pl.col("market_opportunity_index").map_elements(lambda x: f"{x:.2f}", return_dtype=pl.String).alias("Opportunity Index")
        ])
        
        st.dataframe(state_display, width="stretch")
    
    # Geographic Insights Map
    st.header("🗺️ Geographic Revenue Heatmap")
    
    if not overview_data.is_empty():
        # Create a simple bar chart for state revenue (substitute for map)
        top_states_map = overview_data.head(20)
        states_map_pd = top_states_map.to_pandas()
        
        fig_heatmap = px.bar(
            states_map_pd,
            x='state_code',
            y='total_revenue',
            title='Revenue Distribution Across Top 20 States',
            color='total_revenue',
            color_continuous_scale='Reds',
            hover_data=['state_name', 'total_customers', 'market_tier']
        )
        fig_heatmap.update_layout(height=500)
        st.plotly_chart(fig_heatmap, width="stretch")
    
    # Customer Density Analysis
    st.header("👥 Customer Density Insights")
    
    if not overview_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue per customer by state
            density_data = overview_data.head(15)
            density_pd = density_data.to_pandas()
            
            fig_density = px.bar(
                density_pd,
                x='revenue_per_customer',
                y='state_name',
                orientation='h',
                title='Revenue per Customer by State',
                color='revenue_per_customer',
                color_continuous_scale='Blues'
            )
            fig_density.update_layout(height=500)
            st.plotly_chart(fig_density, width="stretch")
        
        with col2:
            # Customers per city
            fig_city_density = px.bar(
                density_pd,
                x='customers_per_city',
                y='state_name',
                orientation='h',
                title='Customer Density (Customers per City)',
                color='customers_per_city',
                color_continuous_scale='Greens'
            )
            fig_city_density.update_layout(height=500)
            st.plotly_chart(fig_city_density, width="stretch")
    
    # Regional Performance Comparison
    if not regional_data.is_empty():
        st.header("📈 Regional Performance Comparison")
        
        regional_comparison = regional_data.select([
            pl.col("geographic_region").alias("Region"),
            pl.col("states_count").alias("States"),
            pl.col("region_customers").alias("Customers"),
            pl.col("region_revenue").map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).alias("Revenue"),
            pl.col("avg_order_value").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("Avg Order Value"),
            pl.col("avg_review_score").map_elements(lambda x: f"{x:.2f}⭐", return_dtype=pl.String).alias("Avg Review")
        ])
        
        st.dataframe(regional_comparison, width="stretch")
    
    # Key Geographic Insights
    if not overview_data.is_empty() and not tier_data.is_empty():
        st.header("📋 Key Geographic KPIs")
        
        # Calculate insights
        top_state = safe_item(overview_data.head(1).select("state_name"), "N/A")
        
        # Fix the issue with empty dataframes
        high_tier_filter = tier_data.filter(pl.col("market_tier") == "High Tier") if not tier_data.is_empty() else pl.DataFrame()
        high_tier_states = safe_aggregate(high_tier_filter, pl.col("states_count"))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Top State", top_state, "By revenue")
        
        with col2:
            regions_count = regional_data.height if not regional_data.is_empty() else 0
            st.metric("Active Regions", f"{regions_count}", "Geographic coverage")
        
        with col3:
            st.metric("High-Tier States", f"{high_tier_states}", "Premium markets")
        
        with col4:
            avg_revenue_per_state = total_revenue / total_states if total_states > 0 else 0
            st.metric("Avg Revenue/State", f"${avg_revenue_per_state:,.0f}", "Market distribution")
    
    # Footer
    st.markdown("---")
    st.markdown("*🗺️ Geographic Analytics - Driving Location-Based Marketing Strategy*")

# Call main function directly for Streamlit pages
main()
