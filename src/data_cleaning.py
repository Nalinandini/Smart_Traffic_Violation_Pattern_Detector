from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
import os
import sys

def clean_data_spark(input_path, output_dir):
    spark = SparkSession.builder.appName('TrafficDataCleaning').getOrCreate()
    df = spark.read.option("header", True).csv(input_path)
    
    # Strip spaces from column headers
    for c in df.columns:
        df = df.withColumnRenamed(c, c.strip())
        
    df_cleaned = df.select(
        col("Violation_Id").alias("violation_id"),
        to_timestamp(col("Timestamp"), "yyyy-MM-dd HH:mm:ss").alias("timestamp_parsed"),
        col("Violation_Type").alias("violation_type"),
        col("Location").alias("location")
    )
    
    df_cleaned = df_cleaned.filter(
        col("violation_id").isNotNull() & 
        col("timestamp_parsed").isNotNull() & 
        col("location").isNotNull()
    )
    
    df_cleaned.write.mode("overwrite").parquet(output_dir)
    print("[SUCCESS] [Spark] Data cleaning completed successfully!")
    df_cleaned.show(5, truncate=False)
    spark.stop()

def clean_data_pandas(input_path, output_dir):
    print("[WARNING] Spark failed or is not configured. Running Pandas fallback...")
    import pandas as pd
    
    df = pd.read_csv(input_path)
    df.columns = [c.strip() for c in df.columns]
    
    df_cleaned = pd.DataFrame()
    df_cleaned["violation_id"] = df["Violation_Id"]
    df_cleaned["timestamp_parsed"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    df_cleaned["violation_type"] = df["Violation_Type"]
    df_cleaned["location"] = df["Location"]
    
    df_cleaned = df_cleaned.dropna(subset=["violation_id", "timestamp_parsed", "location"])
    
    # Ensure directory exists and clean it
    os.makedirs(output_dir, exist_ok=True)
    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
                
    # Save as parquet file inside directory
    output_file = os.path.join(output_dir, "part-0.parquet")
    df_cleaned.to_parquet(output_file, index=False)
    print(f"[SUCCESS] [Pandas] Data cleaning completed successfully! Output saved at {output_file}")
    print(df_cleaned.head(5))

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'data', 'input', 'traffic_violations.csv')
    output_dir = os.path.join(base_dir, 'data', 'cleaned_parquet')
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found. Please run src/generate_mock_data.py first.")
        sys.exit(1)
        
    try:
        clean_data_spark(input_path, output_dir)
    except Exception as e:
        print(f"Spark exception encountered: {str(e)}")
        clean_data_pandas(input_path, output_dir)

if __name__ == "__main__":
    main()
