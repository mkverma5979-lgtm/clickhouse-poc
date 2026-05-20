# NYC Taxi Kepner-Tregoe Analysis Project

**Project Type:** Data Analytics - Business Intelligence Dashboard  
**Framework:** Kepner-Tregoe IS/IS NOT Problem Analysis  
**Technology Stack:** ClickHouse Cloud + Power BI Desktop  
**Created:** May 20, 2026

---

## Project Purpose

This project implements a comprehensive Kepner-Tregoe "IS / IS NOT" analysis framework on NYC Taxi trip data to identify patterns, anomalies, and business insights. The analysis systematically contrasts what IS happening vs what IS NOT happening across multiple dimensions to reveal root causes and distinctive patterns.

**End Goal:** A Power BI dashboard that visually presents the Kepner-Tregoe framework with all analytical logic implemented in ClickHouse SQL (NO DAX in Power BI).

---

## Project Architecture

### 3-Layer Data Architecture (Bronze-Silver-Gold)

```
Bronze Layer (Raw Data)
    ↓
Silver Layer (Cleaned & Materialized Views)
    ↓
Gold Layer (Business Logic Views)
    ↓
Power BI Dashboard (Pure Visualization Layer)
```

**Design Principle:** All business logic lives in SQL. Power BI is a "dumb" UI layer with no calculations, measures, or DAX code.

---

## Data Source

### NYC Taxi Trip Data
- **Source:** NYC Taxi & Limousine Commission (TLC) public dataset
- **Period:** Latest 6 months of Yellow Taxi trip data
- **Volume:** 15,382,212 trips
- **Format:** Parquet files from NYC Open Data portal

**Note:** In future, this ingestion should be automated through a data pipeline, but currently done manually via Python script.

---

## Database Structure

### ClickHouse Cloud Database: `NYCTaxiAnalysis`

#### Bronze Layer (Raw Data)
- **`bronze_taxi_trips`** - Raw trip records with 20 columns, 15.4M rows
  - Partitioned by month: `toYYYYMM(tpep_pickup_datetime)`
  - Engine: MergeTree
  - Order by: `(tpep_pickup_datetime, PULocationID)`
  - **See SCHEMA.md for complete column documentation**

#### Silver Layer (Cleaned Data - Materialized Views)
- **`silver_trips_cleaned`** - All outliers and data quality issues removed
- **`silver_trips_hourly`** - Hourly aggregations with temporal patterns
- **`silver_trips_by_location`** - Geographic aggregations by TLC zone
- **`silver_trips_by_payment`** - Payment method analysis with tip patterns
- **`silver_trips_by_vendor`** - Vendor comparison and data quality metrics

#### Gold Layer (Business Logic for Power BI)
- **`gold_kt_what_is_happening`** - Service patterns, trip types, problem frequencies
- **`gold_kt_where_is_happening`** - Geographic hot/cold zones, location-based metrics
- **`gold_kt_when_is_happening`** - Temporal patterns, peak/off-peak comparisons
- **`gold_kt_extent_magnitude`** - Volume, magnitude, distribution metrics
- **`gold_kt_what_not_happening`** - Absence analysis, NULL patterns, anomalies
- **`gold_kt_characteristics_comparison`** - IS vs IS NOT side-by-side comparisons

---

## Kepner-Tregoe IS/IS NOT Framework

The analysis framework systematically examines 6 dimensions:

### 1. WHAT is happening
- Trip types, service patterns, payment behaviors
- What types of trips are occurring vs not occurring
- Problem frequency by characteristic

### 2. WHERE is happening
- Geographic hot zones vs cold zones
- High-activity areas vs low-activity areas
- Location-based problem rates

### 3. WHEN is happening
- Peak hours vs off-peak hours
- Busy days vs quiet days
- Seasonal patterns and trends

### 4. EXTENT of occurrence
- Volume magnitude (trips per period)
- Financial magnitude (fare distributions)
- Distance and duration patterns

### 5. WHAT IS NOT happening
- Missing patterns and gaps
- NULL value analysis
- Anomalies and data quality issues

