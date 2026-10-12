#!/usr/bin/env python3
"""Inspect the complete prefix of interrupted JSONL output without modifying it."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from dialysislab.trajectory import scan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trajectory', type=Path)
    args = parser.parse_args()
    print(json.dumps(scan(args.trajectory, recover=True), indent=2))


if __name__ == '__main__':
    main()
