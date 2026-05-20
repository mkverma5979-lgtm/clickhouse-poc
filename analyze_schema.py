import clickhouse_connect
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

def connect_to_clickhouse():
    """Establish connection to ClickHouse"""
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST'),
        user=os.getenv('CLICKHOUSE_USER'),
        password=os.getenv('CLICKHOUSE_PASSWORD'),
        secure=os.getenv('CLICKHOUSE_SECURE') == 'True'
    )

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def analyze_table_structure(client):
    """Get table structure and column information"""
    print_section("TABLE STRUCTURE")
    
    # Get column details
    query = """
    SELECT 
        name,
        type,
        default_kind,
        default_expression,
        comment
    FROM system.columns
    WHERE database = 'NYCTaxiAnalysis' AND table = 'bronze_taxi_trips'
    ORDER BY position
    """
    result = client.query(query)
    
    print("\nColumn Details:")
    for row in result.result_set:
        print(f"  - {row[0]:25s} | Type: {row[1]:20s}")
    
    return result.result_set

def get_row_count(client):
    """Get total row count"""
    query = "SELECT count() as total_rows FROM NYCTaxiAnalysis.bronze_taxi_trips"
    result = client.query(query).result_set[0][0]
    print(f"\nTotal Rows: {result:,}")
    return result

def analyze_null_values(client, columns):
    """Analyze NULL values for each column"""
    print_section("NULL VALUE ANALYSIS")
    
    for col in columns:
        col_name = col[0]
        query = f"""
        SELECT 
            countIf({col_name} IS NULL) as null_count,
            count() as total_count,
            round(countIf({col_name} IS NULL) * 100.0 / count(), 2) as null_percentage
        FROM NYCTaxiAnalysis.bronze_taxi_trips
        """
        result = client.query(query).result_set[0]
        if result[0] > 0:
            print(f"  {col_name:25s}: {result[0]:10,} nulls ({result[2]:6.2f}%)")

def analyze_categorical_columns(client):
    """Analyze categorical columns with GROUP BY and COUNT"""
    print_section("CATEGORICAL COLUMN ANALYSIS")
    
    # VendorID
    print("\nVendorID Distribution:")
    query = """
    SELECT VendorID, count() as cnt, round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY VendorID
    ORDER BY cnt DESC
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  VendorID {row[0]}: {row[1]:,} trips ({row[2]}%)")
    
    # payment_type
    print("\nPayment Type Distribution:")
    query = """
    SELECT payment_type, count() as cnt, round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY payment_type
    ORDER BY cnt DESC
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  Payment Type {row[0]}: {row[1]:,} trips ({row[2]}%)")
    
    # RatecodeID
    print("\nRatecode ID Distribution:")
    query = """
    SELECT RatecodeID, count() as cnt, round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY RatecodeID
    ORDER BY cnt DESC
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  RatecodeID {row[0]}: {row[1]:,} trips ({row[2]}%)")
    
    # store_and_fwd_flag
    print("\nStore and Forward Flag Distribution:")
    query = """
    SELECT store_and_fwd_flag, count() as cnt, round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY store_and_fwd_flag
    ORDER BY cnt DESC
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  Store&Fwd '{row[0]}': {row[1]:,} trips ({row[2]}%)")

