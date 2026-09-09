from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col, floor
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
import os
import sys

def run_spark(inp_path, output_dir):
    spark = SparkSession.builder.appName('hotspot').getOrCreate()
    df = spark.read.parquet(inp_path)
    
    geo = df.filter(col('location').rlike('^-?\\d+\\.\\d+,-?\\d+\\.\\d+$'))
    geo = geo.withColumn('lat', split(col('location'), ',').getItem(0).cast('double'))\
             .withColumn('lon', split(col('location'), ',').getItem(1).cast('double'))
             
    ga = geo.withColumn('grid_x', (floor(col('lat') * 100)).cast('int'))\
            .withColumn('grid_y', (floor(col('lon') * 100)).cast('int'))
            
    ga = ga.withColumn('grid_id', col('grid_x').cast('string') + '_' + col('grid_y').cast('string'))
    
    grid_counts = ga.groupBy('grid_id').count().orderBy(col('count').desc())
    print("Top Grids (Spark):")
    grid_counts.show(10)
    
    # Save grid counts
    grid_counts.coalesce(1).write.mode("overwrite").option("header", True).csv(os.path.join(output_dir, "grid_counts_csv"))
    
    # Clustering
    assembler = VectorAssembler(inputCols=['lat', 'lon'], outputCol='features')
    vec = assembler.transform(geo).select('violation_id', 'lat', 'lon', 'features')
    kmeans = KMeans(k=5, seed=42, featuresCol='features')
    model = kmeans.fit(vec)
    clusters = model.transform(vec)
    
    print("Cluster Sizes (Spark):")
    clusters.groupBy('prediction').count().show()
    
    # Save clustered coordinates
    clusters.select('violation_id', 'lat', 'lon', 'prediction')\
            .coalesce(1).write.mode("overwrite").option("header", True).csv(os.path.join(output_dir, "hotspot_clusters_csv"))
            
    spark.stop()
    print("[SUCCESS] [Spark] Hotspot detection completed!")

def custom_kmeans(points, k, max_iters=100, seed=42):
    import numpy as np
    np.random.seed(seed)
    # Initialize centroids randomly from points
    centroids = points[np.random.choice(points.shape[0], k, replace=False)]
    for _ in range(max_iters):
        # Compute distances from points to centroids
        distances = np.linalg.norm(points[:, np.newaxis] - centroids, axis=2)
        # Assign points to closest centroid
        labels = np.argmin(distances, axis=1)
        # Recompute centroids
        new_centroids = []
        for j in range(k):
            members = points[labels == j]
            if len(members) > 0:
                new_centroids.append(members.mean(axis=0))
            else:
                new_centroids.append(centroids[j])
        new_centroids = np.array(new_centroids)
        
        if np.allclose(centroids, new_centroids, atol=1e-5):
            break
        centroids = new_centroids
    return labels

def run_pandas(inp_path, output_dir):
    print("[WARNING] Spark failed or is not configured. Running Pandas/NumPy fallback...")
    import pandas as pd
    import numpy as np
    
    df = pd.read_parquet(inp_path)
    
    # Regex filter for coord pairs
    coord_pattern = r'^-?\d+\.\d+,-?\d+\.\d+$'
    geo_df = df[df['location'].str.match(coord_pattern, na=False)].copy()
    
    # Split coordinates
    coords = geo_df['location'].str.split(',', expand=True)
    geo_df['lat'] = coords[0].astype(float)
    geo_df['lon'] = coords[1].astype(float)
    
    # Grid analysis
    geo_df['grid_x'] = np.floor(geo_df['lat'] * 100).astype(int)
    geo_df['grid_y'] = np.floor(geo_df['lon'] * 100).astype(int)
    geo_df['grid_id'] = geo_df['grid_x'].astype(str) + '_' + geo_df['grid_y'].astype(str)
    
    grid_counts = geo_df.groupby('grid_id').size().reset_index(name='count')
    grid_counts = grid_counts.sort_values(by='count', ascending=False)
    
    print("Top Grids (Pandas):")
    print(grid_counts.head(10))
    
    # Save grid counts
    grid_dir = os.path.join(output_dir, "grid_counts_csv")
    os.makedirs(grid_dir, exist_ok=True)
    for f in os.listdir(grid_dir):
        try: os.remove(os.path.join(grid_dir, f))
        except: pass
    grid_counts.to_csv(os.path.join(grid_dir, "part-0.csv"), index=False)
    
    # Run KMeans clustering
    points = geo_df[['lat', 'lon']].values
    if len(points) >= 5:
        labels = custom_kmeans(points, k=5)
        geo_df['prediction'] = labels
    else:
        geo_df['prediction'] = 0
        
    print("Cluster Sizes (Pandas):")
    print(geo_df.groupby('prediction').size())
    
    # Save clustered coordinates
    clusters_dir = os.path.join(output_dir, "hotspot_clusters_csv")
    os.makedirs(clusters_dir, exist_ok=True)
    for f in os.listdir(clusters_dir):
        try: os.remove(os.path.join(clusters_dir, f))
        except: pass
        
    output_cols = ['violation_id', 'lat', 'lon', 'prediction']
    if 'violation_type' in geo_df.columns:
        output_cols.append('violation_type')
    geo_df[output_cols].to_csv(os.path.join(clusters_dir, "part-0.csv"), index=False)

    # Compute and save cluster centroids summary
    centroid_list = []
    for c_id, group in geo_df.groupby('prediction'):
        top_v = group['violation_type'].mode()[0] if ('violation_type' in group.columns and len(group['violation_type'].mode()) > 0) else 'General'
        centroid_list.append({
            'cluster_id': int(c_id),
            'center_lat': round(float(group['lat'].mean()), 6),
            'center_lon': round(float(group['lon'].mean()), 6),
            'violation_count': len(group),
            'dominant_violation': top_v
        })
    centroids_df = pd.DataFrame(centroid_list)
    centroids_dir = os.path.join(output_dir, "cluster_centroids_csv")
    os.makedirs(centroids_dir, exist_ok=True)
    for f in os.listdir(centroids_dir):
        try: os.remove(os.path.join(centroids_dir, f))
        except: pass
    centroids_df.to_csv(os.path.join(centroids_dir, "part-0.csv"), index=False)
    print(f"[SUCCESS] [Pandas] Hotspot detection and centroids completed! Output saved in {output_dir}")

def main():
    BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INP = os.path.join(BASE, 'data', 'cleaned_parquet')
    OUTDIR = os.path.join(BASE, 'data', 'output')
    
    if not os.path.exists(INP):
        print(f"Error: Cleaned input Parquet path {INP} not found.")
        sys.exit(1)
        
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
