# Kepner-Tregoe Analysis Framework - NYC Taxi Dataset Insights

**Purpose:** This document provides specific guidance for implementing the Kepner-Tregoe "IS / IS NOT" problem analysis framework using the NYC Taxi dataset.

---

## Understanding the IS / IS NOT Framework

The Kepner-Tregoe method systematically analyzes problems by contrasting:
- **WHERE the problem IS occurring** vs. WHERE it IS NOT
- **WHEN the problem IS occurring** vs. WHEN it IS NOT  
- **WHAT the problem IS affecting** vs. WHAT it IS NOT affecting
- **HOW MUCH of a problem exists** (extent/magnitude)

This reveals distinctive patterns that point to root causes.

---

## Dimensional Framework for NYC Taxi Analysis

### 1. TEMPORAL DIMENSIONS (When)

#### Hour of Day
**IS Occurring (High Activity):**
- Peak hours: 5-7 PM (17:00-19:00)
- Secondary peak: 2-3 PM (14:00-15:00)
- Late evening: 9-11 PM (21:00-23:00)

**IS NOT Occurring (Low Activity):**
- Early morning: 3-6 AM
- Mid-morning: 8-10 AM

**Analysis Potential:**
- Compare problem rates during peak vs. off-peak hours
- Identify if issues correlate with rush hour congestion
- Determine if driver behavior differs by time of day

#### Day of Week
**IS Occurring (High Activity):**
- Thursday (15.43% of weekly trips)
- Saturday (15.41%)
- Friday (15.34%)

**IS NOT Occurring (Low Activity):**
- Monday (12.31%)
- Sunday (12.45%)

**Analysis Potential:**
- Weekend vs. weekday problem patterns
- Thursday anomaly investigation (why busiest weekday?)
- Tourist vs. commuter trip differences

#### Month/Season
**NOTE:** Current data has date quality issues, but after correction:

