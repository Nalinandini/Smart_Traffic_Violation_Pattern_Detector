from pyspark.sql import SparkSession
from pyspark.sql.functions import hour, dayofweek, month, year, col
import os
import sys

def run_spark(inp_path, out_dir):
    spark = SparkSession.builder.appName('agg').getOrCreate()
    df = spark.read.parquet(inp_path)
    df = df.withColumn('hour_of_day', hour(col('timestamp_parsed')))\
           .withColumn('day_of_week', dayofweek(col('timestamp_parsed')))\
           .withColumn('month', month(col('timestamp_parsed')))\
           .withColumn('year', year(col('timestamp_parsed')))
           
    per_hour = df.groupBy('hour_of_day').count().orderBy('hour_of_day')
    per_hour.show(10)
    per_hour.write.mode('overwrite').parquet(os.path.join(out_dir, 'per_hour'))
    spark.stop()
    print("[SUCCESS] [Spark] Time aggregations completed!")

def run_pandas(inp_path, out_dir):
    print("[WARNING] Spark failed or is not configured. Running Pandas fallback...")
    import pandas as pd
    
    # Read Parquet directory/file
    df = pd.read_parquet(inp_path)
    
    # Extract time metrics
    df['hour_of_day'] = df['timestamp_parsed'].dt.hour
    df['day_of_week'] = df['timestamp_parsed'].dt.dayofweek + 1 # Spark dayofweek is 1-indexed (Sunday=1, Monday=2...)
    df['month'] = df['timestamp_parsed'].dt.month
    df['year'] = df['timestamp_parsed'].dt.year
    
    # Group by hour of day
    per_hour = df.groupby('hour_of_day').size().reset_index(name='count')
    per_hour = per_hour.sort_values('hour_of_day')
    
    print(per_hour.head(10))
    
    target_dir = os.path.join(out_dir, 'per_hour')
    os.makedirs(target_dir, exist_ok=True)
    # Clean output dir
    for f in os.listdir(target_dir):
        f_path = os.path.join(target_dir, f)
        if os.path.isfile(f_path):
            try: os.remove(f_path)
            except: pass
            
    per_hour.to_parquet(os.path.join(target_dir, 'part-0.parquet'), index=False)
    print(f"[SUCCESS] [Pandas] Time aggregations completed! Saved to {target_dir}")

def main():
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INP = os.path.join(BASE, 'data', 'cleaned_parquet')
    OUTDIR = os.path.join(BASE, 'data', 'aggregations')
    
    if os.environ.get("TRAFFIC_ENGINE", "").lower() == "pandas":
        run_pandas(INP, OUTDIR)
        return
        
    try:
        run_spark(INP, OUTDIR)
    except Exception as e:
        print(f"Spark exception encountered: {str(e)}")
        run_pandas(INP, OUTDIR)

if __name__ == "__main__":
    main()
