# NYC Taxi Dataset - Schema Documentation

**Project:** Kepner-Tregoe Analysis of NYC Taxi Data  
**Database:** NYCTaxiAnalysis (ClickHouse Cloud)  
**Created:** May 20, 2026  
**Last Updated:** May 20, 2026

---

## Overview

This document describes the schema and data structure for the NYC Taxi Analysis project. The database follows a **Bronze-Silver-Gold architecture** with data quality considerations documented throughout.

### Database Architecture

```
NYCTaxiAnalysis (Database)
├── bronze_taxi_trips (Raw data layer - 15.4M records)
├── silver_* (Cleaned & aggregated materialized views)
└── gold_* (Business logic views for Power BI)
```

**Important:** Power BI connects ONLY to gold views. All business logic is in SQL, NO DAX in Power BI.

---

## Dataset Statistics

- **Total Records:** 15,382,212 trips
- **Date Range:** Latest 6 months of NYC Taxi data (see data quality notes)
- **Storage:** ClickHouse Cloud with MergeTree engine
- **Partitioning:** By month (toYYYYMM(tpep_pickup_datetime))

---

## Bronze Layer: bronze_taxi_trips

### Table Structure

| Column Name | Data Type | Nullable | Description |
|-------------|-----------|----------|-------------|
| VendorID | Int32 | Yes | Technology provider ID (1=Creative Mobile, 2=VeriFone, 6/7=Other) |
| tpep_pickup_datetime | DateTime | No | Trip start time when meter was engaged |
| tpep_dropoff_datetime | DateTime | No | Trip end time when meter was disengaged |
| passenger_count | Float64 | Yes | Number of passengers (driver-entered) |
| trip_distance | Float64 | Yes | Trip distance in miles (taximeter) |
| RatecodeID | Float64 | Yes | Rate code (1=Standard, 2=JFK, 3=Newark, 4=Nassau, 5=Negotiated, 6=Group) |
| store_and_fwd_flag | String | Yes | 'Y' if stored before sending to vendor, 'N' if transmitted immediately |
| PULocationID | Int32 | No | TLC Taxi Zone ID for pickup location |
| DOLocationID | Int32 | Yes | TLC Taxi Zone ID for dropoff location |
| payment_type | Int32 | Yes | Payment method (1=Credit, 2=Cash, 3=No charge, 4=Dispute, 0=Unknown) |
| fare_amount | Float64 | Yes | Time-and-distance fare calculated by meter |
| extra | Float64 | Yes | Extra charges (rush hour $0.50, overnight $1.00) |
| mta_tax | Float64 | Yes | MTA tax (typically $0.50 per trip) |
| tip_amount | Float64 | Yes | Tip amount (credit card only, cash tips not recorded) |
| tolls_amount | Float64 | Yes | Total toll amount for trip |
| improvement_surcharge | Float64 | Yes | Improvement surcharge ($1.00 standard) |
| total_amount | Float64 | Yes | Total amount charged to passenger |
| congestion_surcharge | Float64 | Yes | Congestion pricing surcharge ($2.50 in Manhattan CBD) |
| Airport_fee | Float64 | Yes | Airport pickup/dropoff fee ($1.75 standard) |
| cbd_congestion_fee | Float64 | Yes | Central Business District congestion fee (newer charge) |

---

## Column Details & Business Context

### 1. VendorID - Technology Provider

**What it means:** The company that provided the technology/meter system for the taxi.

**Values:**
- **Vendor 2:** 12,229,574 trips (79.5%) - Dominant provider
- **Vendor 1:** 2,937,879 trips (19.1%)
- **Vendor 6:** 23,601 trips (0.15%)
- **Vendor 7:** 191,158 trips (1.24%)

**Data Quality:** Clean, no NULL values

**Use in Analysis:** Compare data quality and patterns between vendors

---

### 2. tpep_pickup_datetime - Trip Start Time

**What it means:** The exact date and time when the taxi driver started the meter.

**Range:** December 31, 2008 to April 1, 2026

**Data Quality Issues:**
- ⚠️ **CRITICAL:** 99.99% of trips dated in 2025-2026 (likely year offset error in source data)
- This affects temporal analysis; consider date corrections in silver layer

**Use in Analysis:**
- Peak hour identification (rush hours, nightlife)
- Day of week patterns (weekday vs weekend)
- Seasonal trends

---

### 3. tpep_dropoff_datetime - Trip End Time

