"""
hdfs_utils.py
-------------
Hadoop HDFS integration utilities.

This module provides:
  - Commands to create HDFS directories, upload the dataset, and verify outputs.
  - A status checker that reports whether HDFS is reachable.
  - Functions that the Streamlit dashboard can call to display HDFS status.

HDFS is NOT required for the dashboard to run. When HDFS is unavailable,
the dashboard operates entirely on local files and clearly labels results
as "Local Processing".
"""

import subprocess
import os
import shutil

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "crop_production_1997_2025.csv"
)
HDFS_BASE = "/user/crop_project"
HDFS_INPUT = HDFS_BASE + "/input"
HDFS_OUTPUT = HDFS_BASE + "/output"
HDFS_MAPREDUCE_OUTPUT = HDFS_BASE + "/mapreduce_output"


def _run(cmd: list) -> dict:
    """Run a shell command and return stdout, stderr, return_code."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        return {
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
        }
    except FileNotFoundError:
        return {"stdout": "", "stderr": "hdfs command not found", "returncode": -1}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out", "returncode": -1}


def check_hdfs_available() -> bool:
    """Return True if the hdfs CLI is present and can reach the namenode."""
    result = _run(["hdfs", "dfs", "-ls", "/"])
    return result["returncode"] == 0


def setup_hdfs_directories() -> dict:
    """Create required HDFS directories. Returns status dict."""
    dirs = [HDFS_BASE, HDFS_INPUT, HDFS_OUTPUT, HDFS_MAPREDUCE_OUTPUT]
    results = {}
    for d in dirs:
        r = _run(["hdfs", "dfs", "-mkdir", "-p", d])
        results[d] = "OK" if r["returncode"] == 0 else r["stderr"]
    return results


def upload_dataset() -> dict:
    """Upload the local CSV to HDFS input directory."""
    r = _run([
        "hdfs", "dfs", "-put", "-f",
        DATA_PATH,
        HDFS_INPUT + "/crop_production_1997_2025.csv"
    ])
    return {
        "success": r["returncode"] == 0,
        "message": r["stdout"] or r["stderr"],
    }


def list_hdfs_files(path: str = HDFS_BASE) -> list:
    """List files in an HDFS path."""
    r = _run(["hdfs", "dfs", "-ls", "-R", path])
    if r["returncode"] != 0:
        return []
    lines = r["stdout"].splitlines()
    return [l for l in lines if l.strip()]


def verify_output(path: str = HDFS_OUTPUT) -> bool:
    """Return True if output files exist in the given HDFS path."""
    r = _run(["hdfs", "dfs", "-test", "-e", path])
    return r["returncode"] == 0


def get_hdfs_status() -> dict:
    """Return a comprehensive HDFS status report for the dashboard."""
    available = check_hdfs_available()
    if not available:
        return {
            "available": False,
            "message": (
                "Hadoop HDFS is not reachable. The 'hdfs' command was not found or "
                "the NameNode is not running. Dashboard is operating in local mode.\n\n"
                "To enable HDFS:\n"
                "  1. Install Hadoop (https://hadoop.apache.org/releases.html)\n"
                "  2. Set HADOOP_HOME and add to PATH\n"
                "  3. Start services: start-dfs.sh && start-yarn.sh\n"
                "  4. Run: python src/hdfs_utils.py setup\n"
            ),
            "directories": {},
            "files": [],
        }

    dirs_status = setup_hdfs_directories()
    files = list_hdfs_files()
    return {
        "available": True,
        "message": "HDFS is reachable and directories are configured.",
        "directories": dirs_status,
        "files": files,
    }


HADOOP_STREAMING_CMD_TEMPLATE = """
# --- Hadoop MapReduce Streaming Command ---
# Run from the project root directory.

HADOOP_JAR=$(find $HADOOP_HOME/share/hadoop/tools/lib -name "hadoop-streaming-*.jar" | head -1)

hdfs dfs -rm -r -f {HDFS_MAPREDUCE_OUTPUT}

hadoop jar $HADOOP_JAR \\
  -files src/mapreduce/mapper.py,src/mapreduce/reducer.py \\
  -mapper  "python3 mapper.py" \\
  -reducer "python3 reducer.py" \\
  -input   {HDFS_INPUT}/crop_production_1997_2025.csv \\
  -output  {HDFS_MAPREDUCE_OUTPUT}

# Verify output
hdfs dfs -ls {HDFS_MAPREDUCE_OUTPUT}
hdfs dfs -cat {HDFS_MAPREDUCE_OUTPUT}/part-00000 | head -20
""".format(
    HDFS_INPUT=HDFS_INPUT,
    HDFS_MAPREDUCE_OUTPUT=HDFS_MAPREDUCE_OUTPUT,
)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        print("Setting up HDFS directories...")
        print(setup_hdfs_directories())
        print("Uploading dataset...")
        print(upload_dataset())
    else:
        print("HDFS Status:")
        status = get_hdfs_status()
        for k, v in status.items():
            print(k + ":", v)
        print()
        print("Streaming command:")
        print(HADOOP_STREAMING_CMD_TEMPLATE)
