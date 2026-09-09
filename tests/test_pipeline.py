import os
import sys
import tempfile
import unittest
import pandas as pd
import numpy as np

# Ensure root directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.generate_mock_data import generate_mock_data
from src.risk_and_anomaly import get_severity_weight, compute_risk_and_anomalies_pandas
from src.hotspot_detection import custom_kmeans

class TestTrafficPipeline(unittest.TestCase):

    def test_mock_data_generation(self):
        """Verify mock data generation produces non-empty CSV with expected schema."""
        target_csv = os.path.join(BASE_DIR, "data", "input", "traffic_violations.csv")
        generate_mock_data()
        self.assertTrue(os.path.exists(target_csv), "Generated mock CSV should exist")
        
        df = pd.read_csv(target_csv)
        expected_cols = {"Violation_Id", "Timestamp", "Violation_Type", "Location"}
        self.assertTrue(expected_cols.issubset(set(df.columns)), f"Columns missing from mock data: {df.columns}")
        self.assertGreaterEqual(len(df), 500, f"Expected at least 500 records, got {len(df)}")

    def test_severity_weighting(self):
        """Verify violation severity weights are assigned correctly."""
        self.assertEqual(get_severity_weight("DUI"), 10)
        self.assertEqual(get_severity_weight("Reckless Driving"), 8)
        self.assertEqual(get_severity_weight("Red Light Violation"), 7)
        self.assertEqual(get_severity_weight("Speeding"), 6)
        self.assertEqual(get_severity_weight("Using Mobile Phone"), 4)
        self.assertEqual(get_severity_weight("Illegal Turn"), 3)
        self.assertEqual(get_severity_weight("Seatbelt Violation"), 2)
        self.assertEqual(get_severity_weight("Unknown Violation"), 3)  # Default fallback

    def test_custom_kmeans(self):
        """Verify custom NumPy KMeans partitions data into k clusters."""
        np.random.seed(42)
        pts1 = np.random.normal(loc=[40.7, -74.0], scale=0.01, size=(50, 2))
        pts2 = np.random.normal(loc=[40.8, -73.9], scale=0.01, size=(50, 2))
        pts = np.vstack([pts1, pts2])
        
        labels = custom_kmeans(pts, k=2, max_iters=50, seed=42)
        self.assertEqual(len(labels), 100)
        self.assertTrue(set(np.unique(labels)).issubset({0, 1}))

    def test_risk_and_anomaly_calculations(self):
        """Verify risk computation and anomaly score calculation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            sample_df = pd.DataFrame({
                "violation_id": [f"V{i:04d}" for i in range(100)],
                "timestamp_parsed": pd.date_range("2026-01-01", periods=100, freq="h"),
                "violation_type": ["DUI" if i % 2 == 0 else "Seatbelt Violation" for i in range(100)],
                "location": ["40.7580,-73.9855" for _ in range(100)]
            })
            
            temp_pq = os.path.join(tmp_dir, "part-0.parquet")
            sample_df.to_parquet(temp_pq, index=False)
            
            out_dir = os.path.join(tmp_dir, "output")
            hourly_risk, loc_risk = compute_risk_and_anomalies_pandas(temp_pq, out_dir)
            
            self.assertIn("total_risk_score", hourly_risk.columns)
            self.assertIn("anomaly_level", hourly_risk.columns)
            self.assertIn("z_score", hourly_risk.columns)
            self.assertEqual(len(loc_risk), 1)
            self.assertEqual(loc_risk.iloc[0]["total_violations"], 100)

    def test_pipeline_outputs_exist(self):
        """Verify all expected output directories and CSV part files exist."""
        data_output = os.path.join(BASE_DIR, "data", "output")
        required_folders = [
            "hotspot_clusters_csv",
            "cluster_centroids_csv",
            "hourly_risk_anomaly_csv",
            "location_risk_csv",
            "time_type_matrix_csv",
            "time_type_aggregation.csv"
        ]
        for folder in required_folders:
            folder_path = os.path.join(data_output, folder)
            self.assertTrue(os.path.exists(folder_path), f"Expected output directory {folder} missing")
            csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
            self.assertGreater(len(csv_files), 0, f"No CSV file found in {folder_path}")

if __name__ == "__main__":
    unittest.main()
