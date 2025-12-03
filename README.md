# Smart Traffic Violation Pattern Detector

## 1. Project Overview
This project analyzes traffic violation data to detect **time-based patterns**, **location hotspots**, and visualize results using an **interactive Streamlit dashboard**.  
The goal is to help authorities understand **when** and **where** violations happen most often and improve road safety planning.

---

## 2. Tech Stack
| Component | Technology |
|-----------|------------|
| Programming Language | Python |
| Big Data Framework | Apache Spark (PySpark) |
| Visualization Dashboard | Streamlit |
| Data Formats | CSV, Parquet |

---

## 3. Dataset
- Input File Path: `data/input/traffic_violations.csv`
- Expected Columns:
  - `Timestamp`
  - `Violation_Type`
  - `Location` (latitude/longitude or place name)

---

## 4. Agile Documentation

### 4.1 Product Backlog (User Stories)
| ID | User Story |
|----|------------|
| US1 | As a traffic analyst, I want clean and structured violation data so I can analyze it accurately. |
| US2 | As a planner, I want violations grouped by time (hour/day/month) to understand peak periods. |
| US3 | As a city authority, I want to detect violation hotspot locations to increase enforcement. |
| US4 | As a decision-maker, I want a dashboard so I can easily explore patterns and insights. |

---

### 4.2 Milestones / Sprints

#### **Milestone 1 – Data Cleaning & Setup**
- Setup project environment and folder structure
- Open dataset, clean null values, format timestamp
- Save cleaned data as Parquet/CSV

#### **Milestone 2 – Time-Based Aggregations**
- Group violations by Hour / Day / Month / Year
- Identify peak hours
- Script: `src/time_aggregations.py`

#### **Milestone 3 – Violation Type & Location Analysis**
- Group violations based on `Violation_Type`
- Aggregate by location & detect hotspots using clustering (KMeans)
- Generate time-type combinations
- Scripts:  
  `src/week3_time_type_aggregation.py`  
  `src/week4_location_aggregation.py`  
  `src/hotspot_detection.py`

#### **Milestone 4 – Dashboard & Final Integration**
- Display charts for:
  - Violations per hour/day
  - Violations per category
  - Hotspot map visualization
- Script: `dashboard/streamlit_dashboard.py`
- Added MIT License & Agile Documentation
- Uploaded project to GitHub

---

## 5. How to Run

### 5.1 Install Dependencies
```bash
pip install pyspark streamlit pandas
