import os
import sys
import numpy as np
import pandas as pd

# Default severity weighting dictionary
SEVERITY_WEIGHTS = {
    "DUI": 10,
    "Reckless Driving": 8,
    "Red Light Violation": 7,
    "Speeding": 6,
    "Using Mobile Phone": 4,
    "Illegal Turn": 3,
    "Seatbelt Violation": 2
}

def get_severity_weight(violation_type):
    """Return severity weight for a given violation type."""
    return SEVERITY_WEIGHTS.get(str(violation_type).strip(), 3)

def compute_risk_and_anomalies_pandas(cleaned_parquet_path, output_dir):
    """
    Computes risk indices, hourly anomaly scores, and location risk profiles
    using Pandas and NumPy.
    """
    print("[INFO] Computing Risk Index and Anomaly Scores with Pandas...")
    
    # Read cleaned data
    df = pd.read_parquet(cleaned_parquet_path)
    if 'timestamp_parsed' not in df.columns:
        df['timestamp_parsed'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
    df['Hour'] = df['timestamp_parsed'].dt.hour
    df['DayOfWeek'] = df['timestamp_parsed'].dt.strftime('%A')
    df['severity_score'] = df['violation_type'].map(lambda vt: get_severity_weight(vt))
    
    # ---------------- 1. Hourly Risk & Anomaly Detection ----------------
    hourly_group = df.groupby('Hour')
    hourly_risk = hourly_group.agg(
        violation_count=('violation_id', 'count'),
        total_risk_score=('severity_score', 'sum'),
        avg_risk_score=('severity_score', 'mean')
    ).reset_index()
    
    # Find most common violation per hour
    mode_violations = df.groupby(['Hour', 'violation_type']).size().reset_index(name='v_count')
    top_per_hour = mode_violations.sort_values(['Hour', 'v_count'], ascending=[True, False]).drop_duplicates('Hour')
    hourly_risk = hourly_risk.merge(top_per_hour[['Hour', 'violation_type']], on='Hour', how='left')
    hourly_risk.rename(columns={'violation_type': 'primary_violation'}, inplace=True)
    
    # Statistical Anomaly Detection (Z-Score on volume)
    mean_volume = hourly_risk['violation_count'].mean()
    std_volume = hourly_risk['violation_count'].std()
    
    if std_volume > 0:
        hourly_risk['z_score'] = ((hourly_risk['violation_count'] - mean_volume) / std_volume).round(2)
    else:
        hourly_risk['z_score'] = 0.0
        
    def classify_anomaly(z):
        if z >= 2.0:
            return "CRITICAL SPIKE"
        elif z >= 1.5:
            return "ELEVATED SURGE"
        elif z <= -1.5:
            return "UNUSUALLY LOW"
        return "NORMAL"
        
    hourly_risk['anomaly_level'] = hourly_risk['z_score'].apply(classify_anomaly)
    hourly_risk['is_anomaly'] = hourly_risk['z_score'].abs() >= 1.5
    
    # ---------------- 2. Location-Based Risk Profile ----------------
    loc_group = df.groupby('location')
    loc_risk = loc_group.agg(
        total_violations=('violation_id', 'count'),
        total_risk_score=('severity_score', 'sum'),
        avg_risk_score=('severity_score', 'mean'),
        high_severity_count=('severity_score', lambda s: (s >= 7).sum())
    ).reset_index()
    loc_risk = loc_risk.sort_values(by='total_risk_score', ascending=False)
    
    # ---------------- 3. Time-Type Heatmap Matrix ----------------
    time_type_matrix = df.groupby(['Hour', 'violation_type']).agg(
        violation_count=('violation_id', 'count'),
        total_risk_score=('severity_score', 'sum')
    ).reset_index()
    
    # Save outputs
    save_output_dataframe(hourly_risk, os.path.join(output_dir, "hourly_risk_anomaly_csv"))
    save_output_dataframe(loc_risk, os.path.join(output_dir, "location_risk_csv"))
    save_output_dataframe(time_type_matrix, os.path.join(output_dir, "time_type_matrix_csv"))
    
    print("[SUCCESS] Risk & Anomaly scoring completed successfully!")
    print(f"Top 3 High-Risk Hours:\n{hourly_risk.sort_values(by='total_risk_score', ascending=False).head(3)[['Hour', 'total_risk_score', 'anomaly_level']]}")
    return hourly_risk, loc_risk

def save_output_dataframe(df, target_dir):
    """Save dataframe as part-0.csv inside target directory."""
    os.makedirs(target_dir, exist_ok=True)
    for f in os.listdir(target_dir):
        fp = os.path.join(target_dir, f)
        if os.path.isfile(fp):
            try:
                os.remove(fp)
            except Exception:
                pass
    df.to_csv(os.path.join(target_dir, "part-0.csv"), index=False)

def run_risk_and_anomaly(cleaned_parquet_path=None, output_dir=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if cleaned_parquet_path is None:
        cleaned_parquet_path = os.path.join(base_dir, "data", "cleaned_parquet")
    if output_dir is None:
        output_dir = os.path.join(base_dir, "data", "output")
        
    if not os.path.exists(cleaned_parquet_path):
        raise FileNotFoundError(f"Cleaned parquet not found at: {cleaned_parquet_path}")
        
    return compute_risk_and_anomalies_pandas(cleaned_parquet_path, output_dir)

if __name__ == "__main__":
    run_risk_and_anomaly()
