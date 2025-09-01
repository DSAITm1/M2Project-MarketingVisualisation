"""
Optimized Marketing Analytics Dashboard
High-performance Streamlit app with modular architecture
"""

import streamlit as st
import polars as pl
import plotly.express as px
import sys
import os
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from utils.database import load_config, get_bigquery_client, get_available_tables
    from utils.visualizations import (create_metric_cards, create_bar_chart, create_pie_chart, 
                                    create_line_chart, display_chart, display_dataframe, COLORS)
    from utils.data_processing import (get_customer_segments, get_order_performance, 
                                     get_review_insights, get_geographic_summary, 
                                     calculate_business_metrics, format_currency)
    from utils.performance import enable_debug_mode, perf_tracker, optimize_dataframe_memory
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.error("Please ensure all utility modules are properly installed")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Marketing Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None

def main():
    """Main application with optimized performance"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("📊 Marketing Analytics Dashboard")
    st.markdown("**Optimized BigQuery Data Visualization**")
    
    # Debug and performance options
    enable_debug_mode()
    
    # Connection check
    client = get_bigquery_client()
    if client is None:
        st.error("❌ Unable to connect to BigQuery. Please check your configuration.")
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            1. Check if `config/bigquery_config.json` exists and is valid
            2. Ensure Google Cloud credentials are properly configured
            3. Verify BigQuery API is enabled for your project
            4. Check if the dataset exists and you have access permissions
            """)
        return
    
    # Sidebar configuration
    create_sidebar()
    
    # Main dashboard
    create_dashboard()

def create_sidebar():
    """Create optimized sidebar with configuration options"""
    st.sidebar.title("⚙️ Configuration")
    
    config = load_config()
    if config:
        st.sidebar.success(f"✅ Project: {config['project_id']}")
        st.sidebar.info(f"📊 Dataset: {config['dataset_id']}")
    
    # Data refresh options
    st.sidebar.subheader("🔄 Data Management")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", help="Clear cache and reload data"):
            st.cache_data.clear()
            st.session_state.data_loaded = False
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    with col2:
        if st.button("🧹 Clear Cache", help="Clear all cached data"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared!")
    
    # Show last refresh time
    if st.session_state.last_refresh:
        st.sidebar.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

def create_dashboard():
    """Create the main optimized dashboard"""
    
    # Load all data with progress indicator
    progress_container = st.container()
    
    with progress_container:
        data_loading_progress = st.progress(0)
        status_text = st.empty()
        
        # Load data progressively
        status_text.text("🔄 Loading customer data...")
        customer_data = get_customer_segments()
        data_loading_progress.progress(25)
        
        status_text.text("🔄 Loading order data...")
        order_data = get_order_performance()
        data_loading_progress.progress(50)
        
        status_text.text("🔄 Loading review data...")
        review_data = get_review_insights()
        data_loading_progress.progress(75)
        
        status_text.text("🔄 Loading geographic data...")
        geo_data = get_geographic_summary()
        data_loading_progress.progress(100)
        
        # Clear progress indicators
        data_loading_progress.empty()
        status_text.empty()
    
    # Check data availability
    data_status = {
        'Customers': not customer_data.empty,
        'Orders': not order_data.empty, 
        'Reviews': not review_data.empty,
        'Geography': not geo_data.empty
    }
    
    # Show data status
    st.subheader("📊 Data Status")
    status_cols = st.columns(len(data_status))
    for i, (name, available) in enumerate(data_status.items()):
        with status_cols[i]:
            if available:
                st.success(f"✅ {name}")
            else:
                st.error(f"❌ {name}")
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Summary", 
        "👥 Customer Deep Dive", 
        "🛒 Order Intelligence", 
        "⭐ Review Insights"
    ])
    
    with tab1:
        create_executive_summary(customer_data, order_data, review_data, geo_data)
    
    with tab2:
        create_customer_intelligence(customer_data)
    
    with tab3:
        create_order_intelligence(order_data)
    
    with tab4:
        create_review_intelligence(review_data)

