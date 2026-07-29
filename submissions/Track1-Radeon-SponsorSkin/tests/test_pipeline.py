from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from sponsorskin.pipeline import run_pipeline
from sponsorskin.schemas import PlacementSettings, Point


def make_inputs() -> tuple[Image.Image, Image.Image, list[Point]]:
    target = Image.new("RGB", (240, 160), (80, 90, 100))
    logo = Image.new("RGBA", (100, 50), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((10, 10, 90, 40), fill=(220, 20, 35, 255))
    points = [
        Point(x=40, y=40),
        Point(x=200, y=40),
        Point(x=200, y=120),
        Point(x=40, y=120),
    ]
    return target, logo, points


def test_passthrough_pipeline_is_reproducible_and_persisted(tmp_path: Path) -> None:
    target, logo, points = make_inputs()

    result = run_pipeline(
        target,
        logo,
        points,
        output_root=tmp_path,
        placement=PlacementSettings(scale=1, mask_padding=4, feather_radius=2),
        seed=7,
    )

    assert result.manifest.backend == "local-passthrough"
    assert result.manifest.model_id is None
    assert result.manifest.seed == 7
    assert result.metrics.outside_changed_ratio == 0
    assert result.metrics.outside_ssim == 1
    assert np.array_equal(result.restoration.image, result.artifacts.rough_composite)
    assert (result.run_directory / "final.png").exists()
    manifest = json.loads((result.run_directory / "manifest.json").read_text())
    assert manifest["run_id"] == result.run_directory.name
    assert manifest["backend_metadata"]["notice"].startswith("Deterministic local preview")


def test_run_directories_are_versioned(tmp_path: Path) -> None:
    target, logo, points = make_inputs()

    first = run_pipeline(target, logo, points, output_root=tmp_path)
    second = run_pipeline(target, logo, points, output_root=tmp_path)

    assert first.run_directory != second.run_directory
    assert len(list(tmp_path.iterdir())) == 2
