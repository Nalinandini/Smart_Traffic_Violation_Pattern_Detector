# Smart Traffic Violation Pattern Detector

## 1. Project Overview
This project analyzes traffic violation data to detect **time-based patterns**, **high-risk location hotspots**, and **traffic surge anomalies**, visualizing results through a modern **interactive Streamlit control center**.  
It equips transport authorities and municipal planners with actionable intelligence on **when**, **where**, and **how severely** infractions occur to optimize traffic patrol deployments and enhance road safety.

---

## 2. Tech Stack
| Component | Technology | Description |
|-----------|------------|-------------|
| Programming Language | Python 3.10+ | Core computational logic |
| Big Data Framework | Apache Spark (PySpark) | Distributed dataset processing and MLlib KMeans |
| Resilient Processing Engine | Pandas, NumPy, PyArrow | High-speed local fallback engine & Parquet persistence |
| Visualization & UI | Streamlit, Altair, Pydeck | Real-time analytics UI, interactive charts & 3D maps |
| Machine Learning & Math | KMeans Clustering, Z-Score | Geospatial hotspot grouping & spike anomaly detection |
| Testing Suite | Python `unittest` | Automated unit and integration testing |

---

## 3. Architecture & File Structure

```
Smart_Traffic_Violation_Pattern_Detector/
├── dashboard/
│   └── streamlit_dashboard.py          # Interactive Streamlit Control Center UI
├── data/
│   ├── input/                          # Raw CSV traffic violation datasets
│   ├── cleaned_parquet/                # Cleaned Parquet records
│   ├── aggregations/                   # Parquet hourly aggregations
│   └── output/                         # Analytics CSV outputs (hotspots, risk, clusters)
├── src/
│   ├── generate_mock_data.py           # Synthetic dataset generator with peak weighting
│   ├── data_cleaning.py                # Schema standardization & cleaning (Spark/Pandas)
│   ├── time_aggregations.py            # Hourly & temporal aggregations
│   ├── week3_time_type_aggregation.py  # Day + Hour + Violation Type cross-aggregations
│   ├── week4_location_aggregation.py   # Location rankings and frequency counts
│   ├── hotspot_detection.py            # Grid binning (0.01°) & KMeans clustering (k=5)
│   └── risk_and_anomaly.py             # Weighted severity scoring & Z-score surge detection
├── tests/
│   └── test_pipeline.py                # Unit tests for generator, weights, clustering & outputs
├── run_pipeline.py                     # Master pipeline runner & CLI orchestrator
├── requirements.txt                    # Project dependency specification
├── .gitignore                          # Git exclusions for caches and transient outputs
├── LICENSE                             # MIT Open-Source License
└── README.md                           # Documentation & Agile specification
```

---

## 4. Key Features

- **Automated Master Pipeline**: Single command `python run_pipeline.py` or one-click in-dashboard trigger to execute the full ETL and ML stages end-to-end.
- **Weighted Severity Risk Index**: Infractions are weighted by severity (e.g., DUI = 10, Reckless = 8, Red Light = 7, Speeding = 6, Seatbelt = 2) to compute realistic traffic danger points.
- **Statistical Surge Anomaly Detection**: Automated Z-Score outlier analysis ($Z \ge 1.5$) flags abnormal volume spikes (e.g., CRITICAL SPIKE at 16:00 rush hour).
- **Dual-Mode Geospatial Mapping**: Toggle between **KMeans Clustered Markers (with Centroid coordinates)** and **3D Hexagon Density Heatmap** using Pydeck.
- **Temporal-Categorical Intensity Matrix**: Cross-tabulation heatmap displaying infraction volume across all 24 hours.
- **Executive Data Export**: One-click download of filtered analytical data and risk audit reports in CSV format.

---

## 5. Agile Documentation

### 5.1 Product Backlog (User Stories)
| ID | User Story | Priority | Status |
|----|------------|----------|--------|
| **US1** | As a traffic analyst, I want clean and structured violation data so I can analyze it accurately. | High | Completed |
| **US2** | As a planner, I want violations grouped by time (hour/day/month) to understand peak periods. | High | Completed |
| **US3** | As an enforcement officer, I want to detect violation hotspot locations using ML clustering. | High | Completed |
| **US4** | As a decision-maker, I want an interactive dashboard to easily explore patterns and insights. | High | Completed |
| **US5** | As a safety director, I want a weighted risk score and anomaly surge alerts for critical hours. | Medium | Completed |
| **US6** | As an engineer, I want a unified orchestrator and automated test suite to verify pipeline integrity. | Medium | Completed |

---

## 6. How to Run

### 6.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 6.2 Run Automated Tests
```bash
python -m unittest tests/test_pipeline.py -v
```

### 6.3 Execute the Analytics Pipeline
Run the unified pipeline orchestrator:
```bash
# Fast local execution (default)
python run_pipeline.py

# Optional: Generate fresh mock data
python run_pipeline.py --generate-data

# Optional: Run with Apache Spark engine
python run_pipeline.py --engine spark
```

### 6.4 Launch the Streamlit Dashboard
```bash
streamlit run dashboard/streamlit_dashboard.py
```
Open your browser at `http://localhost:8501` to access the Control Center.
