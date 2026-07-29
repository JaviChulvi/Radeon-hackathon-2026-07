"""Typed configuration models used by the deterministic pipeline."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MaterialPreset(StrEnum):
    """Material choices shared by the local and future Radeon backends."""

    VINYL = "vinyl"
    FABRIC_PRINT = "fabric_print"
    BILLBOARD = "billboard"
    PAINTED_WALL = "painted_wall"


class Point(BaseModel):
    """A two-dimensional image coordinate."""

    model_config = ConfigDict(frozen=True)

    x: float = Field(ge=0)
    y: float = Field(ge=0)


class PlacementSettings(BaseModel):
    """Controls deterministic placement before generative refinement."""

    model_config = ConfigDict(frozen=True)

    scale: float = Field(default=0.9, gt=0, le=1.0)
    rotation_degrees: float = Field(default=0.0, ge=-180.0, le=180.0)
    opacity: float = Field(default=1.0, gt=0, le=1.0)
    mask_padding: int = Field(default=12, ge=0, le=128)
    feather_radius: float = Field(default=6.0, ge=0, le=64)
    material: MaterialPreset = MaterialPreset.VINYL


class RestorationSettings(BaseModel):
    """Controls how generated illumination is transferred to the exact logo."""

    model_config = ConfigDict(frozen=True)

    shading_strength: float = Field(default=0.65, ge=0, le=1)
    minimum_multiplier: float = Field(default=0.65, gt=0, le=1)
    maximum_multiplier: float = Field(default=1.35, ge=1, le=3)
    smoothing_radius: float = Field(default=10.0, ge=0, le=64)


class QualityMetrics(BaseModel):
    """Measured quality signals for a completed pipeline run."""

    outside_changed_ratio: float = Field(ge=0, le=1)
    outside_mean_absolute_error: float = Field(ge=0)
    outside_ssim: float = Field(ge=-1, le=1)
    logo_mean_delta_e: float = Field(ge=0)
    logo_p95_delta_e: float = Field(ge=0)
    logo_sharpness: float = Field(ge=0)
    edit_mask_coverage: float = Field(ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class EnvironmentSnapshot(BaseModel):
    """Runtime facts captured without requiring PyTorch locally."""

    python_version: str
    platform: str
    machine: str
    torch_version: str | None = None
    rocm_version: str | None = None
    gpu_name: str | None = None


class RunManifest(BaseModel):
    """Reproducibility record stored beside every generated image."""

    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    created_at: datetime
    app_version: str
    backend: str
    model_id: str | None = None
    seed: int
    placement: PlacementSettings
    ordered_points: list[Point]
    environment: EnvironmentSnapshot
    backend_metadata: dict[str, Any] = Field(default_factory=dict)
    output_files: dict[str, str]
    metrics_file: str
