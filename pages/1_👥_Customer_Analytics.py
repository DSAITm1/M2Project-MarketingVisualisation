"""
Customer Analytics Page
Deep analysis of customer segmentation for marketing directors
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

st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide")

@st.cache_data(ttl=1800)
def get_customer_analytics_data():
    """Get comprehensive customer analytics data"""
    client = get_bigquery_client()
    if not client:
        return None
    
    try:
        # Customer segmentation data
        customer_query = """
        SELECT 
            customer_sk,
            customer_id,
            customer_state,
            customer_city,
            total_orders,
            total_spent,
            avg_order_value,
            avg_review_score,
            customer_segment,
            churn_risk_level,
            satisfaction_tier,
            predicted_annual_clv,
            days_as_customer,
            categories_purchased
        FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
        WHERE total_orders > 0
        ORDER BY total_spent DESC
        """
        
        customer_result = client.query(customer_query).result()
        customer_data = pl.from_pandas(customer_result.to_dataframe())
        
        # Segment summary
        segment_query = """
        SELECT 
            customer_segment,
            COUNT(*) as customer_count,
            ROUND(SUM(total_spent), 2) as segment_revenue,
            ROUND(AVG(total_spent), 2) as avg_customer_value,
            ROUND(AVG(avg_order_value), 2) as avg_order_value,
            ROUND(AVG(predicted_annual_clv), 2) as avg_clv
        FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
        WHERE total_orders > 0 AND customer_segment IS NOT NULL
        GROUP BY customer_segment
        ORDER BY segment_revenue DESC
        """
        
        segment_result = client.query(segment_query).result()
        segment_data = pl.from_pandas(segment_result.to_dataframe())
        
        # Geographic distribution
        geo_query = """
        SELECT 
            customer_state,
            COUNT(*) as customer_count,
            ROUND(SUM(total_spent), 2) as state_revenue,
            ROUND(AVG(total_spent), 2) as avg_customer_value
        FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
        WHERE total_orders > 0
        GROUP BY customer_state
        ORDER BY state_revenue DESC
        LIMIT 10
        """
        
        geo_result = client.query(geo_query).result()
        geo_data = pl.from_pandas(geo_result.to_dataframe())
        
        return {
            'customer_data': customer_data,
            'segment_data': segment_data,
            'geo_data': geo_data
        }
        
    except Exception as e:
        st.error(f"Error loading customer analytics: {str(e)}")
        return None

def create_metric_card(title, value, icon, color="blue"):
    """Create a colored metric card"""
    colors = {
        "blue": "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
        "green": "linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%)",
        "orange": "linear-gradient(90deg, #f093fb 0%, #f5576c 100%)",
        "purple": "linear-gradient(90deg, #4facfe 0%, #00f2fe 100%)"
    }
    
    return f"""
    <div style="
        background: {colors[color]};
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
    """Main customer analytics function"""
    st.title("👥 Customer Analytics")
    st.markdown("**Deep Customer Segmentation Analysis for Marketing Strategy**")
    
    # Load data
    with st.spinner("Loading customer analytics..."):
        data = get_customer_analytics_data()
    
    if not data:
        st.error("Unable to load customer analytics data.")
        return
    
    customer_data = data['customer_data']
    segment_data = data['segment_data']
    geo_data = data['geo_data']
    
    # Overall Customer Metrics
    st.header("📊 Customer Portfolio Overview")
    
    total_customers = customer_data.height
    total_revenue = customer_data.select(pl.sum("total_spent")).item()
    avg_clv = customer_data.select(pl.mean("predicted_annual_clv")).item()
    avg_orders = customer_data.select(pl.mean("total_orders")).item()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Total Customers", 
            f"{total_customers:,}", 
            "👥",
            "blue"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Total Revenue", 
            f"${total_revenue:,.0f}", 
            "💰",
            "green"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "Avg Customer CLV", 
            f"${avg_clv:,.0f}", 
            "🎯",
            "orange"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "Avg Orders/Customer", 
            f"{avg_orders:.1f}", 
            "🛒",
            "purple"
        ), unsafe_allow_html=True)
    
    # Customer Segmentation Analysis
    st.header("🎯 Customer Segmentation Analysis")
    
    if not segment_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Segment revenue pie chart
            segment_pd = segment_data.to_pandas()
            fig_pie = px.pie(
                segment_pd,
                values='segment_revenue',
                names='customer_segment',
                title='Revenue Distribution by Customer Segment',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, width="stretch")
        
        with col2:
            # Customer count by segment
            fig_bar = px.bar(
                segment_pd,
                x='customer_segment',
                y='customer_count',
                title='Customer Count by Segment',
                color='customer_segment',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bar.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_bar, width="stretch")
    
    # Segment Performance Table
    st.subheader("📈 Segment Performance Metrics")
    
    if not segment_data.is_empty():
        segment_display = segment_data.select([
            pl.col("customer_segment").alias("Segment"),
            pl.col("customer_count").alias("Customers"),
            pl.col("segment_revenue").map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).alias("Revenue"),
            pl.col("avg_customer_value").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("Avg Customer Value"),
            pl.col("avg_order_value").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("Avg Order Value"),
            pl.col("avg_clv").map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).alias("Predicted CLV")
        ])
        
        st.dataframe(segment_display, width="stretch")
    
    # Geographic Analysis
    st.header("🗺️ Geographic Customer Distribution")
    
    if not geo_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Top states by revenue
            geo_pd = geo_data.to_pandas()
            fig_geo = px.bar(
                geo_pd,
                x='customer_state',
                y='state_revenue',
                title='Top 10 States by Customer Revenue',
                color='state_revenue',
                color_continuous_scale='Blues'
            )
            fig_geo.update_layout(height=400)
            st.plotly_chart(fig_geo, width="stretch")
        
        with col2:
            # Customer count by state
            fig_count = px.bar(
                geo_pd,
                x='customer_state',
                y='customer_count',
                title='Customer Count by State',
                color='customer_count',
                color_continuous_scale='Greens'
            )
            fig_count.update_layout(height=400)
            st.plotly_chart(fig_count, width="stretch")
    
    # Top Customers Analysis
    st.header("🏆 VIP Customer Analysis")
    
    if not customer_data.is_empty():
        # Top 20 customers
        top_customers = customer_data.head(20)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💎 Top Customers by Revenue")
            
            top_display = top_customers.select([
                pl.col("customer_id").alias("Customer ID"),
                pl.col("customer_state").alias("State"),
                pl.col("total_spent").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("Total Spent"),
                pl.col("total_orders").alias("Orders"),
                pl.col("customer_segment").alias("Segment")
            ]).head(10)
            
            st.dataframe(top_display, width="stretch")
        
        with col2:
            # CLV vs Spending scatter plot
            top_pd = top_customers.to_pandas()
            fig_scatter = px.scatter(
                top_pd,
                x='total_spent',
                y='predicted_annual_clv',
                color='customer_segment',
                size='total_orders',
                title='Customer Value vs Predicted CLV',
                labels={
                    'total_spent': 'Total Spent ($)',
                    'predicted_annual_clv': 'Predicted CLV ($)'
                }
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, width="stretch")
    
    # Marketing Insights and Recommendations
    st.header("💡 Marketing Strategy Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🎯 Customer Acquisition Strategy**
        
        • **Focus on High-Value States**: Target advertising in top-performing states
        
        • **Segment-Specific Campaigns**: Tailor messaging for each customer segment
        
        • **Lookalike Targeting**: Find customers similar to VIP segment profiles
        
        • **Geographic Expansion**: Explore underrepresented high-opportunity areas
        """)
    
    with col2:
        st.markdown("""
        **💰 Revenue Optimization**
        
        • **VIP Customer Retention**: Implement loyalty programs for top spenders
        
        • **Cross-selling Opportunities**: Increase order frequency in existing segments
        
        • **CLV Maximization**: Focus on customers with high predicted lifetime value
        
        • **Segment Migration**: Help lower-tier customers move up segments
        """)
    
    with col3:
        st.markdown("""
        **📊 Actionable Next Steps**
        
        • **Personalized Campaigns**: Create segment-specific email campaigns
        
        • **Regional Marketing**: Allocate budget based on state performance
        
        • **Customer Journey Optimization**: Improve experience for each segment
        
        • **Predictive Targeting**: Use CLV models for customer acquisition
        """)
    
    # Quick Stats Summary
    if not segment_data.is_empty():
        st.header("📋 Key Performance Indicators")
        
        # Calculate some KPIs
        vip_customers = segment_data.filter(pl.col("customer_segment").str.contains("VIP|High")).select(pl.sum("customer_count")).item() if not segment_data.is_empty() else 0
        vip_percentage = (vip_customers / total_customers * 100) if total_customers > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("VIP Customer Rate", f"{vip_percentage:.1f}%", "Target: 15%+")
        
        with col2:
            avg_customer_value = total_revenue / total_customers if total_customers > 0 else 0
            st.metric("Avg Customer Value", f"${avg_customer_value:.2f}", "Growing")
        
        with col3:
            top_state_revenue = geo_data.select(pl.max("state_revenue")).item() if not geo_data.is_empty() else 0
            st.metric("Top State Revenue", f"${top_state_revenue:,.0f}", "São Paulo leader")
        
        with col4:
            segments_count = segment_data.height
            st.metric("Active Segments", f"{segments_count}", "Well distributed")
    
    # Footer
    st.markdown("---")
    st.markdown("*🎯 Customer Analytics - Driving Marketing Strategy Through Data*")

# Call main function directly for Streamlit pages
main()
