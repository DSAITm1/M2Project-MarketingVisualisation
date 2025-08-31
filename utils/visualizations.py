"""
Visualization utilities for consistent chart creation
Reusable plotting functions with optimized styling
"""

import streamlit as st
import pandas as pd
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

def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, 
                    labels: Optional[Dict[str, str]] = None) -> go.Figure:
    """Create optimized bar chart"""
    fig = px.bar(
        data, 
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

def create_line_chart(data: pd.DataFrame, x: str, y: str, title: str,
                     labels: Optional[Dict[str, str]] = None) -> go.Figure:
    """Create optimized line chart"""
    fig = px.line(
        data,
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

def create_map_chart(data: pd.DataFrame, lat: str, lon: str, 
                    size: Optional[str] = None, color: Optional[str] = None,
                    title: str = "Geographic Distribution") -> go.Figure:
    """Create optimized map visualization"""
    fig = px.scatter_map(
        data,
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

def display_dataframe(df: pd.DataFrame, title: str, max_rows: int = 100):
    """Display dataframe with consistent styling"""
    st.subheader(title)
    
    if df.empty:
        st.warning("No data available")
        return
    
    # Show data info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rows", f"{len(df):,}")
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
        st.metric("Memory Usage", f"{memory_usage:.1f} MB")
    
    # Display data
    st.dataframe(df.head(max_rows), width="stretch")
    
    if len(df) > max_rows:
        st.info(f"Showing first {max_rows} rows of {len(df):,} total rows")

def create_summary_stats(df: pd.DataFrame, numeric_only: bool = True) -> pd.DataFrame:
    """Create summary statistics for dataframe"""
    if df.empty:
        return pd.DataFrame()
    
    if numeric_only:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            return df[numeric_cols].describe()
    
    return df.describe(include='all')
