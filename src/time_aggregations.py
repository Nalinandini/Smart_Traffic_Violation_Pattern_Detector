from pyspark.sql import SparkSession
from pyspark.sql.functions import hour,dayofweek,month,year,col
import os

spark = SparkSession.builder.appName('agg').getOrCreate()
BASE = os.path.dirname(os.path.dirname(__file__))
INP = os.path.join(BASE,'data','cleaned_parquet')
OUTDIR = os.path.join(BASE,'data','aggregations')
df = spark.read.parquet(INP)
df = df.withColumn('hour_of_day', hour(col('timestamp_parsed'))).withColumn('day_of_week', dayofweek(col('timestamp_parsed'))).withColumn('month', month(col('timestamp_parsed'))).withColumn('year', year(col('timestamp_parsed')))
per_hour = df.groupBy('hour_of_day').count().orderBy('hour_of_day')
per_hour.show(10)
per_hour.write.mode('overwrite').parquet(os.path.join(OUTDIR,'per_hour'))
spark.stop()
