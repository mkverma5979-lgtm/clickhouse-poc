# NYC Taxi Kepner-Tregoe Analysis Dashboard

**A comprehensive IS/IS NOT problem analysis framework applied to NYC Taxi data**

[![ClickHouse](https://img.shields.io/badge/Database-ClickHouse_Cloud-yellow)](https://clickhouse.com/)
[![Power BI](https://img.shields.io/badge/Visualization-Power_BI-orange)](https://powerbi.microsoft.com/)
[![Python](https://img.shields.io/badge/Language-Python_3.13-blue)](https://python.org/)

---

## 📋 Project Overview

This project implements a **Kepner-Tregoe "IS / IS NOT" analysis framework** on 15.4 million NYC Yellow Taxi trip records to identify patterns, anomalies, and business insights through systematic multi-dimensional analysis.

### Key Features

- ✅ **15.4M trips** from latest 6 months of NYC Taxi data
- ✅ **Bronze-Silver-Gold architecture** in ClickHouse Cloud
- ✅ **6 Kepner-Tregoe dimensions** (WHAT, WHERE, WHEN, EXTENT, ABSENCE, CHARACTERISTICS)
- ✅ **Power BI dashboard** with NO DAX (all logic in SQL)
- ✅ **Comprehensive data quality** analysis and cleaning
- ✅ **Fully documented** codebase with schema documentation

---

## 🎯 Kepner-Tregoe Framework

The dashboard systematically analyzes **what IS happening vs what IS NOT happening** across 6 dimensions:

| Dimension | Focus | Key Questions |
|-----------|-------|---------------|
| **WHAT** | Service patterns, trip types | What services are occurring? What's missing? |
| **WHERE** | Geographic analysis | Where are hot zones? Where are cold zones? |
| **WHEN** | Temporal patterns | When are peak periods? When is it quiet? |
| **EXTENT** | Volume & magnitude | How much is occurring? What's the distribution? |
| **ABSENCE** | Data gaps & quality | What data is missing? What's not being reported? |
| **CHARACTERISTICS** | IS vs IS NOT contrasts | How do credit vs cash trips differ? Short vs long? |

---

## 🏗️ Architecture

```
NYC Open Data (Parquet files)
         ↓
   BRONZE LAYER (Raw data - 15.4M rows)
    bronze_taxi_trips
         ↓
   SILVER LAYER (Cleaned & aggregated)
    ├── silver_trips_cleaned (data quality filters)
    ├── silver_trips_hourly (temporal aggregations)
    ├── silver_trips_by_location (geographic aggregations)
    ├── silver_trips_by_payment (payment analysis)
    └── silver_trips_by_vendor (vendor comparison)
         ↓
   GOLD LAYER (Business logic for K-T framework)
    ├── gold_kt_what_is_happening
    ├── gold_kt_where_is_happening
    ├── gold_kt_when_is_happening
    ├── gold_kt_extent_magnitude
    ├── gold_kt_what_not_happening
    └── gold_kt_characteristics_comparison
         ↓
   POWER BI DASHBOARD (Pure visualization - NO DAX)
    7 pages: Executive + 6 K-T dimensions
```

**Design Principle:** All business logic lives in ClickHouse SQL. Power BI is a "dumb" UI layer with no calculations.

---

## 📊 Key Insights

### Service Patterns (WHAT)
- **Vendor 2 dominates:** 79.5% of all trips
- **Credit cards preferred:** 62% vs 9% cash
- **Standard rate:** 66% of trips

### Geographic Patterns (WHERE)
- **Top 15 locations:** 45% of all pickups
- **Hot zones:** Locations 237, 236, 161, 132, 186 (likely Midtown Manhattan)
- **Same-location trips:** 4.74% (circular routes or very short trips)

### Temporal Patterns (WHEN)
- **Peak hour:** 6 PM (7.14% of daily trips)
- **Busiest days:** Thursday, Saturday, Friday (15%+ each)
- **Quietest:** Monday, Sunday (12%)

### Trip Characteristics (EXTENT)
- **Typical trip:** 1.80 miles, 14 minutes, $16.16 fare, $23.99 total
- **Short trips dominate:** <2 miles is most common
- **Outliers minimal:** <1% for most metrics after cleaning

### Data Quality (ABSENCE)
- **27.65% NULL pattern:** One vendor doesn't report passenger_count, RatecodeID, etc.
- **Negative values removed:** 135k negative fares, 137k negative totals
- **Extreme outliers filtered:** trip_distance > 100 miles, duration > 4 hours

### Key Contrasts (CHARACTERISTICS)
- **Credit vs Cash:** 628% more credit card trips
- **Tipping:** Credit card tips 1,397,900% more than cash (cash tips not recorded!)
- **Distance:** Short trips (<2 mi) are 620% more common than long (>10 mi)
- **Fare per mile:** Short trips: $13.21, Long trips: $62.03

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- ClickHouse Cloud account (free tier available)
- Power BI Desktop
- Git

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd NYCTaxiAnalysis
```

### 2. Install Dependencies

```bash
pip install clickhouse-connect python-dotenv pandas requests
```

### 3. Configure ClickHouse Credentials

Create `.env` file in project root:

```env
CLICKHOUSE_HOST=your-host.clickhouse.cloud
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_SECURE=True
CLICKHOUSE_PORT=8443
```

**⚠️ NEVER commit `.env` file to Git!**

### 4. Test Connection

```bash
python test_connection.py
```

### 5. Verify Database

The bronze, silver, and gold layers are already built. Verify with:

```bash
python test_gold_views.py
```

### 6. Connect Power BI

Follow comprehensive guide in [`POWERBI_GUIDE.md`](POWERBI_GUIDE.md)

---

## 📂 Project Structure

```
NYCTaxiAnalysis/
├── .env                           # ClickHouse credentials (NOT in Git)
├── .gitignore                     # Git exclusion rules
├── README.md                      # This file
├── AGENTS.md                      # Project overview for AI tools
├── SCHEMA.md                      # Complete data dictionary
├── POWERBI_GUIDE.md               # Power BI connection & dashboard guide
├── all_sql_code.sql               # Master SQL file with all DDL
│
├── ANALYSIS_SUMMARY.md            # Data analysis findings
├── KEPNER_TREGOE_INSIGHTS.md      # K-T framework design
│
├── ingest_data.py                 # Bronze layer ingestion script
├── test_connection.py             # ClickHouse connection test
├── analyze_schema.py              # Data profiling script
├── create_silver_views.py         # Silver layer creation script
├── create_gold_views.py           # Gold layer creation script
├── test_gold_views.py             # Gold views verification script
│
└── .vscode/                       # VS Code settings
```

---

## 📖 Documentation

| File | Description |
|------|-------------|
| **README.md** | This file - project overview and quick start |
| **SCHEMA.md** | Complete data dictionary with column definitions, data quality notes, and business context |
| **AGENTS.md** | Project structure and purpose for AI tools (OpenCode CLI reference) |
| **POWERBI_GUIDE.md** | Step-by-step guide for connecting Power BI and building dashboard |
| **all_sql_code.sql** | Master SQL file with all DDL for bronze/silver/gold layers |
| **ANALYSIS_SUMMARY.md** | Detailed data analysis findings and statistics |
| **KEPNER_TREGOE_INSIGHTS.md** | K-T framework design and SQL query templates |

---

## 🔧 Scripts

### Data Ingestion

```bash
# Load 6 months of NYC Taxi data into bronze layer
python ingest_data.py
```

**Note:** In production, this should be automated through a data pipeline.

### Create Silver Layer

```bash
# Build cleaned and aggregated materialized views
python create_silver_views.py
```

**Creates:**
- `silver_trips_cleaned` - 15.2M rows (98.7% of bronze retained)
- `silver_trips_hourly` - 2,908 rows
- `silver_trips_by_location` - 523 rows
- `silver_trips_by_payment` - 5 rows
- `silver_trips_by_vendor` - 4 rows

### Create Gold Layer

```bash
# Build Kepner-Tregoe analysis views
python create_gold_views.py
```

**Creates:**
- `gold_kt_what_is_happening` - 9 rows
- `gold_kt_where_is_happening` - 262 rows
- `gold_kt_when_is_happening` - 31 rows
- `gold_kt_extent_magnitude` - 5 rows
- `gold_kt_what_not_happening` - 7 rows
- `gold_kt_characteristics_comparison` - 4 rows

### Test Views

```bash
# Verify all gold views return data
python test_gold_views.py
```

---

## 📊 Power BI Dashboard

### 7-Page Dashboard Structure

1. **Executive Summary** - KPIs and navigation
2. **WHAT Analysis** - Service patterns, vendors, payment methods
3. **WHERE Analysis** - Geographic hot zones, location maps
4. **WHEN Analysis** - Temporal patterns, peak vs off-peak
5. **EXTENT Analysis** - Distributions, magnitudes, outliers
6. **ABSENCE Analysis** - Data quality, NULL patterns, gaps
7. **CHARACTERISTICS** - IS vs IS NOT side-by-side comparisons

### NO DAX Rule

**All business logic is in ClickHouse SQL.** Power BI uses:
- ✅ Direct field references
- ✅ Filters and slicers
- ✅ Conditional formatting
- ❌ NO calculated columns
- ❌ NO DAX measures
- ❌ NO custom calculations

---

## 🗃️ Data Sources

### NYC Taxi Trip Data

- **Source:** NYC Taxi & Limousine Commission (TLC)
- **URL:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Format:** Parquet files
- **Period:** Latest 6 months
- **Volume:** 15.4M trips (Yellow Taxi only)

### TLC Taxi Zones

- **Source:** NYC Open Data
- **URL:** https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/d3c5-ddgc
- **Format:** Shapefile (for mapping in Power BI)

---

## ⚠️ Data Quality Notes

### Critical Issues Addressed

1. **Temporal Anomaly:** 99.99% of trips dated 2025-2026 (likely year offset error) - documented but not corrected
2. **NULL Pattern:** 27.65% of records missing 6 fields (specific vendor doesn't report)
3. **Negative Values:** Removed 135k negative fares, 137k negative totals
4. **Extreme Outliers:** Filtered trip_distance > 100 miles, duration > 4 hours
5. **Logical Impossibilities:** Removed 59,465 trips with 0 passengers, 7 with negative duration

**See `SCHEMA.md` for complete data quality documentation.**

---

## 🤝 Contributing

This is a demonstration project. If you'd like to extend it:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

**Enhancement Ideas:**
- Automate data ingestion pipeline
- Add predictive modeling (demand forecasting)
- Implement incremental refresh
- Create mobile-responsive Power BI layout
- Add real-time data streaming

---

## 📜 License

This project is for educational and analytical purposes.

**Data Source:** NYC TLC Trip Record Data is public domain.

---

## 🙏 Acknowledgments

- **NYC TLC** for providing open data
- **ClickHouse** for fast analytical database
- **Kepner-Tregoe** for the IS/IS NOT problem-solving framework
- **OpenCode CLI** for project scaffolding

---

## 📞 Contact & Support

**Project Documentation:**
- SCHEMA.md - Data dictionary
- POWERBI_GUIDE.md - Dashboard setup
- AGENTS.md - Project structure

**External Resources:**
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [Kepner-Tregoe Method](https://kepner-tregoe.com/)

---

## 🎓 Learning Outcomes

This project demonstrates:

✅ **Bronze-Silver-Gold architecture** for data warehousing  
✅ **Data quality assessment** and cleaning at scale  
✅ **Kepner-Tregoe problem-solving framework** applied to real data  
✅ **SQL-first approach** to business logic (no BI tool lock-in)  
✅ **Materialized views** for performance optimization  
✅ **Comprehensive documentation** for team collaboration  
✅ **Git workflows** for code management  

---

**Built with OpenCode CLI | May 2026**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | May 20, 2026 | Initial release with bronze/silver/gold layers and Power BI dashboard guide |

---

**End of README**
