#!/usr/bin/env python3
import sys

current_crop = None
total = 0.0

for line in sys.stdin:
    line = line.rstrip("\n")
    if "\t" not in line:
        continue

    crop, value = line.rsplit("\t", 1)

    try:
        value = float(value)
    except ValueError:
        continue

    if crop == current_crop:
        total += value
    else:
        if current_crop is not None:
            print(f"{current_crop}\t{total:.2f}")

        current_crop = crop
        total = value

if current_crop is not None:
    print(f"{current_crop}\t{total:.2f}")
