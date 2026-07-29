#!/usr/bin/env python3
"""Benchmark the complete local passthrough pipeline and write JSON evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from sponsorskin.benchmarking import benchmark_local_pipeline
from sponsorskin.telemetry import write_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/local-results.json"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = benchmark_local_pipeline(
        iterations=args.iterations,
        width=args.width,
        height=args.height,
    )
    output_path = write_json_report(report, args.output)
    timings = report["timings_seconds"]
    print(f"Scope: {report['scope']}")
    print(f"Warm mean: {timings['warm_mean']:.4f} seconds")
    print(f"Warm median: {timings['warm_median']:.4f} seconds")
    print(f"JSON report: {output_path.resolve()}")


if __name__ == "__main__":
    main()
