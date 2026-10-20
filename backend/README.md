# 🌾 Crop Production Trends and Agricultural Productivity Analysis Using Big Data

**A complete, production-quality Big Data college project featuring:**
- Real Indian crop data (1997–2025, 463,847 records)
- Interactive India choropleth map
- 7-page professional Streamlit dashboard
- PySpark, Hadoop MapReduce, and Pandas analytics
- Automated test suite (13 tests, all passing)

---

## 📊 Dataset

| Property | Value |
|---|---|
| File | `data/crop_production_1997_2025.csv` |
| Source | Government of India crop statistics (Ministry of Agriculture) |
| Records | 463,847 |
| Year range | 1997–2025 |
| Columns | State_Name, District_Name, Crop_Year, Season, Crop, Area, Production, Data_Type |
| States / UTs | 34 |
| Unique crops | 115 |
| Seasons | Kharif, Rabi, Whole Year, Summer, Winter, Autumn |
| Missing production | 4,973 rows (1.07 %) |
| Duplicates | 0 |

### ⚠️ Data Provenance Note
All rows are labelled `Data_Type = 'Actual'` in the CSV.  
Years **2024 and 2025** each contain exactly 18,844 records — the same count as 2023 — which strongly suggests forward-filling or synthetic extension.  
These years are flagged in the dashboard as **"Potentially Extended"** and must not be cited as verified government statistics.

### Units
- `Area` → **hectares (ha)**
- `Production` → **metric tonnes (t)**
- `Yield` (derived) → `Production / Area` → **t/ha**

---

## 🏗️ Architecture

```
CSV (data/) ─┬─ Pandas cleaning & analysis ─┬─ Streamlit Dashboard
              │                              └─ Downloads / Explorer
              ├─ PySpark pipeline ──────────── outputs/spark/ (CSV + Parquet)
              └─ MapReduce (mapper + reducer) ─ outputs/mapreduce/ (state totals)
                      ↕
              Hadoop HDFS (when configured)
```

### Technology Roles

| Technology | Role |
|---|---|
| **Python 3.13** | Orchestration, application logic, tests |
| **Pandas** | Data inspection, cleaning, validation, all analytics aggregations |
| **PySpark** | Scalable distributed aggregations (state, year, crop, season) |
| **Hadoop HDFS** | Distributed storage for raw CSV and processed outputs |
| **Hadoop MapReduce** | Python Streaming job — production totals by state |
| **Matplotlib** | Static analytical visualizations (dual-axis trend, seasonal bar) |
| **Plotly** | Interactive choropleth map + all interactive charts |
| **Streamlit** | Complete 7-page web dashboard |

---

## 📁 Project Structure

