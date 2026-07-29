#!/usr/bin/env python3
"""Run the complete deterministic SponsorSkin pipeline without AI inference."""

from __future__ import annotations

import argparse
from pathlib import Path

from sponsorskin.cli import add_placement_arguments, placement_from_args, require_four_points
from sponsorskin.pipeline import run_pipeline
from sponsorskin.validation import load_logo_image, load_target_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, default=Path("runs"))
    parser.add_argument("--seed", type=int, default=42)
    add_placement_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_pipeline(
        load_target_image(args.target),
        load_logo_image(args.logo),
        require_four_points(args.point),
        output_root=args.runs_root,
        placement=placement_from_args(args),
        seed=args.seed,
    )
    print(f"Completed local passthrough run: {result.run_directory.resolve()}")
    print(f"Final image: {(result.run_directory / 'final.png').resolve()}")
    print(f"Manifest: {(result.run_directory / 'manifest.json').resolve()}")
    print("No generative model or Radeon GPU was used.")


if __name__ == "__main__":
    main()
