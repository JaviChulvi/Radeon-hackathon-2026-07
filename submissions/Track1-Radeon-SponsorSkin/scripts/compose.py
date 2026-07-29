#!/usr/bin/env python3
"""Create deterministic SponsorSkin artifacts from the command line."""

from __future__ import annotations

import argparse
from pathlib import Path

from sponsorskin.compositing import create_composite, save_composite_artifacts
from sponsorskin.schemas import PlacementSettings, Point
from sponsorskin.validation import load_logo_image, load_target_image


def parse_point(raw_value: str) -> Point:
    """Parse an X,Y command-line coordinate."""

    try:
        x_value, y_value = raw_value.split(",", maxsplit=1)
        return Point(x=float(x_value), y=float(y_value))
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("point must use X,Y format") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--logo", type=Path, required=True)
    parser.add_argument("--point", type=parse_point, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", type=float, default=0.9)
    parser.add_argument("--rotation", type=float, default=0.0)
    parser.add_argument("--opacity", type=float, default=1.0)
    parser.add_argument("--mask-padding", type=int, default=12)
    parser.add_argument("--feather-radius", type=float, default=6.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if len(args.point) != 4:
        raise SystemExit("exactly four --point values are required")
    target = load_target_image(args.target)
    logo = load_logo_image(args.logo)
    settings = PlacementSettings(
        scale=args.scale,
        rotation_degrees=args.rotation,
        opacity=args.opacity,
        mask_padding=args.mask_padding,
        feather_radius=args.feather_radius,
    )
    output = save_composite_artifacts(
        create_composite(target, logo, args.point, settings),
        args.output,
    )
    print(f"Wrote deterministic artifacts to {output.resolve()}")


if __name__ == "__main__":
    main()