def analyze_numeric_columns(client):
    """Analyze numeric columns - min, max, avg, median"""
    print_section("NUMERIC COLUMN ANALYSIS")
    
    numeric_cols = [
        'passenger_count',
        'trip_distance',
        'fare_amount',
        'extra',
        'mta_tax',
        'tip_amount',
        'tolls_amount',
        'improvement_surcharge',
        'total_amount',
        'congestion_surcharge',
        'Airport_fee'
    ]
    
    for col in numeric_cols:
        print(f"\n{col}:")
        query = f"""
        SELECT 
            min({col}) as min_val,
            max({col}) as max_val,
            round(avg({col}), 2) as avg_val,
            round(median({col}), 2) as median_val,
            round(stddevPop({col}), 2) as stddev
        FROM NYCTaxiAnalysis.bronze_taxi_trips
        WHERE {col} IS NOT NULL
        """
        result = client.query(query).result_set[0]
        print(f"  Min: {result[0]}, Max: {result[1]}, Avg: {result[2]}, Median: {result[3]}, StdDev: {result[4]}")
        
        # Check for outliers (values < 0 for amounts, extreme values)
        if 'amount' in col or 'fare' in col or 'tip' in col or 'toll' in col or 'surcharge' in col or 'fee' in col:
            query_neg = f"SELECT countIf({col} < 0) FROM NYCTaxiAnalysis.bronze_taxi_trips"
            neg_count = client.query(query_neg).result_set[0][0]
            if neg_count > 0:
                print(f"  WARNING: {neg_count:,} negative values found")
        
        # Check passenger_count outliers
        if col == 'passenger_count':
            query_zero = f"SELECT countIf({col} = 0) FROM NYCTaxiAnalysis.bronze_taxi_trips"
            zero_count = client.query(query_zero).result_set[0][0]
            if zero_count > 0:
                print(f"  WARNING: {zero_count:,} trips with 0 passengers")
            
            query_high = f"SELECT countIf({col} > 6) FROM NYCTaxiAnalysis.bronze_taxi_trips"
            high_count = client.query(query_high).result_set[0][0]
            if high_count > 0:
                print(f"  WARNING: {high_count:,} trips with >6 passengers")

def analyze_temporal_patterns(client):
    """Analyze temporal distribution"""
    print_section("TEMPORAL PATTERN ANALYSIS")
    
    # Date range
    print("\nDate Range:")
    query = """
    SELECT 
        min(tpep_pickup_datetime) as earliest,
        max(tpep_pickup_datetime) as latest,
        date_diff('day', min(tpep_pickup_datetime), max(tpep_pickup_datetime)) as days_span
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    """
    result = client.query(query).result_set[0]
    print(f"  Earliest: {result[0]}")
    print(f"  Latest: {result[1]}")
    print(f"  Span: {result[2]:,} days")
    
    # Check for data quality issues with dates
    print("\nDate Quality Issues:")
    query = """
    SELECT 
        countIf(tpep_pickup_datetime < '2009-01-01') as before_2009,
        countIf(tpep_pickup_datetime > '2025-01-01') as after_2025,
        countIf(tpep_dropoff_datetime < tpep_pickup_datetime) as dropoff_before_pickup
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    """
    result = client.query(query).result_set[0]
    print(f"  Trips before 2009: {result[0]:,}")
    print(f"  Trips after 2025: {result[1]:,}")
    print(f"  Dropoff before pickup: {result[2]:,}")
    
    # Hour of day distribution
    print("\nHour of Day Distribution (Top 10):")
    query = """
    SELECT 
        toHour(tpep_pickup_datetime) as hour,
        count() as cnt,
        round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY hour
    ORDER BY cnt DESC
    LIMIT 10
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  Hour {row[0]:02d}:00 - {row[1]:,} trips ({row[2]}%)")
    
    # Day of week distribution
    print("\nDay of Week Distribution:")
    query = """
    SELECT 
        toDayOfWeek(tpep_pickup_datetime) as dow,
        CASE toDayOfWeek(tpep_pickup_datetime)
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
            WHEN 7 THEN 'Sunday'
        END as day_name,
        count() as cnt,
        round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY dow, day_name
    ORDER BY dow
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  {row[1]:9s}: {row[2]:,} trips ({row[3]}%)")
    
    # Month distribution
    print("\nMonth Distribution (Top 12):")
    query = """
    SELECT 
        toYear(tpep_pickup_datetime) as year,
        toMonth(tpep_pickup_datetime) as month,
        count() as cnt,
        round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY year, month
    ORDER BY cnt DESC
    LIMIT 12
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  {row[0]}-{row[1]:02d}: {row[2]:,} trips ({row[3]}%)")

def analyze_geographic_patterns(client):
    """Analyze geographic distribution"""
    print_section("GEOGRAPHIC PATTERN ANALYSIS")
    
    # Top pickup locations
    print("\nTop 15 Pickup Locations (PULocationID):")
    query = """
    SELECT 
        PULocationID,
        count() as cnt,
        round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY PULocationID
    ORDER BY cnt DESC
    LIMIT 15
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  Location {row[0]:3d}: {row[1]:,} pickups ({row[2]}%)")
    
    # Top dropoff locations
    print("\nTop 15 Dropoff Locations (DOLocationID):")
    query = """
    SELECT 
        DOLocationID,
        count() as cnt,
        round(count() * 100.0 / (SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips), 2) as pct
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    GROUP BY DOLocationID
    ORDER BY cnt DESC
    LIMIT 15
    """
    result = client.query(query)
    for row in result.result_set:
        print(f"  Location {row[0]:3d}: {row[1]:,} dropoffs ({row[2]}%)")
    
    # Check for NULL or 0 location IDs
    print("\nLocation ID Quality:")
    query = """
    SELECT 
        countIf(PULocationID IS NULL OR PULocationID = 0) as null_pickup,
        countIf(DOLocationID IS NULL OR DOLocationID = 0) as null_dropoff,
        countIf(PULocationID = DOLocationID) as same_location
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    """
    result = client.query(query).result_set[0]
    print(f"  Null/Zero Pickup Locations: {result[0]:,}")
    print(f"  Null/Zero Dropoff Locations: {result[1]:,}")
    print(f"  Same Pickup/Dropoff: {result[2]:,}")

