"""Prepare rights-documented stock targets and deterministic local previews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from sponsorskin.compositing import create_composite
from sponsorskin.schemas import PlacementSettings, Point
from sponsorskin.validation import load_logo_image, load_target_image

PEXELS_LICENSE_URL = "https://www.pexels.com/license/"

REAL_EXAMPLES: tuple[dict[str, Any], ...] = (
    {
        "id": "porsche-911",
        "title": "APEX ZERO — Porsche 911 GT2 RS door",
        "category": "sports_car",
        "source_file": "porsche-911.jpg",
        "target": "real_inputs/porsche-911.jpg",
        "target_size": [768, 1024],
        "logo": "logos/apex-zero.png",
        "material": "vinyl",
        "points": [[485, 510], [730, 535], [715, 625], [480, 600]],
        "source": {
            "photographer": "Dante Juhasz",
            "provider": "Pexels",
            "photo_id": "13990526",
            "page": "https://www.pexels.com/photo/side-of-a-modern-sports-car-13990526/",
            "license": PEXELS_LICENSE_URL,
        },
    },
    {
        "id": "city-bus",
        "title": "NOVA GRID — city bus side panel",
        "category": "bus",
        "source_file": "bus.jpg",
        "target": "real_inputs/city-bus.jpg",
        "target_size": [768, 1024],
        "logo": "logos/nova-grid.png",
        "material": "vinyl",
        "points": [[165, 615], [495, 615], [480, 725], [175, 720]],
        "source": {
            "photographer": "Алёна Жигарева",
            "provider": "Pexels",
            "photo_id": "9006627",
            "page": "https://www.pexels.com/photo/white-and-blue-bus-under-blue-sky-9006627/",
            "license": PEXELS_LICENSE_URL,
        },
    },
    {
        "id": "delivery-truck",
        "title": "KINETIQ — delivery truck box",
        "category": "truck",
        "source_file": "truck.jpg",
        "target": "real_inputs/delivery-truck.jpg",
        "target_size": [1280, 768],
        "logo": "logos/kinetiq.png",
        "material": "vinyl",
        "points": [[285, 300], [850, 300], [850, 480], [285, 480]],
        "source": {
            "photographer": "Michael Lee",
            "provider": "Pexels",
            "photo_id": "28158703",
            "page": (
                "https://www.pexels.com/photo/"
                "a-white-truck-is-parked-on-the-side-of-the-road-28158703/"
            ),
            "license": PEXELS_LICENSE_URL,
        },
    },
    {
        "id": "blank-hoodie",
        "title": "NOVA GRID — blank hoodie chest",
        "category": "hoodie",
        "source_file": "hoodie-vertical.jpg",
        "target": "real_inputs/blank-hoodie.jpg",
        "target_size": [768, 1152],
        "logo": "logos/nova-grid.png",
        "material": "fabric_print",
        "points": [[445, 525], [635, 530], [625, 605], [440, 595]],
        "source": {
            "photographer": "cottonbro studio",
            "provider": "Pexels",
            "photo_id": "5840464",
            "page": "https://www.pexels.com/photo/men-wearing-blank-hoodies-5840464/",
            "license": PEXELS_LICENSE_URL,
            "notice": "Fictional campaign concept; no endorsement by the pictured people.",
        },
    },
    {
        "id": "workshop-cap",
        "title": "APEX ZERO — cap front patch",
        "category": "cap",
        "source_file": "cap-object.jpg",
        "target": "real_inputs/workshop-cap.jpg",
        "target_size": [768, 1152],
        "logo": "logos/apex-zero.png",
        "material": "fabric_print",
        "points": [[335, 775], [575, 790], [560, 875], [325, 850]],
        "source": {
            "photographer": "Yaroslav Shuraev",
            "provider": "Pexels",
            "photo_id": "4888594",
            "page": (
                "https://www.pexels.com/photo/a-close-up-shot-of-a-cap-on-a-wooden-table-4888594/"
            ),
            "license": PEXELS_LICENSE_URL,
        },
    },
    {
        "id": "street-billboard",
        "title": "KINETIQ — street billboard",
        "category": "billboard",
        "source_file": "billboard.jpg",
        "target": "real_inputs/street-billboard.jpg",
        "target_size": [1280, 768],
        "logo": "logos/kinetiq.png",
        "material": "billboard",
        "points": [[220, 65], [1035, 65], [1035, 525], [220, 525]],
        "source": {
            "photographer": "Peter Dyllong",
            "provider": "Pexels",
            "photo_id": "36519146",
            "page": (
                "https://www.pexels.com/photo/blank-billboard-in-urban-street-setting-36519146/"
            ),
            "license": PEXELS_LICENSE_URL,
        },
    },
    {
        "id": "bus-shelter",
        "title": "NOVA GRID — illuminated bus-shelter display",
        "category": "street_furniture",
        "source_file": "bus-shelter.jpg",
        "target": "real_inputs/bus-shelter.jpg",
        "target_size": [1152, 864],
        "logo": "logos/nova-grid.png",
        "material": "billboard",
        "points": [[225, 315], [365, 322], [365, 375], [225, 368]],
        "source": {
            "photographer": "Tembela Bohle",
            "provider": "Pexels",
            "photo_id": "5655660",
            "page": (
                "https://www.pexels.com/photo/"
                "a-bus-shelter-with-billboards-illuminated-at-night-5655660/"
            ),
            "license": PEXELS_LICENSE_URL,
        },
    },
)


def normalize_real_inputs(source_directory: Path, output_root: Path) -> None:
    """Resize downloaded originals into model-safe, committed demo targets."""

    destination_directory = output_root / "real_inputs"
    destination_directory.mkdir(parents=True, exist_ok=True)
    for example in REAL_EXAMPLES:
        source = source_directory / example["source_file"]
        if not source.is_file():
            raise FileNotFoundError(f"Missing downloaded stock source: {source}")
        width, height = example["target_size"]
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            normalized = ImageOps.fit(
                image,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
        normalized.save(
            output_root / example["target"],
            format="JPEG",
            quality=92,
            optimize=True,
            progressive=True,
        )


def build_real_previews(output_root: Path) -> list[dict[str, Any]]:
    """Create exact-logo composites from the committed stock targets."""

    examples = [dict(example) for example in REAL_EXAMPLES]
    preview_directory = output_root / "real_previews"
    preview_directory.mkdir(parents=True, exist_ok=True)
    for example in examples:
        points = [Point(x=x, y=y) for x, y in example["points"]]
        artifacts = create_composite(
            load_target_image(output_root / example["target"]),
            load_logo_image(output_root / example["logo"]),
            points,
            PlacementSettings(
                scale=0.9,
                mask_padding=12,
                feather_radius=6,
                material=example["material"],
            ),
        )
        destination = preview_directory / example["id"]
        destination.mkdir(parents=True, exist_ok=True)
        artifacts.logo_layer.save(destination / "logo_layer.png")
        artifacts.rough_composite.save(destination / "rough_composite.png")
        artifacts.edit_mask.save(destination / "edit_mask.png")
        artifacts.exact_alpha.save(destination / "exact_alpha.png")
        (destination / "preview-metadata.json").write_text(
            json.dumps(
                {
                    "scope": (
                        "Deterministic exact-logo placement preview; "
                        "no FLUX model or Radeon GPU used"
                    ),
                    "example": example,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    (output_root / "real_examples.json").write_text(
        json.dumps(examples, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return examples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("demo_assets"))
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="Optional directory containing the downloaded originals.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.source_dir is not None:
        normalize_real_inputs(args.source_dir, args.output)
    examples = build_real_previews(args.output)
    print(f"Prepared {len(examples)} rights-documented real-world examples.")
    print("Outputs are deterministic composites, not FLUX or Radeon inference results.")


if __name__ == "__main__":
    main()
