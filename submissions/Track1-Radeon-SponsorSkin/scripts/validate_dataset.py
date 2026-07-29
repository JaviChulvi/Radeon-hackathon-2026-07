#!/usr/bin/env python3
"""Validate canonical SponsorSkin paired samples and their rights metadata."""

from __future__ import annotations

import argparse
from pathlib import Path

from sponsorskin.dataset import validate_dataset, write_dataset_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--json", type=Path, help="Write the complete report to this path.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = validate_dataset(args.dataset_root)
    print(f"Samples: {report.valid_sample_count}/{report.sample_count} valid")
    print(f"Splits: {report.split_counts}")
    print(f"Materials: {report.material_counts}")
    for sample in report.samples:
        for error in sample.errors:
            print(f"ERROR {sample.sample_id}: {error}")
        for warning in sample.warnings:
            print(f"WARN  {sample.sample_id}: {warning}")
    if args.json:
        path = write_dataset_report(report, args.json)
        print(f"JSON report: {path.resolve()}")
    if not report.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
