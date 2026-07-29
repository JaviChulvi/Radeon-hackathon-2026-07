#!/usr/bin/env python3
"""Create deterministic SponsorSkin artifacts from the command line."""

from __future__ import annotations

import argparse
from pathlib import Path

from sponsorskin.cli import add_placement_arguments, placement_from_args, require_four_points
from sponsorskin.compositing import create_composite, save_composite_artifacts
from sponsorskin.validation import load_logo_image, load_target_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    add_placement_arguments(parser)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    target = load_target_image(args.target)
    logo = load_logo_image(args.logo)
    output = save_composite_artifacts(
        create_composite(
            target,
            logo,
            require_four_points(args.point),
            placement_from_args(args),
        ),
        args.output,
    )
    print(f"Wrote deterministic artifacts to {output.resolve()}")


if __name__ == "__main__":
    main()
