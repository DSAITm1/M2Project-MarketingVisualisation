"""
Visualization utilities for consistent chart creation
Reusable plotting functions with optimized styling
"""

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any

# Color schemes
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e', 
    'success': '#2ca02c',
    'warning': '#d62728',
    'info': '#9467bd',
    'palette': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
}

def create_metric_cards(metrics: Dict[str, Any], columns: int = 4):
    """Create metric cards in columns"""
    cols = st.columns(columns)
    
    for i, (title, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            if isinstance(value, dict):
                st.metric(title, value.get('value', 'N/A'), value.get('delta', None))
            else:
                st.metric(title, value)

def create_bar_chart(data: pl.DataFrame, x: str, y: str, title: str, 
                    labels: Optional[Dict[str, str]] = None) -> go.Figure:
    """Create optimized bar chart"""
    # Convert to pandas for Plotly compatibility
    pandas_data = data.to_pandas()
    
    fig = px.bar(
        pandas_data, 
        x=x, 
        y=y, 
        title=title,
        labels=labels or {},
        color_discrete_sequence=COLORS['palette']
    )
    
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=400
    )
    
    return fig

def create_pie_chart(values: list, names: list, title: str) -> go.Figure:
    """Create optimized pie chart"""
    fig = px.pie(
        values=values,
        names=names,
        title=title,
        color_discrete_sequence=COLORS['palette']
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=400
    )
    
    return fig

def create_line_chart(data: pl.DataFrame, x: str, y: str, title: str,
                     labels: Optional[Dict[str, str]] = None) -> go.Figure:
    """Create optimized line chart"""
    # Convert to pandas for Plotly compatibility
    pandas_data = data.to_pandas()
    
    fig = px.line(
        pandas_data,
        x=x,
        y=y,
        title=title,
        labels=labels or {},
        color_discrete_sequence=COLORS['palette']
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=400
    )
    
    return fig

def create_map_chart(data: pl.DataFrame, lat: str, lon: str, 
                    size: Optional[str] = None, color: Optional[str] = None,
                    title: str = "Geographic Distribution") -> go.Figure:
    """Create optimized map visualization"""
    # Convert to pandas for Plotly compatibility
    pandas_data = data.to_pandas()
    
    fig = px.scatter_map(
        pandas_data,
        lat=lat,
        lon=lon,
        size=size,
        color=color,
        title=title,
        color_continuous_scale="Viridis",
        height=500
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def display_chart(fig: go.Figure, key: Optional[str] = None):
    """Display chart with consistent styling"""
    st.plotly_chart(fig, width="stretch", key=key)

def display_dataframe(df: pl.DataFrame, title: str, max_rows: int = 100):
    """Display dataframe with consistent styling"""
    st.subheader(title)
    
    if df.is_empty():
        st.warning("No data available")
        return
    
    # Convert to pandas for display
    pandas_df = df.to_pandas()
    
    # Show data info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", f"{len(pandas_df):,}")
    with col2:
        st.metric("Columns", len(pandas_df.columns))
    with col3:
        memory_usage = pandas_df.memory_usage(deep=True).sum() / 1024 / 1024
        st.metric("Memory Usage", f"{memory_usage:.1f} MB")
    
    # Display data
    st.dataframe(pandas_df.head(max_rows), width="stretch")
    
    if len(pandas_df) > max_rows:
        st.info(f"Showing first {max_rows} rows of {len(pandas_df):,} total rows")

def create_summary_stats(df: pl.DataFrame, numeric_only: bool = True) -> pl.DataFrame:
    """Create summary statistics for dataframe"""
    if df.is_empty():
        return pl.DataFrame()
    
    if numeric_only:
        # Get numeric columns
        numeric_cols = []
        for col in df.columns:
            if df.select(pl.col(col).dtype).item() in [pl.Float64, pl.Int64, pl.Float32, pl.Int32]:
                numeric_cols.append(col)
        
        if numeric_cols:
            # Calculate summary statistics for numeric columns
            stats_data = {}
            for col in numeric_cols:
                col_stats = df.select([
                    pl.col(col).count().alias(f"{col}_count"),
                    pl.col(col).mean().alias(f"{col}_mean"),
                    pl.col(col).std().alias(f"{col}_std"),
                    pl.col(col).min().alias(f"{col}_min"),
                    pl.col(col).max().alias(f"{col}_max")
                ])
                for stat_col in col_stats.columns:
                    stats_data[stat_col] = [col_stats.select(pl.col(stat_col)).item()]
            
            return pl.DataFrame(stats_data)
    
    # For non-numeric or all columns, return basic info
    return pl.DataFrame({
        "total_rows": [df.height],
        "total_columns": [len(df.columns)],
        "columns": [", ".join(df.columns)]
    })