def create_executive_summary(customer_data, order_data, review_data, geo_data):
    """Create comprehensive executive summary"""
    st.header("📊 Executive Summary")
    
    # High-level KPIs
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        if not customer_data.empty:
            total_customers = len(customer_data)
            st.metric("👥 Total Customers", f"{total_customers:,}")
    
    with kpi_col2:
        if not order_data.empty:
            total_orders = len(order_data)
            st.metric("🛒 Total Orders", f"{total_orders:,}")
    
    with kpi_col3:
        if not customer_data.empty and 'total_spent' in customer_data.columns:
            total_revenue = customer_data['total_spent'].sum()
            st.metric("💰 Total Revenue", format_currency(total_revenue))
    
    with kpi_col4:
        if not review_data.empty and 'review_score' in review_data.columns:
            avg_rating = review_data['review_score'].mean()
            st.metric("⭐ Avg Rating", f"{avg_rating:.2f}/5")
    
    # Business insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Top Performing States")
        if not geo_data.empty and 'total_revenue' in geo_data.columns:
            top_states = geo_data.groupby('customer_state')['total_revenue'].sum().sort_values(ascending=False).head(5)
            
            for i, (state, revenue) in enumerate(top_states.items()):
                st.write(f"**{i+1}. {state}**: {format_currency(revenue)}")
    
    with col2:
        st.subheader("📈 Growth Opportunities")
        if not customer_data.empty and 'customer_segment' in customer_data.columns:
            segment_counts = customer_data['customer_segment'].value_counts()
            
            # Identify growth opportunities
            if 'At Risk' in segment_counts.index:
                at_risk = segment_counts['At Risk']
                st.warning(f"⚠️ {at_risk:,} customers at risk of churning")
            
            if 'New Customers' in segment_counts.index:
                new_customers = segment_counts['New Customers']
                st.info(f"🆕 {new_customers:,} new customers to nurture")

