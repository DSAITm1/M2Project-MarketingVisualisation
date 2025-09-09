import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from database import get_bigquery_client

st.set_page_config(
    page_title="Customer Segmentation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ff6b6b;
    }
    .filter-container {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def format_currency(value):
    """Format currency values consistently"""
    if pd.isna(value) or value == 0:
        return "$0"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.0f}K" if value >= 10_000 else f"${value:,.0f}"
    else:
        return f"${value:.2f}"

def format_number(value):
    """Format large numbers consistently"""
    if pd.isna(value) or value == 0:
        return "0"
    elif value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.0f}K" if value >= 10_000 else f"{value:,.0f}"
    else:
        return f"{value:.0f}"

def format_percentage(value):
    """Format percentage values consistently"""
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1f}%"

def format_rating(value):
    """Format rating values consistently"""
    if pd.isna(value):
        return "0.0/5"
    return f"{value:.2f}/5"

@st.cache_data
def load_customer_data():
    """Load customer analytics data from BigQuery"""
    client = get_bigquery_client()
    if not client:
        st.error("Could not connect to BigQuery")
        return None, None, None, None
    
    # Customer segments data
    segments_query = """
    SELECT 
        customer_segment,
        customer_id,
        customer_state,
        total_spent,
        total_orders,
        avg_order_value,
        avg_review_score,
        predicted_annual_clv,
        first_order_date,
        last_order_date
    FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
    WHERE total_orders > 0 AND customer_segment IS NOT NULL
    """
    
    # Geographic data
    geo_query = """
    SELECT 
        customer_state,
        customer_city,
        customer_id,
        total_spent,
        total_orders,
        avg_order_value,
        avg_review_score,
        customer_segment
    FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
    WHERE total_orders > 0
    """
    
    # Purchase behavior data
    behavior_query = """
    SELECT 
        customer_id,
        customer_segment,
        customer_state,
        total_orders,
        total_spent,
        avg_order_value,
        avg_review_score,
        CASE 
            WHEN total_orders = 1 THEN 'One-time Buyers'
            WHEN total_orders BETWEEN 2 AND 3 THEN 'Occasional Buyers'
            WHEN total_orders BETWEEN 4 AND 6 THEN 'Regular Buyers'
            ELSE 'Frequent Buyers'
        END as purchase_behavior
    FROM `project-olist-470307.dbt_olist_analytics.customer_analytics_obt`
    WHERE total_orders > 0
    """
    
    try:
        segments_df = client.query(segments_query).result().to_dataframe()
        geo_df = client.query(geo_query).result().to_dataframe()
        behavior_df = client.query(behavior_query).result().to_dataframe()
        
        # Load additional data from JSON if available
        overview_data = None
        try:
            with open('/Users/jefflee/SCTP/M2Project/M2Project-MarketingVisualisation/customer_analytics_snapshot.json', 'r') as f:
                data = json.load(f)
                overview_data = data.get('overview', {})
        except:
            pass
            
        return segments_df, geo_df, behavior_df, overview_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, None

