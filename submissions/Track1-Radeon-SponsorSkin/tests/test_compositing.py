from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from sponsorskin.compositing import create_composite, prepare_logo
from sponsorskin.schemas import PlacementSettings, Point


def make_logo() -> Image.Image:
    logo = Image.new("RGBA", (100, 50), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((10, 10, 90, 40), fill=(230, 20, 30, 255))
    return logo


def test_prepare_logo_preserves_canvas_and_applies_opacity() -> None:
    prepared = prepare_logo(
        make_logo(),
        PlacementSettings(scale=0.5, opacity=0.5, rotation_degrees=5),
    )

    assert prepared.size == (100, 50)
    assert 120 <= prepared.getchannel("A").getextrema()[1] <= 128


def test_create_composite_preserves_pixels_outside_logo() -> None:
    target = Image.new("RGB", (240, 160), (180, 180, 180))
    points = [
        Point(x=40, y=40),
        Point(x=200, y=40),
        Point(x=200, y=120),
        Point(x=40, y=120),
    ]

    artifacts = create_composite(
        target,
        make_logo(),
        points,
        PlacementSettings(scale=1.0, mask_padding=4, feather_radius=2),
    )
    rough = np.asarray(artifacts.rough_composite)
    alpha = np.asarray(artifacts.exact_alpha)

    assert artifacts.rough_composite.size == target.size
    assert artifacts.logo_layer.mode == "RGBA"
    assert artifacts.edit_mask.mode == "L"
    assert tuple(rough[5, 5]) == (180, 180, 180)
    assert np.count_nonzero(alpha) > 0
    assert np.count_nonzero(np.asarray(artifacts.edit_mask)) > np.count_nonzero(alpha)
    assert rough[80, 120, 0] > rough[80, 120, 1]
