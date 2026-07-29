"""Typed configuration models used by the deterministic pipeline."""

from enum import StrEnum

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
