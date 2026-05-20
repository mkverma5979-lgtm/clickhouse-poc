# NYC Taxi Dataset - Comprehensive Analysis Summary

**Database:** NYCTaxiAnalysis  
**Table:** bronze_taxi_trips  
**Total Records:** 15,382,212 trips  
**Analysis Date:** May 20, 2026

---

## Executive Summary

This dataset contains NYC taxi trip records with **15.4 million trips** spanning from December 2008 to April 2026. The data includes trip details, payment information, location data, and fare breakdowns. However, there are **significant data quality issues** that need attention, including temporal anomalies, negative values in financial columns, and substantial NULL values (27.65% for several columns).

---

## Column Inventory and Descriptions

### 1. **VendorID** (Nullable Int32)
**What it is:** Technology provider identifier for the taxi system that provided the trip record.

**Distribution:**
- Vendor 2: 12,229,574 trips (79.5%) - **Dominant vendor**
- Vendor 1: 2,937,879 trips (19.1%)
- Vendor 7: 191,158 trips (1.24%)
- Vendor 6: 23,601 trips (0.15%)

**Quality:** No NULL values. Clean categorical data.

### 2. **tpep_pickup_datetime** (DateTime)
**What it is:** The date and time when the meter was engaged (trip started).

**Range:**
- Earliest: December 31, 2008, 23:03:20
- Latest: April 1, 2026, 00:06:25
- Span: 6,300 days (17+ years)

**Quality Issues:**
- **CRITICAL:** 15,382,210 trips (99.99%) are dated AFTER January 2025 - likely future dates that are data errors
- Only 1 trip is before 2009 (in 2008)
- This suggests the bulk of the data has incorrect timestamps (probably year 2025-2026 when actual dates should be earlier)

### 3. **tpep_dropoff_datetime** (DateTime)
**What it is:** The date and time when the meter was disengaged (trip ended).

**Quality Issues:**
- 7 trips have dropoff BEFORE pickup (impossible)
- Same temporal range issues as pickup datetime

### 4. **passenger_count** (Nullable Float64)
**What it is:** Number of passengers in the vehicle (driver-entered).

**Statistics:**
- Min: 0, Max: 9
- Average: 1.26, Median: 1.0
- Standard Deviation: 0.68

**Distribution:** Most trips have 1 passenger (median = 1).

**Quality Issues:**
- **27.65% NULL values** (4,252,605 trips) - over a quarter of trips have no passenger count
- **59,465 trips with 0 passengers** (data error - taxis need at least 1 passenger)
- 21 trips with >6 passengers (NYC taxis typically hold max 5-6)

### 5. **trip_distance** (Nullable Float64)
**What it is:** Trip distance in miles, measured by taximeter.

**Statistics:**
- Min: 0.0, Max: 328,522.2 miles (!!)
- Average: 6.42 miles, Median: 1.82 miles
- Standard Deviation: 649.55 (extremely high)

**Typical Pattern:** Median of 1.82 miles suggests most trips are short urban rides.

**Quality Issues:**
- **Maximum value of 328,522 miles is impossible** - this is more than 13 times around Earth's circumference
- Extreme outliers indicate meter/GPS errors or data corruption
- High standard deviation shows many anomalous values

### 6. **RatecodeID** (Nullable Float64)
**What it is:** Rate code at end of trip. Standard rates, JFK, Newark, Nassau/Westchester, negotiated fare, or group ride.

**Distribution:**
- RatecodeID 1: 10,096,398 trips (65.64%) - **Standard rate (most common)**
- RatecodeID 99: 468,173 trips (3.04%) - Unknown code (99 is not standard)
- RatecodeID 2: 347,330 trips (2.26%) - JFK airport
- RatecodeID 5: 134,047 trips (0.87%) - Negotiated fare
- RatecodeID 3: 49,809 trips (0.32%) - Newark airport
- RatecodeID 4: 33,840 trips (0.22%) - Nassau/Westchester
- RatecodeID 6: 10 trips (0.0%)

**Quality Issues:**
- **27.65% NULL values** (4,252,605 trips)
- Code 99 appears frequently (3.04%) but is not a standard ratecode - likely error code

### 7. **store_and_fwd_flag** (Nullable String)
**What it is:** Indicates if trip record was held in vehicle memory before sending to vendor ("Y" = yes, "N" = no) due to no server connection.

**Distribution:**
- "N": 11,115,216 trips (72.26%) - **Most trips transmitted immediately**
- NULL: 4,252,605 trips (27.65%)
- "Y": 14,391 trips (0.09%) - Very few store-and-forward trips

**Interpretation:** Vast majority of trips had active connectivity. Store-and-forward is rare.

