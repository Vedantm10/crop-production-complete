from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = (
    SparkSession.builder
    .appName("CropProductionHDFSTest")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

path = "hdfs:///user/vedant/crop/input/crop_production_1997_2025.csv"

try:
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(path)
    )

    print("\n--- Dataset Schema ---")
    df.printSchema()

    print("\n--- First 5 Rows ---")
    df.show(5, truncate=False)

    print("\n--- Total Row Count ---")
    print(df.count())

    print("\n--- Distinct Crops ---")
    print(df.select("Crop").distinct().count())

    print("\nSUCCESS: PySpark read the dataset from HDFS.")

finally:
    spark.stop()
