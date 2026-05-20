# Power BI Connection & Dashboard Guide

**Project:** NYC Taxi Kepner-Tregoe Analysis  
**Database:** ClickHouse Cloud (NYCTaxiAnalysis)  
**Architecture:** All logic in SQL, Power BI as pure visualization layer (NO DAX)

---

## Prerequisites

Before connecting Power BI to ClickHouse, ensure you have:

1. ✅ **Power BI Desktop** installed (download from microsoft.com/power-bi)
2. ✅ **ClickHouse ODBC Driver** (we'll install this below)
3. ✅ **ClickHouse credentials** from `.env` file

---

## Step 1: Install ClickHouse ODBC Driver

### Download and Install

1. Visit: https://github.com/ClickHouse/clickhouse-odbc/releases
2. Download the latest **Windows 64-bit installer** (e.g., `clickhouse-odbc-X.X.X-win64.msi`)
3. Run the installer and follow the prompts
4. Accept default settings
5. Click "Install" and "Finish"

**Verify Installation:**
- Open "ODBC Data Sources (64-bit)" from Windows Start menu
- Check that "ClickHouse ODBC Driver (Unicode)" appears in the Drivers tab

---

## Step 2: Configure ODBC Data Source (DSN)

### Create System DSN

1. Open **ODBC Data Sources (64-bit)** from Windows Start
2. Go to **System DSN** tab
3. Click **Add...**
4. Select **ClickHouse ODBC Driver (Unicode)**
5. Click **Finish**

### Configure Connection

In the ClickHouse ODBC Driver DSN Configuration window, enter:

**From your `.env` file:**

```
Data Source Name:    NYCTaxiAnalysis
Description:         NYC Taxi Kepner-Tregoe Analysis
Host:                sqgfslfoa6.ap-south-1.aws.clickhouse.cloud
Port:                8443
Database:            NYCTaxiAnalysis
Username:            default
Password:            1Ihc~Ix5Xgv98

☑ Use SSL/TLS
☑ Skip SSL Certificate Verification (for ClickHouse Cloud)
```

**Important Settings:**
- **Timeout:** 300 (5 minutes for large queries)
- **SSL Mode:** Require

6. Click **Test** to verify connection
7. If successful, click **OK** to save
8. Click **OK** to close ODBC Data Sources

---

## Step 3: Connect Power BI Desktop to ClickHouse

### Open Power BI Desktop

1. Launch **Power BI Desktop**
2. Close the splash screen
3. Go to **Home → Get Data → More...**

### Add ODBC Connection

1. Search for **ODBC**
2. Select **ODBC** connector
3. Click **Connect**

### Configure Connection

1. **Data source name (DSN):** Select **NYCTaxiAnalysis** from dropdown
2. Click **OK**

### Authentication

1. Select **Database** authentication
2. **User name:** `default`
3. **Password:** `1Ihc~Ix5Xgv98` (from .env file)
4. Click **Connect**

---

## Step 4: Import Gold Views (Data Sources)

### Navigator Window

After connection succeeds, you'll see the Navigator window with available tables/views.

### Select All 6 Gold Views:

Expand **NYCTaxiAnalysis** database and select:

☑ **gold_kt_what_is_happening**  
☑ **gold_kt_where_is_happening**  
☑ **gold_kt_when_is_happening**  
☑ **gold_kt_extent_magnitude**  
☑ **gold_kt_what_not_happening**  
☑ **gold_kt_characteristics_comparison**

### Load Options

1. Choose **Import** mode (NOT DirectQuery for best performance)
2. Click **Load** (NOT Transform Data)
3. Wait for data to load (may take 1-2 minutes for 15M rows of source data)

**Progress:** You'll see loading progress in bottom status bar.

---

## Step 5: Verify Data Load

### Check Data Model

1. Go to **Model** view (left sidebar, table icon)
2. Verify all 6 gold views appear as tables
3. No relationships needed (each view is independent for specific analysis)

### Check Data

1. Go to **Data** view (left sidebar, table with data icon)
2. Click each gold view in the Fields pane
3. Verify data appears in grid

**Expected Row Counts:**
- gold_kt_what_is_happening: **9 rows**
- gold_kt_where_is_happening: **262 rows**
- gold_kt_when_is_happening: **31 rows**
- gold_kt_extent_magnitude: **5 rows**
- gold_kt_what_not_happening: **7 rows**
- gold_kt_characteristics_comparison: **4 rows**

---

## Dashboard Structure: 7 Pages

Now we'll build the Kepner-Tregoe IS/IS NOT dashboard with 7 pages.

---

### Page 1: Executive Summary

**Purpose:** High-level overview with navigation to detailed pages

**Visuals:**

1. **Title Text Box** (top)
   - Text: "NYC Taxi - Kepner-Tregoe Analysis"
   - Format: 28pt, Bold, Center-aligned

2. **KPI Cards** (6 cards in 2 rows of 3)
   - Data: gold_kt_extent_magnitude
   - Card 1: Total Trips (metric_name = "Total Trips", show avg_value)
   - Card 2: Avg Trip Distance (metric_name = "Trip Distance (miles)", show median_value)
   - Card 3: Avg Fare (metric_name = "Fare Amount ($)", show median_value)
   - Card 4: Avg Duration (metric_name = "Duration (minutes)", show median_value)
   - Card 5: Avg Total Amount (metric_name = "Total Amount ($)", show median_value)
   - Card 6: Data Quality Score (from gold_kt_what_not_happening, average of data_quality_score)

3. **Matrix Visual** (K-T Dimensions Overview)
   - Data: Mixed (create bookmarks to each page)
   - Rows: Dimension Name (manually typed: WHAT, WHERE, WHEN, EXTENT, ABSENCE, CHARACTERISTICS)
   - Values: Key Metric, Status
   - **Note:** Use buttons with page navigation actions instead of matrix

**Better Approach: Navigation Buttons**

Create 6 buttons (1 per K-T dimension):
- Button 1: "WHAT is happening" → Navigate to Page 2
- Button 2: "WHERE is happening" → Navigate to Page 3
- Button 3: "WHEN is happening" → Navigate to Page 4
- Button 4: "EXTENT & Magnitude" → Navigate to Page 5
- Button 5: "WHAT NOT happening" → Navigate to Page 6
- Button 6: "CHARACTERISTICS Comparison" → Navigate to Page 7

Format: Large buttons with icons, 3x2 grid

---

### Page 2: WHAT Analysis

**Data Source:** gold_kt_what_is_happening

**Visuals:**

1. **Title:** "WHAT is happening - Service Patterns"

2. **Stacked Bar Chart: Trip Volume by Dimension Category**
   - Axis: characteristic
   - Values: volume
   - Legend: dimension_category
   - Sort: By volume descending
   - Data labels: Show percentage

3. **Table: Detailed Breakdown**
   - Columns: dimension_category, characteristic, volume, percentage, avg_value, problem_indicator
   - Sort: By volume descending
   - Conditional formatting: problem_indicator (red for "High Concern", yellow for "Moderate")

4. **Donut Chart: Vendor Distribution**
   - Legend: characteristic (filter WHERE dimension_category = "Vendor")
   - Values: volume
   - Data labels: Category and percentage

5. **Donut Chart: Payment Method Distribution**
   - Legend: characteristic (filter WHERE dimension_category = "Payment Method")
   - Values: volume
   - Data labels: Category and percentage

**Slicers:**
- dimension_category (dropdown)

---

### Page 3: WHERE Analysis

**Data Source:** gold_kt_where_is_happening

**Visuals:**

1. **Title:** "WHERE is happening - Geographic Analysis"

2. **Map Visual** (if you have location shapefile):
   - Location: location_id (map to TLC zones shapefile)
   - Size: pickup_count
   - Color: zone_classification (hot=red, warm=orange, medium=yellow, cold=blue)
   - **Note:** Requires TLC Taxi Zone shapefile import (optional)

3. **Bar Chart: Top 20 Locations by Trip Volume**
   - Axis: location_name
   - Values: pickup_count
   - Color: zone_classification
   - Sort: By pickup_count descending
   - Filter: Top 20

4. **Table: Hot Zones Detail**
   - Filter: zone_classification = "Hot Zone"
   - Columns: location_id, location_name, pickup_count, percentage_of_total, avg_fare, avg_distance
   - Sort: By pickup_count descending

5. **Table: Cold Zones Detail**
   - Filter: zone_classification = "Cold Zone"
   - Columns: location_id, location_name, pickup_count, percentage_of_total, avg_fare, avg_distance
   - Sort: By pickup_count ascending
   - Purpose: Show what's NOT happening (IS NOT analysis)

**Slicers:**
- zone_classification (dropdown)

---

### Page 4: WHEN Analysis

**Data Source:** gold_kt_when_is_happening

**Visuals:**

1. **Title:** "WHEN is happening - Temporal Patterns"

2. **Line Chart: Trips by Hour of Day**
   - X-Axis: time_value (filter WHERE time_dimension = "Hour of Day")
   - Y-Axis: trip_volume
   - Color: classification (Peak/High/Medium/Off-Peak)
   - Sort: By time_value (0-23)

3. **Bar Chart: Trips by Day of Week**
   - Axis: time_value (filter WHERE time_dimension = "Day of Week")
   - Values: trip_volume
   - Color: classification
   - Sort: By day order (Mon-Sun)

4. **Table: Peak Period Details**
   - Filter: classification = "Peak Period"
   - Columns: time_dimension, time_value, trip_volume, total_revenue, avg_fare, avg_distance
   - Sort: By trip_volume descending

5. **Table: Off-Peak Period Details**
   - Filter: classification = "Off-Peak Period"
   - Columns: time_dimension, time_value, trip_volume, total_revenue, avg_fare, avg_distance
   - Sort: By trip_volume ascending
   - Purpose: IS NOT analysis (what's not happening)

**Slicers:**
- time_dimension (dropdown: Hour of Day, Day of Week)
- classification (multiselect)

---

### Page 5: EXTENT Analysis

**Data Source:** gold_kt_extent_magnitude

**Visuals:**

1. **Title:** "EXTENT & Magnitude - Distributions"

2. **Table: Statistical Summary**
   - Columns: metric_name, min_value, max_value, avg_value, median_value, percentile_95
   - All values formatted as numbers with 2 decimals
   - Conditional formatting: Highlight median_value column

3. **KPI Cards** (5 cards, one per metric):
   - Card 1: Trip Distance - Median (metric_name = "Trip Distance (miles)", show median_value)
   - Card 2: Fare Amount - Median
   - Card 3: Total Amount - Median
   - Card 4: Duration - Median
   - Card 5: Total Trips

4. **Clustered Bar Chart: Min vs Max vs Median**
   - Axis: metric_name (exclude "Total Trips")
   - Values: min_value, max_value, median_value
   - Legend: Value type
   - Data labels: On

5. **Card: Outlier Analysis**
   - Values: outlier_count, outlier_percentage
   - By metric_name
   - Conditional formatting: Red if outlier_percentage > 1%

**Insights Text Box:**
- Add text explaining distributions
- Note: "Median is more reliable than average due to outliers"

---

### Page 6: ABSENCE Analysis

**Data Source:** gold_kt_what_not_happening

**Visuals:**

1. **Title:** "WHAT IS NOT Happening - Data Quality & Gaps"

2. **Bar Chart: NULL Percentage by Dimension**
   - Axis: dimension
   - Values: null_percentage
   - Sort: By null_percentage descending
   - Color: Red gradient (higher = more red)
   - Data labels: Show percentage

3. **Waterfall Chart: Data Completeness**
   - Category: dimension
   - Y-Axis: null_count
   - Show cumulative total
   - Purpose: Visualize data loss through pipeline

4. **Table: Data Quality Scorecard**
   - Columns: dimension, null_count, null_percentage, data_quality_score
   - Sort: By null_percentage descending
   - Conditional formatting:
     - data_quality_score: Green > 90%, Yellow 70-90%, Red < 70%
     - null_percentage: Red > 25%, Yellow 10-25%, Green < 10%

5. **Gauge: Overall Data Quality Score**
   - Value: Average of data_quality_score
   - Min: 0
   - Max: 100
   - Target: 90%
   - Color bands: Red <70%, Yellow 70-90%, Green >90%

**Insights Text Box:**
- "27.65% of records have NULL pattern (same vendor doesn't report these fields)"
- "Data Filtered Out represents trips removed due to quality issues"

---

### Page 7: CHARACTERISTICS Comparison

**Data Source:** gold_kt_characteristics_comparison

**Purpose:** Side-by-side IS vs IS NOT comparisons

**Visuals:**

1. **Title:** "CHARACTERISTICS Comparison - IS vs IS NOT"

2. **Clustered Bar Chart: IS vs IS NOT Values**
   - Axis: comparison_dimension
   - Values: is_metric_value, is_not_metric_value
   - Legend: is_category vs is_not_category
   - Color: Contrasting colors (blue vs orange)
   - Data labels: Show values

3. **Table: Detailed Comparison**
   - Columns: comparison_dimension, is_category, is_not_category, is_metric_value, is_not_metric_value, difference, difference_percentage
   - Sort: By difference_percentage descending
   - Conditional formatting: difference_percentage (green if positive, red if negative)

4. **Cards** (4 cards, one per comparison):
   - Card 1: Payment - Credit vs Cash (show difference_percentage)
   - Card 2: Tip - Credit vs Cash (show difference_percentage)
   - Card 3: Distance - Short vs Long (show difference_percentage)
   - Card 4: Fare - Short vs Long (show difference_percentage)

5. **Clustered Column Chart: Difference Visualization**
   - Axis: comparison_dimension
   - Values: difference
   - Color: By sign (positive=green, negative=red)
   - Data labels: Show difference and percentage

**Insights Text Box:**
- "Credit card trips 628% more than cash"
- "Credit card tips 1,397,900% more than cash (cash tips not recorded)"
- "Short trips (<2 mi) 620% more than long trips (>10 mi)"

---

## Dashboard Design Best Practices

### Color Scheme

**Kepner-Tregoe IS/IS NOT theme:**
- **IS (what's happening):** Blue (#1F77B4)
- **IS NOT (what's not happening):** Orange (#FF7F0E)
- **Peak/High:** Green (#2CA02C)
- **Off-Peak/Low:** Gray (#7F7F7F)
- **Problems/Gaps:** Red (#D62728)

### Formatting

1. **Page Background:** Light gray (#F5F5F5)
2. **Visual Borders:** Subtle gray, rounded corners
3. **Fonts:**
   - Titles: Segoe UI, 16pt, Bold
   - Data labels: Segoe UI, 10pt
   - Values: Segoe UI, 12pt
4. **Number Formatting:**
   - Trips: #,##0 (no decimals)
   - Money: $#,##0.00
   - Percentages: 0.00%
   - Distances: #,##0.00

### NO DAX Rules

**✅ ALLOWED:**
- Direct field references from gold views
- Basic filters and slicers
- Sort by existing fields
- Conditional formatting using field values
- Top N filters

**❌ NOT ALLOWED:**
- Calculated columns
- Measures (DAX formulas)
- Custom calculations
- CALCULATE() or similar DAX functions
- Time intelligence functions

**Why?** All business logic lives in ClickHouse SQL. Power BI is purely for visualization.

---

## Testing the Dashboard

### Validation Checklist

☑ All 6 gold views loaded successfully  
☑ Row counts match expected values  
☑ All 7 pages created  
☑ Navigation buttons work  
☑ Slicers filter data correctly  
☑ Charts show meaningful data  
☑ No DAX measures created  
☑ No calculated columns added  
☑ Colors follow IS/IS NOT theme  
☑ Tooltips show relevant information  

### Sample Questions the Dashboard Answers

**WHAT:**
- Which vendors dominate? (Vendor 2: 79.5%)
- What payment methods are used? (Credit: 62%, Cash: 9%)

**WHERE:**
- What are the hot zones? (Locations 237, 236, 161, 132, 186)
- What areas are underserved? (Cold zones)

**WHEN:**
- When is peak hour? (6 PM: 7.14% of daily trips)
- What day is busiest? (Thursday: 15.43%)

**EXTENT:**
- What's the typical trip? (1.80 miles, 14 min, $16.16 fare, $23.99 total)
- How many outliers? (< 1% for most metrics)

**ABSENCE:**
- What data is missing? (27.65% NULL pattern)
- What's data quality score? (~72%)

**CHARACTERISTICS:**
- Credit vs Cash? (628% more credit trips)
- Short vs Long? (620% more short trips)

---

## Refresh & Maintenance

### Manual Refresh

1. Click **Refresh** button in Home ribbon
2. Wait for data reload (1-2 minutes)
3. Verify updated data

### Scheduled Refresh (Power BI Service)

1. Publish to Power BI Service: File → Publish
2. In Power BI Service, go to dataset Settings
3. Configure Gateway (if on-premise) or Cloud connection
4. Set Schedule: Daily at midnight
5. Configure credentials

---

## Troubleshooting

### Connection Issues

**Problem:** Can't connect to ClickHouse  
**Solution:**
- Verify ODBC DSN configuration
- Test connection in ODBC Data Sources
- Check firewall allows port 8443
- Verify credentials from .env file

**Problem:** Authentication failed  
**Solution:**
- Re-enter password (copy exactly from .env)
- Remove spaces from username/password
- Try "default" as username (lowercase)

### Data Load Issues

**Problem:** Views not appearing in Navigator  
**Solution:**
- Verify views exist in ClickHouse (run test_gold_views.py)
- Check database name: NYCTaxiAnalysis
- Refresh Navigator (click Refresh)

**Problem:** Zero rows loaded  
**Solution:**
- Check view permissions in ClickHouse
- Verify views have data (run test queries)
- Try Import mode instead of DirectQuery

### Visual Issues

**Problem:** Visual shows error  
**Solution:**
- Check field names match gold view columns
- Verify data types are correct
- Remove filters and re-add

**Problem:** Numbers don't match expectations  
**Solution:**
- Verify no DAX measures applied
- Check filters aren't excluding data
- Cross-reference with test_gold_views.py output

---

## Next Steps

After dashboard completion:

1. ✅ Save Power BI file: `NYCTaxiAnalysis_Dashboard.pbix`
2. ✅ Test all pages and interactions
3. ✅ Export to PDF for documentation
4. ✅ Publish to Power BI Service (optional)
5. ✅ Share with stakeholders

---

## Resources

- **ClickHouse ODBC Driver:** https://github.com/ClickHouse/clickhouse-odbc
- **Power BI Desktop:** https://powerbi.microsoft.com/desktop/
- **TLC Taxi Zones Shapefile:** https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc
- **Kepner-Tregoe Method:** https://kepner-tregoe.com/

---

**End of Power BI Guide**
