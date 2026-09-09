from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import os
import sys

def run_spark(input_path, output_path):
    spark = SparkSession.builder.appName("TimeTypeAggregation").getOrCreate()
    df = spark.read.option("header", True).csv(input_path)
    
    # 🔹 Ensure consistent column naming (remove spaces, if any)
    for col_name in df.columns:
        new_col_name = col_name.strip().replace(" ", "_")
        df = df.withColumnRenamed(col_name, new_col_name)
        
    print("[INFO] Columns in dataset:", df.columns)
    
    # 🔹 Convert Timestamp column to proper type if needed
    df = df.withColumn("Timestamp", F.to_timestamp("Timestamp", "yyyy-MM-dd HH:mm:ss"))
    
    # 🔹 Extract hour and day of week
    df = df.withColumn("Hour", F.hour("Timestamp"))
    df = df.withColumn("DayOfWeek", F.date_format("Timestamp", "EEEE"))
    
    # 🔹 Aggregate by DayOfWeek, Hour, and Violation_Type
    agg_df = (
        df.groupBy("DayOfWeek", "Hour", "Violation_Type")
          .count()
          .orderBy("DayOfWeek", "Hour")
    )
    
    agg_df.show(20, truncate=False)
    agg_df.coalesce(1).write.mode("overwrite").option("header", True).csv(output_path)
    print(f"\n[SUCCESS] [Spark] Aggregated results saved successfully at: {output_path}")
    spark.stop()

def run_pandas(input_path, output_path):
    print("[WARNING] Spark failed or is not configured. Running Pandas fallback...")
    import pandas as pd
    
    df = pd.read_csv(input_path)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    
    print("[INFO] Columns in dataset:", list(df.columns))
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    df = df.dropna(subset=['Timestamp'])
    
    # Extract Hour and Day of Week name
    df['Hour'] = df['Timestamp'].dt.hour
    df['DayOfWeek'] = df['Timestamp'].dt.strftime('%A')
    
    # Group by DayOfWeek, Hour, Violation_Type
    agg_df = df.groupby(['DayOfWeek', 'Hour', 'Violation_Type']).size().reset_index(name='count')
    
    # Sort by DayOfWeek and Hour
    # To sort days of week chronologically:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    agg_df['DayOfWeek'] = pd.Categorical(agg_df['DayOfWeek'], categories=day_order, ordered=True)
    agg_df = agg_df.sort_values(by=['DayOfWeek', 'Hour'])
    
    print(agg_df.head(20))
    
    # Save as CSV folder containing a part-0.csv file
    os.makedirs(output_path, exist_ok=True)
    for f in os.listdir(output_path):
        f_path = os.path.join(output_path, f)
        if os.path.isfile(f_path):
            try: os.remove(f_path)
            except: pass
            
    csv_file = os.path.join(output_path, 'part-0.csv')
    agg_df.to_csv(csv_file, index=False)
    print(f"\n[SUCCESS] [Pandas] Aggregated results saved successfully at: {csv_file}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "input", "traffic_violations.csv")
    output_path = os.path.join(base_dir, "data", "output", "time_type_aggregation.csv")
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)
        
    if os.environ.get("TRAFFIC_ENGINE", "").lower() == "pandas":
        run_pandas(input_path, output_path)
        return
        
    try:
        run_spark(input_path, output_path)
    except Exception as e:
        print(f"Spark exception encountered: {str(e)}")
        run_pandas(input_path, output_path)

if __name__ == "__main__":
    main()