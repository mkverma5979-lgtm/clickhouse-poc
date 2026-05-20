"""
Create Gold Layer Views in ClickHouse for Kepner-Tregoe Analysis

This script creates business logic views that directly answer each dimension
of the Kepner-Tregoe IS/IS NOT framework. These views are consumed directly
by Power BI with NO DAX calculations.

Author: OpenCode CLI
Created: May 20, 2026
"""

import clickhouse_connect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_clickhouse_client():
    """Create and return ClickHouse client"""
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST'),
        user=os.getenv('CLICKHOUSE_USER'),
        password=os.getenv('CLICKHOUSE_PASSWORD'),
        secure=os.getenv('CLICKHOUSE_SECURE') == 'True'
    )

def create_gold_kt_what_is_happening(client):
    """
    Gold view: WHAT is happening
    
    Trip types, service patterns, problem frequencies
    """
    print("\n[INFO] Creating gold_kt_what_is_happening view...")
    
    client.command("DROP VIEW IF EXISTS NYCTaxiAnalysis.gold_kt_what_is_happening")
    
    sql = """
    CREATE VIEW NYCTaxiAnalysis.gold_kt_what_is_happening AS
    SELECT
        'Vendor' AS dimension_category,
        concat('Vendor ', toString(VendorID), ' - ', vendor_name) AS characteristic,
        trip_count AS volume,
        round((trip_count * 100.0) / (SELECT sum(trip_count) FROM NYCTaxiAnalysis.silver_trips_by_vendor), 2) AS percentage,
        round(avg_fare, 2) AS avg_value,
        CASE 
            WHEN data_completeness_pct < 50 THEN 'High Concern'
            WHEN data_completeness_pct < 75 THEN 'Moderate Concern'
            ELSE 'Low Concern'
        END AS problem_indicator
    FROM NYCTaxiAnalysis.silver_trips_by_vendor
    
    UNION ALL
    
    SELECT
        'Payment Method' AS dimension_category,
        payment_method_name AS characteristic,
        trip_count AS volume,
        round((trip_count * 100.0) / (SELECT sum(trip_count) FROM NYCTaxiAnalysis.silver_trips_by_payment), 2) AS percentage,
        round(avg_fare, 2) AS avg_value,
        CASE 
            WHEN payment_type = 0 THEN 'Data Quality Issue'
            WHEN payment_type = 4 THEN 'Dispute'
            ELSE 'Normal'
        END AS problem_indicator
    FROM NYCTaxiAnalysis.silver_trips_by_payment
    
    ORDER BY dimension_category, volume DESC
    """
    
    client.command(sql)
    print("[OK] gold_kt_what_is_happening created successfully")

def create_gold_kt_where_is_happening(client):
    """
    Gold view: WHERE is happening
    
    Geographic hot zones vs cold zones, location-based metrics
    """
    print("\n[INFO] Creating gold_kt_where_is_happening view...")
    
    client.command("DROP VIEW IF EXISTS NYCTaxiAnalysis.gold_kt_where_is_happening")
    
    sql = """
    CREATE VIEW NYCTaxiAnalysis.gold_kt_where_is_happening AS
    WITH location_stats AS (
        SELECT
            location_id,
            location_type,
            trip_count,
            round(avg_fare, 2) AS avg_fare,
            round(avg_distance, 2) AS avg_distance,
            same_location_trips,
            -- Calculate percentile rank for classification
            percent_rank() OVER (PARTITION BY location_type ORDER BY trip_count) AS percentile_rank
        FROM NYCTaxiAnalysis.silver_trips_by_location
    )
    SELECT
        location_id,
        concat('Location ', toString(location_id)) AS location_name,
        location_type,
        trip_count AS pickup_count,
        0 AS dropoff_count,  -- Will be filled by location_type='dropoff'
        round((trip_count * 100.0) / (SELECT sum(trip_count) FROM location_stats WHERE location_type = 'pickup'), 4) AS percentage_of_total,
        avg_fare,
        avg_distance,
        same_location_trips,
        CASE 
            WHEN percentile_rank >= 0.95 THEN 'Hot Zone'
            WHEN percentile_rank >= 0.75 THEN 'Warm Zone'
            WHEN percentile_rank >= 0.25 THEN 'Medium Zone'
            ELSE 'Cold Zone'
        END AS zone_classification,
        CASE 
            WHEN same_location_trips > (trip_count * 0.1) THEN 'High Same-Location Pattern'
            ELSE 'Normal'
        END AS problem_indicator
    FROM location_stats
    WHERE location_type = 'pickup'
    ORDER BY trip_count DESC
    """
    
    client.command(sql)
    print("[OK] gold_kt_where_is_happening created successfully")

