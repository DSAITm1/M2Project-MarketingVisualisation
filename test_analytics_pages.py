#!/usr/bin/env python3
"""
Health Check Script for Analytics Dashboard
Quick validation of BigQuery connections and data availability
Usage: python test_analytics_pages.py
"""

import sys
import os
sys.path.append('utils')

from utils.database import get_bigquery_client
import polars as pl

def test_order_analytics():
    """Test Order Analytics queries"""
    print("🛒 Testing Order Analytics...")
    
    client = get_bigquery_client()
    if not client:
        print("❌ Failed to connect to BigQuery")
        return False
    
    try:
        # Test main order query
        query = """
        SELECT 
            COUNT(DISTINCT order_id) as total_orders,
            ROUND(SUM(allocated_payment), 2) as total_revenue,
            ROUND(AVG(allocated_payment), 2) as avg_order_value,
            COUNT(DISTINCT customer_id) as unique_customers
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE order_status IN ('delivered', 'shipped', 'invoiced', 'processing')
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"   ✅ Total Orders: {row.total_orders:,}")
            print(f"   ✅ Total Revenue: ${row.total_revenue:,.2f}")
            print(f"   ✅ Avg Order Value: ${row.avg_order_value:.2f}")
            print(f"   ✅ Unique Customers: {row.unique_customers:,}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Order Analytics failed: {e}")
        return False

def test_review_analytics():
    """Test Review Analytics queries"""
    print("\n⭐ Testing Review Analytics...")
    
    client = get_bigquery_client()
    if not client:
        print("❌ Failed to connect to BigQuery")
        return False
    
    try:
        # Test review query
        query = """
        SELECT 
            COUNT(*) as total_reviews,
            ROUND(AVG(review_score), 2) as avg_rating,
            COUNT(CASE WHEN review_score >= 4 THEN 1 END) as positive_reviews,
            COUNT(CASE WHEN review_score <= 2 THEN 1 END) as negative_reviews
        FROM `project-olist-470307.dbt_olist_analytics.revenue_analytics_obt`
        WHERE review_score IS NOT NULL
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"   ✅ Total Reviews: {row.total_reviews:,}")
            print(f"   ✅ Average Rating: {row.avg_rating:.2f}/5")
            print(f"   ✅ Positive Reviews: {row.positive_reviews:,}")
            print(f"   ✅ Negative Reviews: {row.negative_reviews:,}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Review Analytics failed: {e}")
        return False

def test_geographic_analytics():
    """Test Geographic Analytics queries"""
    print("\n🗺️ Testing Geographic Analytics...")
    
    client = get_bigquery_client()
    if not client:
        print("❌ Failed to connect to BigQuery")
        return False
    
    try:
        # Test geographic query
        query = """
        SELECT 
            COUNT(DISTINCT state_code) as total_states,
            SUM(total_customers) as total_customers,
            ROUND(SUM(total_revenue), 2) as total_revenue,
            ROUND(AVG(market_opportunity_index), 2) as avg_opportunity_index
        FROM `project-olist-470307.dbt_olist_analytics.geographic_analytics_obt`
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"   ✅ Total States: {row.total_states}")
            print(f"   ✅ Total Customers: {row.total_customers:,}")
            print(f"   ✅ Total Revenue: ${row.total_revenue:,.2f}")
            print(f"   ✅ Avg Opportunity Index: {row.avg_opportunity_index:.2f}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Geographic Analytics failed: {e}")
        return False

def main():
    """Run all health checks"""
    print("🏥 Analytics Dashboard Health Check")
    print("=" * 50)
    
    results = []
    results.append(test_order_analytics())
    results.append(test_review_analytics())
    results.append(test_geographic_analytics())
    
    print("\n" + "=" * 50)
    print("📊 Health Check Results:")
    
    if all(results):
        print("🎉 All systems operational!")
        print("✅ Order Analytics: HEALTHY")
        print("✅ Review Analytics: HEALTHY") 
        print("✅ Geographic Analytics: HEALTHY")
        print("\n🚀 Dashboard ready for use.")
    else:
        print("⚠️ Some issues detected:")
        print(f"   Order Analytics: {'HEALTHY' if results[0] else 'UNHEALTHY'}")
        print(f"   Review Analytics: {'HEALTHY' if results[1] else 'UNHEALTHY'}")
        print(f"   Geographic Analytics: {'HEALTHY' if results[2] else 'UNHEALTHY'}")
        print("\n🔧 Check debug_log.md for troubleshooting steps.")

if __name__ == "__main__":
    main()
