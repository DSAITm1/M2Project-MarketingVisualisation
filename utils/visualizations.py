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

def create_metric_cards(metrics, columns: int = 4):
    """Create metric cards in columns - supports both dict and list formats"""
    cols = st.columns(columns)
    
    # Handle different input formats
    if isinstance(metrics, dict):
        items = list(metrics.items())
    elif isinstance(metrics, list):
        # Assume list of tuples (title, value, icon) or (title, value)
        items = metrics
    else:
        st.error("Metrics must be either a dictionary or a list of tuples")
        return
    
    for i, item in enumerate(items):
        with cols[i % columns]:
            if len(item) == 3:  # (title, value, icon)
                title, value, icon = item
                st.metric(f"{icon} {title}", value)
            elif len(item) == 2:  # (title, value)
                title, value = item
                if isinstance(value, dict):
                    st.metric(title, value.get('value', 'N/A'), value.get('delta', None))
                else:
                    st.metric(title, value)
            else:
                st.error(f"Invalid metric format: {item}")

def create_bar_chart(data: pl.DataFrame, x: str, y: str, title: str, 
                    labels: Optional[Dict[str, str]] = None) -> go.Figure:
    """Create optimized bar chart - 100% Polars compatible"""
    # Always work with Polars, convert only for Plotly
    if not isinstance(data, pl.DataFrame):
        # If somehow pandas is passed, convert it to Polars first
        data = pl.from_pandas(data)
    
    # Convert to pandas only for Plotly rendering
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

def create_pie_chart(data: pl.DataFrame, values: str, names: str, title: str) -> go.Figure:
    """Create optimized pie chart - 100% Polars compatible"""
    # Always work with Polars, convert only for Plotly
    if not isinstance(data, pl.DataFrame):
        # If somehow pandas is passed, convert it to Polars first
        data = pl.from_pandas(data)
    
    # Convert to pandas only for Plotly rendering
    pandas_data = data.to_pandas()
    
    fig = px.pie(
        pandas_data,
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
    """Create optimized line chart - 100% Polars compatible"""
    # Always work with Polars, convert only for Plotly
    if not isinstance(data, pl.DataFrame):
        # If somehow pandas is passed, convert it to Polars first
        data = pl.from_pandas(data)
    
    # Convert to pandas only for Plotly rendering
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
    """Create optimized map visualization - 100% Polars compatible"""
    # Always work with Polars, convert only for Plotly
    if not isinstance(data, pl.DataFrame):
        # If somehow pandas is passed, convert it to Polars first
        data = pl.from_pandas(data)
    
    # Convert to pandas only for Plotly rendering
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
    """Display dataframe with consistent styling - 100% Polars compatible"""
    st.subheader(title)
    
    if df.is_empty():
        st.warning("No data available")
        return
    
    # Always work with Polars, convert only for display
    if not isinstance(df, pl.DataFrame):
        # If somehow pandas is passed, convert it to Polars first
        df = pl.from_pandas(df)
    
    # Convert to pandas only for Streamlit display
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
    
    # Display data with pure Polars approach
    display_df = pandas_df[:max_rows] if len(pandas_df) > max_rows else pandas_df
    st.dataframe(display_df, width="stretch")
    
    if len(pandas_df) > max_rows:
        st.info(f"Showing first {max_rows} rows of {len(pandas_df):,} total rows")

def create_summary_stats(df: pl.DataFrame, numeric_only: bool = True) -> pl.DataFrame:
    """Create summary statistics for dataframe"""
    if df.is_empty():
        return pl.DataFrame()
    
    if numeric_only:
        # Get numeric columns
        numeric_cols = []
        try:
            for col in df.columns:
                try:
                    dtype_result = df.select(pl.col(col).dtype)
                    if not dtype_result.is_empty():
                        col_dtype = dtype_result.item()
                        if col_dtype in [pl.Float64, pl.Int64, pl.Float32, pl.Int32]:
                            numeric_cols.append(col)
                except Exception:
                    continue
            
            if numeric_cols:
                # Calculate summary statistics for numeric columns
                stats_data = {}
                for col in numeric_cols:
                    try:
                        col_stats = df.select([
                            pl.col(col).count().alias(f"{col}_count"),
                            pl.col(col).mean().alias(f"{col}_mean"),
                            pl.col(col).std().alias(f"{col}_std"),
                            pl.col(col).min().alias(f"{col}_min"),
                            pl.col(col).max().alias(f"{col}_max")
                        ])
                        for stat_col in col_stats.columns:
                            try:
                                stats_data[stat_col] = [col_stats.select(pl.col(stat_col)).item()] if not col_stats.is_empty() else [0]
                            except Exception:
                                stats_data[stat_col] = [0]
                    except Exception:
                        continue
                
                return pl.DataFrame(stats_data)
        except Exception:
            # If any error occurs, fall through to basic info
            pass
    
    # For non-numeric or all columns, return basic info
    return pl.DataFrame({
        "total_rows": [df.height],
        "total_columns": [len(df.columns)],
        "columns": [", ".join(df.columns)]
    })
