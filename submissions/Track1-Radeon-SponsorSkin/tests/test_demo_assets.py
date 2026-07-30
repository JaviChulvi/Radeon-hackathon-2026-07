from __future__ import annotations

from pathlib import Path

from sponsorskin.demo_assets import generate_assets
from sponsorskin.real_demo_assets import REAL_EXAMPLES, build_real_previews
from sponsorskin.validation import load_logo_image, load_target_image


def test_generated_demo_assets_are_complete(tmp_path: Path) -> None:
    examples = generate_assets(tmp_path)

    assert len(examples) == 3
    for example in examples:
        target = load_target_image(tmp_path / example["target"])
        logo = load_logo_image(tmp_path / example["logo"])
        preview = tmp_path / "local_previews" / example["id"]
        assert target.size == (1280, 768)
        assert logo.mode == "RGBA"
        assert (preview / "rough_composite.png").exists()
        assert (preview / "edit_mask.png").exists()
        assert (preview / "final_local_passthrough.png").exists()
        assert (preview / "preview-metadata.json").exists()


def test_committed_real_demo_assets_are_complete() -> None:
    project_root = Path(__file__).resolve().parents[1]
    examples = build_real_previews(project_root / "demo_assets")

    assert len(examples) == len(REAL_EXAMPLES) == 7
    for example in examples:
        target = load_target_image(project_root / "demo_assets" / example["target"])
        preview = project_root / "demo_assets" / "real_previews" / example["id"]
        assert target.size == tuple(example["target_size"])
        assert (preview / "rough_composite.png").exists()
        assert (preview / "edit_mask.png").exists()
        assert (preview / "logo_layer.png").exists()
        assert (preview / "exact_alpha.png").exists()
        assert (preview / "preview-metadata.json").exists()
