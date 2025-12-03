from pyspark.sql import SparkSession
from pyspark.sql.functions import split,col,floor
import os
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans

spark = SparkSession.builder.appName('hotspot').getOrCreate()
BASE = os.path.dirname(os.path.dirname(__file__))
INP = os.path.join(BASE,'data','cleaned_parquet')
df = spark.read.parquet(INP)
geo = df.filter(col('location').rlike('^-?\\d+\\.\\d+,-?\\d+\\.\\d+$'))
geo = geo.withColumn('lat', split(col('location'),',').getItem(0).cast('double')).withColumn('lon', split(col('location'),',').getItem(1).cast('double'))
ga = geo.withColumn('grid_x',(floor(col('lat')*100)).cast('int')).withColumn('grid_y',(floor(col('lon')*100)).cast('int'))
ga = ga.withColumn('grid_id', col('grid_x').cast('string') + '_' + col('grid_y').cast('string'))
grid_counts = ga.groupBy('grid_id').count().orderBy(col('count').desc())
grid_counts.show(20)
# optional clustering
assembler = VectorAssembler(inputCols=['lat','lon'],outputCol='features')
vec = assembler.transform(geo).select('violation_id','features')
kmeans = KMeans(k=5, seed=42, featuresCol='features')
model = kmeans.fit(vec)
clusters = model.transform(vec)
clusters.groupBy('prediction').count().show()
spark.stop()
