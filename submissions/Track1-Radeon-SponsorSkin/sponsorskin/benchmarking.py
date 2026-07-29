"""Reproducible CPU-safe benchmark for the complete local artifact path."""

from __future__ import annotations

import statistics
import tempfile
import tracemalloc
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from PIL import Image, ImageDraw

from sponsorskin.pipeline import run_pipeline
from sponsorskin.schemas import PlacementSettings, Point
from sponsorskin.telemetry import collect_telemetry


def _synthetic_inputs(
    width: int,
    height: int,
) -> tuple[Image.Image, Image.Image, list[Point]]:
    target = Image.new("RGB", (width, height), (37, 47, 61))
    draw = ImageDraw.Draw(target)
    margin_x, margin_y = round(width * 0.12), round(height * 0.14)
    draw.rectangle(
        (margin_x, margin_y, width - margin_x, height - margin_y),
        fill=(194, 180, 155),
        outline=(230, 220, 205),
        width=max(2, round(min(width, height) * 0.01)),
    )
    logo_width, logo_height = max(64, width // 3), max(32, height // 7)
    logo = Image.new("RGBA", (logo_width, logo_height), (0, 0, 0, 0))
    logo_draw = ImageDraw.Draw(logo)
    inset = max(4, logo_height // 12)
    logo_draw.rounded_rectangle(
        (inset, inset, logo_width - inset, logo_height - inset),
        radius=max(4, logo_height // 6),
        fill=(225, 33, 48, 255),
    )
    points = [
        Point(x=width * 0.2, y=height * 0.25),
        Point(x=width * 0.8, y=height * 0.23),
        Point(x=width * 0.78, y=height * 0.75),
        Point(x=width * 0.22, y=height * 0.77),
    ]
    return target, logo, points


def benchmark_local_pipeline(
    *,
    iterations: int = 5,
    width: int = 1280,
    height: int = 768,
) -> dict[str, Any]:
    """Measure the full passthrough pipeline without implying GPU performance."""

    if iterations < 2:
        raise ValueError("Benchmark requires at least two iterations")
    if width < 64 or height < 64:
        raise ValueError("Benchmark dimensions must be at least 64px per side")

    target, logo, points = _synthetic_inputs(width, height)
    timings: list[float] = []
    run_metrics: dict[str, Any] | None = None
    tracemalloc.start()
    with tempfile.TemporaryDirectory(prefix="sponsorskin-benchmark-") as temporary_root:
        for iteration in range(iterations):
            started_at = perf_counter()
            result = run_pipeline(
                target,
                logo,
                points,
                output_root=temporary_root,
                placement=PlacementSettings(
                    scale=0.9,
                    mask_padding=12,
                    feather_radius=6,
                ),
                seed=42,
            )
            timings.append(perf_counter() - started_at)
            if iteration == iterations - 1:
                run_metrics = result.metrics.model_dump(mode="json")
    _, peak_python_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    warm_timings = timings[1:]
    return {
        "schema_version": "1.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "benchmark": "complete-local-passthrough-pipeline",
        "scope": "CPU-safe local development benchmark; no generative model or Radeon GPU used",
        "backend": "local-passthrough",
        "image": {"width": width, "height": height, "pixels": width * height},
        "iterations": iterations,
        "seed": 42,
        "timings_seconds": {
            "first_run": timings[0],
            "warm_runs": warm_timings,
            "warm_mean": statistics.mean(warm_timings),
            "warm_median": statistics.median(warm_timings),
            "warm_min": min(warm_timings),
            "warm_max": max(warm_timings),
        },
        "python_tracemalloc_peak_bytes": peak_python_bytes,
        "quality_metrics": run_metrics,
        "environment": collect_telemetry(),
    }
