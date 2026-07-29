#!/usr/bin/env python3
"""Report SponsorSkin Python, package, accelerator, and ROCm readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sponsorskin.telemetry import collect_telemetry, write_json_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="Write the complete report to this path.")
    parser.add_argument(
        "--require-rocm",
        action="store_true",
        help="Exit non-zero unless PyTorch reports an available ROCm device.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = collect_telemetry()
    print(f"Scope: {report['scope']}")
    print(f"Python: {report['system']['python_version']} ({report['system']['machine']})")
    torch = report["torch"]
    print(f"PyTorch: {torch['version'] or 'not installed'}")
    print(f"ROCm: {torch['rocm_version'] or 'not detected'}")
    print(f"Accelerator API available: {torch['cuda_api_available']}")
    print(f"Device: {torch['device_name'] or 'none'}")
    if args.json:
        output_path = write_json_report(report, args.json)
        print(f"JSON report: {output_path.resolve()}")
    if args.require_rocm and not report["rocm_ready"]:
        print(
            json.dumps(
                {
                    "error": "ROCm device required but not detected.",
                    "next_step": "Run this command inside the assigned Radeon Cloud environment.",
                }
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