def create_gold_kt_when_is_happening(client):
    """
    Gold view: WHEN is happening
    
    Temporal patterns, peak vs off-peak comparisons
    """
    print("\n[INFO] Creating gold_kt_when_is_happening view...")
    
    client.command("DROP VIEW IF EXISTS NYCTaxiAnalysis.gold_kt_when_is_happening")
    
    sql = """
    CREATE VIEW NYCTaxiAnalysis.gold_kt_when_is_happening AS
    WITH hourly_agg AS (
        SELECT
            'Hour of Day' AS time_dimension,
            toString(pickup_hour) AS time_value,
            sum(trip_count) AS trip_volume,
            round(sum(total_fare), 2) AS total_revenue,
            round(avg(avg_fare), 2) AS avg_fare,
            round(avg(avg_distance), 2) AS avg_distance,
            round(avg(avg_duration), 2) AS avg_duration,
            percent_rank() OVER (ORDER BY sum(trip_count)) AS volume_percentile
        FROM NYCTaxiAnalysis.silver_trips_hourly
        GROUP BY pickup_hour
    ),
    day_of_week_agg AS (
        SELECT
            'Day of Week' AS time_dimension,
            CASE pickup_day_of_week
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
                WHEN 7 THEN 'Sunday'
            END AS time_value,
            sum(trip_count) AS trip_volume,
            round(sum(total_fare), 2) AS total_revenue,
            round(avg(avg_fare), 2) AS avg_fare,
            round(avg(avg_distance), 2) AS avg_distance,
            round(avg(avg_duration), 2) AS avg_duration,
            percent_rank() OVER (ORDER BY sum(trip_count)) AS volume_percentile
        FROM NYCTaxiAnalysis.silver_trips_hourly
        GROUP BY pickup_day_of_week
    )
    SELECT
        time_dimension,
        time_value,
        trip_volume,
        total_revenue,
        avg_fare,
        avg_distance,
        avg_duration,
        CASE 
            WHEN volume_percentile >= 0.75 THEN 'Peak Period'
            WHEN volume_percentile >= 0.50 THEN 'High Activity'
            WHEN volume_percentile >= 0.25 THEN 'Medium Activity'
            ELSE 'Off-Peak Period'
        END AS classification
    FROM hourly_agg
    
    UNION ALL
    
    SELECT
        time_dimension,
        time_value,
        trip_volume,
        total_revenue,
        avg_fare,
        avg_distance,
        avg_duration,
        CASE 
            WHEN volume_percentile >= 0.75 THEN 'Peak Period'
            WHEN volume_percentile >= 0.50 THEN 'High Activity'
            WHEN volume_percentile >= 0.25 THEN 'Medium Activity'
            ELSE 'Off-Peak Period'
        END AS classification
    FROM day_of_week_agg
    
    ORDER BY time_dimension, trip_volume DESC
    """
    
    client.command(sql)
    print("[OK] gold_kt_when_is_happening created successfully")

def create_gold_kt_extent_magnitude(client):
    """
    Gold view: EXTENT and MAGNITUDE
    
    Volume metrics, distributions, outlier detection
    """
    print("\n[INFO] Creating gold_kt_extent_magnitude view...")
    
    client.command("DROP VIEW IF EXISTS NYCTaxiAnalysis.gold_kt_extent_magnitude")
    
    sql = """
    CREATE VIEW NYCTaxiAnalysis.gold_kt_extent_magnitude AS
    SELECT 'Trip Distance (miles)' AS metric_name, 
           round(min(trip_distance), 2) AS min_value,
           round(max(trip_distance), 2) AS max_value,
           round(avg(trip_distance), 2) AS avg_value,
           round(quantile(0.5)(trip_distance), 2) AS median_value,
           round(quantile(0.95)(trip_distance), 2) AS percentile_95,
           toFloat64(sum(CASE WHEN trip_distance > 50 THEN 1 ELSE 0 END)) AS outlier_count,
           round((sum(CASE WHEN trip_distance > 50 THEN 1 ELSE 0 END) * 100.0 / count()), 4) AS outlier_percentage
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    
    UNION ALL
    SELECT 'Fare Amount ($)',
           round(min(fare_amount), 2),
           round(max(fare_amount), 2),
           round(avg(fare_amount), 2),
           round(quantile(0.5)(fare_amount), 2), 
           round(quantile(0.95)(fare_amount), 2),
           toFloat64(sum(CASE WHEN fare_amount > 200 THEN 1 ELSE 0 END)),
           round((sum(CASE WHEN fare_amount > 200 THEN 1 ELSE 0 END) * 100.0 / count()), 4)
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    
    UNION ALL
    SELECT 'Total Amount ($)',
           round(min(total_amount), 2),
           round(max(total_amount), 2),
           round(avg(total_amount), 2),
           round(quantile(0.5)(total_amount), 2),
           round(quantile(0.95)(total_amount), 2),
           toFloat64(sum(CASE WHEN total_amount > 300 THEN 1 ELSE 0 END)),
           round((sum(CASE WHEN total_amount > 300 THEN 1 ELSE 0 END) * 100.0 / count()), 4)
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    
    UNION ALL
    SELECT 'Duration (minutes)',
           round(toFloat64(min(trip_duration_minutes)), 2),
           round(toFloat64(max(trip_duration_minutes)), 2),
           round(avg(trip_duration_minutes), 2),
           round(quantile(0.5)(trip_duration_minutes), 2),
           round(quantile(0.95)(trip_duration_minutes), 2),
           toFloat64(sum(CASE WHEN trip_duration_minutes > 120 THEN 1 ELSE 0 END)),
           round((sum(CASE WHEN trip_duration_minutes > 120 THEN 1 ELSE 0 END) * 100.0 / count()), 4)
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    
    UNION ALL
    SELECT 'Total Trips',
           toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned)),
           toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned)),
           toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned)),
           toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned)),
           toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned)),
           0.0,
           0.0
    """
    
    client.command(sql)
    print("[OK] gold_kt_extent_magnitude created successfully")

