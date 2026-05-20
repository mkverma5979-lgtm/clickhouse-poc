-- ============================================================================
-- NYC TAXI ANALYSIS - COMPLETE SQL CODE
-- ============================================================================
-- Project: Kepner-Tregoe IS/IS NOT Analysis Dashboard
-- Database: NYCTaxiAnalysis (ClickHouse Cloud)
-- Created: May 20, 2026
-- Architecture: Bronze → Silver → Gold layers
-- Power BI: Connects to gold views only (NO DAX calculations)
-- ============================================================================

-- ============================================================================
-- BRONZE LAYER: RAW DATA
-- ============================================================================

-- Table: bronze_taxi_trips
-- Description: Raw NYC Taxi trip data (15.4M rows)
-- Source: NYC TLC Yellow Taxi trip records (latest 6 months)
-- Note: Loaded via Python script ingest_data.py (manual ingestion for now)

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
PARTITION BY toYYYYMM(tpep_pickup_datetime);

-- Data Quality Notes for Bronze Layer:
-- 1. 27.65% of records have NULL values in passenger_count, RatecodeID, etc.
-- 2. 99.99% of trips dated 2025-2026 (temporal anomaly - likely year offset error)
-- 3. Negative financial values present (135k negative fares)
-- 4. Extreme outliers (trip_distance max: 328,522 miles)
-- 5. Logical impossibilities (59,465 trips with 0 passengers)
-- See SCHEMA.md for complete data quality documentation

-- ============================================================================
-- SILVER LAYER: CLEANED & AGGREGATED DATA
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View 1: silver_trips_cleaned
-- Description: Cleaned trip records with data quality filters applied
-- Filters: Removes negative values, extreme outliers, logical impossibilities
-- Adds: Derived fields (trip_duration, hour, day_of_week, quality flags)
-- ----------------------------------------------------------------------------

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
    -- Data Quality Filters:
    AND fare_amount >= 0  -- No negative fares
    AND total_amount >= 0  -- No negative totals
    AND tip_amount >= 0  -- No negative tips
    AND tolls_amount >= 0  -- No negative tolls
    AND improvement_surcharge >= 0  -- No negative surcharges
    AND (congestion_surcharge >= 0 OR congestion_surcharge IS NULL)
    AND (Airport_fee >= 0 OR Airport_fee IS NULL)
    AND trip_distance >= 0  -- No negative distance
    AND trip_distance <= 100  -- Filter extreme outliers (>100 miles)
    AND (passenger_count > 0 OR passenger_count IS NULL)  -- No 0 passengers
    AND tpep_dropoff_datetime >= tpep_pickup_datetime  -- No negative duration
    AND dateDiff('minute', tpep_pickup_datetime, tpep_dropoff_datetime) <= 240  -- Max 4 hours
    AND fare_amount <= 500  -- Reasonable fare cap
    AND total_amount <= 1000;  -- Reasonable total cap

-- Result: 15,178,751 rows (98.7% of bronze data retained after filtering)

-- ----------------------------------------------------------------------------
-- View 2: silver_trips_hourly
-- Description: Hourly aggregations for temporal pattern analysis
-- Use Case: Peak hour identification, time-based trends, K-T "WHEN" analysis
-- ----------------------------------------------------------------------------

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
GROUP BY trip_date, pickup_hour, pickup_day_of_week;

-- Result: 2,908 rows (hourly aggregations across dates)

-- ----------------------------------------------------------------------------
-- View 3: silver_trips_by_location
-- Description: Location-based aggregations (pickup and dropoff separately)
-- Use Case: Geographic hot zone analysis, K-T "WHERE" analysis
-- ----------------------------------------------------------------------------

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
ORDER BY (location_id, location_type);

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
GROUP BY location_id, location_type;

-- Result: 523 rows (262 pickup locations + 261 dropoff locations)

