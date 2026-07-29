from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from sponsorskin.validation import InputValidationError, load_logo_image, load_target_image


def test_target_image_is_loaded_as_rgb(tmp_path: Path) -> None:
    path = tmp_path / "target.png"
    Image.new("RGBA", (64, 48), (1, 2, 3, 100)).save(path)

    image = load_target_image(path)

    assert image.mode == "RGB"
    assert image.size == (64, 48)


def test_transparent_png_logo_is_trimmed(tmp_path: Path) -> None:
    path = tmp_path / "logo.png"
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((20, 10, 79, 69), fill=(255, 0, 0, 255))
    image.save(path)

    logo = load_logo_image(path)

    assert logo.mode == "RGBA"
    assert logo.size == (60, 60)


def test_opaque_png_logo_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "logo.png"
    Image.new("RGB", (64, 64), (255, 0, 0)).save(path)

    with pytest.raises(InputValidationError, match="transparency"):
        load_logo_image(path)


def test_svg_with_external_resource_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
        '<image href="https://example.com/logo.png" width="64" height="64"/>'
        "</svg>",
        encoding="utf-8",
    )

    with pytest.raises(InputValidationError, match="resources"):
        load_logo_image(path)


def test_safe_svg_is_rendered_and_trimmed(tmp_path: Path) -> None:
    path = tmp_path / "safe.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
        '<rect x="10" y="10" width="80" height="30" fill="#ef233c"/>'
        "</svg>",
        encoding="utf-8",
    )

    logo = load_logo_image(path)

    assert logo.mode == "RGBA"
    assert logo.width > logo.height
