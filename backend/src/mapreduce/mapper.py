#!/usr/bin/env python3
"""
mapper.py — Hadoop Streaming Mapper
------------------------------------
Reads crop production CSV lines from stdin and emits:
    state_name\tproduction_value

Usage (local test):
    cat data/crop_production_1997_2025.csv | python3 src/mapreduce/mapper.py

Usage (Hadoop Streaming):
    See hdfs_utils.py for the full streaming command.
"""

import sys

HEADER = "State_Name,District_Name,Crop_Year,Season,Crop,Area,Production,Data_Type"


def main():
    first_line = True
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # Skip the CSV header
        if first_line:
            first_line = False
            if line.startswith("State_Name"):
                continue

        parts = line.split(",")
        # CSV columns: State_Name(0), District_Name(1), Crop_Year(2),
        #              Season(3), Crop(4), Area(5), Production(6), Data_Type(7)
        if len(parts) < 8:
            continue

        state = parts[0].strip()
        production_str = parts[6].strip()

        # Skip rows with missing production
        if not production_str or production_str.lower() in ("", "nan", "none"):
            continue

        try:
            production = float(production_str)
        except ValueError:
            continue

        # Emit: state -> production
        print(state + "\t" + str(production))


if __name__ == "__main__":
    main()