```
crop-production-big-data/
├── app.py                      # Main Streamlit dashboard (7 pages)
├── requirements.txt
├── README.md
├── inspect_data.py             # One-off data inspection script
├── data/
│   └── crop_production_1997_2025.csv   # ← never overwritten
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py        # Cleaning pipeline + quality report
│   ├── data_loader.py          # Streamlit-cached loader
│   ├── pandas_analysis.py      # All aggregation functions
│   ├── pyspark_analysis.py     # PySpark pipeline
│   ├── hdfs_utils.py           # HDFS utilities + commands
│   ├── visualizations.py       # Plotly + Matplotlib chart functions
│   ├── map_utils.py            # GeoJSON + state-name mapping
│   └── mapreduce/
│       ├── __init__.py
│       ├── mapper.py           # Hadoop Streaming mapper
│       └── reducer.py          # Hadoop Streaming reducer
├── assets/
│   └── india_states.geojson    # India state boundaries (36 features)
├── outputs/
│   ├── spark/                  # PySpark CSV and Parquet outputs
│   └── mapreduce/              # Local MapReduce simulation output
├── tests/
│   └── test_pipeline.py        # 13 automated tests
└── .streamlit/
    └── config.toml             # Theme: emerald green / white
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

For PySpark (optional — requires Java):
```bash
# 1. Install JDK 11: https://adoptium.net/
# 2. Set JAVA_HOME environment variable
# 3. PySpark is already in requirements.txt
```

---

## 🚀 Running the Dashboard

```bash
# From the project root directory:
streamlit run app.py
```

Dashboard opens at → **http://localhost:8501**

> **Windows users:** If `streamlit` is not on PATH, use:
> ```powershell
> C:\Users\<YourName>\AppData\Local\Programs\Python\Python313\python.exe -m streamlit run app.py
> ```

---

## 📄 Dashboard Pages

| Page | Description |
|---|---|
| 🏠 Overview Dashboard | KPI cards, India map, top states, year-wise trend, seasonal chart |
| 🗺️ India Production Map | Full-page choropleth, state rankings, metric/year/crop/season filters |
| 🌿 Crop & Seasonal Analysis | Crop trends, multi-crop comparison, seasonal breakdown, yield boxplot |
| 📍 State & District Analysis | State deep-dive, district bar chart, radar chart, rankings table |
| 📈 Historical Trends | Long-term trends, period comparison, data provenance view |
| 🔍 Dataset Explorer | Searchable preview, quality report, column guide, CSV download |
| ⚙️ Big Data Processing | Real status of Pandas, PySpark, HDFS, MapReduce |

---

## ⚡ PySpark Pipeline

```bash
# Run standalone (Java must be installed):
python src/pyspark_analysis.py

# Or via spark-submit:
spark-submit src/pyspark_analysis.py
```

**Outputs written to `outputs/spark/`:**
- `state_aggregation.csv` — total production/area per state
- `year_aggregation.csv` — total production/area per year
- `crop_aggregation.csv` — total production/area per crop
- `season_aggregation.csv` — total production/area per season
- `state_aggregation.parquet` — Parquet format for Spark

The dashboard's **Pandas vs. PySpark tab** compares aggregates and reports the percentage difference.

---

## 🗄️ Hadoop HDFS Workflow

> Requires Hadoop installed and services running (`start-dfs.sh && start-yarn.sh`)

```bash
# 1. Set up directories and upload dataset
python src/hdfs_utils.py setup

# 2. Verify upload
hdfs dfs -ls /user/crop_project/input/

# 3. List all project files
hdfs dfs -ls -R /user/crop_project/
```

**HDFS directory layout:**
```
/user/crop_project/
├── input/
│   └── crop_production_1997_2025.csv
├── output/          ← PySpark outputs (when run from HDFS)
└── mapreduce_output/ ← MapReduce job output
```

---

## 🔀 MapReduce Job

### Local simulation (no Hadoop required)

**Windows PowerShell:**
```powershell
Get-Content data\crop_production_1997_2025.csv |
  python src\mapreduce\mapper.py |
  Sort-Object |
  python src\mapreduce\reducer.py > outputs\mapreduce\state_production_totals.txt
```

**Linux / macOS:**
```bash
cat data/crop_production_1997_2025.csv \
  | python3 src/mapreduce/mapper.py \
  | sort \
  | python3 src/mapreduce/reducer.py > outputs/mapreduce/state_production_totals.txt
```

### Hadoop Streaming (requires Hadoop)

```bash
HADOOP_JAR=$(find $HADOOP_HOME/share/hadoop/tools/lib -name "hadoop-streaming-*.jar" | head -1)

hdfs dfs -rm -r -f /user/crop_project/mapreduce_output

hadoop jar $HADOOP_JAR \
  -files src/mapreduce/mapper.py,src/mapreduce/reducer.py \
  -mapper  "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -input   /user/crop_project/input/crop_production_1997_2025.csv \
  -output  /user/crop_project/mapreduce_output

# Verify
hdfs dfs -ls /user/crop_project/mapreduce_output
hdfs dfs -cat /user/crop_project/mapreduce_output/part-00000 | head -20
```

**Output format:**  `State_Name\tTotal_Production_Tonnes`

---

## 🧪 Running Tests

```bash
# Windows:
set PYTHONIOENCODING=utf-8 && python tests/test_pipeline.py

