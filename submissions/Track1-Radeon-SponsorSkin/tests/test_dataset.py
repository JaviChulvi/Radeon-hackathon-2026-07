from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from sponsorskin.dataset import validate_dataset, validate_sample


def make_sample(root: Path, sample_id: str = "sample-001") -> Path:
    sample = root / sample_id
    sample.mkdir(parents=True)
    source = Image.new("RGB", (320, 192), (40, 50, 60))
    source.save(sample / "source.png")
    source.save(sample / "rough_composite.png")
    source.save(sample / "target.png")
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).rectangle((80, 48, 240, 144), fill=255)
    mask.save(sample / "mask.png")
    logo = Image.new("RGBA", (120, 64), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((8, 8, 112, 56), fill=(225, 33, 48, 255))
    logo.save(sample / "logo.png")
    (sample / "instruction.txt").write_text(
        "Integrate the exact logo as printed billboard graphics.\n",
        encoding="utf-8",
    )
    (sample / "metadata.json").write_text(
        json.dumps(
            {
                "sample_id": sample_id,
                "split": "train",
                "material": "billboard",
                "source_creator": "SponsorSkin synthetic fixture",
                "source_license": "CC0-1.0",
                "logo_creator": "SponsorSkin synthetic fixture",
                "logo_license": "CC0-1.0",
            }
        ),
        encoding="utf-8",
    )
    return sample


def test_valid_canonical_sample(tmp_path: Path) -> None:
    sample = make_sample(tmp_path)

    result = validate_sample(sample)

    assert result.valid
    assert result.image_size == (320, 192)
    assert result.material == "billboard"


def test_missing_sample_files_are_reported(tmp_path: Path) -> None:
    sample = tmp_path / "incomplete"
    sample.mkdir()

    result = validate_sample(sample)

    assert not result.valid
    assert "Missing required files" in result.errors[0]


def test_dataset_aggregate_counts_splits_and_materials(tmp_path: Path) -> None:
    make_sample(tmp_path, "sample-001")
    second = make_sample(tmp_path, "sample-002")
    metadata = json.loads((second / "metadata.json").read_text(encoding="utf-8"))
    metadata["split"] = "validation"
    (second / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    report = validate_dataset(tmp_path)

    assert report.valid
    assert report.sample_count == 2
    assert report.split_counts == {"train": 1, "validation": 1}