**Analysis Potential:**
- Holiday season patterns (December spikes)
- Weather impact (winter vs. summer)
- Tourism season effects
- Major event impacts (conventions, New Year's Eve, etc.)

---

### 2. GEOGRAPHIC DIMENSIONS (Where)

#### Pickup Locations

**IS Occurring (Hot Zones):**
- Location 237: 675,640 pickups (4.39%)
- Location 236: 626,996 pickups (4.08%)
- Location 161: 609,673 pickups (3.96%)
- Location 132: 595,528 pickups (3.87%)
- Location 186: 465,791 pickups (3.03%)

**IS NOT Occurring (Cold Zones):**
- Locations with <1,000 pickups per period
- Outer boroughs vs. Manhattan core
- Residential vs. commercial zones

**Analysis Potential:**
- Compare problem rates: high-traffic vs. low-traffic zones
- Urban core vs. peripheral areas
- Business district vs. residential vs. entertainment zones
- Airport vs. non-airport locations

#### Dropoff Locations

**Similar distribution to pickups** - use same framework

**Special Case:**
- **Same location trips: 728,797 (4.74%)** - investigate these separately

#### Geographic Patterns
- **Cross-borough trips** vs. within-borough
- **Long-distance** (>10 miles) vs. **short-distance** (<2 miles)
- **Bridge/tunnel trips** (with tolls) vs. local trips

---

### 3. TRIP CHARACTERISTIC DIMENSIONS (What)

#### Trip Distance

**Segmentation Bands:**
- **Micro trips:** 0-1 miles (likely neighborhood/same zone)
- **Short trips:** 1-3 miles (median = 1.82 miles)
- **Medium trips:** 3-10 miles
- **Long trips:** 10-30 miles
- **Extreme trips:** >30 miles (outliers)

**Analysis Potential:**
- Short trip profitability vs. long trip
- Driver acceptance patterns by distance
- Pricing efficiency by distance band

#### Trip Duration

**Segmentation Bands:**
- **Quick:** 0-10 minutes
- **Typical:** 10-20 minutes (median = 14 minutes)
- **Extended:** 20-40 minutes
- **Long:** 40+ minutes

**Analysis Potential:**
- Duration vs. distance efficiency (speed analysis)
- Traffic congestion impact
- Route optimization opportunities

#### Passenger Count

**IS Occurring:**
- Solo passengers: Majority (median = 1.0, avg = 1.26)
- 2 passengers: Common

**IS NOT Occurring:**
- Groups 4+: Rare
- Large groups 6+: Extremely rare (21 trips)

**Analysis Potential:**
- Solo vs. group trip behavior
- Fare per passenger efficiency
- Vehicle capacity utilization

---

### 4. FINANCIAL DIMENSIONS (How Much)

#### Fare Amount Bands

**Based on statistics (median $16.20, avg $21.52):**

**IS Occurring (Common):**
- **Low fares:** $0-15 (below median)
- **Medium fares:** $15-30 (around average)

**IS NOT Occurring (Uncommon):**
- **High fares:** $30-100
- **Premium fares:** $100+

**Analysis Potential:**
- Revenue per trip optimization
- Pricing anomaly detection
- Fare vs. distance correlation issues

#### Payment Method

**IS Occurring:**
- **Credit card:** 61.95% (dominant)
- **Cash:** 8.73%

**IS NOT Occurring:**
- **Dispute:** 1.27%
- **No charge:** 0.41%

**Analysis Potential:**
- Payment method fraud patterns
- Tip behavior (credit vs. cash)
- Transaction failure rates
- Digital vs. cash economy trends

#### Tip Behavior

**Segmentation:**
- **No tip:** $0 (common in cash payments)
- **Low tip:** $0.01-2.00
- **Standard tip:** $2.00-5.00 (median $2.00, avg $2.74)
- **Generous tip:** $5.00+

**IMPORTANT:** Cash tips are NOT recorded - credit card only

**Analysis Potential:**
- Service quality correlation
- Time of day tip patterns
- Trip length vs. tip percentage
- Location-based tipping culture

---

### 5. SERVICE TYPE DIMENSIONS

#### Vendor

**IS Occurring:**
- **Vendor 2:** 79.5% (dominant platform)

**IS NOT Occurring:**
- **Vendor 1:** 19.1%
- **Vendor 7:** 1.24%
- **Vendor 6:** 0.15%

**Analysis Potential:**
- Technology platform performance comparison
- Data quality by vendor
- Vendor-specific issues

#### Rate Code

**IS Occurring:**
- **Standard rate (1):** 65.64%

**IS NOT Occurring:**
- **JFK airport (2):** 2.26%
- **Newark airport (3):** 0.32%
- **Negotiated fare (5):** 0.87%
- **Nassau/Westchester (4):** 0.22%

**ANOMALY:**
- **Code 99:** 3.04% (non-standard - investigate)

**Analysis Potential:**
- Airport trip profitability
- Negotiated fare abuse detection
- Rate code misapplication

#### Store and Forward Flag

**IS Occurring:**
- **No (N):** 72.26% (real-time transmission)

**IS NOT Occurring:**
- **Yes (Y):** 0.09% (stored then forwarded)

**Analysis Potential:**
- Connectivity issues by location
- Data quality in store-and-forward trips
- Geographic connectivity gaps

---

### 6. DATA QUALITY DIMENSIONS

#### Complete vs. Incomplete Records

**IS Complete:**
- 72.35% of records (11,129,607 trips)
- Have all fields populated

**IS NOT Complete:**
- 27.65% of records (4,252,605 trips)
- Missing: passenger_count, RatecodeID, store_and_fwd_flag, congestion_surcharge, Airport_fee

**Analysis Potential:**
- Problem rates in complete vs. incomplete records
- Vendor data quality comparison
- Time period data quality evolution

#### Clean vs. Anomalous Values

**IS Clean (majority):**
- Positive financial amounts
- Logical passenger counts (1-6)
- Reasonable trip distances (<50 miles)
- Valid duration (1-120 minutes)

**IS NOT Clean (outliers/errors):**
- Negative amounts: 135k+ fare errors
- Zero passengers: 59,465 trips
- Extreme distances: >100 miles
- Invalid durations: <0 or >24 hours

**Analysis Potential:**
- Error pattern identification
- Anomaly correlation analysis
- Data cleaning impact assessment

---

## Practical IS / IS NOT Query Templates

### Template 1: Problem Rate by Time

```sql
-- Compare problem occurrence rate during peak vs. off-peak hours
SELECT 
    CASE 
        WHEN toHour(tpep_pickup_datetime) BETWEEN 17 AND 19 THEN 'Peak (5-7 PM)'
        WHEN toHour(tpep_pickup_datetime) BETWEEN 3 AND 6 THEN 'Off-Peak (3-6 AM)'
        ELSE 'Other'
    END as time_period,
    count() as total_trips,
    countIf([PROBLEM_CONDITION]) as problem_trips,
    round(countIf([PROBLEM_CONDITION]) * 100.0 / count(), 2) as problem_rate_pct
FROM NYCTaxiAnalysis.bronze_taxi_trips
WHERE time_period IN ('Peak (5-7 PM)', 'Off-Peak (3-6 AM)')
GROUP BY time_period
```

### Template 2: Problem Rate by Location

```sql
-- Compare problem occurrence in hot zones vs. cold zones
SELECT 
    CASE 
        WHEN PULocationID IN (237, 236, 161, 132, 186) THEN 'Hot Zone'
        ELSE 'Other Zones'
    END as zone_type,
    count() as total_trips,
    countIf([PROBLEM_CONDITION]) as problem_trips,
    round(countIf([PROBLEM_CONDITION]) * 100.0 / count(), 2) as problem_rate_pct
FROM NYCTaxiAnalysis.bronze_taxi_trips
GROUP BY zone_type
```

### Template 3: Problem Rate by Trip Characteristics

```sql
-- Compare problem occurrence by trip distance
SELECT 
    CASE 
        WHEN trip_distance < 1 THEN 'Micro (<1 mi)'
        WHEN trip_distance < 3 THEN 'Short (1-3 mi)'
        WHEN trip_distance < 10 THEN 'Medium (3-10 mi)'
        WHEN trip_distance < 30 THEN 'Long (10-30 mi)'
        ELSE 'Extreme (>30 mi)'
    END as distance_band,
    count() as total_trips,
    countIf([PROBLEM_CONDITION]) as problem_trips,
    round(countIf([PROBLEM_CONDITION]) * 100.0 / count(), 2) as problem_rate_pct
FROM NYCTaxiAnalysis.bronze_taxi_trips
WHERE trip_distance IS NOT NULL
GROUP BY distance_band
ORDER BY problem_rate_pct DESC
```

### Template 4: Problem Rate by Payment/Financial

```sql
-- Compare problem occurrence by payment method
SELECT 
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Unknown'
    END as payment_method,
    count() as total_trips,
    countIf([PROBLEM_CONDITION]) as problem_trips,
    round(countIf([PROBLEM_CONDITION]) * 100.0 / count(), 2) as problem_rate_pct
FROM NYCTaxiAnalysis.bronze_taxi_trips
GROUP BY payment_method
ORDER BY problem_rate_pct DESC
```

### Template 5: Multi-Dimensional Analysis

```sql
-- Cross-dimensional IS/IS NOT analysis
SELECT 
    -- WHEN dimension
    CASE 
        WHEN toHour(tpep_pickup_datetime) BETWEEN 17 AND 19 THEN 'Peak Hour'
        ELSE 'Non-Peak'
    END as when_dimension,
    
    -- WHERE dimension
    CASE 
        WHEN PULocationID IN (237, 236, 161, 132, 186) THEN 'Hot Zone'
        ELSE 'Other Zone'
    END as where_dimension,
    
    -- WHAT dimension
    CASE 
        WHEN trip_distance < 3 THEN 'Short Trip'
        ELSE 'Long Trip'
    END as what_dimension,
    
    count() as total_trips,
    countIf([PROBLEM_CONDITION]) as problem_trips,
    round(countIf([PROBLEM_CONDITION]) * 100.0 / count(), 2) as problem_rate_pct
FROM NYCTaxiAnalysis.bronze_taxi_trips
GROUP BY when_dimension, where_dimension, what_dimension
ORDER BY problem_rate_pct DESC
LIMIT 20
```

---

## Example Problem Scenarios

### Scenario 1: High Cancellation Rate Investigation

**Problem:** Drivers are cancelling trips at an unusual rate.

**IS / IS NOT Analysis:**
- **WHEN IS it happening?** Peak hours vs. off-peak
- **WHERE IS it happening?** Specific zones vs. citywide
- **WHAT trips IS it affecting?** Short vs. long distance
- **HOW MUCH?** Percentage of trips affected

**Expected Insights:**
- If peak hours + short trips → Driver preference for longer fares
- If specific zones → Access/traffic issues in those areas
- If low fare amounts → Minimum fare profitability issue

### Scenario 2: Payment Disputes

**Problem:** Increase in payment disputes (payment_type = 4).

**IS / IS NOT Analysis:**
- **WHEN IS it happening?** Late night vs. daytime
- **WHERE IS it happening?** Tourist areas vs. residential
- **WHAT IS the fare pattern?** High fares vs. low fares
- **WHO IS the vendor?** Vendor 1 vs. Vendor 2

**Expected Insights:**
- If late night + high fares → Surge pricing disputes
- If tourist areas → Visitor unfamiliarity with pricing
- If specific vendor → Technology/UX issues

### Scenario 3: Long Trip Duration Anomalies

**Problem:** Some trips have unreasonably long durations.

**IS / IS NOT Analysis:**
- **WHEN IS it happening?** Rush hour vs. off-peak
- **WHERE IS it happening?** Bridge crossings vs. local
- **WHAT IS the distance?** Short distance + long time (traffic) vs. proportional
- **HOW MUCH?** Degree of duration excess

**Expected Insights:**
- If rush hour + bridge crossings → Traffic congestion
- If short distance + long time → Meter running issues
- If specific locations → Route inefficiency

---

## Recommended Analysis Workflow

### Step 1: Define the Problem
Clearly state what the problem is (e.g., "negative fare amounts")

### Step 2: Identify Problem Cases
```sql
-- Flag problem cases
SELECT count() 
FROM NYCTaxiAnalysis.bronze_taxi_trips 
WHERE fare_amount < 0
```

### Step 3: Build IS / IS NOT Comparisons
For each dimension:
- WHERE: hot zones vs. other
- WHEN: peak vs. off-peak
- WHAT: trip characteristics
- HOW MUCH: extent/severity

### Step 4: Calculate Contrast Ratios
```sql
-- Problem rate in IS group / Problem rate in IS NOT group
-- Ratio > 2.0 suggests strong correlation
```

### Step 5: Identify Distinctions
Look for dimensions where IS group has significantly different problem rate than IS NOT group.

### Step 6: Form Hypotheses
Based on distinctions, form testable hypotheses about root causes.

### Step 7: Validate
Test hypotheses against additional data or through targeted investigation.

---

## Key Success Factors

1. **Start with Clean Data:**
   - Filter out obvious errors first
   - Handle NULL values appropriately
   - Exclude temporal anomalies

2. **Use Multiple Dimensions:**
   - Single dimension may be misleading
   - Cross-dimensional patterns reveal deeper insights

3. **Calculate Statistical Significance:**
   - Don't rely on raw counts
   - Use rates/percentages
   - Consider sample sizes

4. **Look for Unexpected Patterns:**
   - The IS/IS NOT framework excels at revealing non-obvious correlations
   - Pay attention to dimensions with extreme contrasts

5. **Iterate:**
   - Start broad, then narrow focus
   - Drill down into promising distinctions
   - Refine dimension boundaries

---

## Conclusion

The NYC Taxi dataset provides rich dimensional data perfect for Kepner-Tregoe analysis:

**Temporal:** Hour, day, month patterns
**Geographic:** 265+ location zones  
**Financial:** Payment methods, fare bands, tip behavior
**Service:** Vendors, rate codes, passenger counts
**Quality:** Complete vs. incomplete records

By systematically comparing problem rates across these dimensions using the IS / IS NOT framework, you can identify distinctive patterns that point directly to root causes.

**Next Steps:**
1. Define specific problem to investigate
2. Build dimension tables for easy querying
3. Create dashboard for IS/IS NOT visualization
4. Implement statistical testing for significance
5. Document findings and hypotheses

This framework transforms the dataset from a collection of trip records into a powerful problem-solving tool.