def create_customer_intelligence(customer_data):
    """Advanced customer analytics with RFM analysis"""
    st.header("👥 Customer Intelligence")
    
    if customer_data.empty:
        st.warning("⚠️ No customer data available")
        return
    
    # Display key customer metrics first
    if 'total_spent' in customer_data.columns and 'total_orders' in customer_data.columns:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_order_value = customer_data['total_spent'].sum() / customer_data['total_orders'].sum()
            st.metric("💰 Avg Order Value", format_currency(avg_order_value))
        
        with col2:
            repeat_customers = (customer_data['total_orders'] > 1).sum()
            repeat_rate = (repeat_customers / len(customer_data)) * 100
            st.metric("🔄 Repeat Customer Rate", f"{repeat_rate:.1f}%")
        
        with col3:
            top_customer_spend = customer_data['total_spent'].max()
            st.metric("👑 Top Customer Value", format_currency(top_customer_spend))
        
        with col4:
            if 'avg_review_score' in customer_data.columns:
                avg_customer_rating = customer_data['avg_review_score'].mean()
                st.metric("⭐ Avg Customer Rating", f"{avg_customer_rating:.2f}/5")

    # Customer segmentation overview with better insights
    if 'customer_segment' in customer_data.columns:
        # Header with explanation link
        col_header, col_link = st.columns([4, 1])
        with col_header:
            st.subheader("🎯 RFM Customer Segmentation Analysis")
        with col_link:
            with st.popover("ℹ️ What do these segments mean?"):
                st.markdown("""
                **🏆 Champions** - Best customers! High spending, frequent orders, recent activity
                > *Strategy: Reward and retain these customers*
                
                **🤝 Loyal Customers** - Consistent customers with recent activity and good spending
                > *Strategy: Upsell and cross-sell opportunities*
                
                **💎 Big Spenders** - High-value customers but order less frequently  
                > *Strategy: Encourage more frequent purchases*
                
                **🆕 New Customers** - Recent customers with lower initial spending
                > *Strategy: Nurture relationships and increase engagement*
                
                **⭐ Potential Loyalists** - Multiple orders with decent spending patterns
                > *Strategy: Develop into loyal customers with targeted campaigns*
                
                **⚠️ At Risk** - Previously active customers with declining engagement
                > *Strategy: Win-back campaigns and re-engagement efforts*
                
                **🛒 One-Time Buyers** - Made only one purchase
                > *Strategy: Convert to repeat customers through follow-up*
                
                **👤 Regular Customers** - Standard customers with average patterns
                > *Strategy: Identify opportunities to move them up segments*
                
                ---
                *RFM Analysis ranks customers on:*
                - **Recency**: How recently they purchased
                - **Frequency**: How often they purchase  
                - **Monetary**: How much they spend
                """)
        
        # Segment insights with actionable recommendations
        segment_stats = customer_data.groupby('customer_segment').agg({
            'customer_unique_id': 'count',
            'total_spent': ['sum', 'mean'],
            'total_orders': 'mean',
            'avg_review_score': 'mean'
        }).round(2)
        
        segment_stats.columns = ['Count', 'Total Revenue', 'Avg Revenue', 'Avg Orders', 'Avg Rating']
        segment_stats = segment_stats.sort_values('Total Revenue', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            segment_counts = customer_data['customer_segment'].value_counts()
            fig = create_pie_chart(
                values=segment_counts.values,
                names=segment_counts.index,
                title="Customer Segment Distribution"
            )
            display_chart(fig)
        
        with col2:
            segment_value = customer_data.groupby('customer_segment')['total_spent'].sum().sort_values(ascending=False)
            fig = create_bar_chart(
                data=segment_value.reset_index(),
                x='customer_segment',
                y='total_spent',
                title="Revenue by Customer Segment",
                labels={'customer_segment': 'Segment', 'total_spent': 'Revenue ($)'}
            )
            display_chart(fig)
        
        # Detailed segment analysis table
        st.subheader("📊 Detailed Segment Analysis")
        display_dataframe(segment_stats, "Customer Segment Performance", max_rows=10)
        
        # Business insights and recommendations
        st.subheader("💡 Strategic Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🎯 Key Opportunities:**")
            
            # Identify opportunities
            if 'Champions' in segment_counts.index:
                champions = segment_counts['Champions']
                st.success(f"✨ **{champions:,} Champions** - Your best customers! Focus on retention programs.")
            
            if 'Big Spenders' in segment_counts.index:
                big_spenders = segment_counts['Big Spenders']
                st.info(f"💎 **{big_spenders:,} Big Spenders** - High value, low frequency. Encourage repeat purchases.")
            
            if 'Potential Loyalists' in segment_counts.index:
                potential = segment_counts['Potential Loyalists']
                st.info(f"🌟 **{potential:,} Potential Loyalists** - Great candidates for loyalty programs.")
        
        with col2:
            st.write("**⚠️ Areas of Concern:**")
            
            if 'At Risk' in segment_counts.index:
                at_risk = segment_counts['At Risk']
                risk_pct = (at_risk / len(customer_data)) * 100
                st.warning(f"🚨 **{at_risk:,} At Risk** ({risk_pct:.1f}%) - Immediate re-engagement needed.")
            
            if 'One-Time Buyers' in segment_counts.index:
                one_time = segment_counts['One-Time Buyers']
                one_time_pct = (one_time / len(customer_data)) * 100
                st.warning(f"📉 **{one_time:,} One-Time Buyers** ({one_time_pct:.1f}%) - Focus on conversion to repeat customers.")
            
            if 'New Customers' in segment_counts.index:
                new_customers = segment_counts['New Customers']
                st.success(f"🆕 **{new_customers:,} New Customers** - Nurture these relationships!")

    # RFM Scores Distribution (if available)
    if all(col in customer_data.columns for col in ['recency_score', 'frequency_score', 'monetary_score']):
        st.subheader("📈 RFM Score Distribution")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            recency_dist = customer_data['recency_score'].value_counts().sort_index()
            fig = create_bar_chart(
                data=recency_dist.reset_index(),
                x='recency_score',
                y='count',
                title="Recency Scores",
                labels={'recency_score': 'Recency Score (1=Old, 5=Recent)', 'count': 'Customers'}
            )
            display_chart(fig)
        
        with col2:
            frequency_dist = customer_data['frequency_score'].value_counts().sort_index()
            fig = create_bar_chart(
                data=frequency_dist.reset_index(),
                x='frequency_score',
                y='count',
                title="Frequency Scores",
                labels={'frequency_score': 'Frequency Score (1=Low, 5=High)', 'count': 'Customers'}
            )
            display_chart(fig)
        
        with col3:
            monetary_dist = customer_data['monetary_score'].value_counts().sort_index()
            fig = create_bar_chart(
                data=monetary_dist.reset_index(),
                x='monetary_score',
                y='count',
                title="Monetary Scores",
                labels={'monetary_score': 'Monetary Score (1=Low, 5=High)', 'count': 'Customers'}
            )
            display_chart(fig)

    # Geographic insights
    st.subheader("🗺️ Geographic Distribution")
    if 'customer_state' in customer_data.columns:
        state_summary = customer_data.groupby('customer_state').agg({
            'customer_unique_id': 'count',
            'total_spent': 'sum',
            'avg_review_score': 'mean'
        }).round(2)
        state_summary.columns = ['Customers', 'Revenue', 'Avg Rating']
        state_summary = state_summary.sort_values('Revenue', ascending=False)
        
        display_dataframe(state_summary, "📊 State Performance Summary", max_rows=20)

def create_order_intelligence(order_data):
    """Advanced order analytics"""
    st.header("🛒 Order Intelligence")
    
    if order_data.empty:
        st.warning("⚠️ No order data available")
        return
    
    # Order performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Order Status Analysis")
        if 'order_status' in order_data.columns:
            status_counts = order_data['order_status'].value_counts()
            fig = create_pie_chart(
                values=status_counts.values,
                names=status_counts.index,
                title="Order Status Distribution"
            )
            display_chart(fig)
    
    with col2:
        st.subheader("💰 Order Value Analysis")
        if 'order_value' in order_data.columns:
            # Create value bins using Polars
            order_data = order_data.with_columns(
                pl.when(pl.col("order_value") < 50).then(pl.lit("Low ($0-50)"))
                .when(pl.col("order_value") < 150).then(pl.lit("Medium ($50-150)"))
                .when(pl.col("order_value") < 300).then(pl.lit("High ($150-300)"))
                .otherwise(pl.lit("Premium ($300+)"))
                .alias("value_segment")
            )
            
            value_counts = order_data.group_by("value_segment").agg(
                pl.col("value_segment").count().alias("count")
            )
            # Convert to pandas for Plotly
            value_counts_pd = value_counts.to_pandas()
            fig = create_bar_chart(
                data=value_counts_pd,
                x='value_segment',
                y='count',
                title="Order Value Distribution",
                labels={'value_segment': 'Value Segment', 'count': 'Number of Orders'}
            )
            display_chart(fig)
    
    # Delivery performance
    if 'delivery_difference' in order_data.columns:
        st.subheader("⏱️ Delivery Performance Analysis")
        
        delivered_orders = order_data[order_data['order_status'] == 'delivered'].copy()
        if not delivered_orders.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                avg_diff = delivered_orders['delivery_difference'].mean()
                on_time_pct = (delivered_orders['delivery_difference'] <= 0).mean() * 100
                early_pct = (delivered_orders['delivery_difference'] < 0).mean() * 100
                
                metrics = {
                    "⏰ Avg Delivery Variance": f"{avg_diff:.1f} days",
                    "✅ On-Time Delivery": f"{on_time_pct:.1f}%",
                    "🚀 Early Delivery": f"{early_pct:.1f}%"
                }
                create_metric_cards(metrics, columns=1)
            
            with col2:
                # Delivery performance histogram
                fig = px.histogram(
                    delivered_orders,
                    x='delivery_difference',
                    title="Delivery Performance Distribution",
                    labels={'delivery_difference': 'Days (Negative = Early)', 'count': 'Orders'},
                    color_discrete_sequence=[COLORS['primary']]
                )
                fig.update_layout(height=300)
                display_chart(fig)

def create_review_intelligence(review_data):
    """Advanced review analytics"""
    st.header("⭐ Review Intelligence")
    
    if review_data.empty:
        st.warning("⚠️ No review data available")
        return
    
    # Review insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⭐ Review Score Analysis")
        if 'review_score' in review_data.columns:
            score_dist = review_data['review_score'].value_counts().sort_index()
            fig = create_bar_chart(
                data=score_dist.reset_index(),
                x='review_score',
                y='count',
                title="Review Score Distribution",
                labels={'review_score': 'Rating', 'count': 'Number of Reviews'}
            )
            display_chart(fig)
    
    with col2:
        st.subheader("📦 Category Performance")
        if 'product_category_name' in review_data.columns:
            category_performance = review_data.groupby('product_category_name').agg({
                'review_score': ['mean', 'count']
            }).round(2)
            category_performance.columns = ['Avg Rating', 'Review Count']
            category_performance = category_performance.sort_values('Avg Rating', ascending=False).head(10)
            
            fig = create_bar_chart(
                data=category_performance.reset_index(),
                x='product_category_name',
                y='Avg Rating',
                title="Top Categories by Rating",
                labels={'product_category_name': 'Category', 'Avg Rating': 'Average Rating'}
            )
            display_chart(fig)
    
    # Time-based analysis
    if 'review_creation_date' in review_data.columns:
        st.subheader("📈 Review Trends Over Time")
        
        # Convert to datetime and extract month using Polars
        review_data_with_month = review_data.with_columns(
            pl.col("review_creation_date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False)
             .dt.truncate("1mo")
             .alias("month")
        )
        
        monthly_trends = review_data_with_month.group_by("month").agg(
            pl.col("review_score").count().alias("Review Count"),
            pl.col("review_score").mean().alias("Average Score")
        ).sort("month")
        
        # Convert to pandas for Plotly
        monthly_trends_pd = monthly_trends.to_pandas()
        monthly_trends_pd['month'] = monthly_trends_pd['month'].astype(str)
        
        # Create dual-axis chart
        fig = px.line(
            monthly_trends,
            x='month',
            y='Average Score',
            title="Monthly Review Trends",
            labels={'month': 'Month', 'Average Score': 'Average Rating'}
        )
        display_chart(fig)

def show_data_summary():
    """Show summary of available data"""
    st.sidebar.subheader("📊 Data Summary")
    
    # Quick data check
    config = load_config()
    if config:
        available_tables = get_available_tables()
        st.sidebar.write(f"📋 Available tables: {len(available_tables)}")
        
        for table in available_tables[:5]:  # Show first 5
            st.sidebar.write(f"• {table}")
        
        if len(available_tables) > 5:
            st.sidebar.write(f"... and {len(available_tables) - 5} more")

if __name__ == "__main__":
    show_data_summary()
    main()