**What it means:** The exact date and time when the taxi driver stopped the meter.

**Derived Metric:** Trip duration = dropoff_datetime - pickup_datetime

**Data Quality Issues:**
- 7 trips have dropoff BEFORE pickup (impossible)
- Same date range issues as pickup_datetime

**Use in Analysis:**
- Trip duration patterns
- Congestion indicators (longer trips in same zones)
- Service quality metrics

---

### 4. passenger_count - Number of Passengers

**What it means:** How many passengers were in the taxi (driver manually enters this).

**Typical Values:**
- **1 passenger:** Most common (median = 1)
- **Average:** 1.26 passengers
- **Range:** 0 to 9 passengers

**Data Quality Issues:**
- ⚠️ **27.65% NULL values** (4,252,605 trips) - significant missing data
- **59,465 trips with 0 passengers** (3.9%) - data error, taxis need at least 1 passenger
- 21 trips with >6 passengers (NYC taxis typically max 5-6)

**Use in Analysis:**
- Group travel vs solo travel patterns
- Revenue per passenger
- Vehicle utilization

**Note:** NULL values represent a specific vendor/system that doesn't report this field.

---

### 5. trip_distance - Miles Traveled

**What it means:** Distance traveled during the trip, measured by the taximeter in miles.

**Typical Values:**
- **Median:** 1.82 miles (typical short urban trip)
- **Average:** 6.42 miles (skewed by longer trips)
- **Standard Deviation:** 649.55 (very high due to outliers)

