"""
Performance monitoring utilities
Track query performance and optimize dashboard loading
"""

import streamlit as st
import time
import pandas as pd
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
    
    def get_performance_summary(self) -> pd.DataFrame:
        """Get performance summary"""
        metrics = st.session_state.performance_metrics
        
        if not metrics:
            return pd.DataFrame()
        
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
        
        return pd.DataFrame(summary_data)
    
    def display_performance_dashboard(self):
        """Display performance monitoring dashboard"""
        if st.session_state.get('show_performance', False):
            st.sidebar.header("⚡ Performance Monitor")
            
            summary_df = self.get_performance_summary()
            if not summary_df.empty:
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

def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize dataframe memory usage"""
    if df.empty:
        return df
    
    optimized_df = df.copy()
    
    # Optimize numeric columns
    for col in optimized_df.select_dtypes(include=['int64']).columns:
        if optimized_df[col].min() >= 0:
            if optimized_df[col].max() < 255:
                optimized_df[col] = optimized_df[col].astype('uint8')
            elif optimized_df[col].max() < 65535:
                optimized_df[col] = optimized_df[col].astype('uint16')
            elif optimized_df[col].max() < 4294967295:
                optimized_df[col] = optimized_df[col].astype('uint32')
        else:
            if optimized_df[col].min() > -128 and optimized_df[col].max() < 127:
                optimized_df[col] = optimized_df[col].astype('int8')
            elif optimized_df[col].min() > -32768 and optimized_df[col].max() < 32767:
                optimized_df[col] = optimized_df[col].astype('int16')
            elif optimized_df[col].min() > -2147483648 and optimized_df[col].max() < 2147483647:
                optimized_df[col] = optimized_df[col].astype('int32')
    
    # Optimize float columns
    for col in optimized_df.select_dtypes(include=['float64']).columns:
        optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
    
    # Optimize object columns (categorical)
    for col in optimized_df.select_dtypes(include=['object']).columns:
        if optimized_df[col].nunique() / len(optimized_df) < 0.5:  # Less than 50% unique values
            optimized_df[col] = optimized_df[col].astype('category')
    
    return optimized_df