def create_gold_kt_what_not_happening(client):
    """
    Gold view: WHAT IS NOT happening
    
    Absence analysis, NULL patterns, data quality issues
    """
    print("\n[INFO] Creating gold_kt_what_not_happening view...")
    
    client.command("DROP VIEW IF EXISTS NYCTaxiAnalysis.gold_kt_what_not_happening")
    
    sql = """
    CREATE VIEW NYCTaxiAnalysis.gold_kt_what_not_happening AS
    SELECT * FROM (
        WITH bronze_stats AS (
            SELECT
                count() AS total_records,
                sum(CASE WHEN passenger_count IS NULL THEN 1 ELSE 0 END) AS passenger_nulls,
                sum(CASE WHEN RatecodeID IS NULL THEN 1 ELSE 0 END) AS ratecode_nulls,
                sum(CASE WHEN store_and_fwd_flag IS NULL THEN 1 ELSE 0 END) AS store_fwd_nulls,
                sum(CASE WHEN congestion_surcharge IS NULL THEN 1 ELSE 0 END) AS congestion_nulls,
                sum(CASE WHEN Airport_fee IS NULL THEN 1 ELSE 0 END) AS airport_nulls,
                sum(CASE WHEN payment_type = 0 OR payment_type IS NULL THEN 1 ELSE 0 END) AS payment_nulls,
                sum(CASE WHEN VendorID IS NULL THEN 1 ELSE 0 END) AS vendor_nulls
            FROM NYCTaxiAnalysis.bronze_taxi_trips
        ),
        cleaned_stats AS (
            SELECT count() AS cleaned_records FROM NYCTaxiAnalysis.silver_trips_cleaned
        )
        SELECT
            'passenger_count' AS dimension,
            toFloat64(passenger_nulls) AS null_count,
            round((passenger_nulls * 100.0 / total_records), 2) AS null_percentage,
            toFloat64(0) AS anomaly_count,
            round(100.0 - (passenger_nulls * 100.0 / total_records), 2) AS data_quality_score
        FROM bronze_stats
        
        UNION ALL
        SELECT 'RatecodeID', toFloat64(ratecode_nulls), round((ratecode_nulls * 100.0 / total_records), 2), 
               toFloat64(0), round(100.0 - (ratecode_nulls * 100.0 / total_records), 2) FROM bronze_stats
        
        UNION ALL
        SELECT 'store_and_fwd_flag', toFloat64(store_fwd_nulls), round((store_fwd_nulls * 100.0 / total_records), 2),
               toFloat64(0), round(100.0 - (store_fwd_nulls * 100.0 / total_records), 2) FROM bronze_stats
        
        UNION ALL
        SELECT 'congestion_surcharge', toFloat64(congestion_nulls), round((congestion_nulls * 100.0 / total_records), 2),
               toFloat64(0), round(100.0 - (congestion_nulls * 100.0 / total_records), 2) FROM bronze_stats
        
        UNION ALL
        SELECT 'Airport_fee', toFloat64(airport_nulls), round((airport_nulls * 100.0 / total_records), 2),
               toFloat64(0), round(100.0 - (airport_nulls * 100.0 / total_records), 2) FROM bronze_stats
        
        UNION ALL
        SELECT 'payment_type', toFloat64(payment_nulls), round((payment_nulls * 100.0 / total_records), 2),
               toFloat64(0), round(100.0 - (payment_nulls * 100.0 / total_records), 2) FROM bronze_stats
        
        UNION ALL
        SELECT 'Data Filtered Out', toFloat64((SELECT total_records FROM bronze_stats) - (SELECT cleaned_records FROM cleaned_stats)),
               round((((SELECT total_records FROM bronze_stats) - (SELECT cleaned_records FROM cleaned_stats)) * 100.0 / (SELECT total_records FROM bronze_stats)), 2),
               toFloat64((SELECT total_records FROM bronze_stats) - (SELECT cleaned_records FROM cleaned_stats)),
               round(((SELECT cleaned_records FROM cleaned_stats) * 100.0 / (SELECT total_records FROM bronze_stats)), 2)
    ) ORDER BY null_percentage DESC
    """
    
    client.command(sql)
    print("[OK] gold_kt_what_not_happening created successfully")

