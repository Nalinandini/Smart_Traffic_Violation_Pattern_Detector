import csv
import random
from datetime import datetime, timedelta
import os

def generate_mock_data():
    # Set seed for reproducibility
    random.seed(42)
    
    # Coordinates of some "hotspot" intersections in NYC area
    hotspots = [
        (40.7580, -73.9855),  # Times Square
        (40.7295, -73.9965),  # Washington Square Park
        (40.7484, -73.9857),  # Empire State Building
        (40.7061, -74.0088),  # Wall Street
        (40.8075, -73.9626)   # Columbia University Area
    ]
    
    violation_types = [
        "Speeding", "Red Light Violation", "Reckless Driving", 
        "Seatbelt Violation", "Using Mobile Phone", "Illegal Turn", "DUI"
    ]
    
    # Make sure target directory exists
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "data", "input")
    os.makedirs(target_dir, exist_ok=True)
    
    output_file = os.path.join(target_dir, "traffic_violations.csv")
    
    print(f"Generating mock traffic data at {output_file}...")
    
    start_date = datetime.now() - timedelta(days=60)
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header row
        writer.writerow(["Violation_Id", "Timestamp", "Violation_Type", "Location"])
        
        # Generate 1500 records
        for i in range(1, 1501):
            violation_id = f"V{i:04d}"
            
            # Select random timestamp with peak hour probability
            day_offset = random.randint(0, 60)
            
            # Weighted hour selection: high traffic / peaks around 8-9 AM and 5-6 PM
            hour_weights = [5, 5, 5, 5, 5, 10, 20, 50, 80, 70, 40, 45, 50, 45, 50, 75, 90, 85, 60, 40, 25, 15, 10, 5]
            hour = random.choices(range(24), weights=hour_weights)[0]
            
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            dt = start_date + timedelta(days=day_offset)
            dt = dt.replace(hour=hour, minute=minute, second=second)
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Choose a random violation type
            v_type = random.choice(violation_types)
            
            # Pick a hotspot and add a small random offset to simulate nearby points
            hotspot = random.choice(hotspots)
            lat = hotspot[0] + random.normalvariate(0, 0.005)
            lon = hotspot[1] + random.normalvariate(0, 0.005)
            location_str = f"{lat:.6f},{lon:.6f}"
            
            writer.writerow([violation_id, timestamp_str, v_type, location_str])
            
    print("Mock traffic data generation complete!")

if __name__ == "__main__":
    generate_mock_data()
