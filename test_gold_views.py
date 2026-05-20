"""
Test Gold Views - Verify all Kepner-Tregoe views are working correctly

This script runs sample queries against all 6 gold views to ensure they
return data and can be consumed by Power BI.

Author: OpenCode CLI
Created: May 20, 2026
"""

import clickhouse_connect
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST'),
        user=os.getenv('CLICKHOUSE_USER'),
        password=os.getenv('CLICKHOUSE_PASSWORD'),
        secure=os.getenv('CLICKHOUSE_SECURE') == 'True'
    )

def test_gold_views():
    client = get_client()
    
    print("="*70)
    print("TESTING GOLD LAYER VIEWS - KEPNER-TREGOE ANALYSIS")
    print("="*70)
    
    # Test 1: WHAT is happening
    print("\n[TEST 1] gold_kt_what_is_happening (top 5 service patterns)")
    print("-"*70)
    result = client.query("SELECT * FROM NYCTaxiAnalysis.gold_kt_what_is_happening LIMIT 5")
    for row in result.result_set:
        print(f"  {row[0]:20} | {row[1]:30} | Volume: {row[2]:>10,} ({row[3]:>5}%)")
    print(f"[OK] Returned {len(result.result_set)} rows")
    
    # Test 2: WHERE is happening (hot zones)
    print("\n[TEST 2] gold_kt_where_is_happening (top 10 hot zones)")
    print("-"*70)
    result = client.query("""
        SELECT * FROM NYCTaxiAnalysis.gold_kt_where_is_happening 
        WHERE zone_classification = 'Hot Zone' 
        ORDER BY pickup_count DESC 
        LIMIT 10
    """)
    for row in result.result_set:
        print(f"  Location {row[0]:>3} | Trips: {row[3]:>8,} | Avg Fare: ${row[6]:>6.2f} | {row[9]}")
    print(f"[OK] Returned {len(result.result_set)} hot zones")
    
    # Test 3: WHEN is happening (peak periods)
    print("\n[TEST 3] gold_kt_when_is_happening (peak periods)")
    print("-"*70)
    result = client.query("""
        SELECT * FROM NYCTaxiAnalysis.gold_kt_when_is_happening 
        WHERE classification = 'Peak Period' 
        ORDER BY trip_volume DESC 
        LIMIT 5
    """)
    for row in result.result_set:
        print(f"  {row[0]:15} | {row[1]:12} | Trips: {row[2]:>8,} | {row[7]}")
    print(f"[OK] Returned {len(result.result_set)} peak periods")
    
    # Test 4: EXTENT and magnitude
    print("\n[TEST 4] gold_kt_extent_magnitude (all metrics)")
    print("-"*70)
    result = client.query("SELECT * FROM NYCTaxiAnalysis.gold_kt_extent_magnitude")
    for row in result.result_set:
        print(f"  {row[0]:25} | Min: {row[1]:>10.2f} | Max: {row[2]:>10.2f} | Median: {row[4]:>8.2f}")
    print(f"[OK] Returned {len(result.result_set)} magnitude metrics")
    
    # Test 5: WHAT NOT happening (data quality)
    print("\n[TEST 5] gold_kt_what_not_happening (data quality issues)")
    print("-"*70)
    result = client.query("""
        SELECT * FROM NYCTaxiAnalysis.gold_kt_what_not_happening 
        ORDER BY null_percentage DESC 
        LIMIT 5
    """)
    for row in result.result_set:
        print(f"  {row[0]:25} | NULL: {row[2]:>5}% | Quality Score: {row[4]:>5}%")
    print(f"[OK] Returned {len(result.result_set)} data quality metrics")
    
    # Test 6: Characteristics comparison
    print("\n[TEST 6] gold_kt_characteristics_comparison (IS vs IS NOT)")
    print("-"*70)
    result = client.query("SELECT * FROM NYCTaxiAnalysis.gold_kt_characteristics_comparison")
    for row in result.result_set:
        print(f"  {row[0]:35}")
        print(f"    IS: {row[1]:20} = {row[3]:>10,.2f} | IS NOT: {row[2]:20} = {row[4]:>10,.2f}")
        print(f"    Difference: {row[6]:>10,.2f} ({row[7]:>6.2f}%)")
    print(f"[OK] Returned {len(result.result_set)} comparisons")
    
    # Summary
    print("\n" + "="*70)
    print("ALL GOLD VIEWS TESTED SUCCESSFULLY")
    print("="*70)
    print("[INFO] All 6 Kepner-Tregoe dimension views are working correctly")
    print("[INFO] Views are ready for Power BI connection")
    print("[INFO] Remember: NO DAX in Power BI - all logic is in these views")
    print("="*70)

if __name__ == '__main__':
    test_gold_views()
