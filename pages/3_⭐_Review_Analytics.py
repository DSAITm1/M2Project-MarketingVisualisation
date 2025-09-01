"""
Review Analytics Page
Deep analysis of customer reviews and satisfaction
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

st.set_page_config(page_title="Review Analytics", page_icon="⭐", layout="wide")

@st.cache_data(ttl=1800)
def get_review_analytics_data():
    """Get comprehensive review analytics data"""
    client = get_bigquery_client()
    if not client:
        return None
    
    try:
        # Review overview using both revenue and customer analytics tables
        review_query = """
        SELECT 
            r.order_id,
            r.customer_id,
            r.product_category_english as product_category_name,
            r.review_score,
            r.seller_state,
            r.allocated_payment as payment_value,
            r.year_month,
            r.customer_state,
            r.satisfaction_level
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt` r
        WHERE r.review_score IS NOT NULL
        ORDER BY r.order_date DESC
        LIMIT 100000
        """
        
        review_result = client.query(review_query).result()
        review_data = pl.from_pandas(review_result.to_dataframe())
        
        # Review trends by month
        monthly_query = """
        SELECT 
            year_month,
            CAST(COUNT(*) AS INT64) as review_count,
            ROUND(AVG(review_score), 2) as avg_review_score,
            CAST(COUNT(CASE WHEN review_score >= 4 THEN 1 END) AS INT64) as positive_reviews,
            CAST(COUNT(CASE WHEN review_score <= 2 THEN 1 END) AS INT64) as negative_reviews
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE review_score IS NOT NULL
        GROUP BY year_month
        ORDER BY year_month
        """
        
        monthly_result = client.query(monthly_query).result()
        monthly_data = pl.from_pandas(monthly_result.to_dataframe())
        
        # Category review performance
        category_query = """
        SELECT 
            product_category_english as product_category_name,
            CAST(COUNT(*) AS INT64) as review_count,
            ROUND(AVG(review_score), 2) as avg_review_score,
            CAST(COUNT(CASE WHEN review_score >= 4 THEN 1 END) AS INT64) as positive_reviews,
            CAST(COUNT(CASE WHEN review_score <= 2 THEN 1 END) AS INT64) as negative_reviews,
            ROUND(AVG(allocated_payment), 2) as avg_order_value
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE review_score IS NOT NULL AND product_category_english IS NOT NULL
        GROUP BY product_category_english
        ORDER BY review_count DESC
        LIMIT 20
        """
        
        category_result = client.query(category_query).result()
        category_data = pl.from_pandas(category_result.to_dataframe())
        
        # Customer satisfaction analysis
        satisfaction_query = """
        SELECT 
            satisfaction_level as satisfaction_tier,
            CAST(COUNT(DISTINCT customer_id) AS INT64) as customer_count,
            ROUND(AVG(review_score), 2) as avg_review_score,
            ROUND(SUM(allocated_payment), 2) as total_revenue,
            ROUND(AVG(allocated_payment), 2) as avg_customer_value
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE satisfaction_level IS NOT NULL
        GROUP BY satisfaction_level
        ORDER BY avg_review_score DESC
        """
        
        satisfaction_result = client.query(satisfaction_query).result()
        satisfaction_data = pl.from_pandas(satisfaction_result.to_dataframe())
        
        return {
            'review_data': review_data,
            'monthly_data': monthly_data,
            'category_data': category_data,
            'satisfaction_data': satisfaction_data
        }
        
    except Exception as e:
        st.error(f"Error loading review analytics: {str(e)}")
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
    """Main review analytics function"""
    st.title("⭐ Review Analytics")
    st.markdown("**Customer Satisfaction and Review Analysis**")
    
    # Load data
    with st.spinner("Loading review analytics..."):
        data = get_review_analytics_data()
    
    if not data:
        st.error("Unable to load review analytics data.")
        return
    
    review_data = data['review_data']
    monthly_data = data['monthly_data']
    category_data = data['category_data']
    satisfaction_data = data['satisfaction_data']
    
    # Overall Review Metrics
    st.header("📊 Review Performance Overview")
    st.markdown("### Core Review Metrics")
    
    if not review_data.is_empty():
        total_reviews = review_data.height
        avg_rating = safe_aggregate(review_data, pl.mean("review_score"))
        positive_reviews = review_data.filter(pl.col("review_score") >= 4).height
        negative_reviews = review_data.filter(pl.col("review_score") <= 2).height
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Total Reviews", 
                f"{int(total_reviews):,}", 
                "⭐",
                "primary",
                "Customer Feedback Count"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "Average Rating", 
                f"{avg_rating:.2f}/5", 
                "📊",
                "success",
                "Overall Satisfaction Score"
            ), unsafe_allow_html=True)
        
        with col3:
            positive_rate = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0
            st.markdown(create_metric_card(
                "Positive Reviews", 
                f"{positive_rate:.1f}%", 
                "👍",
                "warning",
                "4-5 Star Ratings"
            ), unsafe_allow_html=True)
        
        with col4:
            negative_rate = (negative_reviews / total_reviews * 100) if total_reviews > 0 else 0
            st.markdown(create_metric_card(
                "Negative Reviews", 
                f"{negative_rate:.1f}%", 
                "👎",
                "info",
                "1-2 Star Ratings"
            ), unsafe_allow_html=True)
    
    # Review Score Distribution
    st.header("📈 Review Score Distribution")
    
    if not review_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Review score distribution
            score_distribution = review_data.group_by("review_score").agg([
                pl.count("order_id").alias("count")
            ]).sort("review_score")
            
            score_pd = score_distribution.to_pandas()
            fig_distribution = px.bar(
                score_pd,
                x='review_score',
                y='count',
                title='Review Score Distribution',
                color='count',
                color_continuous_scale='RdYlGn'
            )
            fig_distribution.update_layout(height=400)
            st.plotly_chart(fig_distribution, width="stretch")
        
        with col2:
            # Review score pie chart
            score_categories = review_data.with_columns([
                pl.when(pl.col("review_score") >= 4).then(pl.lit("Positive (4-5)"))
                .when(pl.col("review_score") == 3).then(pl.lit("Neutral (3)"))
                .otherwise(pl.lit("Negative (1-2)")).alias("score_category")
            ]).group_by("score_category").agg([
                pl.count("order_id").alias("count")
            ])
            
            categories_pd = score_categories.to_pandas()
            fig_pie = px.pie(
                categories_pd,
                values='count',
                names='score_category',
                title='Review Sentiment Distribution',
                color_discrete_sequence=['#ff4444', '#ffaa00', '#44ff44']
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, width="stretch")
    
    # Monthly Review Trends
    st.header("📅 Review Trends Over Time")
    
    if not monthly_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Average rating trend
            monthly_pd = monthly_data.to_pandas()
            fig_rating_trend = px.line(
                monthly_pd,
                x='year_month',
                y='avg_review_score',
                title='Average Review Score Trend',
                color_discrete_sequence=['#1f77b4']
            )
            fig_rating_trend.update_layout(height=400)
            st.plotly_chart(fig_rating_trend, width="stretch")
        
        with col2:
            # Review volume trend
            fig_volume_trend = px.line(
                monthly_pd,
                x='year_month',
                y='review_count',
                title='Review Volume Trend',
                color_discrete_sequence=['#2ca02c']
            )
            fig_volume_trend.update_layout(height=400)
            st.plotly_chart(fig_volume_trend, width="stretch")
    
    # Category Review Analysis
    st.header("🏷️ Category Review Performance")
    
    if not category_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Top categories by review score
            top_categories = category_data.head(10)
            categories_pd = top_categories.to_pandas()
            
            fig_cat_scores = px.bar(
                categories_pd,
                x='avg_review_score',
                y='product_category_name',
                orientation='h',
                title='Top 10 Categories by Average Review Score',
                color='avg_review_score',
                color_continuous_scale='RdYlGn'
            )
            fig_cat_scores.update_layout(height=500)
            st.plotly_chart(fig_cat_scores, width="stretch")
        
        with col2:
            # Review volume by category
            fig_cat_volume = px.bar(
                categories_pd,
                x='review_count',
                y='product_category_name',
                orientation='h',
                title='Review Count by Category',
                color='review_count',
                color_continuous_scale='Blues'
            )
            fig_cat_volume.update_layout(height=500)
            st.plotly_chart(fig_cat_volume, width="stretch")
    
    # Category Performance Table
    st.subheader("📊 Category Review Metrics")
    
    if not category_data.is_empty():
        category_display = category_data.head(15).select([
            pl.col("product_category_name").alias("Category"),
            pl.col("review_count").alias("Reviews"),
            pl.col("avg_review_score").map_elements(lambda x: f"{x:.2f}⭐", return_dtype=pl.String).alias("Avg Rating"),
            pl.col("positive_reviews").alias("Positive"),
            pl.col("negative_reviews").alias("Negative"),
            pl.col("avg_order_value").map_elements(lambda x: f"${x:.2f}", return_dtype=pl.String).alias("Avg Order Value")
        ])
        
        st.dataframe(category_display, width="stretch")
    
    # Customer Satisfaction Analysis
    st.header("😊 Customer Satisfaction Tiers")
    
    if not satisfaction_data.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            # Satisfaction tier distribution
            satisfaction_pd = satisfaction_data.to_pandas()
            fig_satisfaction = px.pie(
                satisfaction_pd,
                values='customer_count',
                names='satisfaction_tier',
                title='Customer Distribution by Satisfaction Tier',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_satisfaction.update_layout(height=400)
            st.plotly_chart(fig_satisfaction, width="stretch")
        
        with col2:
            # Revenue by satisfaction tier
            fig_satisfaction_revenue = px.bar(
                satisfaction_pd,
                x='satisfaction_tier',
                y='total_revenue',
                title='Revenue by Satisfaction Tier',
                color='total_revenue',
                color_continuous_scale='Greens'
            )
            fig_satisfaction_revenue.update_layout(height=400)
            st.plotly_chart(fig_satisfaction_revenue, width="stretch")
    
    # Geographic Review Analysis
    st.header("🗺️ Geographic Review Patterns")
    
    if not review_data.is_empty():
        # State-wise review analysis
        state_reviews = review_data.group_by("customer_state").agg([
            pl.count("order_id").alias("review_count"),
            pl.mean("review_score").alias("avg_rating"),
            pl.sum("payment_value").alias("total_revenue")
        ]).sort("review_count", descending=True).head(15)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top states by review count
            state_pd = state_reviews.to_pandas()
            fig_state_reviews = px.bar(
                state_pd,
                x='customer_state',
                y='review_count',
                title='Review Count by State (Top 15)',
                color='review_count',
                color_continuous_scale='Blues'
            )
            fig_state_reviews.update_layout(height=400)
            st.plotly_chart(fig_state_reviews, width="stretch")
        
        with col2:
            # Average rating by state
            fig_state_rating = px.bar(
                state_pd,
                x='customer_state',
                y='avg_rating',
                title='Average Rating by State',
                color='avg_rating',
                color_continuous_scale='RdYlGn'
            )
            fig_state_rating.update_layout(height=400)
            st.plotly_chart(fig_state_rating, width="stretch")
    
    # Review Performance Insights
    if not satisfaction_data.is_empty() and not category_data.is_empty():
        st.header("📋 Key Review Insights")
        
        # Calculate insights
        top_category = safe_item(category_data.head(1).select("product_category_name"), "N/A")
        high_satisfaction_filter = satisfaction_data.filter(pl.col("satisfaction_tier").str.contains("High")) if not satisfaction_data.is_empty() else pl.DataFrame()
        high_satisfaction = safe_aggregate(high_satisfaction_filter, pl.col("customer_count").sum())
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Best Category", top_category, "By review volume")
        
        with col2:
            satisfaction_rate = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0
            st.metric("Satisfaction Rate", f"{satisfaction_rate:.1f}%", "4-5 star reviews")
        
        with col3:
            st.metric("High Satisfaction", f"{high_satisfaction:,}", "Customers")
        
        with col4:
            avg_monthly_reviews = safe_aggregate(monthly_data, pl.mean("review_count"))
            st.metric("Monthly Reviews", f"{avg_monthly_reviews:,.0f}", "Average volume")
    
    # Footer
    st.markdown("---")
    st.markdown("*⭐ Review Analytics - Enhancing Customer Satisfaction Through Insights*")

# Call main function directly for Streamlit pages
main()
