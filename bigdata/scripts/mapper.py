#!/usr/bin/env python3
import sys
import csv

reader = csv.DictReader(sys.stdin)

for row in reader:
    crop = (row.get("Crop") or "").strip()
    production = (row.get("Production") or "").strip()

    if not crop or not production:
        continue

    try:
        value = float(production)
    except ValueError:
        continue

    print(f"{crop}\t{value}")
