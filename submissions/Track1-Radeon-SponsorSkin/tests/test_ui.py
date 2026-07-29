from __future__ import annotations

from pathlib import Path

import gradio as gr
import numpy as np
from PIL import Image, ImageDraw

from sponsorskin.schemas import PlacementSettings
from sponsorskin.ui import add_corner, build_app, create_preview, run_local_generation


def make_files(tmp_path: Path) -> tuple[Path, Path]:
    target_path = tmp_path / "target.png"
    logo_path = tmp_path / "logo.png"
    Image.new("RGB", (320, 220), (35, 45, 60)).save(target_path)
    logo = Image.new("RGBA", (120, 60), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rounded_rectangle((8, 8, 112, 52), radius=8, fill=(239, 35, 60, 255))
    logo.save(logo_path)
    return target_path, logo_path


def test_four_corner_state_and_annotations_are_non_destructive() -> None:
    target = Image.new("RGB", (200, 120), (20, 30, 40))
    points: list[tuple[float, float]] = []

    for coordinate in [(20, 20), (180, 20), (180, 100), (20, 100)]:
        annotated, points, status = add_corner(target, points, coordinate)

    assert len(points) == 4
    assert "Four corners selected" in status
    assert not np.array_equal(annotated, target)
    assert np.array_equal(np.asarray(target), np.full((120, 200, 3), (20, 30, 40)))


def test_preview_and_local_generation_share_artifact_contract(tmp_path: Path) -> None:
    target_path, logo_path = make_files(tmp_path)
    points = [(60, 50), (260, 45), (250, 170), (70, 175)]
    settings = PlacementSettings(scale=1)

    preview = create_preview(str(target_path), str(logo_path), points, settings)
    result = run_local_generation(
        str(target_path),
        str(logo_path),
        points,
        settings,
        seed=23,
        runs_root=tmp_path / "runs",
    )

    assert np.array_equal(preview.rough_composite, result.artifacts.rough_composite)
    assert result.manifest.seed == 23
    assert (result.run_directory / "manifest.json").exists()


def test_app_builds_without_starting_a_server() -> None:
    demo = build_app()

    assert isinstance(demo, gr.Blocks)