**Quality Issues:**
- **27.65% NULL values** (same as passenger_count, RatecodeID, etc. - likely same missing records)

### 8. **PULocationID** (Int32)
**What it is:** TLC Taxi Zone ID where meter was engaged (pickup location).

**Top Pickup Locations:**
1. Location 237: 675,640 pickups (4.39%)
2. Location 236: 626,996 pickups (4.08%)
3. Location 161: 609,673 pickups (3.96%)
4. Location 132: 595,528 pickups (3.87%)
5. Location 186: 465,791 pickups (3.03%)

**Pattern:** Top 15 locations account for ~45% of all pickups, showing concentration in busy areas (likely Manhattan commercial districts, airports).

**Quality:** No NULL or zero values. Clean data.

### 9. **DOLocationID** (Nullable Int32)
**What it is:** TLC Taxi Zone ID where meter was disengaged (dropoff location).

**Top Dropoff Locations:**
1. Location 236: 637,664 dropoffs (4.15%)
2. Location 237: 612,597 dropoffs (3.98%)
3. Location 161: 507,030 dropoffs (3.30%)
4. Location 170: 415,868 dropoffs (2.70%)
5. Location 230: 405,164 dropoffs (2.63%)

**Pattern:** Similar distribution to pickups. Locations 236 and 237 are top for both pickup and dropoff.

**Quality:** No NULL or zero values. Clean data.

**Notable:** 728,797 trips (4.74%) have same pickup and dropoff location - could be legitimate short trips or circular routes.

### 10. **payment_type** (Nullable Int32)
**What it is:** Payment method code.

**Distribution:**
- Type 1: 9,529,010 trips (61.95%) - **Credit card (dominant)**
- Type 0: 4,252,605 trips (27.65%) - Unknown/NULL
- Type 2: 1,342,219 trips (8.73%) - Cash
- Type 4: 195,923 trips (1.27%) - Dispute
- Type 3: 62,455 trips (0.41%) - No charge

**Pattern:** Credit card payments dominate (62%), followed by cash (9%). Modern trend toward cashless payments evident.

**Quality Issues:**
- 27.65% have payment_type 0 (unknown) - same NULL pattern as other columns

### 11. **fare_amount** (Nullable Float64)
**What it is:** Time-and-distance fare calculated by meter.

**Statistics:**
- Min: -$2,555.20, Max: $2,555.20
- Average: $21.52, Median: $16.20
- Standard Deviation: $19.06

**Pattern:** Typical fare is $16-20 for median trip.

**Quality Issues:**
- **135,083 negative fares** (data error - fares cannot be negative)
- Symmetric min/max values (-2555.2, +2555.2) suggest possible data truncation or encoding issue

### 12. **extra** (Nullable Float64)
**What it is:** Extra charges (rush hour, overnight surcharges).

**Statistics:**
- Min: -$7.50, Max: $20.71
- Average: $1.06, Median: $0.00
- Standard Deviation: $1.73

**Pattern:** Most trips have no extra charges (median = $0).

**Quality Issues:**
- Negative values present (data error)

### 13. **mta_tax** (Nullable Float64)
**What it is:** MTA tax (typically $0.50 per trip).

**Statistics:**
- Min: -$0.50, Max: $96.00
- Average: $0.48, Median: $0.50
- Standard Deviation: $0.11

**Pattern:** Very consistent at $0.50 (median and average align).

**Quality Issues:**
- Max of $96 is anomalous (should be $0.50)
- Some negative values

### 14. **tip_amount** (Nullable Float64)
**What it is:** Tip amount (automatically populated for credit card; cash tips not included).

**Statistics:**
- Min: -$96.50, Max: $800.00
- Average: $2.74, Median: $2.00
- Standard Deviation: $3.95

**Pattern:** Typical tip is $2, averaging around 10-15% of median fare.

**Quality Issues:**
- **226 negative tips** (data error)
- Max of $800 is very high (generous tipper or data error)

**Important Note:** Cash tips are NOT recorded, so this underrepresents total tips.

### 15. **tolls_amount** (Nullable Float64)
**What it is:** Total tolls paid during trip.

**Statistics:**
- Min: -$111.79, Max: $1,400.00
- Average: $0.51, Median: $0.00
- Standard Deviation: $2.17

**Pattern:** Most trips have no tolls (median = $0). Average suggests occasional high toll trips (bridges, tunnels).

**Quality Issues:**
- **11,887 negative toll amounts** (data error - tolls are always positive)
- Max of $1,400 is extremely high (data error or special case)

### 16. **improvement_surcharge** (Nullable Float64)
**What it is:** Improvement surcharge (typically $0.30, later $1.00).

**Statistics:**
- Min: -$1.00, Max: $1.00
- Average: $0.95, Median: $1.00
- Standard Deviation: $0.25

