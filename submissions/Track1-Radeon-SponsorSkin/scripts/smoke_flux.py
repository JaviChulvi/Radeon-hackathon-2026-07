#!/usr/bin/env python3
"""Run one real FLUX.2 Klein masked edit after validating Radeon/ROCm."""

from __future__ import annotations

import argparse
from pathlib import Path

from sponsorskin.cli import add_placement_arguments, placement_from_args, require_four_points
from sponsorskin.inference import BackendUnavailableError, Flux2KleinRefiner
from sponsorskin.pipeline import run_pipeline
from sponsorskin.schemas import Flux2Settings
from sponsorskin.telemetry import collect_telemetry
from sponsorskin.validation import load_logo_image, load_target_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, default=Path("runs/radeon-smoke"))
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
    telemetry = collect_telemetry()
    if not telemetry["rocm_ready"]:
        raise SystemExit(
            "ROCm readiness check failed. Run scripts/doctor.py --require-rocm "
            "inside Radeon Cloud before downloading the model."
        )
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
    try:
        result = run_pipeline(
            load_target_image(args.target),
            load_logo_image(args.logo),
            require_four_points(args.point),
            output_root=args.runs_root,
            placement=placement_from_args(args),
            backend=backend,
            seed=args.seed,
        )
    except BackendUnavailableError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Radeon FLUX.2 run: {result.run_directory.resolve()}")
    print(f"Latency: {result.refinement.latency_seconds:.3f} seconds")
    print(
        f"Peak allocated VRAM: "
        f"{result.refinement.metadata['peak_allocated_bytes'] / (1024**3):.2f} GiB"
    )


if __name__ == "__main__":
    main()
