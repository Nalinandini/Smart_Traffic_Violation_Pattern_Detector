from pyspark.sql import SparkSession
import os
import sys

def run_spark(input_path, output_dir):
    spark = SparkSession.builder.appName("LocationAggregation").getOrCreate()
    df = spark.read.option("header", True).csv(input_path, inferSchema=True)
    violations_per_location = df.groupBy("Location").count().orderBy("count", ascending=False)
    
    top_n = 10
    top_locations = violations_per_location.limit(top_n)
    
    violations_per_location.coalesce(1).write.mode("overwrite").option("header", True).csv(os.path.join(output_dir, "violations_per_location_csv"))
    top_locations.coalesce(1).write.mode("overwrite").option("header", True).csv(os.path.join(output_dir, "top_locations_csv"))
    
    print("[SUCCESS] [Spark] Location aggregations completed!")
    spark.stop()

def run_pandas(input_path, output_dir):
    print("[WARNING] Spark failed or is not configured. Running Pandas fallback...")
    import pandas as pd
    
    df = pd.read_csv(input_path)
    # Strip spaces from column headers
    df.columns = [c.strip() for c in df.columns]
    
    violations_per_location = df.groupby('Location').size().reset_index(name='count')
    violations_per_location = violations_per_location.sort_values(by='count', ascending=False)
    
    top_locations = violations_per_location.head(10)
    
    # Save violations_per_location
    loc_dir = os.path.join(output_dir, "violations_per_location_csv")
    os.makedirs(loc_dir, exist_ok=True)
    for f in os.listdir(loc_dir):
        try: os.remove(os.path.join(loc_dir, f))
        except: pass
    violations_per_location.to_csv(os.path.join(loc_dir, "part-0.csv"), index=False)
    
    # Save top_locations
    top_dir = os.path.join(output_dir, "top_locations_csv")
    os.makedirs(top_dir, exist_ok=True)
    for f in os.listdir(top_dir):
        try: os.remove(os.path.join(top_dir, f))
        except: pass
    top_locations.to_csv(os.path.join(top_dir, "part-0.csv"), index=False)
    
    print(f"[SUCCESS] [Pandas] Location aggregations completed! Saved in {output_dir}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "input", "traffic_violations.csv")
    output_dir = os.path.join(base_dir, "data", "output")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)
        
    try:
        run_spark(input_path, output_dir)
    except Exception as e:
        print(f"Spark exception encountered: {str(e)}")
        run_pandas(input_path, output_dir)

if __name__ == "__main__":
    main()