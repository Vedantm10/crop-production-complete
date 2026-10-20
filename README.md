# Crop Production Trends and Agricultural Productivity Analysis

## Project Structure

- backend/: Python API and Streamlit application
- frontend/: Next.js and React analytics dashboard
- bigdata/scripts/: Hadoop MapReduce and PySpark scripts
- bigdata/results/: Generated Big Data analysis outputs
- bigdata/docs/: Big Data setup and usage documentation

## Technologies

- Python, Pandas, FastAPI, Streamlit
- Next.js, React, TypeScript
- Hadoop HDFS, Hadoop MapReduce
- Apache Spark / PySpark

## Big Data Environment

Hadoop and PySpark are configured in Ubuntu on WSL.
The original dataset is stored in the backend data directory and is also available in HDFS.

## Running the Backend

Activate the backend virtual environment and run the FastAPI server from the backend directory.

## Running the Frontend

Run npm run dev from the frontend directory.
