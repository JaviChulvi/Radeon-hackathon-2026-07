"""Shared command-line parsing helpers."""

from __future__ import annotations

import argparse

from sponsorskin.schemas import MaterialPreset, PlacementSettings, Point


def parse_point(raw_value: str) -> Point:
    """Parse an X,Y command-line coordinate."""

    try:
        x_value, y_value = raw_value.split(",", maxsplit=1)
        return Point(x=float(x_value), y=float(y_value))
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("point must use X,Y format") from exc


def add_placement_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared placement controls to a parser."""

    parser.add_argument("--point", type=parse_point, action="append", required=True)
    parser.add_argument("--scale", type=float, default=0.9)
    parser.add_argument("--rotation", type=float, default=0.0)
    parser.add_argument("--opacity", type=float, default=1.0)
    parser.add_argument("--mask-padding", type=int, default=12)
    parser.add_argument("--feather-radius", type=float, default=6.0)
    parser.add_argument(
        "--material",
        choices=[preset.value for preset in MaterialPreset],
        default=MaterialPreset.VINYL.value,
    )


def placement_from_args(args: argparse.Namespace) -> PlacementSettings:
    """Build validated placement settings from parsed arguments."""

    return PlacementSettings(
        scale=args.scale,
        rotation_degrees=args.rotation,
        opacity=args.opacity,
        mask_padding=args.mask_padding,
        feather_radius=args.feather_radius,
        material=args.material,
    )


def require_four_points(points: list[Point]) -> list[Point]:
    """Reject incomplete or ambiguous placement selections."""

    if len(points) != 4:
        raise SystemExit("exactly four --point values are required")
    return points
