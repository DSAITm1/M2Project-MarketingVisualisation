"""
Database utilities for BigQuery operations
Centralized database connection and query functions
"""

import streamlit as st
import polars as pl
from google.cloud import bigquery
from google.auth import default
import json
import os
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data
def load_config() -> Dict[str, Any]:
    """Load BigQuery configuration with error handling"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bigquery_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['project_id', 'dataset_id']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        
        return config
    except FileNotFoundError:
        st.error("❌ Configuration file not found. Please check config/bigquery_config.json")
        return {}
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON in configuration file")
        return {}
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        return {}

@st.cache_resource
def get_bigquery_client() -> Optional[bigquery.Client]:
    """Initialize BigQuery client with caching and error handling"""
    try:
        config = load_config()
        if not config:
            return None
        
        credentials, _ = default()
        client = bigquery.Client(credentials=credentials, project=config['project_id'])
        
        # Test connection
        client.query("SELECT 1 as test").result()
        logger.info(f"✅ Connected to BigQuery project: {config['project_id']}")
        
        return client
    except Exception as e:
        st.error(f"❌ Failed to connect to BigQuery: {str(e)}")
        logger.error(f"BigQuery connection failed: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def execute_query(query: str, query_name: str = "Unknown") -> pl.DataFrame:
    """Execute BigQuery query with caching and error handling"""
    try:
        client = get_bigquery_client()
        if client is None:
            return pl.DataFrame()
        
        logger.info(f"Executing query: {query_name}")
        # Get pandas DataFrame from BigQuery and convert to Polars
        pandas_df = client.query(query).to_dataframe()
        
        if pandas_df.empty:
            st.warning(f"⚠️ Query '{query_name}' returned no data")
            return pl.DataFrame()
        else:
            logger.info(f"✅ Query '{query_name}' returned {len(pandas_df)} rows")
            return pl.from_pandas(pandas_df)
    except Exception as e:
        st.error(f"❌ Error executing query '{query_name}': {str(e)}")
        logger.error(f"Query execution failed for '{query_name}': {str(e)}")
        return pl.DataFrame()

@st.cache_data(ttl=3600)
def load_table_data(table_name: str, limit: Optional[int] = None) -> pl.DataFrame:
    """Load data from BigQuery table with caching"""
    config = load_config()
    if not config:
        return pl.DataFrame()
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
    SELECT *
    FROM `{config['project_id']}.{config['dataset_id']}.{table_name}`
    {limit_clause}
    """
    
    return execute_query(query, f"Load {table_name}")

def normalize_datetime_columns(df: pl.DataFrame, columns: list = None) -> pl.DataFrame:
    """Normalize datetime columns to remove timezone information"""
    if df.is_empty():
        return df
    
    # Auto-detect datetime columns if not specified
    if columns is None:
        columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    
    expressions = []
    for col in columns:
        if col in df.columns:
            try:
                # Convert to datetime if not already, then normalize timezone
                expressions.append(
                    pl.col(col)
                    .str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S%.f%z", strict=False)
                    .dt.convert_time_zone("UTC")
                    .dt.replace_time_zone(None)
                    .alias(col)
                )
            except Exception as e:
                logger.warning(f"Failed to normalize datetime column {col}: {str(e)}")
                expressions.append(pl.col(col))  # Keep original if conversion fails
    
    if expressions:
        return df.with_columns(expressions)
    return df

def get_available_tables() -> list:
    """Get list of available tables from config"""
    config = load_config()
    return [t['table_name'] for t in config.get('recommended_tables', [])]

def validate_dataframe(df: pl.DataFrame, required_columns: list = None) -> bool:
    """Validate dataframe has required columns and data"""
    if df.is_empty():
        return False
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.warning(f"⚠️ Missing required columns: {missing_cols}")
            return False
    
    return True
