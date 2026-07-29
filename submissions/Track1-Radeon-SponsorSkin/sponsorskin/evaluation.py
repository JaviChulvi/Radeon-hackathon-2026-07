"""Quality metrics and warnings for SponsorSkin pipeline outputs."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image
from skimage.color import deltaE_ciede2000, rgb2lab
from skimage.metrics import structural_similarity

from sponsorskin.compositing import CompositeArtifacts
from sponsorskin.schemas import QualityMetrics


def evaluate_quality(artifacts: CompositeArtifacts, final: Image.Image) -> QualityMetrics:
    """Compare a final image with deterministic references and protected pixels."""

    if final.size != artifacts.original.size:
        raise ValueError("Final image size must match the original image")

    original = np.asarray(artifacts.original, dtype=np.uint8)
    rough = np.asarray(artifacts.rough_composite, dtype=np.uint8)
    result = np.asarray(final.convert("RGB"), dtype=np.uint8)
    edit_mask = np.asarray(artifacts.edit_mask, dtype=np.uint8)
    exact_alpha = np.asarray(artifacts.exact_alpha, dtype=np.uint8)
    outside = edit_mask <= 1

    absolute_difference = np.abs(result.astype(np.int16) - original.astype(np.int16))
    changed = np.any(absolute_difference > 1, axis=2)
    outside_changed_ratio = float(changed[outside].mean()) if np.any(outside) else 0.0
    outside_mae = float(absolute_difference[outside].mean()) if np.any(outside) else 0.0

    outside_only_result = result.copy()
    outside_only_result[~outside] = original[~outside]
    outside_ssim = float(
        structural_similarity(
            original,
            outside_only_result,
            channel_axis=2,
            data_range=255,
        )
    )

    logo_interior = exact_alpha >= 230
    if not np.any(logo_interior):
        logo_interior = exact_alpha > 0
    rough_lab = rgb2lab(rough.astype(np.float32) / 255)
    result_lab = rgb2lab(result.astype(np.float32) / 255)
    delta_e = deltaE_ciede2000(rough_lab, result_lab)[logo_interior]
    mean_delta_e = float(delta_e.mean()) if delta_e.size else 0.0
    p95_delta_e = float(np.percentile(delta_e, 95)) if delta_e.size else 0.0

    grayscale = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
    laplacian = cv2.Laplacian(grayscale, cv2.CV_64F)
    logo_pixels = exact_alpha > 0
    sharpness = float(laplacian[logo_pixels].var()) if np.any(logo_pixels) else 0.0
    coverage = float((edit_mask > 0).mean())

    warnings: list[str] = []
    if outside_changed_ratio > 0.001:
        warnings.append("Pixels outside the edit mask changed.")
    if outside_ssim < 0.995:
        warnings.append("Outside-mask structural preservation is below target.")
    if mean_delta_e > 15:
        warnings.append("Logo colors drifted substantially from the rough composite.")
    if sharpness < 20:
        warnings.append("The restored logo may be too soft.")

    return QualityMetrics(
        outside_changed_ratio=outside_changed_ratio,
        outside_mean_absolute_error=outside_mae,
        outside_ssim=outside_ssim,
        logo_mean_delta_e=mean_delta_e,
        logo_p95_delta_e=p95_delta_e,
        logo_sharpness=sharpness,
        edit_mask_coverage=coverage,
        warnings=warnings,
    )
