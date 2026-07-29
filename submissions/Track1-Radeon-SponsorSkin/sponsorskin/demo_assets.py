"""Generate fictional, deterministic demo fixtures and local rough previews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from sponsorskin.compositing import create_composite, save_composite_artifacts
from sponsorskin.schemas import PlacementSettings, Point
from sponsorskin.validation import load_logo_image, load_target_image

CANVAS_SIZE = (1280, 768)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def _textured_canvas(
    base_color: tuple[int, int, int],
    *,
    seed: int,
    strength: int,
) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = np.full((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), base_color, dtype=np.int16)
    noise = rng.normal(0, strength, base.shape[:2])[..., None]
    textured = np.clip(base + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(textured, mode="RGB").filter(ImageFilter.GaussianBlur(0.35))


def _billboard_scene() -> Image.Image:
    image = _textured_canvas((71, 83, 96), seed=11, strength=5)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 470, 1280, 768), fill=(45, 49, 53))
    draw.polygon(
        [(140, 110), (1140, 95), (1190, 675), (90, 690)],
        fill=(154, 145, 130),
        outline=(213, 204, 190),
        width=10,
    )
    for x_value in range(140, 1160, 80):
        draw.line((x_value, 120, x_value - 40, 680), fill=(132, 123, 109), width=3)
    draw.polygon(
        [(210, 180), (1070, 150), (1030, 580), (240, 610)],
        fill=(222, 216, 202),
        outline=(73, 73, 69),
        width=14,
    )
    draw.text((72, 708), "PROCEDURAL BILLBOARD FIXTURE", font=_font(24), fill=(225, 225, 225))
    return image


def _vehicle_scene() -> Image.Image:
    image = _textured_canvas((24, 28, 36), seed=22, strength=4)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 590, 1280, 768), fill=(35, 37, 41))
    draw.ellipse((120, 520, 420, 820), fill=(17, 18, 22), outline=(100, 105, 112), width=15)
    draw.ellipse((860, 510, 1160, 810), fill=(17, 18, 22), outline=(100, 105, 112), width=15)
    draw.polygon(
        [(90, 545), (220, 260), (520, 165), (935, 205), (1170, 420), (1130, 610), (150, 625)],
        fill=(40, 103, 152),
        outline=(117, 180, 218),
        width=10,
    )
    draw.polygon(
        [(300, 280), (530, 190), (800, 215), (900, 295)],
        fill=(19, 32, 45),
        outline=(128, 156, 176),
        width=7,
    )
    for y_value in range(325, 550, 24):
        draw.line((315, y_value, 960, y_value - 25), fill=(47, 117, 168), width=2)
    draw.text((72, 708), "PROCEDURAL VEHICLE-PANEL FIXTURE", font=_font(24), fill=(225, 225, 225))
    return image


def _fabric_scene() -> Image.Image:
    image = _textured_canvas((55, 57, 64), seed=33, strength=5)
    draw = ImageDraw.Draw(image)
    draw.polygon(
        [
            (370, 115),
            (520, 70),
            (640, 145),
            (760, 70),
            (910, 115),
            (1080, 330),
            (920, 430),
            (870, 700),
            (410, 700),
            (360, 430),
            (200, 330),
        ],
        fill=(119, 31, 46),
        outline=(190, 79, 91),
        width=10,
    )
    draw.polygon([(520, 70), (640, 145), (760, 70), (720, 205), (560, 205)], fill=(38, 39, 44))
    for x_value in range(390, 900, 34):
        shade = 86 + ((x_value // 34) % 3) * 14
        draw.line((x_value, 180, x_value + 25, 690), fill=(shade, 27, 39), width=9)
    draw.text((72, 708), "PROCEDURAL FABRIC FIXTURE", font=_font(24), fill=(225, 225, 225))
    return image


def _logo(
    wordmark: str,
    *,
    fill: tuple[int, int, int],
    accent: tuple[int, int, int],
) -> Image.Image:
    image = Image.new("RGBA", (520, 190), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 512, 182), radius=38, fill=(*fill, 255))
    draw.polygon([(45, 145), (108, 45), (171, 145)], fill=(*accent, 255))
    draw.polygon([(78, 123), (108, 76), (138, 123)], fill=(*fill, 255))
    draw.text((205, 60), wordmark, font=_font(48), fill=(*accent, 255))
    return image


def _examples() -> list[dict]:
    return [
        {
            "id": "billboard",
            "title": "NOVA GRID billboard",
            "target": "inputs/billboard.png",
            "logo": "logos/nova-grid.png",
            "material": "billboard",
            "points": [[255, 235], [1015, 210], [980, 530], [285, 550]],
        },
        {
            "id": "vehicle-panel",
            "title": "APEX ZERO vehicle panel",
            "target": "inputs/vehicle-panel.png",
            "logo": "logos/apex-zero.png",
            "material": "vinyl",
            "points": [[350, 340], [945, 315], [900, 515], [380, 535]],
        },
        {
            "id": "fabric",
            "title": "KINETIQ fabric print",
            "target": "inputs/fabric.png",
            "logo": "logos/kinetiq.png",
            "material": "fabric_print",
            "points": [[440, 300], [840, 300], [820, 505], [460, 505]],
        },
    ]


def generate_assets(output_root: Path, *, force: bool = False) -> list[dict]:
    """Generate all fixtures and their deterministic SponsorSkin artifacts."""

    examples = _examples()
    input_directory = output_root / "inputs"
    logo_directory = output_root / "logos"
    preview_directory = output_root / "local_previews"
    for directory in (input_directory, logo_directory, preview_directory):
        directory.mkdir(parents=True, exist_ok=True)

    scenes = {
        "billboard": _billboard_scene(),
        "vehicle-panel": _vehicle_scene(),
        "fabric": _fabric_scene(),
    }
    logos = {
        "nova-grid": _logo("NOVA GRID", fill=(209, 36, 52), accent=(255, 255, 255)),
        "apex-zero": _logo("APEX ZERO", fill=(12, 18, 27), accent=(65, 219, 190)),
        "kinetiq": _logo("KINETIQ", fill=(242, 168, 26), accent=(33, 35, 42)),
    }
    for name, image in scenes.items():
        destination = input_directory / f"{name}.png"
        if destination.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {destination}; pass --force")
        image.save(destination, optimize=True)
    for name, image in logos.items():
        destination = logo_directory / f"{name}.png"
        if destination.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {destination}; pass --force")
        image.save(destination, optimize=True)

    for example in examples:
        points = [Point(x=x, y=y) for x, y in example["points"]]
        artifacts = create_composite(
            load_target_image(output_root / example["target"]),
            load_logo_image(output_root / example["logo"]),
            points,
            PlacementSettings(
                scale=0.88,
                mask_padding=16,
                feather_radius=7,
                material=example["material"],
            ),
        )
        destination = preview_directory / example["id"]
        save_composite_artifacts(artifacts, destination)
        artifacts.rough_composite.save(destination / "final_local_passthrough.png")
        (destination / "preview-metadata.json").write_text(
            json.dumps(
                {
                    "scope": "Deterministic local preview; no model or Radeon GPU used",
                    "example": example,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    (output_root / "examples.json").write_text(
        json.dumps(examples, indent=2) + "\n",
        encoding="utf-8",
    )
    return examples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("demo_assets"))
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    examples = generate_assets(args.output, force=args.force)
    print(f"Generated {len(examples)} fictional demo fixtures in {args.output.resolve()}")
    print("Local previews are deterministic and contain no generative or Radeon output.")


if __name__ == "__main__":
    main()
