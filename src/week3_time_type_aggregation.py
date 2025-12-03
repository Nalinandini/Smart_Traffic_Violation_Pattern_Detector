from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Initialize Spark Session
spark = SparkSession.builder.appName("TimeTypeAggregation").getOrCreate()

# Load dataset
input_path = r"C:\Users\ASUS\OneDrive\Documents\Smart_Traffic _Violation _Pattern_Detector\data\input\traffic_violations.csv"
df = spark.read.option("header", True).csv(input_path)

# 🔹 Ensure consistent column naming (remove spaces, if any)
for col_name in df.columns:
    new_col_name = col_name.strip().replace(" ", "_")
    df = df.withColumnRenamed(col_name, new_col_name)

# 🔹 Confirm columns (for debugging)
print("✅ Columns in dataset:", df.columns)

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
# Save aggregated result
output_path = "../data/output/time_type_aggregation.csv"
agg_df.coalesce(1).write.mode("overwrite").option("header", True).csv(output_path)


print(f"\n✅ Aggregated results saved successfully at: {output_path}")