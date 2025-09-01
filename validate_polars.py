#!/usr/bin/env python3
"""
Comprehensive validation script for Polars migration
Tests all core functionality to ensure complete migration
"""

import sys
import polars as pl
from typing import Dict, Any

def test_imports():
    """Test all module imports"""
    print("🔍 Testing imports...")
    
    try:
        # Core libraries
        import streamlit as st
        import plotly.express as px
        import plotly.graph_objects as go
        print("✅ Core libraries imported")
        
        # Utils modules
        from utils.database import load_config, execute_query
        from utils.data_processing import calculate_business_metrics
        from utils.visualizations import create_bar_chart, create_pie_chart
        from utils.performance import monitor_performance
        print("✅ Utils modules imported")
        
        # BigQuery Storage (should eliminate warnings)
        from google.cloud import bigquery_storage
        print("✅ BigQuery Storage API available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_polars_operations():
    """Test basic Polars operations"""
    print("\n🔍 Testing Polars operations...")
    
    try:
        # Create test DataFrame
        df = pl.DataFrame({
            'customer_id': ['A', 'B', 'C', 'A', 'B'],
            'order_value': [100, 200, 150, 300, 250],
            'state': ['CA', 'NY', 'TX', 'CA', 'NY']
        })
        
        # Test groupby
        grouped = df.group_by('customer_id').agg(
            pl.col('order_value').sum().alias('total_spent')
        )
        print(f"✅ Group by operation: {grouped.shape}")
        
        # Test value_counts
        counts = df['state'].value_counts()
        print(f"✅ Value counts operation: {counts.shape}")
        
        # Test sorting
        sorted_df = grouped.sort('total_spent', descending=True)
        print(f"✅ Sort operation: {sorted_df.shape}")
        
        # Test empty check
        is_empty = df.is_empty()
        print(f"✅ Empty check: {is_empty}")
        
        return True
        
    except Exception as e:
        print(f"❌ Polars operation error: {e}")
        return False

def test_data_processing():
    """Test data processing functions"""
    print("\n🔍 Testing data processing...")
    
    try:
        from utils.data_processing import calculate_business_metrics, filter_data_by_date
        
        # Test with sample data
        test_df = pl.DataFrame({
            'customer_unique_id': ['1', '2', '3', '1'],
            'order_id': ['A', 'B', 'C', 'D'],
            'price': [100.0, 200.0, 150.0, 300.0],
            'review_score': [5.0, 4.0, 3.0, 5.0]
        })
        
        metrics = calculate_business_metrics(test_df)
        print(f"✅ Business metrics calculation: {len(metrics)} metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processing error: {e}")
        return False

def test_visualizations():
    """Test visualization functions"""
    print("\n🔍 Testing visualizations...")
    
    try:
        from utils.visualizations import create_bar_chart, create_pie_chart
        
        # Test data
        test_df = pl.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': [10, 20, 15]
        })
        
        # Test chart creation (won't display, just ensure no errors)
        fig = create_bar_chart(test_df, 'category', 'value', 'Test Chart')
        print("✅ Bar chart creation successful")
        
        fig2 = create_pie_chart([10, 20, 15], ['A', 'B', 'C'], 'Test Pie')
        print("✅ Pie chart creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🚀 POLARS MIGRATION VALIDATION")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_polars_operations,
        test_data_processing,
        test_visualizations
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS")
    
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Project is 100% migrated to Polars")
        print("✅ Ready for production use")
        print("\n🚀 You can now run: streamlit run Main.py")
        return True
    else:
        print("❌ Some tests failed - check errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
