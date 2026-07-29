from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from sponsorskin.compositing import create_composite
from sponsorskin.restoration import restore_exact_logo
from sponsorskin.schemas import PlacementSettings, Point, RestorationSettings


def make_artifacts():
    target = Image.new("RGB", (240, 160), (160, 170, 180))
    logo = Image.new("RGBA", (100, 50), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((10, 10, 90, 40), fill=(240, 30, 40, 255))
    points = [
        Point(x=40, y=40),
        Point(x=200, y=40),
        Point(x=200, y=120),
        Point(x=40, y=120),
    ]
    return create_composite(
        target,
        logo,
        points,
        PlacementSettings(scale=1, mask_padding=5, feather_radius=2),
    )


def test_passthrough_restoration_does_not_double_composite_logo() -> None:
    artifacts = make_artifacts()

    restored = restore_exact_logo(artifacts, artifacts.rough_composite)

    assert np.array_equal(restored.image, artifacts.rough_composite)


def test_restoration_forces_original_pixels_outside_edit_mask() -> None:
    artifacts = make_artifacts()
    changed_everywhere = Image.new("RGB", artifacts.original.size, (0, 0, 0))

    restored = restore_exact_logo(
        artifacts,
        changed_everywhere,
        RestorationSettings(shading_strength=0),
    )
    result = np.asarray(restored.image)
    original = np.asarray(artifacts.original)
    outside = np.asarray(artifacts.edit_mask) == 0

    assert np.array_equal(result[outside], original[outside])
    assert not np.array_equal(result[80, 120], original[80, 120])
