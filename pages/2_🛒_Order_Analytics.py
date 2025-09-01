"""
Order Analytics Page
Deep analysis of order trends and delivery performance
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

from utils.database import get_bigquery_client
from utils.data_processing import safe_aggregate, safe_item

st.set_page_config(page_title="Order Analytics", page_icon="🛒", layout="wide")

@st.cache_data(ttl=1800)
def get_order_analytics_data():
    """Get comprehensive order analytics data using revenue_analytics_obt"""
    client = get_bigquery_client()
    if not client:
        st.error("Failed to connect to BigQuery")
        return None
    
    try:
        # Order metrics query using revenue_analytics_obt
        order_query = """
        SELECT 
            order_id,
            customer_id,
            order_status,
            order_date,
            product_id,
            product_category_english as product_category_name,
            seller_id,
            seller_state,
            seller_city,
            item_price as price,
            freight_cost as freight_value,
            payment_type,
            payment_installments,
            allocated_payment as payment_value,
            review_score,
            year_month,
            satisfaction_level,
            shipping_complexity
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE order_status IN ('delivered', 'shipped', 'invoiced', 'processing')
        ORDER BY order_date DESC
        LIMIT 50000
        """
        
        order_result = client.query(order_query).result()
        order_data = pl.from_pandas(order_result.to_dataframe())
        
        if order_data.is_empty():
            st.warning("No order data found")
            return None
        
        # Monthly trends
        monthly_query = """
        SELECT 
            year_month,
            CAST(COUNT(DISTINCT order_id) AS INT64) as order_count,
            ROUND(SUM(allocated_payment), 2) as total_revenue,
            ROUND(AVG(allocated_payment), 2) as avg_order_value,
            CAST(COUNT(DISTINCT customer_id) AS INT64) as unique_customers
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE order_status IN ('delivered', 'shipped', 'invoiced', 'processing')
        GROUP BY year_month
        ORDER BY year_month
        """
        
        monthly_result = client.query(monthly_query).result()
        monthly_data = pl.from_pandas(monthly_result.to_dataframe())
        
        # Category performance
        category_query = """
        SELECT 
            product_category_english as product_category_name,
            CAST(COUNT(DISTINCT order_id) AS INT64) as order_count,
            ROUND(SUM(allocated_payment), 2) as category_revenue,
            ROUND(AVG(allocated_payment), 2) as avg_order_value,
            ROUND(AVG(review_score), 2) as avg_review_score
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE order_status = 'delivered' AND product_category_english IS NOT NULL
        GROUP BY product_category_english
        ORDER BY category_revenue DESC
        LIMIT 15
        """
        
        category_result = client.query(category_query).result()
        category_data = pl.from_pandas(category_result.to_dataframe())
        
        # Delivery performance (using available satisfaction_level)
        delivery_query = """
        SELECT 
            satisfaction_level as delivery_performance,
            CAST(COUNT(DISTINCT order_id) AS INT64) as order_count,
            ROUND(AVG(review_score), 2) as avg_review_score,
            ROUND(COUNT(DISTINCT order_id) * 100.0 / SUM(COUNT(DISTINCT order_id)) OVER(), 2) as percentage
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE order_status = 'delivered' AND satisfaction_level IS NOT NULL
        GROUP BY satisfaction_level
        ORDER BY order_count DESC
        """
        
        delivery_result = client.query(delivery_query).result()
        delivery_data = pl.from_pandas(delivery_result.to_dataframe())
        
        return {
            'order_data': order_data,
            'monthly_data': monthly_data,
            'category_data': category_data,
            'delivery_data': delivery_data
        }
        
    except Exception as e:
        st.error(f"Error loading order analytics: {str(e)}")
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
    """Main order analytics function"""
    st.title("🛒 Order Analytics")
    st.markdown("**Deep Analysis of Order Trends and Performance**")
    
    # Load data
    with st.spinner("Loading order analytics..."):
        data = get_order_analytics_data()
    
    if not data:
        st.error("Unable to load order analytics data. Please check your database connection and try again.")
        st.info("Debug info: Make sure BigQuery credentials are properly configured.")
        return
    
    order_data = data['order_data']
    monthly_data = data['monthly_data']
    category_data = data['category_data']
    delivery_data = data['delivery_data']
    
    # Check if we have any data
    if order_data.is_empty():
        st.warning("No order data available for analysis.")
        return
    
    # Overall Order Metrics
    st.header("📊 Order Performance Overview")
    st.markdown("### Core Order Metrics")
    
    if not order_data.is_empty():
        total_orders = safe_aggregate(order_data, pl.n_unique("order_id"))
        total_revenue = safe_aggregate(order_data, pl.sum("payment_value"))
        avg_order_value = safe_aggregate(order_data, pl.mean("payment_value"))
        unique_customers = safe_aggregate(order_data, pl.n_unique("customer_id"))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Total Orders", 
                f"{int(total_orders):,}", 
                "🛒",
                "primary",
                "Completed Transactions"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Total Revenue", 
                f"${total_revenue:,.0f}", 
                "💰",
                "success",
                "Order Generated Revenue"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                "Avg Order Value", 
                f"${avg_order_value:.2f}", 
                "📈",
                "warning",
                "Revenue per Order"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Unique Customers", 
                f"{int(unique_customers):,}", 
                "👥",
                "info",
                "Active Order Customers"
            ), unsafe_allow_html=True)
    
    # Monthly Trends Analysis
    st.header("📈 Order Trends Over Time")
    
    if not monthly_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly order count
            monthly_pd = monthly_data.to_pandas()
            fig_orders = px.line(
                monthly_pd,
                x='year_month',
                y='order_count',
                title='Monthly Order Count Trend',
                color_discrete_sequence=['#1f77b4']
            )
            fig_orders.update_layout(height=400)
            st.plotly_chart(fig_orders, width="stretch")
        
        with col2:
            # Monthly revenue
            fig_revenue = px.line(
                monthly_pd,
                x='year_month',
                y='total_revenue',
                title='Monthly Revenue Trend',
                color_discrete_sequence=['#2ca02c']
            )
            fig_revenue.update_layout(height=400)
            st.plotly_chart(fig_revenue, width="stretch")
        
        # Average order value trend
        fig_aov = px.line(
            monthly_pd,
            x='year_month',
            y='avg_order_value',
            title='Average Order Value Trend',
            color_discrete_sequence=['#ff7f0e']
        )
        fig_aov.update_layout(height=400)
        st.plotly_chart(fig_aov, width="stretch")
    
    # Category Performance Analysis
    st.header("🏷️ Product Category Performance")
    
    if not category_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Top categories by revenue
            category_pd = category_data.head(10).to_pandas()
            fig_cat_revenue = px.bar(
                category_pd,
                x='category_revenue',
                y='product_category_name',
                orientation='h',
                title='Top 10 Categories by Revenue',
                color='category_revenue',
                color_continuous_scale='Blues'
            )
            fig_cat_revenue.update_layout(height=500)
            st.plotly_chart(fig_cat_revenue, use_container_width=True)
        
        with col2:
            # Category order count
            fig_cat_orders = px.bar(
                category_pd,
                x='order_count',
                y='product_category_name',
                orientation='h',
                title='Top 10 Categories by Order Count',
                color='order_count',
                color_continuous_scale='Greens'
            )
            fig_cat_orders.update_layout(height=500)
            st.plotly_chart(fig_cat_orders, use_container_width=True)
    
    # Category Performance Table
    st.subheader("📊 Category Performance Metrics")
    
    if not category_data.is_empty():
        category_display = category_data.head(10).select([
            pl.col("product_category_name").alias("Category"),
            pl.col("order_count").alias("Orders"),
            pl.col("category_revenue").map_elements(lambda x: f"${x:,.0f}", return_dtype=pl.String).alias("Revenue"),
            pl.col("avg_order_value").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("Avg Order Value"),
            pl.col("avg_review_score").map_elements(lambda x: f"{x:.2f}⭐", return_dtype=pl.String).alias("Avg Review")
        ])
        
        st.dataframe(category_display, use_container_width=True)
    
    # Delivery Performance Analysis
    st.header("🚚 Delivery Performance Analysis")
    
    if not delivery_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Delivery performance distribution
            delivery_pd = delivery_data.to_pandas()
            fig_delivery = px.pie(
                delivery_pd,
                values='order_count',
                names='delivery_performance',
                title='Delivery Performance Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_delivery.update_layout(height=400)
            st.plotly_chart(fig_delivery, use_container_width=True)
        
        with col2:
            # Review scores by delivery performance
            fig_review = px.bar(
                delivery_pd,
                x='delivery_performance',
                y='avg_review_score',
                title='Review Scores by Delivery Performance',
                color='avg_review_score',
                color_continuous_scale='RdYlGn'
            )
            fig_review.update_layout(height=400)
            st.plotly_chart(fig_review, use_container_width=True)
    
    # Payment Analysis
    st.header("💳 Payment Analysis")
    
    if not order_data.is_empty():
        # Payment type distribution
        payment_summary = order_data.group_by("payment_type").agg([
            pl.count("order_id").alias("order_count"),
            pl.sum("payment_value").alias("total_revenue"),
            pl.mean("payment_value").alias("avg_payment")
        ]).sort("total_revenue", descending=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Payment type revenue
            payment_pd = payment_summary.to_pandas()
            fig_payment = px.pie(
                payment_pd,
                values='total_revenue',
                names='payment_type',
                title='Revenue by Payment Type',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_payment.update_layout(height=400)
            st.plotly_chart(fig_payment, use_container_width=True)
        
        with col2:
            # Installment analysis
            installment_summary = order_data.group_by("payment_installments").agg([
                pl.count("order_id").alias("order_count"),
                pl.mean("payment_value").alias("avg_payment")
            ]).sort("payment_installments")
            
            installment_pd = installment_summary.head(10).to_pandas()
            fig_installments = px.bar(
                installment_pd,
                x='payment_installments',
                y='order_count',
                title='Order Count by Payment Installments',
                color='order_count',
                color_continuous_scale='Blues'
            )
            fig_installments.update_layout(height=400)
            st.plotly_chart(fig_installments, use_container_width=True)
    
    # Geographic Analysis
    st.header("🗺️ Geographic Order Distribution")
    
    if not order_data.is_empty():
        # State-wise analysis
        state_summary = order_data.group_by("seller_state").agg([
            pl.count("order_id").alias("order_count"),
            pl.sum("payment_value").alias("total_revenue"),
            pl.mean("review_score").alias("avg_review")
        ]).sort("total_revenue", descending=True).head(15)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top states by revenue
            state_pd = state_summary.to_pandas()
            fig_state_revenue = px.bar(
                state_pd,
                x='seller_state',
                y='total_revenue',
                title='Top 15 States by Revenue',
                color='total_revenue',
                color_continuous_scale='Viridis'
            )
            fig_state_revenue.update_layout(height=400)
            st.plotly_chart(fig_state_revenue, use_container_width=True)
        
        with col2:
            # State order count
            fig_state_orders = px.bar(
                state_pd,
                x='seller_state',
                y='order_count',
                title='Order Count by State',
                color='order_count',
                color_continuous_scale='Plasma'
            )
            fig_state_orders.update_layout(height=400)
            st.plotly_chart(fig_state_orders, use_container_width=True)
    
    # Quick Order Insights
    if not monthly_data.is_empty() and not category_data.is_empty():
        st.header("📋 Key Order Insights")
        
        # Calculate insights
        recent_growth = 0
        if monthly_data.height >= 2:
            latest_revenue = safe_item(monthly_data.tail(1).select("total_revenue"))
            previous_revenue = safe_item(monthly_data.tail(2).head(1).select("total_revenue"))
            recent_growth = ((latest_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        top_category = safe_item(category_data.head(1).select("product_category_name"), "N/A")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Recent Growth", f"{recent_growth:.1f}%", f"Month-over-month")
        
        with col2:
            st.metric("Top Category", top_category, "By revenue")
        
        with col3:
            delivery_filter = delivery_data.filter(pl.col("delivery_performance") == "high") if not delivery_data.is_empty() else pl.DataFrame()
            delivery_rate = safe_aggregate(delivery_filter, pl.col("percentage"))
            st.metric("High Satisfaction", f"{delivery_rate:.1f}%", "Performance")
        
        with col4:
            avg_installments = safe_aggregate(order_data, pl.mean("payment_installments"))
            st.metric("Avg Installments", f"{avg_installments:.1f}", "Payment flexibility")
    
    # Footer
    st.markdown("---")
    st.markdown("*🛒 Order Analytics - Optimizing Order Management and Growth*")

# Call main function directly for Streamlit pages
main()
