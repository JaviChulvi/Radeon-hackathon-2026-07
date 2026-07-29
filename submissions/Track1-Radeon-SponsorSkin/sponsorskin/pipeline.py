"""End-to-end local pipeline with replaceable refinement backend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

from sponsorskin.compositing import CompositeArtifacts, create_composite, save_composite_artifacts
from sponsorskin.evaluation import evaluate_quality
from sponsorskin.inference import PassthroughRefiner, RefinementBackend, RefinementResult
from sponsorskin.projects import capture_environment, create_run_directory
from sponsorskin.restoration import RestorationResult, restore_exact_logo
from sponsorskin.schemas import (
    PlacementSettings,
    Point,
    QualityMetrics,
    RestorationSettings,
    RunManifest,
)
from sponsorskin.version import __version__

APP_VERSION = __version__


@dataclass(frozen=True)
class PipelineRun:
    """In-memory results and persisted location of a completed run."""

    run_directory: Path
    artifacts: CompositeArtifacts
    refinement: RefinementResult
    restoration: RestorationResult
    metrics: QualityMetrics
    manifest: RunManifest


def run_pipeline(
    target: Image.Image,
    logo: Image.Image,
    points: list[Point],
    *,
    output_root: str | Path,
    placement: PlacementSettings | None = None,
    restoration: RestorationSettings | None = None,
    backend: RefinementBackend | None = None,
    seed: int = 42,
) -> PipelineRun:
    """Run composition, refinement, restoration, evaluation, and persistence."""

    active_placement = placement or PlacementSettings()
    active_backend = backend or PassthroughRefiner()
    artifacts = create_composite(target, logo, points, active_placement)
    refinement = active_backend.refine(
        artifacts.rough_composite,
        artifacts.edit_mask,
        material=active_placement.material,
        seed=seed,
    )
    restored = restore_exact_logo(artifacts, refinement.image, restoration)
    metrics = evaluate_quality(artifacts, restored.image)

    run_id, run_directory = create_run_directory(output_root)
    save_composite_artifacts(artifacts, run_directory)
    logo.convert("RGBA").save(run_directory / "logo_original.png")
    refinement.image.save(run_directory / "refined.png")
    restored.image.save(run_directory / "final.png")
    restored.shading_map.save(run_directory / "shading_map.png")
    metrics_path = run_directory / "metrics.json"
    metrics_path.write_text(metrics.model_dump_json(indent=2), encoding="utf-8")

    output_files = {
        name: name
        for name in [
            "original.png",
            "logo_original.png",
            "logo_layer.png",
            "rough_composite.png",
            "edit_mask.png",
            "exact_alpha.png",
            "refined.png",
            "final.png",
            "shading_map.png",
        ]
    }
    manifest = RunManifest(
        run_id=run_id,
        created_at=datetime.now(UTC),
        app_version=APP_VERSION,
        backend=refinement.backend,
        model_id=refinement.model_id,
        seed=seed,
        placement=active_placement,
        ordered_points=[Point(x=x, y=y) for x, y in artifacts.ordered_points],
        environment=capture_environment(),
        backend_metadata={
            **refinement.metadata,
            "latency_seconds": refinement.latency_seconds,
        },
        output_files=output_files,
        metrics_file=metrics_path.name,
    )
    (run_directory / "manifest.json").write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return PipelineRun(
        run_directory=run_directory,
        artifacts=artifacts,
        refinement=refinement,
        restoration=restored,
        metrics=metrics,
        manifest=manifest,
    )
