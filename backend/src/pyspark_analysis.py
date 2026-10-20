"""
pyspark_analysis.py
-------------------
PySpark processing pipeline for the crop production dataset.

Run this script independently with:
    python src/pyspark_analysis.py

Or through spark-submit:
    spark-submit src/pyspark_analysis.py

Outputs are saved to outputs/spark/ as CSV and Parquet files.
"""

import os
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "spark")
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "crop_production_1997_2025.csv")


def run_spark_pipeline(data_path: str = DATA_PATH, output_dir: str = OUTPUT_DIR) -> dict:
    """
    Execute the PySpark aggregation pipeline.

    Returns a dict with keys:
        success (bool), message (str), outputs (list), record_counts (dict)
    """
    result = {
        "success": False,
        "message": "",
        "outputs": [],
        "record_counts": {},
    }

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
        from pyspark.sql.types import DoubleType, IntegerType
    except ImportError:
        result["message"] = (
            "PySpark is not installed. Install with: pip install pyspark\n"
            "Java 8 or 11 must also be installed and JAVA_HOME set."
        )
        return result

    os.makedirs(output_dir, exist_ok=True)

    try:
        spark = (
            SparkSession.builder
            .appName("CropProductionAnalysis")
            .master("local[*]")
            .config("spark.driver.memory", "2g")
            .config("spark.sql.shuffle.partitions", "8")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("ERROR")

        # --- Load ---
        df = spark.read.csv(data_path, header=True, inferSchema=True)
        df = df.withColumn("Area", F.col("Area").cast(DoubleType()))
        df = df.withColumn("Production", F.col("Production").cast(DoubleType()))
        df = df.withColumn("Crop_Year", F.col("Crop_Year").cast(IntegerType()))

        # Drop rows with null Area (none exist, but defensive)
        df = df.filter(F.col("Area").isNotNull())

        total_records = df.count()
        result["record_counts"]["raw"] = total_records

        # --- Aggregation 1: By State ---
        state_agg = (
            df.filter(F.col("Production").isNotNull())
            .groupBy("State_Name")
            .agg(
                F.sum("Production").alias("Total_Production"),
                F.sum("Area").alias("Total_Area"),
                F.count("Production").alias("Record_Count"),
            )
            .orderBy(F.desc("Total_Production"))
        )
        state_out = os.path.join(output_dir, "state_aggregation.csv")
        state_agg.coalesce(1).write.mode("overwrite").option("header", True).csv(
            state_out + "_dir"
        )
        # Rename single partition to flat file
        _save_spark_to_csv(state_out + "_dir", state_out)
        result["outputs"].append(state_out)
        result["record_counts"]["state_agg"] = state_agg.count()

        # --- Aggregation 2: By Year ---
        year_agg = (
            df.filter(F.col("Production").isNotNull())
            .groupBy("Crop_Year")
            .agg(
                F.sum("Production").alias("Total_Production"),
                F.sum("Area").alias("Total_Area"),
                F.count("Production").alias("Record_Count"),
            )
            .orderBy("Crop_Year")
        )
        year_out = os.path.join(output_dir, "year_aggregation.csv")
        year_agg.coalesce(1).write.mode("overwrite").option("header", True).csv(
            year_out + "_dir"
        )
        _save_spark_to_csv(year_out + "_dir", year_out)
        result["outputs"].append(year_out)

        # --- Aggregation 3: By Crop ---
        crop_agg = (
            df.filter(F.col("Production").isNotNull())
            .groupBy("Crop")
            .agg(
                F.sum("Production").alias("Total_Production"),
                F.sum("Area").alias("Total_Area"),
                F.count("Production").alias("Record_Count"),
            )
            .orderBy(F.desc("Total_Production"))
        )
        crop_out = os.path.join(output_dir, "crop_aggregation.csv")
        crop_agg.coalesce(1).write.mode("overwrite").option("header", True).csv(
            crop_out + "_dir"
        )
        _save_spark_to_csv(crop_out + "_dir", crop_out)
        result["outputs"].append(crop_out)

        # --- Aggregation 4: By Season ---
        season_agg = (
            df.filter(F.col("Production").isNotNull())
            .groupBy("Season")
            .agg(
                F.sum("Production").alias("Total_Production"),
                F.sum("Area").alias("Total_Area"),
                F.count("Production").alias("Record_Count"),
            )
            .orderBy(F.desc("Total_Production"))
        )
        season_out = os.path.join(output_dir, "season_aggregation.csv")
        season_agg.coalesce(1).write.mode("overwrite").option("header", True).csv(
            season_out + "_dir"
        )
        _save_spark_to_csv(season_out + "_dir", season_out)
        result["outputs"].append(season_out)

        # --- Parquet output (state level) ---
        parquet_out = os.path.join(output_dir, "state_aggregation.parquet")
        state_agg.write.mode("overwrite").parquet(parquet_out)
        result["outputs"].append(parquet_out)

        spark.stop()

        result["success"] = True
        result["message"] = (
            "PySpark pipeline completed successfully. "
            "Outputs written to: " + output_dir
        )

    except Exception as e:
        result["message"] = "PySpark pipeline failed: " + str(e)

    return result


def _save_spark_to_csv(spark_dir: str, target_path: str):
    """Move the single CSV part file out of a Spark output directory."""
    import shutil, glob
    parts = glob.glob(os.path.join(spark_dir, "part-*.csv"))
    if parts:
        shutil.copy(parts[0], target_path)
    shutil.rmtree(spark_dir, ignore_errors=True)


def check_spark_outputs(output_dir: str = OUTPUT_DIR) -> dict:
    """Return which PySpark output files exist and their sizes."""
    files = [
        "state_aggregation.csv",
        "year_aggregation.csv",
        "crop_aggregation.csv",
        "season_aggregation.csv",
        "state_aggregation.parquet",
    ]
    status = {}
    for f in files:
        path = os.path.join(output_dir, f)
        if os.path.isdir(path):
            status[f] = {"exists": True, "type": "parquet_dir"}
        elif os.path.isfile(path):
            status[f] = {"exists": True, "size_kb": round(os.path.getsize(path) / 1024, 1)}
        else:
            status[f] = {"exists": False}
    return status


if __name__ == "__main__":
    print("Running PySpark pipeline...")
    result = run_spark_pipeline()
    print("Success:", result["success"])
    print("Message:", result["message"])
    for out in result["outputs"]:
        print("  Output:", out)
