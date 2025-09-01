"""
Review Analytics Page
Customer review sentiment and satisfaction analysis
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

st.set_page_config(page_title="Review Analytics", page_icon="⭐", layout="wide")

@st.cache_data(ttl=1800)
def get_review_overview_data():
    """Get review analytics overview data using BigQuery SQL"""
    client = get_bigquery_client()
    
    query = """
    WITH review_analytics AS (
        SELECT 
            r.review_id,
            r.review_score,
            CASE 
                WHEN r.review_creation_date IS NULL OR TRIM(CAST(r.review_creation_date AS STRING)) = ''
                THEN NULL 
                ELSE TIMESTAMP(r.review_creation_date)
            END as review_creation_date,
            CASE 
                WHEN r.review_answer_timestamp IS NULL OR TRIM(CAST(r.review_answer_timestamp AS STRING)) = ''
                THEN NULL 
                ELSE TIMESTAMP(r.review_answer_timestamp) 
            END as review_answer_timestamp,
            r.review_comment_title,
            r.review_comment_message,
            COALESCE(o.order_value, 0) as order_value,
            c.customer_state
        FROM `project-olist-470307.dbt_olist_dwh.dim_order_reviews` r
        LEFT JOIN `project-olist-470307.dbt_olist_dwh.fact_orders` o 
            ON r.order_sk = o.order_sk
        LEFT JOIN `project-olist-470307.dbt_olist_dwh.dim_customers` c
            ON o.customer_sk = c.customer_sk
        WHERE r.review_score IS NOT NULL
    ),
    
    review_overview AS (
        SELECT 
            COUNT(*) as total_reviews,
            ROUND(AVG(review_score), 2) as avg_rating,
            COUNT(CASE WHEN review_score >= 4 THEN 1 END) as positive_reviews,
            COUNT(CASE WHEN review_score <= 2 THEN 1 END) as negative_reviews,
            COUNT(CASE WHEN review_comment_message IS NOT NULL 
                      AND TRIM(review_comment_message) != '' THEN 1 END) as reviews_with_comments,
            ROUND(AVG(order_value), 2) as avg_order_value_per_review
        FROM review_analytics
    ),
    
    monthly_reviews AS (
        SELECT 
            EXTRACT(YEAR FROM review_creation_date) as year,
            EXTRACT(MONTH FROM review_creation_date) as month,
            COUNT(*) as review_count,
            ROUND(AVG(review_score), 2) as avg_monthly_rating
        FROM review_analytics
        WHERE review_creation_date IS NOT NULL
        GROUP BY year, month
        ORDER BY year DESC, month DESC
        LIMIT 24
    ),
    
    score_distribution AS (
        SELECT 
            review_score,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM review_analytics
        GROUP BY review_score
        ORDER BY review_score
    ),
    
    state_reviews AS (
        SELECT 
            customer_state,
            COUNT(*) as review_count,
            ROUND(AVG(review_score), 2) as avg_rating,
            COUNT(CASE WHEN review_score >= 4 THEN 1 END) as positive_count
        FROM review_analytics
        WHERE customer_state IS NOT NULL
        GROUP BY customer_state
        HAVING COUNT(*) >= 100
        ORDER BY review_count DESC
        LIMIT 15
    )
    
    SELECT 
        'overview' as data_type,
        NULL as year, NULL as month, NULL as review_score, NULL as customer_state,
        total_reviews, avg_rating, positive_reviews, negative_reviews, 
        reviews_with_comments, avg_order_value_per_review,
        NULL as review_count, NULL as percentage, NULL as positive_count
    FROM review_overview
    
    UNION ALL
    
    SELECT 
        'monthly' as data_type,
        year, month, NULL as review_score, NULL as customer_state,
        NULL as total_reviews, avg_monthly_rating as avg_rating, 
        NULL as positive_reviews, NULL as negative_reviews,
        NULL as reviews_with_comments, NULL as avg_order_value_per_review,
        review_count, NULL as percentage, NULL as positive_count
    FROM monthly_reviews
    
    UNION ALL
    
    SELECT 
        'distribution' as data_type,
        NULL as year, NULL as month, review_score, NULL as customer_state,
        NULL as total_reviews, NULL as avg_rating, NULL as positive_reviews, NULL as negative_reviews,
        NULL as reviews_with_comments, NULL as avg_order_value_per_review,
        count as review_count, percentage, NULL as positive_count
    FROM score_distribution
    
    UNION ALL
    
    SELECT 
        'state' as data_type,
        NULL as year, NULL as month, NULL as review_score, customer_state,
        NULL as total_reviews, avg_rating, NULL as positive_reviews, NULL as negative_reviews,
        NULL as reviews_with_comments, NULL as avg_order_value_per_review,
        review_count, NULL as percentage, positive_count
    FROM state_reviews
    
    ORDER BY data_type, year DESC, month DESC, review_score, review_count DESC
    """
    
    try:
        job = client.query(query)
        results = job.result()
        df = pl.from_pandas(results.to_dataframe())
        return df
    except Exception as e:
        st.error(f"Error loading review data: {str(e)}")
        return pl.DataFrame()

def format_percentage_polars(df, col):
    """Format percentage using Polars (10% processing)"""
    return df.with_columns(
        pl.col(col).map_elements(lambda x: f"{x:.1f}%" if x is not None else "0%", return_dtype=pl.Utf8)
    )

def format_currency_polars(df, col):
    """Format currency using Polars (10% processing)"""
    return df.with_columns(
        pl.col(col).map_elements(lambda x: f"${x:,.2f}" if x is not None else "$0.00", return_dtype=pl.Utf8)
    )

def display_review_overview(df):
    """Display review overview metrics"""
    overview_data = df.filter(pl.col("data_type") == "overview")
    
    if overview_data.height > 0:
        row = overview_data.row(0, named=True)
        
        # Create metric cards
        metrics = [
            ("Total Reviews", f"{row['total_reviews']:,}", "📊"),
            ("Average Rating", f"{row['avg_rating']:.2f}/5", "⭐"),
            ("Positive Reviews", f"{row['positive_reviews']:,}", "👍"),
            ("With Comments", f"{row['reviews_with_comments']:,}", "💬")
        ]
        
        create_metric_cards(metrics)

def display_review_trends(df):
    """Display monthly review trends"""
    monthly_data = df.filter(pl.col("data_type") == "monthly")
    
    if monthly_data.height > 0:
        # Sort and prepare data for visualization
        monthly_sorted = monthly_data.sort(["year", "month"])
        
        # Convert to pandas for Plotly (final 10% processing)
        monthly_pd = monthly_sorted.to_pandas()
        monthly_pd['month_year'] = monthly_pd['year'].astype(str) + '-' + monthly_pd['month'].astype(str).str.zfill(2)
        
        fig = px.line(
            monthly_pd, 
            x='month_year', 
            y='review_count',
            title='Monthly Review Volume Trends',
            labels={'review_count': 'Number of Reviews', 'month_year': 'Month-Year'}
        )
        fig.update_layout(height=400)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig, use_container_width=True)
        
        # Average rating trend
        fig2 = px.line(
            monthly_pd,
            x='month_year',
            y='avg_rating',
            title='Monthly Average Rating Trends',
            labels={'avg_rating': 'Average Rating', 'month_year': 'Month-Year'}
        )
        fig2.update_layout(height=400)
        
        with col2:
            st.plotly_chart(fig2, use_container_width=True)

def display_score_distribution(df):
    """Display review score distribution"""
    distribution_data = df.filter(pl.col("data_type") == "distribution")
    
    if distribution_data.height > 0:
        # Format percentages using Polars (10% processing)
        formatted_data = format_percentage_polars(distribution_data, "percentage")
        
        # Convert to pandas for visualization
        dist_pd = formatted_data.to_pandas()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                dist_pd,
                x='review_score',
                y='review_count',
                title='Review Score Distribution',
                labels={'review_score': 'Rating', 'review_count': 'Number of Reviews'},
                text='review_count'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig2 = px.pie(
                dist_pd,
                values='review_count',
                names='review_score',
                title='Review Score Percentage',
                labels={'review_score': 'Rating'}
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)

def display_state_analysis(df):
    """Display review analysis by state"""
    state_data = df.filter(pl.col("data_type") == "state")
    
    if state_data.height > 0:
        # Convert to pandas for visualization
        state_pd = state_data.to_pandas()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                state_pd,
                x='customer_state',
                y='review_count',
                title='Review Volume by State (Top 15)',
                labels={'customer_state': 'State', 'review_count': 'Number of Reviews'},
                text='review_count'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig2 = px.bar(
                state_pd,
                x='customer_state',
                y='avg_rating',
                title='Average Rating by State',
                labels={'customer_state': 'State', 'avg_rating': 'Average Rating'},
                text=state_pd['avg_rating'].round(2)
            )
            fig2.update_traces(textposition='outside')
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Display detailed table
        st.subheader("State Review Details")
        display_cols = ['customer_state', 'review_count', 'avg_rating', 'positive_count']
        st.dataframe(state_pd[display_cols], use_container_width=True)

def main():
    """Main function for Review Analytics page"""
    st.title("⭐ Review Analytics")
    st.markdown("Customer review sentiment and satisfaction analysis")
    
    # Load data
    with st.spinner("Loading review analytics data..."):
        df = get_review_overview_data()
    
    if df.height == 0:
        st.warning("No review data available")
        return
    
    # Overview metrics
    st.header("📊 Review Overview")
    display_review_overview(df)
    
    # Review trends
    st.header("📈 Review Trends")
    display_review_trends(df)
    
    # Score analysis
    st.header("⭐ Score Analysis")
    display_score_distribution(df)
    
    # Geographic analysis
    st.header("🗺️ Geographic Analysis")
    display_state_analysis(df)

if __name__ == "__main__":
    main()