def create_gold_kt_characteristics_comparison(client):
    """
    Gold view: CHARACTERISTICS Comparison (IS vs IS NOT)
    
    Side-by-side comparisons for contrasting analysis
    """
    print("\n[INFO] Creating gold_kt_characteristics_comparison view...")
    
    client.command("DROP VIEW IF EXISTS NYCTaxiAnalysis.gold_kt_characteristics_comparison")
    
    sql = """
    CREATE VIEW NYCTaxiAnalysis.gold_kt_characteristics_comparison AS
    SELECT 
        'Payment Method: Credit vs Cash' AS comparison_dimension,
        'Credit Card' AS is_category,
        'Cash' AS is_not_category,
        toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 1)) AS is_metric_value,
        toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2)) AS is_not_metric_value,
        'Trip Count' AS metric_type,
        round(toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 1)) - 
              toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2)), 2) AS difference,
        round(((toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 1)) - 
               toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2))) * 100.0 / 
               toFloat64((SELECT trip_count FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2))), 2) AS difference_percentage
    
    UNION ALL
    SELECT 
        'Tip Amount: Credit vs Cash',
        'Credit Card',
        'Cash',
        round((SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 1), 2),
        round((SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2), 2),
        'Average Tip ($)',
        round((SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 1) - 
              (SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2), 2),
        round(((SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 1) - 
               (SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2)) * 100.0 / 
               (SELECT avg_tip FROM NYCTaxiAnalysis.silver_trips_by_payment WHERE payment_type = 2), 2)
    
    UNION ALL
    SELECT 
        'Trip Distance: Short vs Long',
        'Short (<2 miles)',
        'Long (>10 miles)',
        toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance < 2)),
        toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10)),
        'Trip Count',
        round(toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance < 2)) - 
              toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10)), 2),
        round(((toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance < 2)) - 
               toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10))) * 100.0 / 
               toFloat64((SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10))), 2)
    
    UNION ALL
    SELECT 
        'Average Fare: Short vs Long',
        'Short (<2 miles)',
        'Long (>10 miles)',
        round((SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance < 2), 2),
        round((SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10), 2),
        'Average Fare ($)',
        round((SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance < 2) - 
              (SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10), 2),
        round(((SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance < 2) - 
               (SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10)) * 100.0 / 
               (SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10), 2)
    """
    
    client.command(sql)
    print("[OK] gold_kt_characteristics_comparison created successfully")

def verify_gold_views(client):
    """Verify all gold views were created successfully"""
    print("\n" + "="*60)
    print("GOLD LAYER VERIFICATION")
    print("="*60)
    
    views = [
        'gold_kt_what_is_happening',
        'gold_kt_where_is_happening',
        'gold_kt_when_is_happening',
        'gold_kt_extent_magnitude',
        'gold_kt_what_not_happening',
        'gold_kt_characteristics_comparison'
    ]
    
    for view in views:
        try:
            result = client.query(f"SELECT count() FROM NYCTaxiAnalysis.{view}")
            count = result.result_set[0][0]
            print(f"[OK] {view:45} {count:>10,} rows")
        except Exception as e:
            print(f"[ERROR] {view:45} {e}")
    
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("CREATING GOLD LAYER VIEWS FOR KEPNER-TREGOE ANALYSIS")
    print("="*60)
    
    try:
        # Connect to ClickHouse
        client = get_clickhouse_client()
        print("[OK] Connected to ClickHouse Cloud\n")
        
        # Create all gold views
        create_gold_kt_what_is_happening(client)
        create_gold_kt_where_is_happening(client)
        create_gold_kt_when_is_happening(client)
        create_gold_kt_extent_magnitude(client)
        create_gold_kt_what_not_happening(client)
        create_gold_kt_characteristics_comparison(client)
        
        # Verify all views
        verify_gold_views(client)
        
        print("\n" + "="*60)
        print("[SUCCESS] All gold views created successfully!")
        print("[INFO] These views are ready for Power BI connection")
        print("[INFO] NO DAX required - all logic is in these views")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create gold views: {e}")
        raise
