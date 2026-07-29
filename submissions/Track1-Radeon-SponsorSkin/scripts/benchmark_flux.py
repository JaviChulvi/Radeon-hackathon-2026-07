#!/usr/bin/env python3
"""Measure cold-start and warm FLUX.2 runs on a verified Radeon/ROCm device."""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path
from time import perf_counter

from sponsorskin.cli import add_placement_arguments, placement_from_args, require_four_points
from sponsorskin.inference import BackendUnavailableError, Flux2KleinRefiner
from sponsorskin.pipeline import run_pipeline
from sponsorskin.schemas import Flux2Settings
from sponsorskin.telemetry import collect_telemetry, write_json_report
from sponsorskin.validation import load_logo_image, load_target_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, default=Path("runs/radeon-benchmark"))
    parser.add_argument("--output", type=Path, default=Path("benchmarks/radeon-results.json"))
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-id", default="black-forest-labs/FLUX.2-klein-4B")
    parser.add_argument("--model-revision")
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--strength", type=float, default=0.65)
    parser.add_argument("--maximum-pixels", type=int, default=1024 * 1024)
    parser.add_argument("--cpu-offload", action="store_true")
    add_placement_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.iterations < 2:
        raise SystemExit("--iterations must be at least 2 to measure warm inference")
    environment = collect_telemetry()
    if not environment["rocm_ready"]:
        raise SystemExit("Radeon benchmark refused: scripts/doctor.py did not detect ROCm.")

    backend = Flux2KleinRefiner(
        Flux2Settings(
            model_id=args.model_id,
            model_revision=args.model_revision,
            num_inference_steps=args.steps,
            strength=args.strength,
            maximum_pixels=args.maximum_pixels,
            enable_cpu_offload=args.cpu_offload,
        )
    )
    target = load_target_image(args.target)
    logo = load_logo_image(args.logo)
    points = require_four_points(args.point)
    placement = placement_from_args(args)
    records: list[dict] = []
    try:
        for iteration in range(args.iterations):
            wall_started = perf_counter()
            result = run_pipeline(
                target,
                logo,
                points,
                output_root=args.runs_root,
                placement=placement,
                backend=backend,
                seed=args.seed,
            )
            records.append(
                {
                    "iteration": iteration,
                    "wall_seconds": perf_counter() - wall_started,
                    "inference_seconds": result.refinement.latency_seconds,
                    "peak_allocated_bytes": result.refinement.metadata["peak_allocated_bytes"],
                    "run_directory": str(result.run_directory),
                    "quality_metrics": result.metrics.model_dump(mode="json"),
                }
            )
    except BackendUnavailableError as exc:
        raise SystemExit(str(exc)) from exc

    warm_inference = [record["inference_seconds"] for record in records[1:]]
    report = {
        "schema_version": "1.0",
        "scope": "Measured FLUX.2 Klein inference on Radeon/ROCm",
        "environment": environment,
        "model": {
            "id": backend.settings.model_id,
            "revision": backend.settings.model_revision,
            "steps": backend.settings.num_inference_steps,
            "strength": backend.settings.strength,
            "maximum_pixels": backend.settings.maximum_pixels,
            "cpu_offload": backend.settings.enable_cpu_offload,
        },
        "seed": args.seed,
        "iterations": args.iterations,
        "cold": records[0],
        "warm": {
            "records": records[1:],
            "inference_mean_seconds": statistics.mean(warm_inference),
            "inference_median_seconds": statistics.median(warm_inference),
            "inference_min_seconds": min(warm_inference),
            "inference_max_seconds": max(warm_inference),
            "maximum_peak_allocated_bytes": max(
                record["peak_allocated_bytes"] for record in records
            ),
        },
    }
    output_path = write_json_report(report, args.output)
    print(f"Cold wall time: {records[0]['wall_seconds']:.3f} seconds")
    print(f"Warm inference mean: {report['warm']['inference_mean_seconds']:.3f} seconds")
    print(
        f"Maximum peak allocated VRAM: "
        f"{report['warm']['maximum_peak_allocated_bytes'] / (1024**3):.2f} GiB"
    )
    print(f"JSON report: {output_path.resolve()}")


if __name__ == "__main__":
    main()