def analyze_trip_duration(client):
    """Analyze trip duration"""
    print_section("TRIP DURATION ANALYSIS")
    
    query = """
    SELECT 
        round(min(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime)), 2) as min_minutes,
        round(max(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime)), 2) as max_minutes,
        round(avg(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime)), 2) as avg_minutes,
        round(median(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime)), 2) as median_minutes
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    """
    result = client.query(query).result_set[0]
    print(f"  Min Duration: {result[0]} minutes")
    print(f"  Max Duration: {result[1]} minutes")
    print(f"  Avg Duration: {result[2]} minutes")
    print(f"  Median Duration: {result[3]} minutes")
    
    # Check for anomalies
    query = """
    SELECT 
        countIf(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) < 0) as negative_duration,
        countIf(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) = 0) as zero_duration,
        countIf(date_diff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) > 1440) as over_24hrs
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    """
    result = client.query(query).result_set[0]
    if result[0] > 0:
        print(f"  WARNING: {result[0]:,} trips with negative duration")
    if result[1] > 0:
        print(f"  NOTE: {result[1]:,} trips with 0 minute duration")
    if result[2] > 0:
        print(f"  WARNING: {result[2]:,} trips over 24 hours")

def sample_data(client):
    """Get sample rows"""
    print_section("SAMPLE DATA (First 5 Rows)")
    
    query = """
    SELECT *
    FROM NYCTaxiAnalysis.bronze_taxi_trips
    LIMIT 5
    """
    result = client.query(query)
    
    # Get column names
    col_query = """
    SELECT name
    FROM system.columns
    WHERE database = 'NYCTaxiAnalysis' AND table = 'bronze_taxi_trips'
    ORDER BY position
    """
    columns = [row[0] for row in client.query(col_query).result_set]
    
    print("\nColumns:", ", ".join(columns))
    print("\nSample rows:")
    for i, row in enumerate(result.result_set, 1):
        print(f"\nRow {i}:")
        for col, val in zip(columns, row):
            print(f"  {col:25s}: {val}")

def main():
    """Main analysis function"""
    try:
        print("Connecting to ClickHouse...")
        client = connect_to_clickhouse()
        print("Connected successfully!")
        
        # Run all analyses
        columns = analyze_table_structure(client)
        get_row_count(client)
        analyze_null_values(client, columns)
        analyze_categorical_columns(client)
        analyze_numeric_columns(client)
        analyze_temporal_patterns(client)
        analyze_geographic_patterns(client)
        analyze_trip_duration(client)
        sample_data(client)
        
        print_section("ANALYSIS COMPLETE")
        print("\nAnalysis completed successfully!")
        print("This data will be used to create SCHEMA.md and design the Kepner-Tregoe framework.")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
