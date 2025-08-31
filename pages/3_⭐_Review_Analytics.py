"""
Review Analytics Page
Customer review sentiment and satisfaction analysis
"""

import streamlit as st
import pandas as pd
from pandas import DatetimeTZDtype
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
from google.auth import default
import json
from datetime import datetime

st.set_page_config(page_title="Review Analytics", page_icon="⭐", layout="wide")

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
def load_review_analytics():
    """Load review analytics from BigQuery"""
    config = load_config()
    client = get_bigquery_client()
    
    query = f"""
    WITH review_analytics AS (
        SELECT 
            r.review_id,
            oi.order_id,
            oi.review_score,
            r.review_comment_title,
            r.review_comment_message,
            r.review_creation_date,
            r.review_answer_timestamp,
            o.order_status,
            o.order_purchase_timestamp,
            o.order_delivered_customer_date,
            c.customer_state,
            c.customer_city,
            SUM(oi.price) as order_value,
            COUNT(oi.order_item_id) as item_count
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_order_reviews` r
            ON oi.review_sk = r.review_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
            ON oi.order_sk = o.order_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c 
            ON oi.customer_sk = c.customer_sk
        WHERE oi.review_score IS NOT NULL
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
    )
    SELECT * FROM review_analytics
    LIMIT 10000
    """
    
    try:
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error loading review analytics: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("⭐ Review Analytics")
    st.markdown("**Customer satisfaction and review sentiment analysis**")
    
    # Load data
    with st.spinner("Loading review analytics data..."):
        df = load_review_analytics()
    
    if df.empty:
        st.error("No review data available.")
        return
    
    # Convert date columns and normalize timezones
    date_columns = ['review_creation_date', 'review_answer_timestamp', 
                   'order_purchase_timestamp', 'order_delivered_customer_date']
    
    for col in date_columns:
        if col in df.columns:
            # Handle timezone-aware and timezone-naive datetimes consistently
            df[col] = pd.to_datetime(df[col], errors='coerce')
            # Check for timezone-aware datetimes and normalize
            if isinstance(df[col].dtype, DatetimeTZDtype):
                df[col] = df[col].dt.tz_convert('UTC').dt.tz_localize(None)
            # If already timezone-naive, leave as is
    
    # Key metrics
    st.header("📊 Review Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_reviews = len(df)
        st.metric("Total Reviews", f"{total_reviews:,}")
    
    with col2:
        avg_score = df['review_score'].mean()
        st.metric("Average Score", f"{avg_score:.2f}")
    
    with col3:
        review_rate = (df['review_score'].notna().sum() / len(df)) * 100
        st.metric("Review Rate", f"{review_rate:.1f}%")
    
    with col4:
        satisfaction_rate = (df['review_score'] >= 4).mean() * 100
        st.metric("Satisfaction Rate (4-5⭐)", f"{satisfaction_rate:.1f}%")
    
    # Review score analysis
    st.header("⭐ Review Score Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌟 Score Distribution")
        score_counts = df['review_score'].value_counts().sort_index()
        fig = px.bar(
            x=score_counts.index,
            y=score_counts.values,
            title="Review Score Distribution",
            labels={'x': 'Review Score', 'y': 'Count'},
            color=score_counts.index,
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("📈 Scores Over Time")
        if 'review_creation_date' in df.columns:
            df['review_date'] = df['review_creation_date'].dt.date
            daily_scores = df.groupby('review_date')['review_score'].mean().reset_index()
            
            fig = px.line(
                daily_scores,
                x='review_date',
                y='review_score',
                title="Average Daily Review Score",
                labels={'review_score': 'Average Score', 'review_date': 'Date'}
            )
            fig.add_hline(y=avg_score, line_dash="dash", line_color="red", 
                         annotation_text=f"Overall Average: {avg_score:.2f}")
            st.plotly_chart(fig, width="stretch")
    
    # Geographic analysis
    st.header("🗺️ Geographic Review Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Review Scores by State")
        state_reviews = df.groupby('customer_state').agg({
            'review_score': ['count', 'mean'],
            'order_value': 'mean'
        }).round(2)
        state_reviews.columns = ['Review Count', 'Avg Score', 'Avg Order Value']
        state_reviews = state_reviews.reset_index()
        
        fig = px.scatter(
            state_reviews.head(20),
            x='Review Count',
            y='Avg Score',
            size='Avg Order Value',
            hover_name='customer_state',
            title="State Review Performance",
            labels={'Avg Score': 'Average Review Score'}
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("🏆 Top States by Satisfaction")
        top_states = state_reviews.nlargest(15, 'Avg Score')
        fig = px.bar(
            top_states,
            x='customer_state',
            y='Avg Score',
            title="Top 15 States by Average Review Score"
        )
        st.plotly_chart(fig, width="stretch")
    
    # Order value vs review score
    st.header("💰 Order Value vs Satisfaction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Value vs Score Correlation")
        fig = px.scatter(
            df.sample(min(5000, len(df))),  # Sample for performance
            x='order_value',
            y='review_score',
            color='customer_state',
            title="Order Value vs Review Score",
            labels={'order_value': 'Order Value ($)', 'review_score': 'Review Score'}
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.subheader("📈 Score by Value Range")
        # Create value bins
        df['value_range'] = pd.cut(df['order_value'], 
                                 bins=[0, 50, 100, 200, 500, float('inf')],
                                 labels=['$0-50', '$50-100', '$100-200', '$200-500', '$500+'])
        
        score_by_range = df.groupby('value_range')['review_score'].mean().reset_index()
        fig = px.bar(
            score_by_range,
            x='value_range',
            y='review_score',
            title="Average Review Score by Order Value Range"
        )
        st.plotly_chart(fig, width="stretch")
    
    # Comment analysis
    st.header("💬 Review Comments Analysis")
    
    # Comments with text
    comments_df = df[df['review_comment_message'].notna() & (df['review_comment_message'] != '')]
    
    col1, col2 = st.columns(2)
    
    with col1:
        comment_rate = (len(comments_df) / len(df)) * 100
        st.metric("Comment Rate", f"{comment_rate:.1f}%")
        
        # Score distribution for comments vs no comments
        fig = go.Figure()
        
        # Comments
        fig.add_trace(go.Histogram(
            x=comments_df['review_score'],
            name='With Comments',
            opacity=0.7,
            nbinsx=5
        ))
        
        # No comments
        no_comments_df = df[df['review_comment_message'].isna() | (df['review_comment_message'] == '')]
        fig.add_trace(go.Histogram(
            x=no_comments_df['review_score'],
            name='No Comments',
            opacity=0.7,
            nbinsx=5
        ))
        
        fig.update_layout(
            title="Review Scores: Comments vs No Comments",
            xaxis_title="Review Score",
            yaxis_title="Count",
            barmode='overlay'
        )
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        if not comments_df.empty:
            st.subheader("📝 Sample Review Comments")
            
            # Sample comments by score
            score_filter = st.selectbox("Filter by Score", [1, 2, 3, 4, 5], index=4)
            score_comments = comments_df[comments_df['review_score'] == score_filter]
            
            if not score_comments.empty:
                sample_comments = score_comments['review_comment_message'].head(5)
                for i, comment in enumerate(sample_comments):
                    with st.expander(f"Comment {i+1}"):
                        st.write(comment)
    
    # Detailed data table
    st.header("📋 Review Analytics Data")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_range = st.slider("Review Score Range", 1, 5, (1, 5))
    
    with col2:
        min_order_value = st.number_input("Min Order Value ($)", min_value=0.0, value=0.0)
    
    with col3:
        state_filter = st.multiselect(
            "Filter by State",
            df['customer_state'].unique(),
            default=df['customer_state'].unique()[:10]
        )
    
    # Apply filters
    filtered_df = df[
        (df['review_score'] >= score_range[0]) &
        (df['review_score'] <= score_range[1]) &
        (df['order_value'] >= min_order_value) &
        (df['customer_state'].isin(state_filter))
    ]
    
    st.dataframe(filtered_df, width="stretch")

if __name__ == "__main__":
    main()
