import os
import sys
import time
import argparse

# Add workspace directory to python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configure stdout/stderr for utf-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from src.generate_mock_data import generate_mock_data
from src.data_cleaning import main as run_cleaning
from src.time_aggregations import main as run_time_aggregations
from src.week3_time_type_aggregation import main as run_time_type_aggregation
from src.week4_location_aggregation import main as run_location_aggregation
from src.hotspot_detection import main as run_hotspot_detection
from src.risk_and_anomaly import run_risk_and_anomaly

def execute_pipeline(generate_mock=False, progress_callback=None):
    """
    Executes the complete traffic pattern analytics pipeline end-to-end.
    
    Args:
        generate_mock (bool): Whether to generate new mock traffic records.
        progress_callback (callable): Optional callback(step_idx, total_steps, message).
    """
    total_steps = 7 if generate_mock else 6
    current_step = 0
    start_time = time.time()
    
    def log_progress(msg):
        nonlocal current_step
        current_step += 1
        elapsed = time.time() - start_time
        print(f"\n[{current_step}/{total_steps}] [+{elapsed:.1f}s] {msg}", flush=True)
        if progress_callback:
            progress_callback(current_step, total_steps, msg)

    print("=" * 65, flush=True)
    print("[TRAFFIC-DETECTOR] PIPELINE ORCHESTRATOR STARTED", flush=True)
    print("=" * 65, flush=True)
    
    input_file = os.path.join(BASE_DIR, "data", "input", "traffic_violations.csv")
    
    # Step 1: Mock Data Generation (if requested or input is missing)
    if generate_mock or not os.path.exists(input_file):
        log_progress("Generating Synthetic Traffic Violation Dataset...")
        generate_mock_data()
    else:
        print("[INFO] Using existing input dataset: " + input_file, flush=True)

    # Step 2: Data Cleaning & Parquet Transformation
    log_progress("Cleaning & Parsing Raw Ingestion Records...")
    run_cleaning()
    
    # Step 3: Temporal Aggregations (Hourly / Day)
    log_progress("Computing Hourly & Temporal Aggregations...")
    run_time_aggregations()
    
    # Step 4: Time-Type Aggregations
    log_progress("Aggregating Violations by Day, Hour, and Category...")
    run_time_type_aggregation()
    
    # Step 5: Location Aggregations & High-Frequency Corridor Ranking
    log_progress("Calculating Location-Specific Violation Rankings...")
    run_location_aggregation()
    
    # Step 6: Geospatial Grid Binning & Machine Learning Clustering
    log_progress("Running Spatial Grid Binning & Hotspot Clustering...")
    run_hotspot_detection()
    
    # Step 7: Risk Scoring & Temporal Anomaly Detection
    log_progress("Computing Weighted Risk Index & Spike Anomaly Alerts...")
    run_risk_and_anomaly()
    
    total_time = time.time() - start_time
    print("\n" + "=" * 65, flush=True)
    print(f"[SUCCESS] PIPELINE EXECUTION COMPLETED IN {total_time:.2f} SECONDS", flush=True)
    print("=" * 65, flush=True)
    return True

def main():
    parser = argparse.ArgumentParser(description="Smart Traffic Violation Pattern Detector - Pipeline Orchestrator")
    parser.add_argument("--generate-data", action="store_true", help="Generate fresh synthetic dataset before execution")
    parser.add_argument("--all", action="store_true", help="Run entire pipeline including data generation")
    parser.add_argument("--engine", choices=["auto", "spark", "pandas"], default="pandas", 
                        help="Processing engine: pandas (default, fast local execution) or spark (big data framework)")
    
    args = parser.parse_args()
    if args.engine != "auto":
        os.environ["TRAFFIC_ENGINE"] = args.engine
        
    gen_data = args.generate_data or args.all
    execute_pipeline(generate_mock=gen_data)

if __name__ == "__main__":
    main()
