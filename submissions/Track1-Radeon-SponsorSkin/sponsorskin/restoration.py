"""Reintroduce exact logo geometry while retaining local illumination."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from sponsorskin.compositing import CompositeArtifacts
from sponsorskin.schemas import RestorationSettings


@dataclass(frozen=True)
class RestorationResult:
    """Restored final image and a visualizable illumination map."""

    image: Image.Image
    shading_map: Image.Image


def _srgb_to_linear(values: np.ndarray) -> np.ndarray:
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, 0, 1)
    return np.where(clipped <= 0.0031308, clipped * 12.92, 1.055 * clipped ** (1 / 2.4) - 0.055)


def _as_linear_rgb(image: Image.Image) -> np.ndarray:
    return _srgb_to_linear(np.asarray(image.convert("RGB"), dtype=np.float32) / 255)


def _luminance(linear_rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * linear_rgb[..., 0] + 0.7152 * linear_rgb[..., 1] + 0.0722 * linear_rgb[..., 2]


def _smooth_ratio(
    ratio: np.ndarray,
    valid: np.ndarray,
    smoothing_radius: float,
) -> np.ndarray:
    if not smoothing_radius:
        return np.where(valid, ratio, 1.0)
    sigma = float(smoothing_radius)
    weights = cv2.GaussianBlur(valid.astype(np.float32), (0, 0), sigmaX=sigma, sigmaY=sigma)
    weighted = cv2.GaussianBlur(
        np.where(valid, ratio, 0).astype(np.float32),
        (0, 0),
        sigmaX=sigma,
        sigmaY=sigma,
    )
    return np.where(weights > 1e-5, weighted / np.maximum(weights, 1e-5), 1.0)


def restore_exact_logo(
    artifacts: CompositeArtifacts,
    refined: Image.Image,
    settings: RestorationSettings | None = None,
) -> RestorationResult:
    """Restore logo pixels and force preservation outside the edit mask."""

    active_settings = settings or RestorationSettings()
    if refined.size != artifacts.original.size:
        raise ValueError("Refined image size must match the original image")

    refined_rgb = refined.convert("RGB")
    rough_rgb = np.asarray(artifacts.rough_composite, dtype=np.uint8)
    if np.array_equal(np.asarray(refined_rgb, dtype=np.uint8), rough_rgb):
        alpha = np.asarray(artifacts.exact_alpha, dtype=np.uint8)
        neutral_value = round(
            (1 - active_settings.minimum_multiplier)
            / (active_settings.maximum_multiplier - active_settings.minimum_multiplier)
            * 255
        )
        shading_visual = np.where(alpha > 0, neutral_value, 0).astype(np.uint8)
        return RestorationResult(
            image=refined_rgb.copy(),
            shading_map=Image.fromarray(shading_visual, mode="L"),
        )

    original_linear = _as_linear_rgb(artifacts.original)
    rough_linear = _as_linear_rgb(artifacts.rough_composite)
    refined_linear = _as_linear_rgb(refined_rgb)
    logo_linear = _as_linear_rgb(artifacts.logo_layer)
    alpha = np.asarray(artifacts.exact_alpha, dtype=np.float32) / 255
    valid = alpha >= 0.2

    rough_luminance = _luminance(rough_linear)
    refined_luminance = _luminance(refined_linear)
    raw_ratio = refined_luminance / np.maximum(rough_luminance, 1e-4)
    raw_ratio = np.clip(
        raw_ratio,
        active_settings.minimum_multiplier,
        active_settings.maximum_multiplier,
    )
    smooth_ratio = _smooth_ratio(raw_ratio, valid, active_settings.smoothing_radius)
    ratio = 1 + (smooth_ratio - 1) * active_settings.shading_strength

    shaded_logo = np.clip(logo_linear * ratio[..., None], 0, 1)
    desired_logo_composite = (
        original_linear * (1 - alpha[..., None]) + shaded_logo * alpha[..., None]
    )
    candidate = refined_linear.copy()
    candidate[alpha > 0] = desired_logo_composite[alpha > 0]

    edit_weight = np.asarray(artifacts.edit_mask, dtype=np.float32) / 255
    final_linear = (
        original_linear * (1 - edit_weight[..., None]) + candidate * edit_weight[..., None]
    )
    final = np.round(_linear_to_srgb(final_linear) * 255).astype(np.uint8)
    original = np.asarray(artifacts.original, dtype=np.uint8)
    final[edit_weight == 0] = original[edit_weight == 0]

    shading_visual = np.round(
        np.clip(
            (ratio - active_settings.minimum_multiplier)
            / (active_settings.maximum_multiplier - active_settings.minimum_multiplier),
            0,
            1,
        )
        * 255
    ).astype(np.uint8)
    shading_visual[alpha == 0] = 0
    return RestorationResult(
        image=Image.fromarray(final, mode="RGB"),
        shading_map=Image.fromarray(shading_visual, mode="L"),
    )