# Linux / macOS:
PYTHONIOENCODING=utf-8 python tests/test_pipeline.py

# With pytest (if installed):
pip install pytest
pytest tests/ -v
```

**Test results (all 13 pass):**
```
✅ test_raw_load
✅ test_clean_adds_columns
✅ test_no_negative_area
✅ test_no_negative_production
✅ test_quality_report_keys
✅ test_state_name_mapping
✅ test_yearwise_production_monotone_years
✅ test_top_states_count
✅ test_no_duplicate_key
✅ test_build_state_map_df
✅ test_crop_trend_rice
✅ test_mapreduce_mapper
✅ test_mapreduce_reducer

Results: 13 passed, 0 failed out of 13 tests
```

---

## 🗺️ India Map — State Name Matching

The GeoJSON file uses different state name spellings than the CSV. All 34 CSV states are mapped:

| CSV Name | GeoJSON Name | Note |
|---|---|---|
| Andaman And Nicobar Islands | Andaman and Nicobar | — |
| Odisha | Orissa | Older GeoJSON spelling |
| Uttarakhand | Uttaranchal | Older GeoJSON spelling |
| Ladakh | Jammu and Kashmir | Carved out 2019; no separate geometry |
| The Dadra And Nagar Haveli And Daman And Diu | Dadra and Nagar Haveli | Merged UT 2020 |

---

## 📉 Data Limitations

1. **Years 2024–2025:** Identical record counts to 2023 — likely forward-filled. Labelled as "Potentially Extended".
2. **4,973 missing Production values** (~1.07%): Not filled with zero. Excluded from aggregations.
3. **Units not stated in CSV header:** Verified from official ICRISAT/DACFW sources (Area = ha, Production = tonnes).
4. **Ladakh** (created 2019) has no separate map boundary in the GeoJSON — visualised under J&K geometry.
5. **Telangana** data starts 2014 (bifurcation from Andhra Pradesh). Long-term AP comparisons may be discontinuous.
6. **Zero Area/Production rows:** 3,223 zero-area and 7,280 zero-production rows exist in the data. These are preserved (some crops may be reported with zero harvest in drought years).
7. Correlations visible in charts do **not** imply causation.

---

## 🎓 Viva Explanation (Quick Reference)

### Problem Statement
India is the world's second-largest agricultural producer. Analysing 29 years of district-level crop data across 115 crops and 34 states requires Big Data tools to process at scale and interactive visualisations to derive insights.

### Data Flow
1. **Raw CSV** → loaded by Pandas → cleaned (whitespace, type coercion, yield derived)
2. **Pandas analytics** → KPI cards, charts, rankings on the Streamlit dashboard
3. **PySpark** → same aggregations at distributed scale → outputs compared to Pandas for validation
4. **Hadoop HDFS** → stores raw and processed data in a distributed filesystem
5. **MapReduce** → mapper emits `(state, production)` pairs → reducer sums by state

### Why Big Data?
- 463,847 records spanning 29 years × 34 states × 737 districts × 115 crops × 6 seasons
- PySpark partitions the data across all available CPU cores using DataFrames
- HDFS provides fault-tolerant, replicated storage for the dataset
- MapReduce demonstrates the foundational distributed computing paradigm

### Key Findings from the Data
- **Kerala and Tamil Nadu** are consistently the highest producers (driven by high-value crops like coconut, sugarcane)
- **Kharif season** accounts for the largest share of production
- **Rice and Maize** are the most frequently reported crops
- Production shows an overall upward trend from 1997 to 2023 with weather-related dips

---

## 🔮 Future Improvements

- Add real-time price data from Agmarknet API
- Weather correlation analysis using IMD rainfall data
- Predictive modelling (ARIMA / ML) for crop yield forecasting
- District-level GeoJSON for sub-state choropleth
- HDFS integration with HBase for real-time queries

---

## 👤 Author

**College Big Data Project**  
Python · Pandas · PySpark · Hadoop · Streamlit · Plotly · Matplotlib