**Data Quality Issues:**
- ⚠️ **Maximum value: 328,522 miles** (impossible - 13x Earth's circumference!)
- Extreme outliers indicate meter/GPS errors
- Recommend filtering trips > 100 miles as data errors

**Use in Analysis:**
- Short trips (<2 miles) vs long trips (>10 miles)
- Revenue per mile
- Geographic spread of taxi service
- Correlation with fare amount

---

### 6. RatecodeID - Fare Rate Type

**What it means:** The rate structure applied to the trip.

**Values:**
- **1 = Standard rate:** 10,096,398 trips (65.64%) - Normal metered rate
- **2 = JFK airport:** 347,330 trips (2.26%) - Flat rate to/from JFK
- **3 = Newark airport:** 49,809 trips (0.32%) - Flat rate to/from Newark
- **4 = Nassau/Westchester:** 33,840 trips (0.22%) - Suburban rates
- **5 = Negotiated fare:** 134,047 trips (0.87%) - Pre-arranged rate
- **6 = Group ride:** 10 trips (0.0%) - Shared ride
- **99 = Unknown:** 468,173 trips (3.04%) - Non-standard code, likely error

**Data Quality Issues:**
- ⚠️ **27.65% NULL values** (same missing record pattern as passenger_count)
- Code 99 not standard (investigate further)

**Use in Analysis:**
- Airport trips vs city trips
- Special rate usage patterns
- Vendor differences in rate code assignment

---

### 7. store_and_fwd_flag - Data Transmission Status

**What it means:** Whether the trip record was stored in the taxi's memory before being sent to the vendor's server (due to connectivity issues).

**Values:**
- **'N':** 11,115,216 trips (72.26%) - Transmitted immediately
- **'Y':** 14,391 trips (0.09%) - Stored and forwarded later
- **NULL:** 4,252,605 trips (27.65%)

**Data Quality Issues:**
- ⚠️ **27.65% NULL values** (same pattern)

**Use in Analysis:**
- Network connectivity patterns by location
- Data reliability indicator
- Potential data delay issues

---

### 8. PULocationID - Pickup Location Zone

**What it means:** NYC Taxi & Limousine Commission (TLC) zone ID where the trip started.

**Hot Zones (Top 5):**
1. **Location 237:** 675,640 pickups (4.39%)
2. **Location 236:** 626,996 pickups (4.08%)
3. **Location 161:** 609,673 pickups (3.96%)
4. **Location 132:** 595,528 pickups (3.87%)
5. **Location 186:** 465,791 pickups (3.03%)

**Pattern:** Top 15 locations account for ~45% of all pickups (high concentration in Manhattan core).

**Data Quality:** Clean, no NULL values

**Use in Analysis:**
- Geographic demand patterns
- High-activity vs low-activity zones (IS vs IS NOT)
- Route analysis (combined with DOLocationID)

**Reference:** TLC publishes taxi zone shapefiles and lookup tables online.

---

### 9. DOLocationID - Dropoff Location Zone

**What it means:** NYC TLC zone ID where the trip ended.

**Hot Zones (Top 5):**
1. **Location 236:** 637,664 dropoffs (4.15%)
2. **Location 237:** 612,597 dropoffs (3.98%)
3. **Location 161:** 507,030 dropoffs (3.30%)
4. **Location 170:** 415,868 dropoffs (2.70%)
5. **Location 230:** 405,164 dropoffs (2.63%)

**Special Case:** 728,797 trips (4.74%) have **same pickup and dropoff location** - investigate separately.

**Data Quality:** Clean, no NULL values

**Use in Analysis:**
- Destination patterns
- Popular routes (pickup-dropoff pairs)
- Same-zone trips (potential circular rides or very short trips)

---

### 10. payment_type - Payment Method

**What it means:** How the passenger paid for the trip.

**Values:**
- **1 = Credit card:** 9,529,010 trips (61.95%) - Dominant payment method
- **2 = Cash:** 1,342,219 trips (8.73%)
- **3 = No charge:** 62,455 trips (0.41%) - Free trips (promotional, disputes)
- **4 = Dispute:** 195,923 trips (1.27%) - Payment disputed
- **0 = Unknown/NULL:** 4,252,605 trips (27.65%)

**Data Quality Issues:**
- ⚠️ **27.65% NULL/Unknown** (same pattern)

**Use in Analysis:**
- Cashless trend analysis
- Tipping behavior (credit card vs cash)
- Dispute patterns by location/time
- Modern payment adoption

**Important:** Cash tips are NOT recorded in tip_amount field (credit card tips only).

---

### 11. fare_amount - Base Fare

**What it means:** The time-and-distance fare calculated by the taximeter (does not include tips, tolls, or surcharges).

**Typical Values:**
- **Median:** $16.20 (typical fare)
- **Average:** $21.52 (higher due to outliers)
- **Range:** -$2,555.20 to +$2,555.20

**Data Quality Issues:**
- ⚠️ **135,083 negative fares** (0.88%) - data errors (refunds or system errors)
- Symmetric min/max suggests data truncation or encoding limits
- Extreme outliers present

**Use in Analysis:**
- Revenue patterns
- Fare per mile calculations
- Price sensitivity analysis
- Correlation with tip amounts

**Cleaning Recommendation:** Filter out negative fares and values > $500 as anomalies.

---

### 12. extra - Extra Charges

**What it means:** Additional charges for rush hour ($0.50) and overnight service ($1.00).

**Typical Values:**
- **Median:** $0.00 (most trips have no extra charges)
- **Average:** $1.06
- **Range:** -$7.50 to $20.71

**Data Quality Issues:**
- ⚠️ Some negative values (data errors)

**Use in Analysis:**
- Rush hour vs off-peak patterns
- Overnight service usage

---

### 13. mta_tax - MTA Tax

**What it means:** Metropolitan Transportation Authority tax imposed on all taxi trips (typically $0.50).

**Typical Values:**
- **Median:** $0.50 (standard rate)
- **Average:** $0.48
- **Range:** -$0.50 to $96.00 (!!)

**Data Quality Issues:**
- ⚠️ Max of $96 is anomalous (should always be $0.50)
- Some negative values

**Use in Analysis:**
- Validate tax compliance
- Identify system errors

---

### 14. tip_amount - Tip Amount

**What it means:** Tip amount given by passenger.

**Typical Values:**
- **Median:** $2.00
- **Average:** $2.74 (about 10-15% of median fare)
- **Range:** -$96.50 to $800.00

**Data Quality Issues:**
- ⚠️ 226 negative tips (data errors)
- Max of $800 is very high (generous tipper or error)

**Use in Analysis:**
- Tipping behavior by payment method
- Tipping patterns by location/time
- Service quality indicator
- Credit vs cash comparison

**CRITICAL NOTE:** This field only captures credit card tips. Cash tips are NOT recorded, so total tip analysis is incomplete.

---

### 15. tolls_amount - Toll Charges

**What it means:** Total amount of tolls paid during the trip (bridges, tunnels).

**Typical Values:**
- **Median:** $0.00 (most trips have no tolls)
- **Average:** $0.51
- **Range:** -$111.79 to $1,400.00

**Data Quality Issues:**
- ⚠️ **11,887 negative toll amounts** (data errors - tolls are always positive)
- Max of $1,400 extremely high (error or special case)

**Use in Analysis:**
- Bridge/tunnel usage patterns
- Cross-borough trip identification
- Route optimization
- High-toll trips (airport, outer boroughs)

---

### 16. improvement_surcharge - Improvement Surcharge

**What it means:** Improvement surcharge mandated by NYC ($0.30 initially, later $1.00).

**Typical Values:**
- **Median:** $1.00 (current standard rate)
- **Average:** $0.95
- **Range:** -$1.00 to $1.00

**Data Quality Issues:**
- ⚠️ **136,371 negative surcharges** (0.89%) - data errors

**Use in Analysis:**
- Validate surcharge compliance
- Historical rate changes

---

### 17. total_amount - Total Charge

**What it means:** Total amount charged to passenger (sum of fare + extras + tax + tips + tolls + surcharges).

**Typical Values:**
- **Median:** $23.94 (typical total bill)
- **Average:** $30.10
- **Range:** -$2,560.20 to +$2,560.20

**Data Quality Issues:**
- ⚠️ **137,449 negative totals** (0.89%) - data errors
- Symmetric min/max suggests truncation

**Use in Analysis:**
- Total revenue analysis
- Trip value distribution
- High-value vs low-value trip patterns
- Outlier detection

**Cleaning Recommendation:** Filter negatives and totals > $1,000 as anomalies.

---

### 18. congestion_surcharge - Congestion Surcharge

**What it means:** Congestion pricing surcharge for trips in Manhattan's Central Business District ($2.50 standard).

**Typical Values:**
- **Median:** $2.50 (standard rate)
- **Average:** $2.17
- **Range:** -$2.50 to $2.50

**Data Quality Issues:**
- ⚠️ **27.65% NULL values** (same missing record pattern)
- ⚠️ **107,601 negative surcharges** (data errors)

**Use in Analysis:**
- CBD trip identification
- Congestion pricing impact analysis
- Manhattan core vs outer area patterns

---

### 19. Airport_fee - Airport Fee

**What it means:** Fee for trips to/from NYC airports ($1.75 standard).

**Typical Values:**
- **Median:** $0.00 (most trips not to/from airport)
- **Average:** $0.15
- **Range:** -$2.00 to $27.00

**Data Quality Issues:**
- ⚠️ **27.65% NULL values**
- ⚠️ **28,659 negative fees** (data errors)
- Max of $27 very high (should be $1.75)

**Use in Analysis:**
- Airport trip identification
- Airport vs city trip comparisons
- RatecodeID validation

---

### 20. cbd_congestion_fee - CBD Congestion Fee

**What it means:** Central Business District congestion fee (newer charge, recently added).

**Typical Values:** Appears to be $0.75 in sample data.

**Data Quality:** New field, limited usage.

**Use in Analysis:**
- New policy impact analysis
- CBD trip tracking

---

## Data Quality Summary

### Critical Issues to Address in Silver Layer

#### 1. NULL Value Pattern (27.65% of records)
**Affected Fields:**
- passenger_count
- RatecodeID
- store_and_fwd_flag
- congestion_surcharge
- Airport_fee
- payment_type (code 0)

**Pattern:** These 4,252,605 trips all have the same fields missing - likely one vendor/system that doesn't report these fields.

**Strategy:** Flag these records and handle separately in analysis.

---

#### 2. Temporal Anomaly (SEVERE)
- 99.99% of trips dated 2025-2026 (future dates)
- Only 2 trips from 2008-2009 era

**Strategy:** Assume 6-month window but validate temporal patterns carefully. May need date correction in silver layer.

---

#### 3. Negative Financial Values

| Field | Negative Count | Percentage |
|-------|----------------|------------|
| fare_amount | 135,083 | 0.88% |
| total_amount | 137,449 | 0.89% |
| improvement_surcharge | 136,371 | 0.89% |
| congestion_surcharge | 107,601 | 0.96% (of non-null) |
| tolls_amount | 11,887 | 0.08% |
| tip_amount | 226 | 0.001% |
| Airport_fee | 28,659 | 0.26% (of non-null) |

**Strategy:** Filter out negative values in silver layer (likely refunds/adjustments or encoding errors).

---

#### 4. Extreme Outliers

| Field | Anomaly | Cleaning Threshold |
|-------|---------|-------------------|
| trip_distance | Max 328,522 miles | Filter > 100 miles |
| fare_amount | Min/Max ±$2,555 | Filter > $500 |
| total_amount | Min/Max ±$2,560 | Filter > $1,000 |
| tolls_amount | Max $1,400 | Filter > $100 |
| mta_tax | Max $96 | Should be $0.50 |
| duration | Max 9,265 min (6.4 days) | Filter > 240 min (4 hours) |

**Strategy:** Apply filters in silver layer to remove data quality issues.

---

#### 5. Logical Impossibilities

- **59,465 trips with 0 passengers** (3.9%) - filter out
- **7 trips with dropoff before pickup** - filter out
- **308,577 trips with 0-minute duration** (2%) - investigate separately
- **144 trips over 24 hours duration** - likely meter left running

**Strategy:** Create data quality flags and exclude from standard analysis.

---

## Temporal Patterns (for Kepner-Tregoe Analysis)

### Peak Hours
- **6:00 PM (18:00):** 1,097,594 trips (7.14%) - HIGHEST
- **5:00 PM (17:00):** 1,034,100 trips (6.72%)
- **7:00 PM (19:00):** 981,913 trips (6.38%)

### Low Activity Hours
- **4:00 AM:** Lowest activity
- **3:00 AM - 6:00 AM:** Off-peak period

### Busiest Days
- **Thursday:** 2,373,022 trips (15.43%)
- **Saturday:** 2,371,143 trips (15.41%)
- **Friday:** 2,359,734 trips (15.34%)

### Quietest Days
- **Monday:** 1,893,017 trips (12.31%)
- **Sunday:** 1,915,073 trips (12.45%)

---

## Geographic Patterns (for Kepner-Tregoe Analysis)

### Concentration
- Top 15 pickup locations = ~45% of all pickups
- Top 15 dropoff locations = ~44% of all dropoffs

### Hottest Zones
Locations 237, 236, 161, 132, 186 (likely Midtown Manhattan, Times Square, Penn Station, Financial District)

### Special Cases
- **Same location trips:** 728,797 (4.74%) - pickup and dropoff in same zone

---

## Trip Characteristics (for Kepner-Tregoe Analysis)

### Typical Trip
- **Duration:** 14 minutes (median)
- **Distance:** 1.82 miles (median)
- **Fare:** $16.20 (median)
- **Total:** $23.94 (median)
- **Passengers:** 1 (median)

### Payment Trends
- **Credit card dominance:** 62% of trips
- **Cash declining:** Only 9% of trips
- **Tipping on credit:** Average $2.74 (visible tips only)

---

## Silver & Gold Layer Strategy

### Silver Layer (Cleaned Materialized Views)
1. **silver_trips_cleaned** - All outliers and errors removed
2. **silver_trips_hourly** - Hourly aggregations
3. **silver_trips_by_location** - Location-based metrics
4. **silver_trips_by_payment** - Payment method analysis
5. **silver_trips_by_vendor** - Vendor comparison

### Gold Layer (Business Logic for Power BI)
1. **gold_kt_what_is_happening** - Service patterns
2. **gold_kt_where_is_happening** - Geographic analysis
3. **gold_kt_when_is_happening** - Temporal patterns
4. **gold_kt_extent_magnitude** - Volume & magnitude
5. **gold_kt_what_not_happening** - Absence & gaps
6. **gold_kt_characteristics_comparison** - IS vs IS NOT contrasts

---

## References & External Resources

- **NYC TLC Trip Data:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **TLC Taxi Zones:** https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc
- **Data Dictionary:** https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

---

## Document Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-05-20 | 1.0 | Initial schema documentation created from ANALYSIS_SUMMARY.md |

---

## For Future AI Tools & CLIs

This schema file is designed to be readable by any AI tool or command-line interface. Key information:

- **Connection:** See `.env` file for ClickHouse credentials (DO NOT commit .env to Git)
- **Primary Table:** `NYCTaxiAnalysis.bronze_taxi_trips`
- **Row Count:** 15,382,212 rows
- **Key for Joins:** Use `PULocationID` and `DOLocationID` with TLC zone lookup tables
- **Date Field:** Use `tpep_pickup_datetime` for temporal analysis (note data quality issues)
- **Cleaning Required:** Apply filters documented in "Data Quality Summary" section
- **Analysis Framework:** Kepner-Tregoe IS/IS NOT - see KEPNER_TREGOE_INSIGHTS.md

---

**End of Schema Documentation**
