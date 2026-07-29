from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def test_compose_cli_writes_complete_artifact_set(tmp_path: Path) -> None:
    target_path = tmp_path / "target.png"
    logo_path = tmp_path / "logo.png"
    output_path = tmp_path / "output"
    Image.new("RGB", (320, 200), (35, 45, 60)).save(target_path)
    logo = Image.new("RGBA", (120, 60), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rounded_rectangle((8, 8, 112, 52), radius=8, fill=(239, 35, 60, 255))
    logo.save(logo_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/compose.py",
            "--target",
            str(target_path),
            "--logo",
            str(logo_path),
            "--point",
            "60,50",
            "--point",
            "260,45",
            "--point",
            "250,150",
            "--point",
            "70,155",
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Wrote deterministic artifacts" in result.stdout
    assert {path.name for path in output_path.iterdir()} == {
        "edit_mask.png",
        "exact_alpha.png",
        "logo_layer.png",
        "original.png",
        "rough_composite.png",
    }


def test_local_cli_writes_versioned_reproducible_run(tmp_path: Path) -> None:
    target_path = tmp_path / "target.png"
    logo_path = tmp_path / "logo.png"
    runs_path = tmp_path / "runs"
    Image.new("RGB", (320, 200), (35, 45, 60)).save(target_path)
    logo = Image.new("RGBA", (120, 60), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((8, 8, 112, 52), fill=(239, 35, 60, 255))
    logo.save(logo_path)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_local.py",
            "--target",
            str(target_path),
            "--logo",
            str(logo_path),
            "--point",
            "60,50",
            "--point",
            "260,45",
            "--point",
            "250,150",
            "--point",
            "70,155",
            "--runs-root",
            str(runs_path),
            "--seed",
            "17",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    run_path = next(runs_path.iterdir())
    assert "No generative model or Radeon GPU was used." in result.stdout
    assert (run_path / "final.png").exists()
    assert (run_path / "metrics.json").exists()
    assert (run_path / "manifest.json").exists()
