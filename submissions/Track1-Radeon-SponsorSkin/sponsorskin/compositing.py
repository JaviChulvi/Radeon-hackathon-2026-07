"""Deterministic exact-logo preparation, warping, masking, and compositing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from sponsorskin.geometry import perspective_matrix, validate_quadrilateral
from sponsorskin.schemas import PlacementSettings, Point


@dataclass(frozen=True)
class CompositeArtifacts:
    """All deterministic outputs needed by refinement and evaluation."""

    original: Image.Image
    logo_layer: Image.Image
    rough_composite: Image.Image
    edit_mask: Image.Image
    exact_alpha: Image.Image
    ordered_points: tuple[tuple[float, float], ...]


def prepare_logo(logo: Image.Image, settings: PlacementSettings) -> Image.Image:
    """Scale, rotate, and apply opacity without changing the source canvas aspect."""

    rgba = logo.convert("RGBA")
    canvas = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    scaled_size = (
        max(1, round(rgba.width * settings.scale)),
        max(1, round(rgba.height * settings.scale)),
    )
    scaled = rgba.resize(scaled_size, Image.Resampling.LANCZOS)
    offset = ((rgba.width - scaled.width) // 2, (rgba.height - scaled.height) // 2)
    canvas.alpha_composite(scaled, offset)
    if settings.rotation_degrees:
        canvas = canvas.rotate(
            settings.rotation_degrees,
            resample=Image.Resampling.BICUBIC,
            expand=False,
        )
    if settings.opacity < 1:
        alpha = canvas.getchannel("A").point(lambda value: round(value * settings.opacity))
        canvas.putalpha(alpha)
    return canvas


def _warp_logo(
    logo: Image.Image,
    *,
    target_size: tuple[int, int],
    destination_points: np.ndarray,
) -> Image.Image:
    logo_array = np.asarray(logo, dtype=np.uint8)
    matrix = perspective_matrix(logo.size, destination_points)
    target_width, target_height = target_size
    warped = cv2.warpPerspective(
        logo_array,
        matrix,
        (target_width, target_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    return Image.fromarray(warped, mode="RGBA")


def _create_edit_mask(
    exact_alpha: Image.Image,
    *,
    padding: int,
    feather_radius: float,
) -> Image.Image:
    mask = np.where(np.asarray(exact_alpha, dtype=np.uint8) > 0, 255, 0).astype(np.uint8)
    if padding:
        kernel_size = padding * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        mask = cv2.dilate(mask, kernel)
    if feather_radius:
        mask = cv2.GaussianBlur(mask, (0, 0), sigmaX=feather_radius, sigmaY=feather_radius)
    return Image.fromarray(mask, mode="L")


def create_composite(
    target: Image.Image,
    logo: Image.Image,
    points: list[Point],
    settings: PlacementSettings | None = None,
) -> CompositeArtifacts:
    """Create the exact rough composite and masks for a selected surface."""

    active_settings = settings or PlacementSettings()
    original = target.convert("RGB")
    ordered = validate_quadrilateral(points, image_size=original.size)
    prepared_logo = prepare_logo(logo, active_settings)
    logo_layer = _warp_logo(
        prepared_logo,
        target_size=original.size,
        destination_points=ordered,
    )
    exact_alpha = logo_layer.getchannel("A")
    rough = Image.alpha_composite(original.convert("RGBA"), logo_layer).convert("RGB")
    edit_mask = _create_edit_mask(
        exact_alpha,
        padding=active_settings.mask_padding,
        feather_radius=active_settings.feather_radius,
    )
    return CompositeArtifacts(
        original=original,
        logo_layer=logo_layer,
        rough_composite=rough,
        edit_mask=edit_mask,
        exact_alpha=exact_alpha,
        ordered_points=tuple((float(x), float(y)) for x, y in ordered),
    )


def save_composite_artifacts(artifacts: CompositeArtifacts, output_dir: str | Path) -> Path:
    """Persist deterministic outputs without overwriting the input files."""

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    artifacts.original.save(destination / "original.png")
    artifacts.logo_layer.save(destination / "logo_layer.png")
    artifacts.rough_composite.save(destination / "rough_composite.png")
    artifacts.edit_mask.save(destination / "edit_mask.png")
    artifacts.exact_alpha.save(destination / "exact_alpha.png")
    return destination