-- ----------------------------------------------------------------------------
-- View 4: silver_trips_by_payment
-- Description: Payment method analysis with tip patterns
-- Use Case: Credit vs cash comparison, tipping behavior, K-T "WHAT" analysis
-- ----------------------------------------------------------------------------

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
ORDER BY payment_type;

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
GROUP BY payment_type;

-- Result: 5 rows (one per payment type)
-- Key Insight: Credit card dominates (62% of trips), cash only 9%

-- ----------------------------------------------------------------------------
-- View 5: silver_trips_by_vendor
-- Description: Vendor comparison with data quality metrics
-- Use Case: Vendor performance comparison, data completeness analysis
-- ----------------------------------------------------------------------------

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
ORDER BY VendorID;

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
GROUP BY VendorID;

-- Result: 4 rows (Vendor 1, 2, 6, 7)
-- Key Insight: Vendor 2 dominates (79.5% of trips)

-- ============================================================================
-- GOLD LAYER: BUSINESS LOGIC VIEWS FOR KEPNER-TREGOE ANALYSIS
-- ============================================================================
-- These views are consumed directly by Power BI with NO DAX calculations
-- Each view corresponds to one dimension of the Kepner-Tregoe IS/IS NOT framework
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Gold View 1: gold_kt_what_is_happening
-- K-T Dimension: WHAT is happening (trip types, service patterns)
-- Power BI Pages: Executive Summary, WHAT Analysis page
-- ----------------------------------------------------------------------------

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

ORDER BY dimension_category, volume DESC;

-- Result: 9 rows (4 vendors + 5 payment methods)
-- Power BI Usage: Bar charts showing trip distribution by vendor and payment method

-- ----------------------------------------------------------------------------
-- Gold View 2: gold_kt_where_is_happening
-- K-T Dimension: WHERE is happening (geographic hot zones vs cold zones)
-- Power BI Pages: WHERE Analysis page (with map visual)
-- ----------------------------------------------------------------------------

CREATE VIEW NYCTaxiAnalysis.gold_kt_where_is_happening AS
WITH location_stats AS (
    SELECT
        location_id,
        location_type,
        trip_count,
        round(avg_fare, 2) AS avg_fare,
        round(avg_distance, 2) AS avg_distance,
        same_location_trips,
        percent_rank() OVER (PARTITION BY location_type ORDER BY trip_count) AS percentile_rank
    FROM NYCTaxiAnalysis.silver_trips_by_location
)
SELECT
    location_id,
    concat('Location ', toString(location_id)) AS location_name,
    location_type,
    trip_count AS pickup_count,
    0 AS dropoff_count,
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
ORDER BY trip_count DESC;

-- Result: 262 rows (pickup locations with zone classifications)
-- Power BI Usage: Map visual with location hot spots, bar charts for top/bottom locations

-- ----------------------------------------------------------------------------
-- Gold View 3: gold_kt_when_is_happening
-- K-T Dimension: WHEN is happening (temporal patterns, peak vs off-peak)
-- Power BI Pages: WHEN Analysis page
-- ----------------------------------------------------------------------------

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

ORDER BY time_dimension, trip_volume DESC;

-- Result: 31 rows (24 hours + 7 days of week)
-- Power BI Usage: Line charts for hourly trends, bar charts for day-of-week patterns

-- ----------------------------------------------------------------------------
-- Gold View 4: gold_kt_extent_magnitude
-- K-T Dimension: EXTENT and MAGNITUDE (volume, distributions, outliers)
-- Power BI Pages: EXTENT Analysis page
-- ----------------------------------------------------------------------------

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
       0.0;

-- Result: 5 rows (distance, fare, total, duration, trip count stats)
-- Power BI Usage: KPI cards, histograms, distribution charts

-- ----------------------------------------------------------------------------
-- Gold View 5: gold_kt_what_not_happening
-- K-T Dimension: WHAT IS NOT happening (absence analysis, data quality)
-- Power BI Pages: ABSENCE Analysis page
-- ----------------------------------------------------------------------------

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
) ORDER BY null_percentage DESC;

