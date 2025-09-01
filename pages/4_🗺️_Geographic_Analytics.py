"""
Geographic Analytics Page
Location-based insights and geospatial analysis
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.database import load_config, get_bigquery_client, execute_query
from utils.visualizations import (create_metric_cards, create_bar_chart, create_pie_chart, 
                                create_line_chart, display_chart, display_dataframe)
from utils.data_processing import get_geographic_summary, format_currency

st.set_page_config(page_title="Geographic Analytics", page_icon="🗺️", layout="wide")

@st.cache_data(ttl=3600)
def load_geographic_analytics():
    """Load geographic analytics from BigQuery"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    WITH geo_analytics AS (
        SELECT 
            c.customer_state,
            c.customer_city,
            g.geolocation_lat,
            g.geolocation_lng,
            COUNT(DISTINCT c.customer_unique_id) as customer_count,
            COUNT(DISTINCT oi.order_id) as order_count,
            SUM(oi.price) as total_revenue,
            AVG(oi.price) as avg_order_value,
            AVG(oi.review_score) as avg_review_score,
            COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN oi.order_id END) as delivered_orders
        FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c
            ON oi.customer_sk = c.customer_sk
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_geolocation` g 
            ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
        JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
            ON oi.order_sk = o.order_sk
        WHERE g.geolocation_lat IS NOT NULL 
        AND g.geolocation_lng IS NOT NULL
        AND g.geolocation_lat BETWEEN -35 AND 10  -- Brazil bounds
        AND g.geolocation_lng BETWEEN -75 AND -30 -- Brazil bounds
        GROUP BY 1, 2, 3, 4
        HAVING customer_count > 0
    )
    SELECT * FROM geo_analytics
    LIMIT 5000
    """
    
    return execute_query(query, "geographic_analytics")

@st.cache_data(ttl=3600)
def load_state_summary():
    """Load state-level summary data"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    query = f"""
    SELECT 
        c.customer_state,
        COUNT(DISTINCT c.customer_unique_id) as customer_count,
        COUNT(DISTINCT oi.order_id) as order_count,
        SUM(oi.price) as total_revenue,
        AVG(oi.price) as avg_order_value,
        AVG(oi.review_score) as avg_review_score,
        COUNT(DISTINCT CASE WHEN o.order_status = 'delivered' THEN oi.order_id END) as delivered_orders
    FROM `{config['project_id']}.{config['dataset_id']}.fact_order_items` oi
    JOIN `{config['project_id']}.{config['dataset_id']}.dim_customer` c
        ON oi.customer_sk = c.customer_sk
    JOIN `{config['project_id']}.{config['dataset_id']}.dim_orders` o 
        ON oi.order_sk = o.order_sk
    GROUP BY 1
    HAVING customer_count > 0
    ORDER BY total_revenue DESC
    """
    
    return execute_query(query, "state_summary")

def main():
    st.title("🗺️ Geographic Market Intelligence")
    st.markdown("**Strategic Geographic Insights for Marketing Directors**")
    
    # Load data
    with st.spinner("Loading geographic data..."):
        geo_df = load_geographic_analytics()
        state_df = load_state_summary()
    
    if geo_df.is_empty() and state_df.is_empty():
        st.error("No geographic data available.")
        return
    
    # Executive Summary for Marketing Director
    st.header("📊 Geographic Market Overview")

    if not state_df.is_empty():
        # Calculate key market metrics
        total_states = len(state_df)
        total_customers = state_df.select('customer_count').sum().to_series().to_list()[0]
        total_revenue = state_df.select('total_revenue').sum().to_series().to_list()[0]
        avg_order_value = state_df.select('avg_order_value').mean().to_series().to_list()[0]

        # Market concentration analysis
        top_5_revenue = state_df.sort('total_revenue', descending=True).limit(5).select('total_revenue').sum().to_series().to_list()[0]
        market_concentration = (top_5_revenue / total_revenue) * 100

        # Geographic performance metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("🏛️ States Active", f"{total_states}", help="Number of states with customer activity")
            st.metric("👥 Total Customers", f"{total_customers:,}", help="Total unique customers across all states")

        with col2:
            st.metric("💰 Total Revenue", f"${total_revenue:,.0f}", help="Total revenue from all geographic markets")
            st.metric("🛒 Avg Order Value", f"${avg_order_value:.2f}", help="Average order value across markets")

        with col3:
            st.metric("🎯 Market Concentration", f"{market_concentration:.1f}%", help="Revenue concentration in top 5 states")
            top_state = state_df['customer_state'][0]
            st.metric("🏆 Top Market", f"{top_state}", help="State with highest revenue")

        with col4:
            # Calculate market penetration opportunity
            avg_customers_per_state = total_customers / total_states
            st.metric("📊 Avg Customers/State", f"{avg_customers_per_state:,.0f}")
            st.metric("🚀 Growth Potential", "High" if market_concentration > 70 else "Medium", help="Market expansion opportunities")

    # Strategic Market Insights
    st.header("🎯 Strategic Market Intelligence")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        st.subheader("💰 Revenue Optimization Opportunities")

        if not state_df.is_empty():
            # High-potential markets
            median_customers = state_df.select('customer_count').median().to_series().to_list()[0]
            quantile_80_revenue = state_df.select('total_revenue').quantile(0.8).to_series().to_list()[0]
            
            high_potential = state_df.filter(
                (pl.col('customer_count') > median_customers) &
                (pl.col('avg_review_score') > 4.0) &
                (pl.col('total_revenue') < quantile_80_revenue)
            )

            if not high_potential.is_empty():
                st.success(f"🎯 **{len(high_potential)} high-potential markets** with strong satisfaction but below-average revenue")
                st.info("**Recommendation**: Invest in targeted marketing campaigns in these states")

            # Market efficiency analysis
            revenue_per_customer = state_df['total_revenue'] / state_df['customer_count']
            revenue_threshold = revenue_per_customer.quantile(0.8)
            efficient_markets = state_df.filter(revenue_per_customer > revenue_threshold)
            st.metric("⚡ High-Efficiency Markets", f"{efficient_markets.height} states", help="Markets with highest revenue per customer")

    with insights_col2:
        st.subheader("📈 Market Expansion Strategy")

        if not state_df.is_empty():
            # Underpenetrated markets
            quantile_30_customers = state_df.select('customer_count').quantile(0.3).to_series().to_list()[0]
            
            underpenetrated = state_df.filter(
                (pl.col('customer_count') < quantile_30_customers) &
                (pl.col('avg_review_score') > 3.5)
            )

            if not underpenetrated.is_empty():
                st.warning(f"🚀 **{len(underpenetrated)} underpenetrated markets** with growth potential")
                st.info("**Recommendation**: Consider market entry strategies for these states")

            # Customer satisfaction leaders
            satisfaction_leaders = state_df[state_df['avg_review_score'] > 4.2]
            st.success(f"⭐ **{len(satisfaction_leaders)} markets** with exceptional customer satisfaction")
            st.info("**Recommendation**: Use these as benchmark markets for best practices")

    # Market Performance Dashboard
    st.header("📊 Market Performance Dashboard")

    if not state_df.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Revenue by State")
            top_revenue_states = state_df.sort('total_revenue', descending=True).limit(15)
            fig = px.bar(
                top_revenue_states,
                x='customer_state',
                y='total_revenue',
                title="Top 15 States by Revenue",
                labels={'total_revenue': 'Revenue ($)', 'customer_state': 'State'}
            )
            st.plotly_chart(fig, width="stretch")
        
        with col2:
            st.subheader("👥 Customers by State")
            top_customer_states = state_df.nlargest(15, 'customer_count')
            fig = px.bar(
                top_customer_states,
                x='customer_state',
                y='customer_count',
                title="Top 15 States by Customer Count",
                labels={'customer_count': 'Customer Count', 'customer_state': 'State'}
            )
            st.plotly_chart(fig, width="stretch")
    
    # Map visualization
    st.header("🗺️ Interactive Map")
    
    if not geo_df.is_empty():
        # Filter for better visualization
        map_data = geo_df.filter(
            (pl.col('customer_count') >= 5) &  # At least 5 customers
            (pl.col('geolocation_lat').is_not_null()) &
            (pl.col('geolocation_lng').is_not_null())
        )
        
        if not map_data.is_empty():
            col1, col2 = st.columns([3, 1])
            
            with col2:
                st.subheader("🎛️ Map Controls")
                
                # Map type selection
                map_type = st.selectbox(
                    "Map Visualization",
                    ["Customer Count", "Revenue", "Avg Review Score", "Order Count"]
                )
                
                # Color column mapping
                color_mapping = {
                    "Customer Count": "customer_count",
                    "Revenue": "total_revenue",
                    "Avg Review Score": "avg_review_score",
                    "Order Count": "order_count"
                }
                
                color_col = color_mapping[map_type]
                
                # Size control
                size_by = st.selectbox(
                    "Bubble Size by",
                    ["Customer Count", "Revenue", "Order Count"],
                    index=1
                )
                
                size_mapping = {
                    "Customer Count": "customer_count",
                    "Revenue": "total_revenue",
                    "Order Count": "order_count"
                }
                
                size_col = size_mapping[size_by]
            
            with col1:
                st.subheader(f"📍 Brazil Map - {map_type}")
                
                fig = px.scatter_mapbox(
                    map_data,
                    lat='geolocation_lat',
                    lon='geolocation_lng',
                    color=color_col,
                    size=size_col,
                    hover_name='customer_city',
                    hover_data={
                        'customer_state': True,
                        'customer_count': True,
                        'total_revenue': ':.2f',
                        'avg_review_score': ':.2f'
                    },
                    color_continuous_scale='Viridis',
                    mapbox_style='open-street-map',
                    zoom=3,
                    center={'lat': -15, 'lon': -50},  # Center on Brazil
                    title=f"Geographic Distribution - {map_type}"
                )
                
                fig.update_layout(height=600)
                st.plotly_chart(fig, width="stretch")
    
    # Regional comparison
    st.header("🏛️ Regional Comparison")
    
    if not state_df.is_empty():
        # Define Brazilian regions (simplified)
        region_mapping = {
            'SP': 'Southeast', 'RJ': 'Southeast', 'MG': 'Southeast', 'ES': 'Southeast',
            'RS': 'South', 'SC': 'South', 'PR': 'South',
            'BA': 'Northeast', 'PE': 'Northeast', 'CE': 'Northeast', 'PB': 'Northeast',
            'RN': 'Northeast', 'AL': 'Northeast', 'SE': 'Northeast', 'PI': 'Northeast', 'MA': 'Northeast',
            'GO': 'Central-West', 'MT': 'Central-West', 'MS': 'Central-West', 'DF': 'Central-West',
            'AM': 'North', 'PA': 'North', 'RO': 'North', 'AC': 'North', 'RR': 'North', 'AP': 'North', 'TO': 'North'
        }
        
        state_df = state_df.with_columns(
            pl.col('customer_state').map_dict(region_mapping, default='Other').alias('region')
        )
        
        regional_summary = state_df.group_by('region').agg([
            pl.col('customer_count').sum().alias('customer_count'),
            pl.col('order_count').sum().alias('order_count'),
            pl.col('total_revenue').sum().alias('total_revenue'),
            pl.col('avg_order_value').mean().alias('avg_order_value'),
            pl.col('avg_review_score').mean().alias('avg_review_score')
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌎 Revenue by Region")
            fig = px.pie(
                regional_summary,
                values='total_revenue',
                names='region',
                title="Revenue Distribution by Brazilian Region"
            )
            st.plotly_chart(fig, width="stretch")
        
        with col2:
            st.subheader("⭐ Customer Satisfaction by Region")
            fig = px.bar(
                regional_summary,
                x='region',
                y='avg_review_score',
                title="Average Review Score by Region"
            )
            st.plotly_chart(fig, width="stretch")
    
    # Market Opportunity Analysis
    st.header("🚀 Market Opportunity Analysis")
    
    if not state_df.is_empty():
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💎 High-Value Market Opportunities")
            
            # Identify markets with high growth potential
            quantile_60_customers = state_df.select('customer_count').quantile(0.6).to_series().to_list()[0]
            quantile_70_revenue = state_df.select('total_revenue').quantile(0.7).to_series().to_list()[0]
            
            high_potential_markets = state_df.filter(
                (pl.col('customer_count') > quantile_60_customers) &
                (pl.col('avg_review_score') > 4.0) &
                (pl.col('total_revenue') < quantile_70_revenue)
            ).sort('total_revenue', descending=True).limit(5)
            
            if not high_potential_markets.is_empty():
                st.success("**Top 5 High-Potential Markets for Investment:**")
                for row in high_potential_markets.iter_rows(named=True):
                    st.write(f"🏆 **{row['customer_state']}**: {row['customer_count']:,} customers, "
                           f"${row['total_revenue']:,.0f} revenue, "
                           f"{row['avg_review_score']:.1f}⭐ satisfaction")
                st.info("💡 **Strategy**: Targeted marketing campaigns and loyalty programs")
            
            # Market penetration analysis
            total_customers = state_df.select('customer_count').sum().to_series().to_list()[0]
            market_penetration = (total_customers / 211000000) * 100  # Brazil population estimate
            st.metric("🌍 Market Penetration", f"{market_penetration:.3f}%", 
                     help="Percentage of Brazilian population as customers")
        
        with col2:
            st.subheader("🎯 Strategic Expansion Targets")
            
            # Identify underserved markets with good satisfaction
            quantile_40_customers = state_df.select('customer_count').quantile(0.4).to_series().to_list()[0]
            quantile_20_revenue = state_df.select('total_revenue').quantile(0.2).to_series().to_list()[0]
            
            expansion_targets = state_df.filter(
                (pl.col('customer_count') < quantile_40_customers) &
                (pl.col('avg_review_score') > 3.8) &
                (pl.col('total_revenue') > quantile_20_revenue)
            ).sort('total_revenue', descending=True).limit(5)
            
            if not expansion_targets.is_empty():
                st.warning("**Top 5 Strategic Expansion Markets:**")
                for row in expansion_targets.iter_rows(named=True):
                    st.write(f"🚀 **{row['customer_state']}**: {row['customer_count']:,} customers, "
                           f"${row['total_revenue']:,.0f} revenue, "
                           f"{row['avg_review_score']:.1f}⭐ satisfaction")
                st.info("💡 **Strategy**: Market development and customer acquisition campaigns")
            
            # Revenue growth potential
            total_revenue = state_df.select('total_revenue').sum().to_series().to_list()[0]
            total_customers = state_df.select('customer_count').sum().to_series().to_list()[0]
            avg_revenue_per_customer = total_revenue / total_customers
            potential_new_customers = int(total_customers * 0.2)  # 20% growth target
            potential_revenue = potential_new_customers * avg_revenue_per_customer
            st.metric("💰 Revenue Growth Potential", f"${potential_revenue:,.0f}", 
                     help="Potential revenue from 20% customer base expansion")
    
    # Strategic Recommendations
    st.header("🎯 Strategic Recommendations")
    
    if not state_df.is_empty():
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.subheader("📈 Revenue Optimization")
            
            # Top revenue states for focus
            top_revenue_states = state_df.sort('total_revenue', descending=True).limit(3)
            st.success("**Focus Revenue Optimization in Top Markets:**")
            for row in top_revenue_states.iter_rows(named=True):
                st.write(f"💰 **{row['customer_state']}**: ${row['total_revenue']:,.0f} revenue")
            st.info("**Action Items:**\n"
                   "• Implement premium product positioning\n"
                   "• Develop loyalty programs\n"
                   "• Optimize pricing strategies\n"
                   "• Enhance customer experience")
            
            # Cross-selling opportunities
            quantile_80_order_value = state_df.select('avg_order_value').quantile(0.8).to_series().to_list()[0]
            high_value_states = state_df.filter(pl.col('avg_order_value') > quantile_80_order_value)
            st.metric("🎯 High-Value Markets", f"{len(high_value_states)} states", 
                     help="States with above-average order values")
        
        with rec_col2:
            st.subheader("🚀 Market Expansion")
            
            # Market expansion priorities
            quantile_50_customers = state_df.select('customer_count').quantile(0.5).to_series().to_list()[0]
            
            expansion_priority = state_df.filter(
                (pl.col('customer_count') < quantile_50_customers) &
                (pl.col('avg_review_score') > 4.0)
            ).sort('avg_review_score', descending=True).limit(3)
            
            if not expansion_priority.is_empty():
                st.warning("**Priority Markets for Expansion:**")
                for row in expansion_priority.iter_rows(named=True):
                    st.write(f"🚀 **{row['customer_state']}**: High satisfaction ({row['avg_review_score']:.1f}⭐) "
                           f"with growth potential")
                st.info("**Action Items:**\n"
                       "• Launch targeted marketing campaigns\n"
                       "• Partner with local influencers\n"
                       "• Develop region-specific promotions\n"
                       "• Invest in local market research")
            
            # Customer satisfaction improvement
            low_satisfaction_states = state_df.filter(pl.col('avg_review_score') < 3.8)
            if not low_satisfaction_states.is_empty():
                st.error(f"⚠️ **{len(low_satisfaction_states)} markets** need satisfaction improvement")
                st.info("**Action Items:**\n"
                       "• Conduct customer feedback analysis\n"
                       "• Improve delivery processes\n"
                       "• Enhance product quality\n"
                       "• Implement service recovery programs")
    
    # Business Intelligence Summary
    st.header("📊 Business Intelligence Summary")
    
    if not state_df.is_empty():
        # Key business insights
        total_market_revenue = state_df.select('total_revenue').sum().to_series().to_list()[0]
        total_market_customers = state_df.select('customer_count').sum().to_series().to_list()[0]
        avg_market_satisfaction = state_df.select('avg_review_score').mean().to_series().to_list()[0]
        
        # Market concentration analysis
        top_3_revenue = state_df.sort('total_revenue', descending=True).limit(3).select('total_revenue').sum().to_series().to_list()[0]
        concentration_ratio = (top_3_revenue / total_market_revenue) * 100
        
        # Geographic diversity score
        revenue_std = state_df.select('total_revenue').std().to_series().to_list()[0]
        revenue_mean = state_df.select('total_revenue').mean().to_series().to_list()[0]
        diversity_score = (revenue_std / revenue_mean) * 100
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.subheader("💰 Market Performance")
            st.metric("Total Market Revenue", f"${total_market_revenue:,.0f}")
            st.metric("Market Concentration", f"{concentration_ratio:.1f}%", 
                     help="Revenue share of top 3 states")
            st.metric("Geographic Diversity", f"{diversity_score:.1f}%", 
                     help="Revenue distribution variance across states")
        
        with summary_col2:
            st.subheader("👥 Customer Insights")
            st.metric("Total Customers", f"{total_market_customers:,}")
            st.metric("Avg Satisfaction", f"{avg_market_satisfaction:.2f}⭐")
            avg_customers_per_state = total_market_customers / len(state_df)
            st.metric("Avg Customers/State", f"{avg_customers_per_state:,.0f}")
        
        with summary_col3:
            st.subheader("🎯 Strategic KPIs")
            # Calculate customer lifetime value proxy
            avg_order_value = state_df.select('avg_order_value').mean().to_series().to_list()[0]
            total_orders = state_df.select('order_count').sum().to_series().to_list()[0]
            total_customers = state_df.select('customer_count').sum().to_series().to_list()[0]
            avg_orders_per_customer = total_orders / total_customers
            clv_proxy = avg_order_value * avg_orders_per_customer
            st.metric("Customer Value Proxy", f"${clv_proxy:.2f}")
            
            # Market efficiency ratio
            revenue_per_customer = total_market_revenue / total_market_customers
            st.metric("Revenue/Customer", f"${revenue_per_customer:.2f}")
            
            # Growth opportunity index
            satisfaction_weighted_opportunity = (avg_market_satisfaction / 5.0) * (1 - concentration_ratio/100)
            st.metric("Growth Opportunity", f"{satisfaction_weighted_opportunity:.2f}", 
                     help="Combined satisfaction and diversification opportunity")
        
        # Executive insights
        st.subheader("🏆 Executive Insights")
        
        insights = []
        
        if concentration_ratio > 60:
            insights.append("⚠️ **High market concentration** - Consider diversification strategies")
        else:
            insights.append("✅ **Balanced market distribution** - Good geographic diversification")
        
        if avg_market_satisfaction > 4.0:
            insights.append("⭐ **Excellent customer satisfaction** - Leverage as competitive advantage")
        elif avg_market_satisfaction < 3.5:
            insights.append("⚠️ **Customer satisfaction needs improvement** - Priority action required")
        
        if diversity_score > 100:
            insights.append("📊 **High geographic variance** - Opportunity for market balancing")
        else:
            insights.append("🎯 **Stable geographic performance** - Consistent market presence")
        
        for insight in insights:
            st.info(insight)
        
        # Strategic priorities
        st.subheader("🎯 Strategic Priorities")
        
        priorities = [
            "1. **Revenue Optimization**: Focus on top-performing markets (SP, RJ, MG)",
            "2. **Market Expansion**: Target high-satisfaction, underpenetrated states",
            "3. **Customer Experience**: Maintain high satisfaction levels across all markets",
            "4. **Geographic Diversification**: Balance revenue concentration risks",
            "5. **Local Market Adaptation**: Develop region-specific marketing strategies"
        ]
        
        for priority in priorities:
            st.write(priority)
    
    # Detailed data tables
    st.header("📋 Geographic Data")
    
    tab1, tab2 = st.tabs(["State Summary", "City Details"])
    
    with tab1:
        if not state_df.is_empty():
            st.subheader("🏛️ State Performance Summary")
            display_df = state_df.with_columns(
                (pl.col('delivered_orders') / pl.col('order_count') * 100).round(1).alias('delivery_rate')
            )
            st.dataframe(display_df, width="stretch")
    
    with tab2:
        if not geo_df.is_empty():
            st.subheader("🏙️ City-Level Details")
            
            # City filters
            col1, col2 = st.columns(2)
            
            with col1:
                min_customers = st.number_input("Min Customers", min_value=1, value=10)
            
            with col2:
                selected_states = st.multiselect(
                    "Filter by State",
                    geo_df['customer_state'].unique(),
                    default=geo_df['customer_state'].unique()[:10]
                )
            
            filtered_geo = geo_df[
                (geo_df['customer_count'] >= min_customers) &
                (geo_df['customer_state'].isin(selected_states))
            ]
            
            st.dataframe(filtered_geo, width="stretch")

if __name__ == "__main__":
    main()
