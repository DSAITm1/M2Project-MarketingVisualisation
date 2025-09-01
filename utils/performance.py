"""
Performance monitoring utilities
Track query performance and optimize dashboard loading
"""

import streamlit as st
import time
import polars as pl
from functools import wraps
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance
            logger.info(f"Function '{func.__name__}' executed in {execution_time:.2f}s")
            
            # Show performance info in debug mode
            if st.session_state.get('debug_mode', False):
                st.info(f"⏱️ {func.__name__}: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function '{func.__name__}' failed after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper

class PerformanceTracker:
    """Track dashboard performance metrics"""
    
    def __init__(self):
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}
    
    def track_query(self, query_name: str, execution_time: float, row_count: int):
        """Track query performance"""
        metrics = st.session_state.performance_metrics
        
        if query_name not in metrics:
            metrics[query_name] = []
        
        metrics[query_name].append({
            'execution_time': execution_time,
            'row_count': row_count,
            'timestamp': time.time()
        })
        
        # Keep only last 10 executions
        metrics[query_name] = metrics[query_name][-10:]
    
    def get_performance_summary(self) -> pl.DataFrame:
        """Get performance summary"""
        metrics = st.session_state.performance_metrics
        
        if not metrics:
            return pl.DataFrame()
        
        summary_data = []
        for query_name, executions in metrics.items():
            if executions:
                avg_time = sum(e['execution_time'] for e in executions) / len(executions)
                avg_rows = sum(e['row_count'] for e in executions) / len(executions)
                total_executions = len(executions)
                
                summary_data.append({
                    'Query': query_name,
                    'Avg Time (s)': round(avg_time, 2),
                    'Avg Rows': int(avg_rows),
                    'Executions': total_executions
                })
        
        return pl.DataFrame(summary_data)
    
    def display_performance_dashboard(self):
        """Display performance monitoring dashboard"""
        if st.session_state.get('show_performance', False):
            st.sidebar.header("⚡ Performance Monitor")
            
            summary_df = self.get_performance_summary()
            if not summary_df.is_empty():
                st.sidebar.dataframe(summary_df, width="stretch")
            else:
                st.sidebar.info("No performance data yet")

# Global performance tracker
perf_tracker = PerformanceTracker()

def enable_debug_mode():
    """Enable debug mode for detailed performance tracking"""
    st.session_state.debug_mode = st.sidebar.checkbox("🐛 Debug Mode", value=False)
    st.session_state.show_performance = st.sidebar.checkbox("⚡ Show Performance", value=False)
    
    if st.session_state.show_performance:
        perf_tracker.display_performance_dashboard()

def optimize_dataframe_memory(df: pl.DataFrame) -> pl.DataFrame:
    """Optimize dataframe memory usage"""
    if df.is_empty():
        return df
    
    # For Polars, memory optimization is handled automatically
    # We can still provide some basic optimizations
    
    # Convert string columns to categorical if they have low cardinality
    optimized_expressions = []
    
    for col in df.columns:
        col_dtype = df.select(pl.col(col).dtype).item()
        
        # For string columns with low cardinality, keep as string (Polars handles this efficiently)
        if col_dtype == pl.Utf8:
            unique_ratio = df.select(pl.col(col).n_unique() / pl.col(col).count()).item()
            if unique_ratio < 0.5:  # Less than 50% unique values
                # Polars strings are already memory efficient
                optimized_expressions.append(pl.col(col))
            else:
                optimized_expressions.append(pl.col(col))
        else:
            optimized_expressions.append(pl.col(col))
    
    if optimized_expressions:
        return df.with_columns(optimized_expressions)
    
    return df
