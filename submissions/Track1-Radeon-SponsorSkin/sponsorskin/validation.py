"""Input loading and security validation for target images and logos."""

from __future__ import annotations

import io
from pathlib import Path

from defusedxml import ElementTree as DefusedET
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000
MIN_IMAGE_SIDE = 32
MAX_IMAGE_SIDE = 8192
UNSAFE_SVG_TAGS = {"script", "foreignObject"}
UNSAFE_URI_PREFIXES = ("http:", "https:", "file:", "ftp:", "javascript:", "//")


class InputValidationError(ValueError):
    """Raised when user-provided media cannot be processed safely."""


def _read_limited(path: Path) -> bytes:
    if not path.is_file():
        raise InputValidationError(f"File does not exist: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise InputValidationError(f"File exceeds {MAX_FILE_BYTES // (1024 * 1024)} MiB: {path}")
    return path.read_bytes()


def _validate_dimensions(image: Image.Image, *, label: str) -> None:
    width, height = image.size
    if width < MIN_IMAGE_SIDE or height < MIN_IMAGE_SIDE:
        raise InputValidationError(f"{label} must be at least {MIN_IMAGE_SIDE}px per side")
    if width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE:
        raise InputValidationError(f"{label} exceeds the {MAX_IMAGE_SIDE}px side limit")
    if width * height > MAX_IMAGE_PIXELS:
        raise InputValidationError(f"{label} exceeds the {MAX_IMAGE_PIXELS:,}-pixel limit")


def _open_raster(data: bytes, *, label: str) -> Image.Image:
    try:
        with Image.open(io.BytesIO(data)) as candidate:
            candidate.verify()
        with Image.open(io.BytesIO(data)) as candidate:
            image = ImageOps.exif_transpose(candidate).copy()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise InputValidationError(f"{label} is not a valid image") from exc
    _validate_dimensions(image, label=label)
    return image


def load_target_image(path: str | Path) -> Image.Image:
    """Load a target photograph as an orientation-corrected RGB image."""

    source = Path(path)
    if source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise InputValidationError("Target must be JPEG, PNG, or WebP")
    return _open_raster(_read_limited(source), label="Target image").convert("RGB")


def _local_name(value: str) -> str:
    return value.rsplit("}", maxsplit=1)[-1]


def _validate_svg(data: bytes) -> None:
    lowered = data.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise InputValidationError("SVG declarations and entities are not allowed")
    try:
        root = DefusedET.fromstring(data)
    except DefusedET.ParseError as exc:
        raise InputValidationError("Logo is not valid SVG") from exc

    if _local_name(root.tag) != "svg":
        raise InputValidationError("Logo document root must be <svg>")

    for element in root.iter():
        if _local_name(element.tag) in UNSAFE_SVG_TAGS:
            raise InputValidationError(f"SVG element <{_local_name(element.tag)}> is not allowed")
        for attribute, raw_value in element.attrib.items():
            value = raw_value.strip().lower()
            attribute_name = _local_name(attribute)
            if attribute_name == "href" and value and not value.startswith("#"):
                raise InputValidationError("External or embedded SVG resources are not allowed")
            if any(prefix in value for prefix in UNSAFE_URI_PREFIXES):
                raise InputValidationError("External SVG references are not allowed")
            if "url(" in value and "url(#" not in value:
                raise InputValidationError("External SVG paint resources are not allowed")


def _render_svg(data: bytes) -> Image.Image:
    _validate_svg(data)
    try:
        import cairosvg

        rendered = cairosvg.svg2png(bytestring=data, output_width=2048)
    except (ImportError, ValueError, OSError) as exc:
        raise InputValidationError("SVG logo could not be rendered") from exc
    return _open_raster(rendered, label="Rendered SVG logo").convert("RGBA")


def _trim_transparent(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    if alpha.getbbox() is None:
        raise InputValidationError("Logo is fully transparent")
    if alpha.getextrema()[0] == 255:
        raise InputValidationError("PNG logo must include transparency")
    return image.crop(alpha.getbbox())


def load_logo_image(path: str | Path) -> Image.Image:
    """Load and trim a safe SVG or transparent PNG logo as RGBA."""

    source = Path(path)
    data = _read_limited(source)
    suffix = source.suffix.lower()
    if suffix == ".svg":
        image = _render_svg(data)
    elif suffix == ".png":
        image = _open_raster(data, label="PNG logo").convert("RGBA")
    else:
        raise InputValidationError("Logo must be SVG or transparent PNG")
    return _trim_transparent(image)