**Pattern:** Very consistent at $1.00.

**Quality Issues:**
- **136,371 negative surcharges** (data error)

### 17. **total_amount** (Nullable Float64)
**What it is:** Total amount charged to passenger (sum of all charges).

**Statistics:**
- Min: -$2,560.20, Max: $2,560.20
- Average: $30.10, Median: $23.94
- Standard Deviation: $22.78

**Pattern:** Typical total is $24, averaging around $30.

**Quality Issues:**
- **137,449 negative total amounts** (data error - total bill cannot be negative)
- Symmetric min/max suggests data truncation

### 18. **congestion_surcharge** (Nullable Float64)
**What it is:** Congestion pricing surcharge (Manhattan CBD).

**Statistics:**
- Min: -$2.50, Max: $2.50
- Average: $2.17, Median: $2.50
- Standard Deviation: $0.91

**Pattern:** Most trips with this charge have $2.50 (standard rate).

**Quality Issues:**
- **27.65% NULL values** (4,252,605 trips) - same missing record pattern
- **107,601 negative surcharges** (data error)

### 19. **Airport_fee** (Nullable Float64)
**What it is:** Airport fee for trips to/from airports.

**Statistics:**
- Min: -$2.00, Max: $27.00
- Average: $0.15, Median: $0.00
- Standard Deviation: $0.53

**Pattern:** Most trips have no airport fee (median = $0). Low average suggests few airport trips.

**Quality Issues:**
- **27.65% NULL values**
- **28,659 negative fees** (data error)
- Max of $27 is very high for airport fee

### 20. **cbd_congestion_fee** (Nullable Float64)
**What it is:** Central Business District congestion fee (newer charge).

**Statistics:** Present in dataset but appears to be a recent addition (0.75 in sample rows).

---

## Temporal Patterns

### Hour of Day Distribution
**Peak Hours:**
- 6:00 PM (18:00): 1,097,594 trips (7.14%) - **Highest**
- 5:00 PM (17:00): 1,034,100 trips (6.72%)
- 7:00 PM (19:00): 981,913 trips (6.38%)
- 4:00 PM (16:00): 924,233 trips (6.01%)

**Pattern:** Clear evening rush hour peak (4-7 PM), with activity concentrated in late afternoon/evening.

### Day of Week Distribution
**Busiest Days:**
- Thursday: 2,373,022 trips (15.43%)
- Saturday: 2,371,143 trips (15.41%)
- Friday: 2,359,734 trips (15.34%)

**Quietest Days:**
- Monday: 1,893,017 trips (12.31%)
- Sunday: 1,915,073 trips (12.45%)

**Pattern:** Weekend and Thursday are busiest. Weekday evenings for work/entertainment, weekends for leisure.

### Month Distribution
**CRITICAL DATA QUALITY ISSUE:**
- December 2025: 4,305,003 trips (28%)
- March 2026: 3,952,436 trips (25.7%)
- January 2026: 3,724,894 trips (24.2%)
- February 2026: 3,399,866 trips (22.1%)

**The data is timestamped in 2025-2026, but we are analyzing in May 2026, and this appears to be historical data. The dates are almost certainly incorrect (year offset error in data import or meter system).**

---

## Geographic Patterns

### Location Concentration
- **Top 15 pickup locations** account for ~45% of all pickups
- **Top 15 dropoff locations** account for ~44% of all dropoffs

### Most Active Zones
**Locations 236, 237, 161, 132, 186** are the busiest for both pickup and dropoff.

These likely correspond to:
- Midtown Manhattan
- Penn Station area
- Times Square
- Financial District
- Major transportation hubs

**Same Location Trips:** 728,797 trips (4.74%) start and end at same location - could be circular routes, very short trips, or meter testing.

---

## Trip Duration Analysis

**Statistics:**
- Min: -186 minutes (impossible)
- Max: 9,265 minutes (154 hours = 6.4 days!)
- Average: 17.85 minutes
- Median: 14.0 minutes

**Typical Trip:** 14 minutes (median) is typical NYC taxi trip.

**Quality Issues:**
- **5 trips with negative duration** (dropoff before pickup)
- **308,577 trips with 0-minute duration** (2% of all trips) - instant trips or rounding
- **144 trips over 24 hours** - likely meter left running or data error

---

## Data Quality Summary

### Critical Issues

1. **Temporal Anomalies (SEVERE):**
   - 99.99% of trips dated 2025-2026 (future dates, likely year offset error)
   - Only 1 trip from 2008-2009 era (when data should be from)
   - Suggests systemic date/time error in data ingestion or source system