### 6. CHARACTERISTICS (IS vs IS NOT comparisons)
- Credit card vs Cash trips
- Short trips vs Long trips
- Airport vs City trips
- Peak vs Off-peak trips
- Complete records vs Incomplete records

**Reference:** See `KEPNER_TREGOE_INSIGHTS.md` for detailed framework implementation guidance.

---

## Key Files & Their Purpose

### Documentation
- **`SCHEMA.md`** ⭐ - Complete data dictionary and schema documentation
  - Column definitions in plain English
  - Data quality issues documented
  - Statistical summaries
  - Business context for each field
  - **READ THIS FIRST before querying the database**

- **`AGENTS.md`** (this file) - Project overview and structure
- **`ANALYSIS_SUMMARY.md`** - Detailed data analysis results
- **`KEPNER_TREGOE_INSIGHTS.md`** - Framework design and SQL templates
- **`README.md`** - Project setup and usage instructions

### Code Files
- **`all_sql_code.sql`** - Master SQL file with all DDL for bronze/silver/gold layers
- **`ingest_data.py`** - Bronze layer data ingestion script (manual, should be pipeline in future)
- **`test_connection.py`** - ClickHouse connection test script
- **`analyze_schema.py`** - Data profiling and analysis script

### Configuration
- **`.env`** - ClickHouse Cloud connection credentials (DO NOT COMMIT TO GIT)
- **`.gitignore`** - Git exclusion rules (includes .env)

---

## Data Quality Considerations

### Critical Issues Addressed in Silver Layer

1. **Temporal Anomaly:** 99.99% of trips dated 2025-2026 (likely year offset error)
2. **NULL Pattern:** 27.65% of records missing passenger_count, RatecodeID, and 4 other fields
3. **Negative Values:** Financial fields have negative values (135k negative fares)
4. **Extreme Outliers:** trip_distance max of 328,522 miles (impossible)
5. **Logical Impossibilities:** 59,465 trips with 0 passengers, 7 trips with negative duration

**Strategy:** Silver layer applies filters and data quality flags. Gold layer excludes problematic records unless specifically analyzing data quality issues.

**Detail:** See "Data Quality Summary" section in SCHEMA.md for complete documentation.

---

## Power BI Dashboard Structure

### 7 Dashboard Pages

1. **Executive Summary** - Overview with 6 K-T dimension cards and navigation
2. **WHAT Analysis** - Trip types, vendor patterns, service characteristics
3. **WHERE Analysis** - Geographic hot zones, location maps, route patterns
4. **WHEN Analysis** - Temporal patterns, peak hours, day/week/month trends
5. **EXTENT Analysis** - Volume and magnitude distributions, outlier detection
6. **ABSENCE Analysis** - What's NOT happening, gaps, data quality issues
7. **CHARACTERISTICS Comparison** - Side-by-side IS vs IS NOT comparisons

**Design Rule:** NO DAX calculations, NO measures, NO calculated columns. All logic in gold views.

---

## Development Workflow

### Current State (Completed)
✅ ClickHouse Cloud account created  
✅ Bronze layer data loaded (15.4M trips)  
✅ Data analysis completed  
✅ SCHEMA.md documentation created  
✅ AGENTS.md created

### In Progress
🔨 Silver layer materialized views  
🔨 Gold layer business logic views  
🔨 SQL code documentation

### Upcoming
⏳ Power BI connection setup  
⏳ Dashboard development  
⏳ Git repository setup and version control

---

## How to Use This Project

### For Data Analysts
1. **Read SCHEMA.md first** to understand the data structure and quality issues
2. Review KEPNER_TREGOE_INSIGHTS.md for the analytical framework
3. Query gold views in ClickHouse for pre-calculated metrics
4. Use Power BI to visualize the results (no custom calculations needed)

### For Developers
1. Review `.env.example` for connection setup (actual `.env` file not in Git)
2. Run `test_connection.py` to verify ClickHouse connectivity
3. Review `all_sql_code.sql` for view definitions
4. Modify silver/gold views as needed for new analysis requirements

