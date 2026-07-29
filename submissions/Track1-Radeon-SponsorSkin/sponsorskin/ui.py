"""Thin Gradio callbacks for the local SponsorSkin workflow."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import gradio as gr
from PIL import Image, ImageDraw

from sponsorskin.compositing import CompositeArtifacts, create_composite
from sponsorskin.inference import (
    BackendUnavailableError,
    Flux2KleinRefiner,
    PassthroughRefiner,
    RefinementBackend,
)
from sponsorskin.pipeline import PipelineRun, run_pipeline
from sponsorskin.schemas import Flux2Settings, MaterialPreset, PlacementSettings, Point
from sponsorskin.validation import load_logo_image, load_target_image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = PROJECT_ROOT / "runs"
POINT_COLORS = ("#ff355e", "#ff9f1c", "#2ec4b6", "#4d96ff")
SPONSORSKIN_CSS = """
.sponsorskin-hero { padding: 1rem 0 0.5rem; }
.local-badge { border-left: 4px solid #e12d39; padding: 0.6rem 0.9rem; }
.primary-action button { font-weight: 700; }
"""


def backend_from_environment(
    *,
    strength: float,
    num_inference_steps: int,
) -> RefinementBackend:
    """Construct the explicitly selected app backend without loading model weights."""

    backend_name = os.getenv("SPONSORSKIN_BACKEND", "passthrough").strip().lower()
    if backend_name in {"passthrough", "local"}:
        return PassthroughRefiner()
    if backend_name in {"flux2", "flux2-klein-inpaint-rocm"}:
        return Flux2KleinRefiner(
            Flux2Settings(
                strength=strength,
                num_inference_steps=num_inference_steps,
                model_revision=os.getenv("SPONSORSKIN_MODEL_REVISION") or None,
                enable_cpu_offload=os.getenv("SPONSORSKIN_CPU_OFFLOAD", "0") == "1",
            )
        )
    raise ValueError(f"SPONSORSKIN_BACKEND must be 'passthrough' or 'flux2', not {backend_name!r}.")


def _point_models(points: list[tuple[float, float]] | None) -> list[Point]:
    coordinates = points or []
    if len(coordinates) != 4:
        raise ValueError("Select exactly four surface corners before continuing.")
    return [Point(x=x, y=y) for x, y in coordinates]


def placement_settings(
    scale: float,
    rotation: float,
    opacity: float,
    mask_padding: int,
    feather_radius: float,
    material: str,
) -> PlacementSettings:
    """Build validated settings from Gradio component values."""

    return PlacementSettings(
        scale=scale,
        rotation_degrees=rotation,
        opacity=opacity,
        mask_padding=mask_padding,
        feather_radius=feather_radius,
        material=material,
    )


def annotate_points(
    target: Image.Image,
    points: list[tuple[float, float]] | None,
) -> Image.Image:
    """Draw selection order without modifying the source image."""

    annotated = target.convert("RGB").copy()
    draw = ImageDraw.Draw(annotated)
    active_points = points or []
    if len(active_points) > 1:
        draw.line(active_points, fill="#ffffff", width=3, joint="curve")
    if len(active_points) == 4:
        draw.line([active_points[-1], active_points[0]], fill="#ffffff", width=3)
    radius = max(7, round(min(annotated.size) * 0.012))
    for index, (x_value, y_value) in enumerate(active_points):
        center = (round(x_value), round(y_value))
        bounds = (
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        )
        draw.ellipse(bounds, fill=POINT_COLORS[index], outline="#ffffff", width=2)
        draw.text(
            (center[0] + radius + 3, center[1] - radius),
            str(index + 1),
            fill="#ffffff",
            stroke_width=2,
            stroke_fill="#111111",
        )
    return annotated


def add_corner(
    target: Image.Image,
    points: list[tuple[float, float]] | None,
    coordinate: tuple[int | float, int | float],
) -> tuple[Image.Image, list[tuple[float, float]], str]:
    """Add one unique corner and return an annotated selection canvas."""

    active_points = list(points or [])
    if len(active_points) >= 4:
        return (
            annotate_points(target, active_points),
            active_points,
            "Four corners selected. Reset the selection to change them.",
        )
    x_value, y_value = float(coordinate[0]), float(coordinate[1])
    if not (0 <= x_value < target.width and 0 <= y_value < target.height):
        raise ValueError("Selected corner falls outside the target image.")
    if any((x_value - x) ** 2 + (y_value - y) ** 2 < 16 for x, y in active_points):
        raise ValueError("Select four distinct corners.")
    active_points.append((x_value, y_value))
    remaining = 4 - len(active_points)
    status = (
        "Four corners selected. Build a preview or adjust the controls."
        if remaining == 0
        else f"Corner {len(active_points)} recorded. Select {remaining} more."
    )
    return annotate_points(target, active_points), active_points, status


def load_target_canvas(target_path: str | None) -> tuple[Image.Image | None, list, str]:
    """Validate a target upload and initialize its selection state."""

    if not target_path:
        return None, [], "Upload a target photo to begin."
    target = load_target_image(target_path)
    return target, [], "Target ready. Click four corners on the surface in any order."


def reset_corner_selection(target_path: str | None) -> tuple[Image.Image | None, list, str]:
    """Clear points while retaining a valid uploaded target."""

    return load_target_canvas(target_path)


def select_corner(
    target_path: str | None,
    points: list[tuple[float, float]] | None,
    event: gr.SelectData,
) -> tuple[Image.Image, list[tuple[float, float]], str]:
    """Gradio selection adapter for :func:`add_corner`."""

    if not target_path:
        raise gr.Error("Upload a target photo before selecting corners.")
    coordinate = event.index
    if not isinstance(coordinate, (tuple, list)) or len(coordinate) != 2:
        raise gr.Error("The selected image coordinate could not be read.")
    try:
        return add_corner(load_target_image(target_path), points, coordinate)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc


def create_preview(
    target_path: str,
    logo_path: str,
    points: list[tuple[float, float]] | None,
    settings: PlacementSettings,
) -> CompositeArtifacts:
    """Create the deterministic visual preview used by the UI."""

    return create_composite(
        load_target_image(target_path),
        load_logo_image(logo_path),
        _point_models(points),
        settings,
    )


def run_local_generation(
    target_path: str,
    logo_path: str,
    points: list[tuple[float, float]] | None,
    settings: PlacementSettings,
    *,
    seed: int,
    runs_root: str | Path = RUNS_ROOT,
    backend: RefinementBackend | None = None,
) -> PipelineRun:
    """Run and persist the complete workflow with an explicitly selected backend."""

    return run_pipeline(
        load_target_image(target_path),
        load_logo_image(logo_path),
        _point_models(points),
        output_root=runs_root,
        placement=settings,
        backend=backend,
        seed=seed,
    )


def preview_for_ui(
    target_path: str | None,
    logo_path: str | None,
    points: list[tuple[float, float]] | None,
    scale: float,
    rotation: float,
    opacity: float,
    mask_padding: int,
    feather_radius: float,
    material: str,
) -> tuple[Image.Image, Image.Image, Image.Image, str]:
    """Validate UI inputs and return visual composition artifacts."""

    if not target_path or not logo_path:
        raise gr.Error("Upload both a target photo and a logo.")
    try:
        artifacts = create_preview(
            target_path,
            logo_path,
            points,
            placement_settings(
                scale,
                rotation,
                opacity,
                mask_padding,
                feather_radius,
                material,
            ),
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    return (
        artifacts.rough_composite,
        artifacts.edit_mask,
        artifacts.logo_layer,
        "Deterministic preview ready. No model or GPU was used.",
    )


def generate_for_ui(
    target_path: str | None,
    logo_path: str | None,
    points: list[tuple[float, float]] | None,
    scale: float,
    rotation: float,
    opacity: float,
    mask_padding: int,
    feather_radius: float,
    material: str,
    refinement_strength: float,
    inference_steps: int,
    seed: int,
) -> tuple[
    Image.Image,
    Image.Image,
    Image.Image,
    Image.Image,
    dict[str, Any],
    str,
    str,
    str,
]:
    """Run the local pipeline and adapt outputs for Gradio components."""

    if not target_path or not logo_path:
        raise gr.Error("Upload both a target photo and a logo.")
    try:
        backend = backend_from_environment(
            strength=refinement_strength,
            num_inference_steps=inference_steps,
        )
        result = run_local_generation(
            target_path,
            logo_path,
            points,
            placement_settings(
                scale,
                rotation,
                opacity,
                mask_padding,
                feather_radius,
                material,
            ),
            seed=seed,
            backend=backend,
        )
    except (BackendUnavailableError, ValueError) as exc:
        raise gr.Error(str(exc)) from exc
    return (
        result.artifacts.original,
        result.artifacts.rough_composite,
        result.refinement.image,
        result.restoration.image,
        result.metrics.model_dump(mode="json"),
        str(result.run_directory / "final.png"),
        str(result.run_directory / "manifest.json"),
        (
            (
                f"Local run `{result.run_directory.name}` completed with the passthrough backend. "
                "No generative model or Radeon GPU was used."
            )
            if result.manifest.backend == "local-passthrough"
            else (
                f"Radeon run `{result.run_directory.name}` completed with "
                f"`{result.manifest.backend}` in "
                f"{result.refinement.latency_seconds:.3f} seconds."
            )
        ),
    )


def build_app() -> gr.Blocks:
    """Build the SponsorSkin local development application."""

    radeon_mode = os.getenv("SPONSORSKIN_BACKEND", "passthrough").strip().lower() in {
        "flux2",
        "flux2-klein-inpaint-rocm",
    }
    mode_title = "RADEON FLUX.2 MODE" if radeon_mode else "LOCAL PASSTHROUGH MODE"
    mode_description = (
        "runs masked FLUX.2 Klein inference through ROCm and records measured device evidence."
        if radeon_mode
        else (
            "validates the complete workflow, restoration, metrics, and exports without running "
            "a generative model or claiming Radeon performance."
        )
    )
    with gr.Blocks(title="Radeon SponsorSkin") as demo:
        points_state = gr.State([])
        gr.Markdown(
            f"""
            # Radeon SponsorSkin · Creation Lab
            Turn a photo and an authorized logo into a perspective-correct sponsorship mockup.

            <div class="local-badge"><strong>{mode_title}</strong> —
            {mode_description}</div>
            """,
            elem_classes="sponsorskin-hero",
        )

        with gr.Row():
            with gr.Column(scale=2):
                target_file = gr.File(
                    label="1 · Target photo (JPEG, PNG, or WebP)",
                    file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    type="filepath",
                )
                logo_file = gr.File(
                    label="2 · Authorized logo (SVG or transparent PNG)",
                    file_types=[".svg", ".png"],
                    type="filepath",
                )
                selection_canvas = gr.Image(
                    label="3 · Click four surface corners",
                    type="pil",
                    interactive=False,
                    buttons=["fullscreen"],
                    height=520,
                )
                placement_status = gr.Markdown("Upload a target photo to begin.")
                reset_button = gr.Button("Reset corners", variant="secondary")
            with gr.Column(scale=1):
                gr.Markdown("### Placement controls")
                scale = gr.Slider(0.1, 1.0, value=0.9, step=0.01, label="Logo scale")
                rotation = gr.Slider(-180, 180, value=0, step=1, label="Rotation (degrees)")
                opacity = gr.Slider(0.1, 1.0, value=1, step=0.01, label="Opacity")
                mask_padding = gr.Slider(0, 128, value=12, step=1, label="Mask padding")
                feather_radius = gr.Slider(0, 64, value=6, step=0.5, label="Mask feather")
                material = gr.Dropdown(
                    choices=[preset.value for preset in MaterialPreset],
                    value=MaterialPreset.VINYL.value,
                    label="Surface material",
                )
                gr.Markdown("### Refinement controls")
                refinement_strength = gr.Slider(
                    0.1,
                    1.0,
                    value=0.65,
                    step=0.05,
                    label="Refinement strength (FLUX.2 mode)",
                )
                inference_steps = gr.Slider(
                    1,
                    20,
                    value=4,
                    step=1,
                    label="Inference steps (FLUX.2 mode)",
                )
                seed = gr.Number(value=42, precision=0, label="Seed")
                preview_button = gr.Button("Build deterministic preview")
                generate_button = gr.Button(
                    (
                        "Run Radeon FLUX.2 pipeline"
                        if radeon_mode
                        else "Run complete local pipeline"
                    ),
                    variant="primary",
                    elem_classes="primary-action",
                )
                action_status = gr.Markdown("Ready.")

        with gr.Tabs():
            with gr.Tab("Preview artifacts"), gr.Row():
                rough_preview = gr.Image(label="Rough composite", type="pil")
                mask_preview = gr.Image(label="Edit mask", type="pil")
                logo_preview = gr.Image(label="Exact warped logo", type="pil")
            with gr.Tab("Pipeline comparison"), gr.Row():
                original_result = gr.Image(label="Original", type="pil")
                rough_result = gr.Image(label="Rough", type="pil")
                refined_result = gr.Image(
                    label=("Refined (FLUX.2)" if radeon_mode else "Refined (passthrough)"),
                    type="pil",
                )
                final_result = gr.Image(label="Final", type="pil")
            with gr.Tab("Quality & downloads"):
                metrics_json = gr.JSON(label="Quality metrics")
                with gr.Row():
                    final_download = gr.File(label="Download final PNG")
                    manifest_download = gr.File(label="Download run manifest")

        setting_inputs = [
            target_file,
            logo_file,
            points_state,
            scale,
            rotation,
            opacity,
            mask_padding,
            feather_radius,
            material,
        ]
        target_file.change(
            load_target_canvas,
            inputs=target_file,
            outputs=[selection_canvas, points_state, placement_status],
        )
        selection_canvas.select(
            select_corner,
            inputs=[target_file, points_state],
            outputs=[selection_canvas, points_state, placement_status],
        )
        reset_button.click(
            reset_corner_selection,
            inputs=target_file,
            outputs=[selection_canvas, points_state, placement_status],
        )
        preview_button.click(
            preview_for_ui,
            inputs=setting_inputs,
            outputs=[rough_preview, mask_preview, logo_preview, action_status],
        )
        generate_button.click(
            generate_for_ui,
            inputs=[*setting_inputs, refinement_strength, inference_steps, seed],
            outputs=[
                original_result,
                rough_result,
                refined_result,
                final_result,
                metrics_json,
                final_download,
                manifest_download,
                action_status,
            ],
        )
    return demo
