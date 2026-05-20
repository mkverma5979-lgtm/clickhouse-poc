"""
NYC Taxi Data Ingestion Script

This script downloads the latest 6 months of NYC Taxi trip data and imports it 
into ClickHouse Cloud under the NYCTaxiAnalysis database in the bronze schema.

NOTE: In future, this ingestion step should be automated through a data pipeline,
but we are doing it manually for now.
"""

import clickhouse_connect
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
import pandas as pd

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

def create_database_and_schema(client):
    """Create NYCTaxiAnalysis database"""
    print("[INFO] Creating NYCTaxiAnalysis database...")
    
    # Create database
    client.command("CREATE DATABASE IF NOT EXISTS NYCTaxiAnalysis")
    print("[OK] Database 'NYCTaxiAnalysis' created/verified")
    
    # Note: ClickHouse doesn't have explicit "schemas" like PostgreSQL
    # We'll use table naming convention: bronze_tablename, silver_tablename, gold_tablename
    # Or we can create separate databases for bronze, silver, gold
    # For now, we'll use table prefixes within NYCTaxiAnalysis database
    
def create_bronze_table(client):
    """Create bronze layer table for NYC Taxi data"""
    print("[INFO] Creating bronze table for NYC Taxi trips...")
    
    # Drop table if exists (for clean run)
    client.command("DROP TABLE IF EXISTS NYCTaxiAnalysis.bronze_taxi_trips")
    
    # Create table with NYC Taxi data schema (using Nullable for columns that may have NULL values)
    # Note: Columns used in ORDER BY cannot be nullable
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS NYCTaxiAnalysis.bronze_taxi_trips
    (
        VendorID Nullable(Int32),
        tpep_pickup_datetime DateTime,
        tpep_dropoff_datetime DateTime,
        passenger_count Nullable(Float64),
        trip_distance Nullable(Float64),
        RatecodeID Nullable(Float64),
        store_and_fwd_flag Nullable(String),
        PULocationID Int32,
        DOLocationID Nullable(Int32),
        payment_type Nullable(Int32),
        fare_amount Nullable(Float64),
        extra Nullable(Float64),
        mta_tax Nullable(Float64),
        tip_amount Nullable(Float64),
        tolls_amount Nullable(Float64),
        improvement_surcharge Nullable(Float64),
        total_amount Nullable(Float64),
        congestion_surcharge Nullable(Float64),
        Airport_fee Nullable(Float64),
        cbd_congestion_fee Nullable(Float64)
    )
    ENGINE = MergeTree()
    ORDER BY (tpep_pickup_datetime, PULocationID)
    PARTITION BY toYYYYMM(tpep_pickup_datetime)
    """
    
    client.command(create_table_sql)
    print("[OK] Bronze table created successfully")

def get_taxi_data_urls(months=6):
    """Generate URLs for the last N months of NYC Yellow Taxi data"""
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
    
    urls = []
    current_date = datetime.now()
    
    for i in range(months):
        # Calculate the date for each month back
        date = current_date - timedelta(days=30*i)
        year = date.year
        month = date.month
        
        url = base_url.format(year=year, month=month)
        urls.append((f"{year}-{month:02d}", url))
    
    return urls

def download_and_insert_data(client):
    """Download NYC Taxi data and insert into ClickHouse"""
    print("[INFO] Starting data download and ingestion...")
    print("[NOTE] This may take several minutes depending on your internet speed...")
    
    # Get URLs for last 6 months
    data_urls = get_taxi_data_urls(months=6)
    
    total_rows = 0
    
    for month, url in data_urls:
        try:
            print(f"\n[INFO] Processing data for {month}...")
            print(f"[INFO] Downloading from: {url}")
            
            # Download parquet file
            response = requests.get(url, timeout=300)
            
            if response.status_code == 200:
                # Save temporarily
                temp_file = f"temp_taxi_data_{month}.parquet"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                
                # Read with pandas
                df = pd.read_parquet(temp_file)
                print(f"[OK] Downloaded {len(df)} rows for {month}")
                
                # Handle NULL values for non-nullable columns (PULocationID)
                # Fill with 0 for location IDs that are NULL
                df['PULocationID'] = df['PULocationID'].fillna(0).astype(int)
                
                # Insert into ClickHouse
                client.insert_df('NYCTaxiAnalysis.bronze_taxi_trips', df)
                print(f"[OK] Inserted {len(df)} rows into ClickHouse")
                
                total_rows += len(df)
                
                # Clean up temp file
                os.remove(temp_file)
                
            else:
                print(f"[WARN] Could not download data for {month} (Status: {response.status_code})")
                
        except Exception as e:
            print(f"[ERROR] Failed to process {month}: {e}")
            continue
    
    print(f"\n[OK] Total rows inserted: {total_rows:,}")
    return total_rows

def verify_data(client):
    """Verify the imported data"""
    print("\n[INFO] Verifying imported data...")
    
    # Count rows
    result = client.query("SELECT count() FROM NYCTaxiAnalysis.bronze_taxi_trips")
    row_count = result.result_set[0][0]
    print(f"[OK] Total rows in bronze_taxi_trips: {row_count:,}")
    
    # Get date range
    result = client.query("""
        SELECT 
            min(tpep_pickup_datetime) as earliest_trip,
            max(tpep_pickup_datetime) as latest_trip
        FROM NYCTaxiAnalysis.bronze_taxi_trips
    """)
    earliest, latest = result.result_set[0]
    print(f"[OK] Date range: {earliest} to {latest}")
    
    # Sample data
    print("\n[INFO] Sample data (first 5 rows):")
    result = client.query("SELECT * FROM NYCTaxiAnalysis.bronze_taxi_trips LIMIT 5")
    for row in result.result_set:
        print(f"  {row}")

if __name__ == '__main__':
    print("=" * 60)
    print("NYC Taxi Data Ingestion - Bronze Layer")
    print("=" * 60)
    print("\nNOTE: In future, this ingestion step should be automated")
    print("through a data pipeline, but we are doing it manually for now.\n")
    
    try:
        # Connect to ClickHouse
        client = get_clickhouse_client()
        print("[OK] Connected to ClickHouse Cloud\n")
        
        # Create database and schema
        create_database_and_schema(client)
        
        # Create bronze table
        create_bronze_table(client)
        
        # Download and insert data
        download_and_insert_data(client)
        
        # Verify data
        verify_data(client)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Data ingestion completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Ingestion failed: {e}")
        raise
