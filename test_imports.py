#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

try:
    # Test utils imports
    from utils.database import load_config, execute_query
    print("✅ Utils database imports successful")

    from utils.visualizations import create_bar_chart
    print("✅ Utils visualizations imports successful")

    from utils.data_processing import get_customer_segments
    print("✅ Utils data_processing imports successful")

    # Test core imports (updated for Polars)
    import polars as pl
    import plotly.express as px

    print("✅ All core imports successful!")
    print("🎉 The ModuleNotFoundError has been resolved!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Other error: {e}")
    sys.exit(1)
