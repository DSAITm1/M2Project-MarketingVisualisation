"""
Utils package for Marketing Analytics Dashboard
Common utilities for database operations, visualizations, and data processing
"""

from .database import (
    load_config,
    get_bigquery_client, 
    execute_query,
    load_table_data,
    normalize_datetime_columns,
    get_available_tables,
    validate_dataframe
)

from .visualizations import (
    create_metric_cards,
    create_bar_chart,
    create_pie_chart,
    create_line_chart,
    create_map_chart,
    display_chart,
    display_dataframe,
    create_summary_stats,
    COLORS
)

from .data_processing import (
    get_customer_segments,
    get_order_performance,
    get_review_insights,
    get_geographic_summary,
    calculate_business_metrics,
    filter_data_by_date,
    get_top_n_analysis,
    format_currency,
    format_percentage
)

__version__ = "1.0.0"
__all__ = [
    # Database utilities
    'load_config', 'get_bigquery_client', 'execute_query', 'load_table_data',
    'normalize_datetime_columns', 'get_available_tables', 'validate_dataframe',
    
    # Visualization utilities  
    'create_metric_cards', 'create_bar_chart', 'create_pie_chart', 'create_line_chart',
    'create_map_chart', 'display_chart', 'display_dataframe', 'create_summary_stats', 'COLORS',
    
    # Data processing utilities
    'get_customer_segments', 'get_order_performance', 'get_review_insights', 
    'get_geographic_summary', 'calculate_business_metrics', 'filter_data_by_date',
    'get_top_n_analysis', 'format_currency', 'format_percentage'
]
