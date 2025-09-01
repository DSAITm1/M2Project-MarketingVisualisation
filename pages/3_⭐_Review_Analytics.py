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

from utils.database import load_config, get_bigquery_client, execute_query
from utils.visualizations import (create_metric_cards, create_bar_chart, create_pie_chart, 
                                create_line_chart, display_chart, display_dataframe)
from utils.data_processing import get_review_insights, format_currency

st.set_page_config(page_title="Review Analytics", page_icon="⭐", layout="wide")

@st.cache_data(ttl=3600)
def load_review_analytics():
    """Load review analytics from BigQuery"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
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
    """
    
    return execute_query(query, "review_analytics")

def main():
    st.title("⭐ Customer Voice Intelligence")
    st.markdown("**Strategic Customer Satisfaction & Sentiment Analysis for Marketing Directors**")
    
    # Load data
    with st.spinner("Loading customer voice analytics..."):
        df = load_review_analytics()
    
    if df.is_empty():
        st.error("No customer voice data available.")
        return
    
    # Convert date columns and normalize timezones
    date_columns = ['review_creation_date', 'review_answer_timestamp', 
                   'order_purchase_timestamp', 'order_delivered_customer_date']
    
    for col in date_columns:
        if col in df.columns:
            # Handle timezone-aware and timezone-naive datetimes consistently
            df = df.with_columns(
                pl.col(col).str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
                .dt.replace_time_zone("UTC")
                .dt.convert_time_zone("UTC")
                .dt.replace_time_zone(None)
                .alias(col)
            )
    
    # Executive Summary for Marketing Director
    st.header("📊 Customer Voice Executive Summary")

    if not df.is_empty():
        # Calculate key customer experience metrics
        total_reviews = len(df)
        avg_satisfaction = df['review_score'].mean()
        satisfaction_rate = (df['review_score'] >= 4).mean() * 100
        promoter_rate = (df['review_score'] >= 5).mean() * 100
        detractor_rate = (df['review_score'] <= 2).mean() * 100
        net_promoter_score = promoter_rate - detractor_rate
        
        # Customer experience insights
        comment_rate = (df['review_comment_message'].notna() & (df['review_comment_message'] != '')).mean() * 100
        avg_order_value = df['order_value'].mean()
        
        # Geographic coverage
        states_covered = df['customer_state'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("👥 Total Customer Reviews", f"{total_reviews:,}", help="Total customer feedback collected")
            st.metric("⭐ Average Satisfaction", f"{avg_satisfaction:.2f}/5.0", help="Overall customer satisfaction score")

        with col2:
            st.metric("😊 Satisfaction Rate (4-5⭐)", f"{satisfaction_rate:.1f}%", help="Percentage of highly satisfied customers")
            st.metric("🌟 Promoter Rate (5⭐)", f"{promoter_rate:.1f}%", help="Percentage of brand promoters")

        with col3:
            st.metric("📈 Net Promoter Score", f"{net_promoter_score:+.1f}", 
                     help="NPS = % Promoters - % Detractors", 
                     delta=f"{net_promoter_score:+.1f}")
            st.metric("� Comment Rate", f"{comment_rate:.1f}%", help="Percentage of customers providing detailed feedback")

        with col4:
            st.metric("🗺️ Markets Covered", f"{states_covered} states", help="Geographic reach of customer feedback")
            st.metric("💰 Avg Order Value", f"${avg_order_value:.2f}", help="Average order value from reviewed purchases")

    # Strategic Customer Insights
    st.header("🎯 Strategic Customer Insights")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        st.subheader("💎 Customer Satisfaction Drivers")
        
        # Analyze satisfaction by order value ranges
        df = df.with_columns(
            pl.col('order_value').cut(
                bins=[0, 50, 100, 200, 500, float('inf')],
                labels=['Budget (<$50)', 'Value ($50-100)', 'Standard ($100-200)', 
                       'Premium ($200-500)', 'Luxury ($500+)']
            ).alias('value_segment')
        )
        
        satisfaction_by_value = df.group_by('value_segment').agg([
            pl.col('review_score').mean().alias('mean'),
            pl.col('review_score').count().alias('count')
        ]).with_columns([
            pl.col('mean').round(2),
            pl.col('count').round(2)
        ])
        
        # Find the highest and lowest performing segments
        best_segment = satisfaction_by_value.loc[satisfaction_by_value['mean'].idxmax()]
        worst_segment = satisfaction_by_value.loc[satisfaction_by_value['mean'].idxmin()]
        
        st.success(f"🏆 **Best Performing Segment**: {best_segment['value_segment']} "
                  f"({best_segment['mean']:.2f}⭐ from {best_segment['count']:,} reviews)")
        st.error(f"⚠️ **Improvement Needed**: {worst_segment['value_segment']} "
                f"({worst_segment['mean']:.2f}⭐ from {worst_segment['count']:,} reviews)")
        
        st.info("💡 **Strategic Insight**: Focus premium customer experience on budget segments to improve overall satisfaction")

    with insights_col2:
        st.subheader("🌍 Geographic Satisfaction Patterns")
        
        # Geographic satisfaction analysis
        geo_satisfaction = df.group_by('customer_state').agg([
            pl.col('review_score').mean().alias('avg_score'),
            pl.col('review_score').count().alias('review_count'),
            pl.col('order_value').mean().alias('avg_order_value')
        ]).with_columns([
            pl.col('avg_score').round(2),
            pl.col('avg_order_value').round(2)
        ])
        
        # Top and bottom performing states
        top_states = geo_satisfaction.sort('avg_score', descending=True).limit(3)
        bottom_states = geo_satisfaction.sort('avg_score').limit(3)
        
        st.success("**Top Performing Markets:**")
        for idx, row in top_states.iterrows():
            st.write(f"⭐ **{row['customer_state']}**: {row['avg_score']:.2f}⭐ "
                   f"({row['review_count']:,} reviews)")
        
        st.warning("**Markets Needing Attention:**")
        for idx, row in bottom_states.iterrows():
            st.write(f"⚠️ **{row['customer_state']}**: {row['avg_score']:.2f}⭐ "
                   f"({row['review_count']:,} reviews)")
        
        st.info("💡 **Strategic Insight**: Replicate best practices from top markets to improve bottom performers")

    # Customer Experience Dashboard
    st.header("📊 Customer Experience Dashboard")
    
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
            df = df.with_columns(
                pl.col('review_creation_date').dt.date().alias('review_date')
            )
            daily_scores = df.group_by('review_date').agg(
                pl.col('review_score').mean()
            )
            
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
        state_reviews = df.group_by('customer_state').agg([
            pl.col('review_score').count().alias('Review Count'),
            pl.col('review_score').mean().alias('Avg Score'),
            pl.col('order_value').mean().alias('Avg Order Value')
        ]).with_columns([
            pl.col('Avg Score').round(2),
            pl.col('Avg Order Value').round(2)
        ])
        
        fig = px.scatter(
            state_reviews.sort('Review Count', descending=True).limit(20),
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
        top_states = state_reviews.sort('Avg Score', descending=True).limit(15)
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
        df = df.with_columns(
            pl.col('order_value').cut(
                bins=[0, 50, 100, 200, 500, float('inf')],
                labels=['$0-50', '$50-100', '$100-200', '$200-500', '$500+']
            ).alias('value_range')
        )
        
        score_by_range = df.group_by('value_range').agg(
            pl.col('review_score').mean()
        )
        fig = px.bar(
            score_by_range,
            x='value_range',
            y='review_score',
            title="Average Review Score by Order Value Range"
        )
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
        if not comments_df.is_empty():
            st.subheader("📝 Sample Review Comments")
            
            # Sample comments by score
            score_filter = st.selectbox("Filter by Score", [1, 2, 3, 4, 5], index=4)
            score_comments = comments_df.filter(pl.col('review_score') == score_filter)
            
            if not score_comments.is_empty():
                sample_comments = score_comments.select('review_comment_message').limit(5).to_series().to_list()
                for i, comment in enumerate(sample_comments):
                    with st.expander(f"Comment {i+1}"):
                        st.write(comment)
    
    # Strategic Recommendations
    st.header("🎯 Strategic Recommendations")
    
    if not df.is_empty():
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.subheader("🚀 Customer Experience Optimization")
            
            # Identify key improvement areas
            low_satisfaction_reviews = df[df['review_score'] <= 3]
            high_value_low_satisfaction = low_satisfaction_reviews[low_satisfaction_reviews['order_value'] > df['order_value'].quantile(0.8)]
            
            st.error("**Critical Focus Areas:**")
            st.write(f"⚠️ **{len(low_satisfaction_reviews):,} reviews** with scores ≤ 3 need immediate attention")
            if not high_value_low_satisfaction.is_empty():
                st.write(f"💰 **{len(high_value_low_satisfaction)} high-value customers** with low satisfaction")
            
            st.success("**Action Items:**")
            st.write("• Implement proactive customer service for high-value orders")
            st.write("• Develop automated satisfaction surveys post-delivery")
            st.write("• Create customer feedback integration in product development")
            st.write("• Establish customer success teams for premium segments")
            
            # Promoter program opportunity
            promoter_opportunity = df[df['review_score'] >= 4]
            st.metric("🌟 Promoter Program Potential", f"{len(promoter_opportunity):,} customers", 
                     help="Customers who could become brand advocates")
        
        with rec_col2:
            st.subheader("📈 Voice of Customer Strategy")
            
            # Comment analysis insights
            comments_with_feedback = df[df['review_comment_message'].notna() & (df['review_comment_message'] != '')]
            high_score_comments = comments_with_feedback[comments_with_feedback['review_score'] >= 4]
            low_score_comments = comments_with_feedback[comments_with_feedback['review_score'] <= 2]
            
            st.info("**Voice of Customer Insights:**")
            st.write(f"💬 **{len(comments_with_feedback):,} customers** provided detailed feedback")
            st.write(f"⭐ **{len(high_score_comments)} positive comments** contain success factors")
            st.write(f"⚠️ **{len(low_score_comments)} negative comments** highlight pain points")
            
            st.success("**Strategic Initiatives:**")
            st.write("• Launch referral program leveraging top promoters")
            st.write("• Analyze comment themes for product improvement")
            st.write("• Implement real-time feedback collection")
            st.write("• Create customer advocacy and loyalty programs")
            
            # Geographic expansion opportunity
            top_markets = geo_satisfaction.limit(5)
            st.metric("🎯 Top Markets for Expansion", f"{len(top_markets)} high-satisfaction states", 
                     help="Markets with proven customer satisfaction")
    
    # Business Intelligence Summary
    st.header("📊 Customer Voice Intelligence Summary")
    
    if not df.is_empty():
        # Key business intelligence metrics
        total_feedback_volume = len(df)
        customer_satisfaction_index = avg_satisfaction * 20  # Convert to 100-point scale
        feedback_engagement_rate = comment_rate
        customer_loyalty_index = net_promoter_score + 100  # Convert to 0-200 scale
        
        # Customer experience health score
        health_score = (satisfaction_rate + promoter_rate - detractor_rate) / 3
        
        # Revenue impact analysis
        high_satisfaction_revenue = df[df['review_score'] >= 4]['order_value'].sum()
        total_revenue_from_reviews = df['order_value'].sum()
        satisfaction_revenue_percentage = (high_satisfaction_revenue / total_revenue_from_reviews) * 100
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.subheader("🎯 Customer Experience Health")
            st.metric("Customer Satisfaction Index", f"{customer_satisfaction_index:.1f}/100")
            st.metric("Feedback Engagement Rate", f"{feedback_engagement_rate:.1f}%")
            st.metric("Overall Health Score", f"{health_score:.1f}%")
        
        with summary_col2:
            st.subheader("💰 Business Impact")
            st.metric("Revenue from Satisfied Customers", f"${high_satisfaction_revenue:,.0f}")
            st.metric("Satisfaction Revenue Share", f"{satisfaction_revenue_percentage:.1f}%")
            st.metric("Customer Loyalty Index", f"{customer_loyalty_index:.1f}/200")
        
        with summary_col3:
            st.subheader("📈 Strategic KPIs")
            # Customer lifetime value correlation
            clv_correlation = df['order_value'].corr(df['review_score'])
            st.metric("CLV-Satisfaction Correlation", f"{clv_correlation:.3f}")
            
            # Feedback velocity (recent feedback rate)
            if 'review_creation_date' in df.columns:
                max_date = df.select('review_creation_date').max().to_series().to_list()[0]
                recent_reviews = df.filter(pl.col('review_creation_date') >= max_date - pl.duration(days=30))
                feedback_velocity = len(recent_reviews) / 30
                st.metric("Daily Feedback Velocity", f"{feedback_velocity:.1f}")
            
            # Market penetration through feedback
            feedback_coverage = (states_covered / 27) * 100  # Brazil has 27 states
            st.metric("Market Feedback Coverage", f"{feedback_coverage:.1f}%")
        
        # Executive insights
        st.subheader("🏆 Executive Insights")
        
        insights = []
        
        if net_promoter_score > 30:
            insights.append("🌟 **Excellent NPS** - Strong foundation for growth marketing")
        elif net_promoter_score > 0:
            insights.append("📈 **Good NPS** - Opportunity to convert more promoters")
        else:
            insights.append("⚠️ **NPS needs improvement** - Focus on customer experience recovery")
        
        if feedback_engagement_rate > 20:
            insights.append("💬 **High engagement** - Customers are willing to provide feedback")
        else:
            insights.append("📝 **Low engagement** - Need to encourage more detailed feedback")
        
        if satisfaction_revenue_percentage > 70:
            insights.append("💰 **Strong revenue correlation** - Satisfaction drives business results")
        else:
            insights.append("📊 **Revenue opportunity** - Improve satisfaction to boost revenue")
        
        for insight in insights:
            st.info(insight)
        
        # Strategic priorities
        st.subheader("🎯 Strategic Priorities")
        
        priorities = [
            "1. **Customer Experience Excellence**: Achieve 90%+ satisfaction rate across all segments",
            "2. **Voice of Customer Integration**: Implement feedback in product development and service design",
            "3. **Promoter Program Development**: Convert satisfied customers into brand advocates",
            "4. **Geographic Expansion Strategy**: Replicate success from top-performing markets",
            "5. **Real-time Feedback Systems**: Enable immediate response to customer concerns"
        ]
        
        for priority in priorities:
            st.write(priority)
    
    # Detailed Customer Feedback Analysis
    st.header("📋 Customer Feedback Data Explorer")
    
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