### For OpenCode CLI and AI Tools
- **Primary reference:** SCHEMA.md contains all column definitions and business context
- **Database:** NYCTaxiAnalysis on ClickHouse Cloud
- **Main table:** bronze_taxi_trips (15.4M rows)
- **Query strategy:** Use gold views for analytics (pre-aggregated)
- **Date field:** tpep_pickup_datetime (note quality issues documented in SCHEMA.md)
- **Location fields:** PULocationID and DOLocationID (TLC zone IDs, no NULLs)

---

## Analytical Queries

### Common Query Patterns

```sql
-- Example: Get peak hour trip counts
SELECT hour, trip_count, classification
FROM NYCTaxiAnalysis.gold_kt_when_is_happening
WHERE time_dimension = 'hour'
ORDER BY trip_volume DESC;

-- Example: Get hot zones vs cold zones
SELECT location_id, pickup_count, zone_classification
FROM NYCTaxiAnalysis.gold_kt_where_is_happening
WHERE zone_classification IN ('hot', 'cold')
ORDER BY pickup_count DESC;

-- Example: Credit card vs cash comparison
SELECT comparison_dimension, is_category, is_not_category,
       is_metric_value, is_not_metric_value, difference_percentage
FROM NYCTaxiAnalysis.gold_kt_characteristics_comparison
WHERE comparison_dimension = 'payment_method';
```

More examples in KEPNER_TREGOE_INSIGHTS.md.

---

## External References

- **NYC TLC Trip Data:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **TLC Taxi Zones Shapefile:** https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc
- **Data Dictionary (Official):** https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf
- **Kepner-Tregoe Method:** https://kepner-tregoe.com/

---

## Team & Collaboration

### Git Repository
- **Status:** To be initialized and pushed to remote
- **Branch Strategy:** Main branch for stable code, feature branches for development
- **Commit Guidelines:** Descriptive messages, commit SQL changes separately from Python

### Version Control Notes
- `.env` file is excluded from Git (contains sensitive credentials)
- Use `.env.example` as template for new team members
- All SQL DDL in `all_sql_code.sql` for easy review and deployment

---

## Future Enhancements

### Automation Opportunities
1. **Data Pipeline:** Automate monthly data ingestion (currently manual Python script)
2. **Incremental Updates:** Implement incremental refresh instead of full reload
3. **Data Quality Alerts:** Automated monitoring for anomaly detection
4. **Scheduled Refresh:** Power BI scheduled refresh from ClickHouse

### Analysis Extensions
1. **Predictive Modeling:** Demand forecasting by location/time
2. **Route Optimization:** Identify efficient pickup/dropoff patterns
3. **Pricing Analysis:** Dynamic fare optimization insights
4. **Driver Behavior:** Vendor performance comparison

### Dashboard Enhancements
1. **Interactive Filters:** Cross-page filtering in Power BI
2. **Drill-Through Pages:** Detailed analysis on click
3. **Mobile Layout:** Responsive design for mobile viewing
4. **Export Capabilities:** Scheduled report distribution

---

## Troubleshooting

### ClickHouse Connection Issues
- Verify credentials in `.env` file
- Run `python test_connection.py` to diagnose
- Check firewall settings (ClickHouse Cloud port 8443)
- Ensure `clickhouse-connect` Python package installed

### Data Quality Questions
- Refer to "Data Quality Summary" in SCHEMA.md
- Silver layer filters handle most issues automatically
- For custom analysis, apply filters documented in SCHEMA.md

### Power BI Connection Issues
- Install ClickHouse ODBC driver
- Configure DSN with credentials from `.env`
- Test connection before importing views

### Git Issues
- Ensure `.gitignore` excludes `.env` before first commit
- Never commit credentials to repository
- Use `git status` to verify excluded files

---

## Contact & Support

For questions about this project:
- Review documentation files (SCHEMA.md, KEPNER_TREGOE_INSIGHTS.md)
- Check ANALYSIS_SUMMARY.md for data insights
- Refer to official NYC TLC documentation for data definitions

---

## Document Version

**Version:** 1.0  
**Created:** May 20, 2026  
**Last Updated:** May 20, 2026  
**Author:** Generated by OpenCode CLI with claude-sonnet-4-7

---

**End of AGENTS.md**