2. **NULL Value Pattern (27.65% of records):**
   - **4,252,605 trips** (27.65%) have NULL for: passenger_count, RatecodeID, store_and_fwd_flag, congestion_surcharge, Airport_fee
   - This represents a complete missing record pattern - likely a data source that didn't provide these fields

3. **Negative Financial Values:**
   - fare_amount: 135,083 negative (0.88%)
   - total_amount: 137,449 negative (0.89%)
   - improvement_surcharge: 136,371 negative (0.89%)
   - congestion_surcharge: 107,601 negative (0.96% of non-null)
   - tolls_amount: 11,887 negative (0.08%)
   - tip_amount: 226 negative (0.001%)
   - Airport_fee: 28,659 negative (0.26% of non-null)
   - **Pattern:** Likely refunds/adjustments or data encoding errors

4. **Extreme Outliers:**
   - trip_distance: Max 328,522 miles (impossible - meter error)
   - fare_amount: Symmetric -2555.2 to +2555.2 (suggests data truncation)
   - total_amount: Symmetric -2560.2 to +2560.2
   - tolls_amount: Max $1,400 (excessive)
   - mta_tax: Max $96 (should be $0.50)

5. **Logical Impossibilities:**
   - 59,465 trips with 0 passengers (3.9%)
   - 7 trips with dropoff before pickup
   - 5 trips with negative duration
   - 144 trips over 24 hours duration

### Data Reliability Assessment

**RELIABLE COLUMNS:**
- VendorID (clean categorical)
- PULocationID (no nulls, reasonable values)
- DOLocationID (no nulls, reasonable values)
- Location zone patterns (consistent)

**MODERATELY RELIABLE:**
- payment_type (after handling unknowns)
- Datetime fields (after correcting year offset)
- Median values for numeric fields (after outlier removal)

**REQUIRES CLEANING:**
- All financial amount fields (remove negatives, filter outliers)
- trip_distance (remove extreme outliers)
- passenger_count (remove 0s, handle nulls)
- RatecodeID (handle nulls, investigate code 99)
- Duration calculations (filter impossible values)

**MISSING DATA STRATEGY NEEDED:**
- 27.65% of records need imputation or exclusion for: passenger_count, RatecodeID, store_and_fwd_flag, congestion_surcharge, Airport_fee

---

## Recommendations for Kepner-Tregoe Analysis

### IS / IS NOT Framework Dimensions

Based on this analysis, the following dimensions are most valuable for problem differentiation:

1. **Temporal Dimensions:**
   - Hour of day (clear peak patterns)
   - Day of week (weekend vs. weekday)
   - Time period (after correcting dates)

2. **Geographic Dimensions:**
   - Pickup location zone (high vs. low activity)
   - Dropoff location zone
   - Same zone trips vs. cross-zone

3. **Financial Dimensions:**
   - Fare amount (high vs. low)
   - Payment method (credit vs. cash)
   - Tip amount (generous vs. no tip)

4. **Trip Characteristics:**
   - Trip distance (short vs. long)
   - Trip duration (quick vs. extended)
   - Passenger count (solo vs. group)

5. **Service Dimensions:**
   - Vendor (Vendor 1 vs. Vendor 2)
   - Rate code (standard vs. special)
   - Airport trips vs. non-airport

6. **Data Quality Flags:**
   - Records with nulls vs. complete records
   - Records with anomalies vs. clean records

### Priority Data Cleaning Steps

1. **Correct temporal data** (investigate and fix year offset)
2. **Filter outliers** (trip_distance > 100 miles, duration > 4 hours, fare > $500)
3. **Remove impossible records** (negative amounts, 0 passengers, negative duration)
4. **Handle NULL pattern** (decide: impute, exclude, or flag for analysis)
5. **Validate location zones** against TLC taxi zone lookup table
6. **Standardize RatecodeID** (map code 99 to appropriate category)

---

## Conclusion

The NYC Taxi dataset contains **15.4 million trip records** with rich detail on trip logistics, payments, and geography. The data shows clear patterns in urban taxi usage with evening peaks, weekend activity, and concentration in key Manhattan zones.

However, **significant data quality issues exist**, particularly:
- Systematic date errors (99.99% of data incorrectly timestamped in 2025-2026)
- 27.65% of records missing key fields
- Financial anomalies (negative values, extreme outliers)
- Logical impossibilities (0 passengers, negative durations)

**Before analysis**, data cleaning is essential. After cleaning, the dataset will be excellent for:
- Temporal pattern analysis (hourly/daily/seasonal trends)
- Geographic hotspot analysis
- Payment behavior analysis
- Demand forecasting
- Kepner-Tregoe problem analysis using multi-dimensional IS/IS NOT framework

The comprehensive column inventory and quality assessment provided here will guide SCHEMA.md creation and analytical framework design.