-- Result: 7 rows (6 fields with NULLs + 1 row showing filtered data)
-- Power BI Usage: Bar chart showing data completeness, waterfall chart of data filtering

-- ----------------------------------------------------------------------------
-- Gold View 6: gold_kt_characteristics_comparison
-- K-T Dimension: CHARACTERISTICS (IS vs IS NOT side-by-side comparisons)
-- Power BI Pages: CHARACTERISTICS Comparison page
-- ----------------------------------------------------------------------------

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
           (SELECT avg(fare_amount) FROM NYCTaxiAnalysis.silver_trips_cleaned WHERE trip_distance > 10), 2);

-- Result: 4 rows (4 key IS vs IS NOT comparisons)
-- Power BI Usage: Stacked bar charts showing side-by-side comparisons

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check all views exist and have data:
SELECT 'bronze_taxi_trips' AS layer, count() AS row_count FROM NYCTaxiAnalysis.bronze_taxi_trips
UNION ALL
SELECT 'silver_trips_cleaned', count() FROM NYCTaxiAnalysis.silver_trips_cleaned
UNION ALL
SELECT 'silver_trips_hourly', count() FROM NYCTaxiAnalysis.silver_trips_hourly
UNION ALL
SELECT 'silver_trips_by_location', count() FROM NYCTaxiAnalysis.silver_trips_by_location
UNION ALL
SELECT 'silver_trips_by_payment', count() FROM NYCTaxiAnalysis.silver_trips_by_payment
UNION ALL
SELECT 'silver_trips_by_vendor', count() FROM NYCTaxiAnalysis.silver_trips_by_vendor
UNION ALL
SELECT 'gold_kt_what_is_happening', count() FROM NYCTaxiAnalysis.gold_kt_what_is_happening
UNION ALL
SELECT 'gold_kt_where_is_happening', count() FROM NYCTaxiAnalysis.gold_kt_where_is_happening
UNION ALL
SELECT 'gold_kt_when_is_happening', count() FROM NYCTaxiAnalysis.gold_kt_when_is_happening
UNION ALL
SELECT 'gold_kt_extent_magnitude', count() FROM NYCTaxiAnalysis.gold_kt_extent_magnitude
UNION ALL
SELECT 'gold_kt_what_not_happening', count() FROM NYCTaxiAnalysis.gold_kt_what_not_happening
UNION ALL
SELECT 'gold_kt_characteristics_comparison', count() FROM NYCTaxiAnalysis.gold_kt_characteristics_comparison;

-- Sample queries for each gold view (for testing before Power BI connection):

-- Sample: WHAT is happening
SELECT * FROM NYCTaxiAnalysis.gold_kt_what_is_happening LIMIT 10;

-- Sample: WHERE is happening (top 10 hot zones)
SELECT * FROM NYCTaxiAnalysis.gold_kt_where_is_happening 
WHERE zone_classification = 'Hot Zone' 
ORDER BY pickup_count DESC 
LIMIT 10;

-- Sample: WHEN is happening (peak hours)
SELECT * FROM NYCTaxiAnalysis.gold_kt_when_is_happening 
WHERE classification = 'Peak Period' 
ORDER BY trip_volume DESC;

-- Sample: EXTENT and magnitude
SELECT * FROM NYCTaxiAnalysis.gold_kt_extent_magnitude;

-- Sample: WHAT NOT happening (biggest data gaps)
SELECT * FROM NYCTaxiAnalysis.gold_kt_what_not_happening 
ORDER BY null_percentage DESC;

-- Sample: Characteristics comparison
SELECT * FROM NYCTaxiAnalysis.gold_kt_characteristics_comparison;

-- ============================================================================
-- END OF SQL CODE
-- ============================================================================
-- Next Steps:
-- 1. Connect Power BI Desktop to ClickHouse using ODBC driver
-- 2. Import all 6 gold views as data sources
-- 3. Build 7 dashboard pages (no DAX, direct field references only)
-- 4. See Power BI connection guide in project documentation
-- ============================================================================
