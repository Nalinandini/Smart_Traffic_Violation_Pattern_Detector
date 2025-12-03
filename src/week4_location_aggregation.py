# week4_location_aggregation.py

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("LocationAggregation").getOrCreate()

df = spark.read.option("header", True).csv("../data/input/traffic_violations.csv", inferSchema=True)

violations_per_location = df.groupBy("Location").count().orderBy("count", ascending=False)

top_n = 10
top_locations = violations_per_location.limit(top_n)

output_dir = "../data/output/"

# ✅ Save only as CSV to avoid native Hadoop errors
violations_per_location.coalesce(1).write.mode("overwrite").option("header", True).csv(output_dir + "violations_per_location_csv")
top_locations.coalesce(1).write.mode("overwrite").option("header", True).csv(output_dir + "top_locations_csv")

print("✅ Week 4 Location Aggregations Completed Successfully! (CSV output)")

spark.stop()