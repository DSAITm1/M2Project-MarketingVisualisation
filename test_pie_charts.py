#!/usr/bin/env python3
"""
Quick test to verify all pie chart calls are fixed
"""
import polars as pl
import sys
import traceback

def test_pie_chart_calls():
    """Test that all pie chart calls use the correct signature"""
    
    # Mock data for testing
    test_data = pl.DataFrame({
        'customer_segment': ['Premium', 'Regular', 'Basic'],
        'count': [10, 20, 30],
        'order_status': ['delivered', 'pending', 'cancelled'],
        'len': [15, 25, 35]
    })
    
    try:
        from utils.visualizations import create_pie_chart
        
        # Test 1: Customer segment distribution (Main.py style)
        segment_counts = test_data.select(['customer_segment', 'count'])
        fig1 = create_pie_chart(
            data=segment_counts,
            values='count',
            names='customer_segment',
            title="Customer Segment Distribution"
        )
        print("✅ Test 1: Customer segment pie chart")
        
        # Test 2: Order status distribution (Main.py style)
        status_counts = test_data.select(['order_status', 'count'])
        fig2 = create_pie_chart(
            data=status_counts,
            values='count',
            names='order_status',
            title="Order Status Distribution"
        )
        print("✅ Test 2: Order status pie chart")
        
        # Test 3: Customer Analytics style (with len column)
        segment_len = test_data.select(['customer_segment', 'len'])
        fig3 = create_pie_chart(
            data=segment_len,
            values='len',
            names='customer_segment',
            title="Customer Segments"
        )
        print("✅ Test 3: Customer Analytics pie chart")
        
        print("\n🎉 ALL PIE CHART TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Pie chart test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pie_chart_calls()
    sys.exit(0 if success else 1)
