#!/usr/bin/env python3
"""
reducer.py — Hadoop Streaming Reducer
--------------------------------------
Reads sorted key-value pairs from stdin (state \t production)
and emits total production per state.

Usage (local test):
    cat data/crop_production_1997_2025.csv \\
      | python3 src/mapreduce/mapper.py \\
      | sort \\
      | python3 src/mapreduce/reducer.py

Usage (Hadoop Streaming):
    See hdfs_utils.py for the full streaming command.
"""

import sys


def main():
    current_state = None
    current_total = 0.0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        parts = line.split("\t")
        if len(parts) != 2:
            continue

        state = parts[0]
        try:
            production = float(parts[1])
        except ValueError:
            continue

        if state == current_state:
            current_total += production
        else:
            if current_state is not None:
                print(current_state + "\t" + str(round(current_total, 2)))
            current_state = state
            current_total = production

    # Emit last state
    if current_state is not None:
        print(current_state + "\t" + str(round(current_total, 2)))


if __name__ == "__main__":
    main()