def create_segment_summary_chart(filtered_data):
    """Create segment summary visualization"""
    if filtered_data.empty:
        return None
        
    segment_summary = filtered_data.groupby('customer_segment').agg({
        'customer_id': 'count',
        'total_spent': 'mean',
        'avg_order_value': 'mean',
        'avg_review_score': 'mean'
    }).round(2)
    
    segment_summary.columns = ['Customer Count', 'Avg Spent', 'Avg Order Value', 'Avg Rating']
    segment_summary = segment_summary.reset_index()
    
    # Create subplot with better formatting
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Customer Count by Segment', 'Average Spent by Segment'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Customer count bar chart
    fig.add_trace(
        go.Bar(
            x=segment_summary['customer_segment'],
            y=segment_summary['Customer Count'],
            name='Customer Count',
            marker_color='#1f77b4',
            text=[format_number(x) for x in segment_summary['Customer Count']],
            textposition='auto'
        ),
        row=1, col=1
    )
    
    # Average spent bar chart
    fig.add_trace(
        go.Bar(
            x=segment_summary['customer_segment'],
            y=segment_summary['Avg Spent'],
            name='Avg Spent ($)',
            marker_color='#ff7f0e',
            text=[format_currency(x) for x in segment_summary['Avg Spent']],
            textposition='auto'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text="Customer Segmentation Overview",
        template="plotly_white"
    )
    
    # Format y-axes
    fig.update_yaxes(title_text="Number of Customers", row=1, col=1)
    fig.update_yaxes(title_text="Average Spent ($)", row=1, col=2)
    
    return fig

def create_geographic_map(filtered_data):
    """Create geographic distribution map"""
    if filtered_data.empty:
        return None
        
    state_summary = filtered_data.groupby('customer_state').agg({
        'customer_id': 'count',
        'total_spent': 'sum',
        'avg_order_value': 'mean'
    }).round(2)
    
    state_summary.columns = ['Customer Count', 'Total Revenue', 'Avg Order Value']
    state_summary = state_summary.reset_index().sort_values('Total Revenue', ascending=False)
    
    # Create enhanced bar chart
    fig = px.bar(
        state_summary.head(10),
        x='customer_state',
        y='Total Revenue',
        color='Customer Count',
        title='Geographic Distribution - Top 10 States',
        labels={
            'customer_state': 'State', 
            'Total Revenue': 'Total Revenue ($)',
            'Customer Count': 'Customer Count'
        },
        color_continuous_scale='Blues',
        text='Total Revenue'
    )
    
    # Format text on bars
    fig.update_traces(
        texttemplate='%{text:$,.0f}',
        textposition='outside'
    )
    
    fig.update_layout(
        height=400,
        template="plotly_white",
        xaxis_title="State",
        yaxis_title="Total Revenue ($)"
    )
    
    # Format y-axis to show currency
    fig.update_yaxes(tickformat='$,.0f')
    
    return fig

def create_behavior_analysis_chart(filtered_data):
    """Create purchase behavior analysis chart"""
    if filtered_data.empty:
        return None
        
    behavior_summary = filtered_data.groupby('purchase_behavior').agg({
        'customer_id': 'count',
        'total_spent': 'mean',
        'avg_review_score': 'mean'
    }).round(2)
    
    behavior_summary.columns = ['Customer Count', 'Avg Spent', 'Avg Rating']
    behavior_summary = behavior_summary.reset_index()
    
    # Create enhanced donut chart
    fig = px.pie(
        behavior_summary,
        values='Customer Count',
        names='purchase_behavior',
        title='Customer Distribution by Purchase Behavior',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Add value labels
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont_size=12
    )
    
    fig.update_layout(
        height=400,
        template="plotly_white",
        annotations=[dict(text='Purchase<br>Behavior', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    
    return fig

def create_segment_metrics_table(filtered_data):
    """Create detailed segment metrics table"""
    if filtered_data.empty:
        return pd.DataFrame()
        
    segment_details = filtered_data.groupby('customer_segment').agg({
        'customer_id': 'count',
        'total_spent': ['mean', 'sum'],
        'total_orders': 'mean',
        'avg_order_value': 'mean',
        'avg_review_score': 'mean'
    }).round(2)
    
    # Flatten column names
    segment_details.columns = ['Customer Count', 'Avg Spent', 'Total Revenue', 'Avg Orders', 'Avg Order Value', 'Avg Rating']
    segment_details = segment_details.reset_index()
    
    # Calculate percentage of base
    total_customers = segment_details['Customer Count'].sum()
    segment_details['% of Base'] = (segment_details['Customer Count'] / total_customers * 100).round(1)
    
    # Format currency and numeric columns for display
    segment_details_display = segment_details.copy()
    segment_details_display['Avg Spent'] = segment_details_display['Avg Spent'].apply(format_currency)
    segment_details_display['Total Revenue'] = segment_details_display['Total Revenue'].apply(format_currency)
    segment_details_display['Avg Order Value'] = segment_details_display['Avg Order Value'].apply(format_currency)
    segment_details_display['Customer Count'] = segment_details_display['Customer Count'].apply(format_number)
    segment_details_display['Avg Orders'] = segment_details_display['Avg Orders'].apply(lambda x: f"{x:.1f}")
    segment_details_display['Avg Rating'] = segment_details_display['Avg Rating'].apply(lambda x: f"{x:.2f}/5")
    segment_details_display['% of Base'] = segment_details_display['% of Base'].apply(lambda x: f"{x:.1f}%")
    
    return segment_details_display

# Main app
def main():
    st.title("📊 Customer Segmentation Dashboard")
    st.markdown("Interactive visualization dashboard for customer analytics and marketing insights")
    
    # Load data
    segments_df, geo_df, behavior_df, overview_data = load_customer_data()
    
    if segments_df is None:
        st.error("Unable to load data. Please check your connection.")
        return
    
    # Sidebar filters
    st.sidebar.header("🎛️ Filters")
    
    # Segment filter
    available_segments = sorted(segments_df['customer_segment'].unique())
    selected_segments = st.sidebar.multiselect(
        "Customer Segments",
        available_segments,
        default=available_segments
    )
    
    # State filter
    available_states = sorted(geo_df['customer_state'].unique())
    selected_states = st.sidebar.multiselect(
        "States",
        available_states,
        default=available_states[:10]  # Default to top 10
    )
    
    # Purchase behavior filter
    available_behaviors = sorted(behavior_df['purchase_behavior'].unique())
    selected_behaviors = st.sidebar.multiselect(
        "Purchase Behavior",
        available_behaviors,
        default=available_behaviors
    )
    
    # Spending range filter
    min_spent = float(segments_df['total_spent'].min())
    max_spent = float(segments_df['total_spent'].max())
    spending_range = st.sidebar.slider(
        "Total Spent Range ($)",
        min_value=min_spent,
        max_value=max_spent,
        value=(min_spent, max_spent)
    )
    
    # Orders range filter
    min_orders = int(segments_df['total_orders'].min())
    max_orders = int(segments_df['total_orders'].max())
    orders_range = st.sidebar.slider(
        "Total Orders Range",
        min_value=min_orders,
        max_value=max_orders,
        value=(min_orders, max_orders)
    )
    
    # Apply filters
    filtered_segments = segments_df[
        (segments_df['customer_segment'].isin(selected_segments)) &
        (segments_df['customer_state'].isin(selected_states)) &
        (segments_df['total_spent'].between(spending_range[0], spending_range[1])) &
        (segments_df['total_orders'].between(orders_range[0], orders_range[1]))
    ]
    
    filtered_geo = geo_df[
        (geo_df['customer_segment'].isin(selected_segments)) &
        (geo_df['customer_state'].isin(selected_states)) &
        (geo_df['total_spent'].between(spending_range[0], spending_range[1])) &
        (geo_df['total_orders'].between(orders_range[0], orders_range[1]))
    ]
    
    filtered_behavior = behavior_df[
        (behavior_df['customer_segment'].isin(selected_segments)) &
        (behavior_df['customer_state'].isin(selected_states)) &
        (behavior_df['purchase_behavior'].isin(selected_behaviors)) &
        (behavior_df['total_spent'].between(spending_range[0], spending_range[1])) &
        (behavior_df['total_orders'].between(orders_range[0], orders_range[1]))
    ]
    
    # Overview metrics
    if overview_data:
        st.subheader("📈 Overall Performance")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Total Customers", 
                format_number(overview_data.get('total_customers', 0)),
                help="Total active customers in database"
            )
        with col2:
            st.metric(
                "Total Revenue", 
                format_currency(overview_data.get('total_revenue', 0)),
                help="All-time revenue generated"
            )
        with col3:
            st.metric(
                "Avg Customer Value", 
                format_currency(overview_data.get('avg_customer_value', 0)),
                help="Average revenue per customer"
            )
        with col4:
            st.metric(
                "Customer Satisfaction", 
                format_rating(overview_data.get('avg_customer_rating', 0)),
                help="Average review score across all customers"
            )
    
    # Filtered metrics
    st.subheader("🎯 Filtered Data Overview")
    if not filtered_segments.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Filtered Customers", 
                format_number(len(filtered_segments)),
                help="Customers matching current filters"
            )
        with col2:
            filtered_revenue = filtered_segments['total_spent'].sum()
            st.metric(
                "Filtered Revenue", 
                format_currency(filtered_revenue),
                help="Total revenue from filtered customers"
            )
        with col3:
            avg_filtered_value = filtered_segments['total_spent'].mean()
            st.metric(
                "Avg Filtered Value", 
                format_currency(avg_filtered_value),
                help="Average value of filtered customers"
            )
        with col4:
            avg_filtered_rating = filtered_segments['avg_review_score'].mean()
            st.metric(
                "Avg Rating", 
                format_rating(avg_filtered_rating),
                help="Average rating of filtered customers"
            )
    else:
        st.warning("⚠️ No data matches the current filter selection. Please adjust your filters.")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Segmentation", "🗺️ Geographic", "🛒 Behavior", "📋 Data Table"])
    
    with tab1:
        st.subheader("Customer Segmentation Analysis")
        
        # Segment overview chart
        if not filtered_segments.empty:
            fig_segments = create_segment_summary_chart(filtered_segments)
            if fig_segments:
                st.plotly_chart(fig_segments, use_container_width=True)
            
            # Detailed metrics table
            st.subheader("📋 Segment Details")
            segment_table = create_segment_metrics_table(filtered_segments)
            if not segment_table.empty:
                st.dataframe(segment_table, use_container_width=True, hide_index=True)
            
            # Segment comparison scatter plot
            st.subheader("💎 Segment Performance Comparison")
            fig_scatter = px.scatter(
                filtered_segments,
                x='avg_order_value',
                y='total_spent',
                color='customer_segment',
                size='total_orders',
                title='Customer Value vs Order Value by Segment',
                labels={
                    'avg_order_value': 'Average Order Value ($)', 
                    'total_spent': 'Total Spent ($)',
                    'customer_segment': 'Customer Segment',
                    'total_orders': 'Total Orders'
                },
                hover_data=['avg_review_score'],
                template="plotly_white"
            )
            
            # Format axes
            fig_scatter.update_xaxes(tickformat='$,.0f')
            fig_scatter.update_yaxes(tickformat='$,.0f')
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("⚠️ No segmentation data available for the selected filters.")
    
    with tab2:
        st.subheader("Geographic Distribution Analysis")
        
        if not filtered_geo.empty:
            # Geographic map/chart
            fig_geo = create_geographic_map(filtered_geo)
            if fig_geo:
                st.plotly_chart(fig_geo, use_container_width=True)
            
            # State-wise segment distribution
            st.subheader("🎯 Segment Distribution by State")
            state_segment_pivot = filtered_geo.groupby(['customer_state', 'customer_segment']).size().reset_index(name='count')
            if not state_segment_pivot.empty:
                fig_state_segment = px.bar(
                    state_segment_pivot,
                    x='customer_state',
                    y='count',
                    color='customer_segment',
                    title='Customer Segments by State',
                    labels={'customer_state': 'State', 'count': 'Customer Count', 'customer_segment': 'Segment'},
                    template="plotly_white"
                )
                fig_state_segment.update_layout(xaxis_title="State", yaxis_title="Customer Count")
                st.plotly_chart(fig_state_segment, use_container_width=True)
            
            # Top cities
            st.subheader("🏙️ Top Cities")
            city_summary = filtered_geo.groupby('customer_city').agg({
                'customer_id': 'count',
                'total_spent': 'sum'
            }).round(2)
            city_summary.columns = ['Customer Count', 'Total Revenue']
            city_summary = city_summary.reset_index().sort_values('Total Revenue', ascending=False).head(10)
            
            # Format the display data
            city_summary_display = city_summary.copy()
            city_summary_display['Customer Count'] = city_summary_display['Customer Count'].apply(format_number)
            city_summary_display['Total Revenue'] = city_summary_display['Total Revenue'].apply(format_currency)
            
            st.dataframe(city_summary_display, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No geographic data available for the selected filters.")
    
    with tab3:
        st.subheader("📊 Purchase Behavior Analysis")
        
        if not filtered_behavior.empty:
            # Behavior distribution
            fig_behavior = create_behavior_analysis_chart(filtered_behavior)
            if fig_behavior:
                st.plotly_chart(fig_behavior, use_container_width=True)
            
            # Behavior vs spending
            st.subheader("💰 Spending Patterns by Behavior")
            fig_behavior_spending = px.box(
                filtered_behavior,
                x='purchase_behavior',
                y='total_spent',
                title='Spending Distribution by Purchase Behavior',
                labels={'purchase_behavior': 'Purchase Behavior', 'total_spent': 'Total Spent ($)'},
                template="plotly_white"
            )
            fig_behavior_spending.update_layout(
                xaxis_title="Purchase Behavior",
                yaxis_title="Total Spent ($)",
                yaxis_tickformat="$,.0f"
            )
            st.plotly_chart(fig_behavior_spending, use_container_width=True)
            
            # Behavior summary table
            st.subheader("📈 Behavior Summary Metrics")
            behavior_summary = filtered_behavior.groupby('purchase_behavior').agg({
                'customer_id': 'count',
                'total_spent': 'mean',
                'avg_order_value': 'mean',
                'avg_review_score': 'mean'
            }).round(2)
            behavior_summary.columns = ['Customer Count', 'Avg Spent', 'Avg Order Value', 'Avg Rating']
            behavior_summary = behavior_summary.reset_index()
            
            # Format the display data
            behavior_summary_display = behavior_summary.copy()
            behavior_summary_display['Customer Count'] = behavior_summary_display['Customer Count'].apply(format_number)
            behavior_summary_display['Avg Spent'] = behavior_summary_display['Avg Spent'].apply(format_currency)
            behavior_summary_display['Avg Order Value'] = behavior_summary_display['Avg Order Value'].apply(format_currency)
            behavior_summary_display['Avg Rating'] = behavior_summary_display['Avg Rating'].apply(format_rating)
            
            st.dataframe(behavior_summary_display, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No behavior data available for the selected filters.")
    
    with tab4:
        st.subheader("📋 Raw Data Export")
        
        # Data export options
        col1, col2 = st.columns(2)
        with col1:
            data_view = st.selectbox(
                "Select Data View",
                ["Segmentation Data", "Geographic Data", "Behavior Data"]
            )
        with col2:
            max_rows = st.number_input("Max Rows to Display", min_value=10, max_value=1000, value=100)
        
        if data_view == "Segmentation Data":
            if not filtered_segments.empty:
                st.dataframe(filtered_segments.head(max_rows), use_container_width=True)
                st.download_button(
                    "📥 Download Segmentation Data",
                    filtered_segments.to_csv(index=False),
                    "segmentation_data.csv",
                    "text/csv",
                    help="Download the filtered segmentation data as CSV"
                )
            else:
                st.warning("⚠️ No segmentation data available for the selected filters.")
        elif data_view == "Geographic Data":
            if not filtered_geo.empty:
                st.dataframe(filtered_geo.head(max_rows), use_container_width=True)
                st.download_button(
                    "📥 Download Geographic Data",
                    filtered_geo.to_csv(index=False),
                    "geographic_data.csv",
                    "text/csv",
                    help="Download the filtered geographic data as CSV"
                )
            else:
                st.warning("⚠️ No geographic data available for the selected filters.")
        else:
            if not filtered_behavior.empty:
                st.dataframe(filtered_behavior.head(max_rows), use_container_width=True)
                st.download_button(
                    "📥 Download Behavior Data",
                    filtered_behavior.to_csv(index=False),
                    "behavior_data.csv",
                    "text/csv",
                    help="Download the filtered behavior data as CSV"
                )
            else:
                st.warning("⚠️ No behavior data available for the selected filters.")

if __name__ == "__main__":
    main()
