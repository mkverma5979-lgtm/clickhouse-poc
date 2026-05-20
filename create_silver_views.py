"""
Create Silver Layer Materialized Views in ClickHouse

This script creates cleaned and aggregated materialized views from the bronze layer.
Silver views handle data quality issues and provide optimized data for gold layer.

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

def create_silver_trips_cleaned(client):
    """
    Create silver_trips_cleaned materialized view
    
    This view filters out data quality issues:
    - Negative financial values
    - Extreme outliers (distance > 100 miles, duration > 4 hours)
    - Logical impossibilities (0 passengers, negative duration)
    - Trip distance and fare anomalies
    """
    print("\n[INFO] Creating silver_trips_cleaned materialized view...")
    
    # Drop if exists
    client.command("DROP TABLE IF EXISTS NYCTaxiAnalysis.silver_trips_cleaned")
    
    sql = """
    CREATE MATERIALIZED VIEW NYCTaxiAnalysis.silver_trips_cleaned
    ENGINE = MergeTree()
    ORDER BY (tpep_pickup_datetime, PULocationID)
    PARTITION BY toYYYYMM(tpep_pickup_datetime)
    POPULATE
    AS
    SELECT
        VendorID,
        tpep_pickup_datetime,
        tpep_dropoff_datetime,
        passenger_count,
        trip_distance,
        RatecodeID,
        store_and_fwd_flag,
        PULocationID,
        DOLocationID,
        payment_type,
        fare_amount,
        extra,
        mta_tax,
        tip_amount,
        tolls_amount,
        improvement_surcharge,
        total_amount,
        congestion_surcharge,
        Airport_fee,
        cbd_congestion_fee,
        -- Derived fields
        dateDiff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) AS trip_duration_minutes,
        toHour(tpep_pickup_datetime) AS pickup_hour,
        toDayOfWeek(tpep_pickup_datetime) AS pickup_day_of_week,
        toDate(tpep_pickup_datetime) AS trip_date,
        -- Data quality flags
        CASE 
            WHEN passenger_count IS NULL OR RatecodeID IS NULL OR congestion_surcharge IS NULL 
            THEN 1 
            ELSE 0 
        END AS has_null_pattern,
        CASE
            WHEN PULocationID = DOLocationID THEN 1
            ELSE 0
        END AS is_same_location_trip
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    WHERE 1=1
        -- Filter out data quality issues
        AND fare_amount >= 0  -- No negative fares
        AND total_amount >= 0  -- No negative totals
        AND tip_amount >= 0  -- No negative tips
        AND tolls_amount >= 0  -- No negative tolls
        AND improvement_surcharge >= 0  -- No negative surcharges
        AND (congestion_surcharge >= 0 OR congestion_surcharge IS NULL)  -- No negative congestion
        AND (Airport_fee >= 0 OR Airport_fee IS NULL)  -- No negative airport fees
        AND trip_distance >= 0  -- No negative distance
        AND trip_distance <= 100  -- Filter extreme outliers
        AND (passenger_count > 0 OR passenger_count IS NULL)  -- No 0 passengers (NULL ok)
        AND tpep_dropoff_datetime >= tpep_pickup_datetime  -- No negative duration
        AND dateDiff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) <= 240  -- Max 4 hours
        AND fare_amount <= 500  -- Reasonable fare cap
        AND total_amount <= 1000  -- Reasonable total cap
    """
    
    client.command(sql)
    print("[OK] silver_trips_cleaned created successfully")
    
    # Get row count
    result = client.query("SELECT count() FROM NYCTaxiAnalysis.silver_trips_cleaned")
    count = result.result_set[0][0]
    print(f"[OK] Rows in silver_trips_cleaned: {count:,}")

def create_silver_trips_hourly(client):
    """
    Create silver_trips_hourly materialized view
    
    Hourly aggregations for temporal analysis
    """
    print("\n[INFO] Creating silver_trips_hourly materialized view...")
    
    client.command("DROP TABLE IF EXISTS NYCTaxiAnalysis.silver_trips_hourly")
    
    sql = """
    CREATE MATERIALIZED VIEW NYCTaxiAnalysis.silver_trips_hourly
    ENGINE = SummingMergeTree()
    ORDER BY (trip_date, pickup_hour)
    PARTITION BY toYYYYMM(trip_date)
    POPULATE
    AS
    SELECT
        trip_date,
        pickup_hour,
        pickup_day_of_week,
        count() AS trip_count,
        sum(trip_distance) AS total_distance,
        sum(fare_amount) AS total_fare,
        sum(tip_amount) AS total_tips,
        sum(total_amount) AS total_revenue,
        avg(trip_distance) AS avg_distance,
        avg(fare_amount) AS avg_fare,
        avg(tip_amount) AS avg_tip,
        avg(total_amount) AS avg_total,
        avg(trip_duration_minutes) AS avg_duration,
        avg(passenger_count) AS avg_passengers,
        sum(CASE WHEN payment_type = 1 THEN 1 ELSE 0 END) AS credit_card_count,
        sum(CASE WHEN payment_type = 2 THEN 1 ELSE 0 END) AS cash_count
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    GROUP BY trip_date, pickup_hour, pickup_day_of_week
    """
    
    client.command(sql)
    print("[OK] silver_trips_hourly created successfully")
    
    result = client.query("SELECT count() FROM NYCTaxiAnalysis.silver_trips_hourly")
    count = result.result_set[0][0]
    print(f"[OK] Rows in silver_trips_hourly: {count:,}")

def create_silver_trips_by_location(client):
    """
    Create silver_trips_by_location materialized view
    
    Location-based aggregations for geographic analysis
    """
    print("\n[INFO] Creating silver_trips_by_location materialized view...")
    
    client.command("DROP TABLE IF EXISTS NYCTaxiAnalysis.silver_trips_by_location")
    
    # Create as regular table first, then insert aggregated data
    sql_create = """
    CREATE TABLE NYCTaxiAnalysis.silver_trips_by_location
    (
        location_id Int32,
        location_type String,
        trip_count UInt64,
        total_fare Float64,
        total_revenue Float64,
        avg_fare Float64,
        avg_distance Float64,
        avg_duration Float64,
        same_location_trips UInt64
    )
    ENGINE = SummingMergeTree()
    ORDER BY (location_id, location_type)
    """
    
    client.command(sql_create)
    
    # Insert aggregated data
    sql_insert = """
    INSERT INTO NYCTaxiAnalysis.silver_trips_by_location
    SELECT
        location_id,
        location_type,
        count() AS trip_count,
        sum(fare_amount) AS total_fare,
        sum(total_amount) AS total_revenue,
        avg(fare_amount) AS avg_fare,
        avg(trip_distance) AS avg_distance,
        avg(trip_duration_minutes) AS avg_duration,
        sum(CASE WHEN is_same_location_trip = 1 THEN 1 ELSE 0 END) AS same_location_trips
    FROM (
        SELECT
            PULocationID AS location_id,
            'pickup' AS location_type,
            fare_amount,
            total_amount,
            trip_distance,
            trip_duration_minutes,
            is_same_location_trip
        FROM NYCTaxiAnalysis.silver_trips_cleaned
        
        UNION ALL
        
        SELECT
            DOLocationID AS location_id,
            'dropoff' AS location_type,
            fare_amount,
            total_amount,
            trip_distance,
            trip_duration_minutes,
            0 AS is_same_location_trip
        FROM NYCTaxiAnalysis.silver_trips_cleaned
    )
    GROUP BY location_id, location_type
    """
    
    client.command(sql_insert)
    print("[OK] silver_trips_by_location created successfully")
    
    result = client.query("SELECT count() FROM NYCTaxiAnalysis.silver_trips_by_location")
    count = result.result_set[0][0]
    print(f"[OK] Rows in silver_trips_by_location: {count:,}")

def create_silver_trips_by_payment(client):
    """
    Create silver_trips_by_payment materialized view
    
    Payment method analysis with tip patterns
    """
    print("\n[INFO] Creating silver_trips_by_payment materialized view...")
    
    client.command("DROP TABLE IF EXISTS NYCTaxiAnalysis.silver_trips_by_payment")
    
    # Create as regular table
    sql_create = """
    CREATE TABLE NYCTaxiAnalysis.silver_trips_by_payment
    (
        payment_type Int32,
        payment_method_name String,
        trip_count UInt64,
        total_fare Float64,
        total_tips Float64,
        total_revenue Float64,
        avg_fare Float64,
        avg_tip Float64,
        avg_total Float64,
        tip_percentage Float64
    )
    ENGINE = SummingMergeTree()
    ORDER BY payment_type
    """
    
    client.command(sql_create)
    
    # Insert aggregated data
    sql_insert = """
    INSERT INTO NYCTaxiAnalysis.silver_trips_by_payment
    SELECT
        payment_type,
        CASE 
            WHEN payment_type = 1 THEN 'Credit Card'
            WHEN payment_type = 2 THEN 'Cash'
            WHEN payment_type = 3 THEN 'No Charge'
            WHEN payment_type = 4 THEN 'Dispute'
            ELSE 'Unknown'
        END AS payment_method_name,
        count() AS trip_count,
        sum(fare_amount) AS total_fare,
        sum(tip_amount) AS total_tips,
        sum(total_amount) AS total_revenue,
        avg(fare_amount) AS avg_fare,
        avg(tip_amount) AS avg_tip,
        avg(total_amount) AS avg_total,
        CASE 
            WHEN sum(fare_amount) > 0 
            THEN (sum(tip_amount) / sum(fare_amount)) * 100 
            ELSE 0 
        END AS tip_percentage
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    WHERE payment_type IS NOT NULL
    GROUP BY payment_type
    """
    
    client.command(sql_insert)
    print("[OK] silver_trips_by_payment created successfully")
    
    result = client.query("SELECT count() FROM NYCTaxiAnalysis.silver_trips_by_payment")
    count = result.result_set[0][0]
    print(f"[OK] Rows in silver_trips_by_payment: {count:,}")

def create_silver_trips_by_vendor(client):
    """
    Create silver_trips_by_vendor materialized view
    
    Vendor comparison and data quality metrics
    """
    print("\n[INFO] Creating silver_trips_by_vendor materialized view...")
    
    client.command("DROP TABLE IF EXISTS NYCTaxiAnalysis.silver_trips_by_vendor")
    
    # Create as regular table
    sql_create = """
    CREATE TABLE NYCTaxiAnalysis.silver_trips_by_vendor
    (
        VendorID Int32,
        vendor_name String,
        trip_count UInt64,
        total_fare Float64,
        total_revenue Float64,
        avg_fare Float64,
        avg_distance Float64,
        avg_duration Float64,
        trips_with_nulls UInt64,
        trips_complete UInt64,
        data_completeness_pct Float64
    )
    ENGINE = SummingMergeTree()
    ORDER BY VendorID
    """
    
    client.command(sql_create)
    
    # Insert aggregated data
    sql_insert = """
    INSERT INTO NYCTaxiAnalysis.silver_trips_by_vendor
    SELECT
        VendorID,
        CASE 
            WHEN VendorID = 1 THEN 'Creative Mobile Technologies'
            WHEN VendorID = 2 THEN 'VeriFone Inc'
            ELSE 'Other'
        END AS vendor_name,
        count() AS trip_count,
        sum(fare_amount) AS total_fare,
        sum(total_amount) AS total_revenue,
        avg(fare_amount) AS avg_fare,
        avg(trip_distance) AS avg_distance,
        avg(trip_duration_minutes) AS avg_duration,
        sum(CASE WHEN has_null_pattern = 1 THEN 1 ELSE 0 END) AS trips_with_nulls,
        sum(CASE WHEN has_null_pattern = 0 THEN 1 ELSE 0 END) AS trips_complete,
        (sum(CASE WHEN has_null_pattern = 0 THEN 1 ELSE 0 END) * 100.0 / count()) AS data_completeness_pct
    FROM NYCTaxiAnalysis.silver_trips_cleaned
    WHERE VendorID IS NOT NULL
    GROUP BY VendorID
    """
    
    client.command(sql_insert)
    print("[OK] silver_trips_by_vendor created successfully")
    
    result = client.query("SELECT count() FROM NYCTaxiAnalysis.silver_trips_by_vendor")
    count = result.result_set[0][0]
    print(f"[OK] Rows in silver_trips_by_vendor: {count:,}")

def verify_silver_views(client):
    """Verify all silver views were created successfully"""
    print("\n" + "="*60)
    print("SILVER LAYER VERIFICATION")
    print("="*60)
    
    views = [
        'silver_trips_cleaned',
        'silver_trips_hourly',
        'silver_trips_by_location',
        'silver_trips_by_payment',
        'silver_trips_by_vendor'
    ]
    
    for view in views:
        try:
            result = client.query(f"SELECT count() FROM NYCTaxiAnalysis.{view}")
            count = result.result_set[0][0]
            print(f"[OK] {view:40} {count:>15,} rows")
        except Exception as e:
            print(f"[ERROR] {view:40} {e}")
    
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("CREATING SILVER LAYER MATERIALIZED VIEWS")
    print("="*60)
    
    try:
        # Connect to ClickHouse
        client = get_clickhouse_client()
        print("[OK] Connected to ClickHouse Cloud\n")
        
        # Create all silver views
        create_silver_trips_cleaned(client)
        create_silver_trips_hourly(client)
        create_silver_trips_by_location(client)
        create_silver_trips_by_payment(client)
        create_silver_trips_by_vendor(client)
        
        # Verify all views
        verify_silver_views(client)
        
        print("\n" + "="*60)
        print("[SUCCESS] All silver views created successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create silver views: {e}")
        raise
