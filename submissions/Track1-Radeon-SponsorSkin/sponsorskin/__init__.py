"""Radeon SponsorSkin application package."""

from sponsorskin.compositing import CompositeArtifacts, create_composite
from sponsorskin.pipeline import PipelineRun, run_pipeline
from sponsorskin.schemas import PlacementSettings, Point

__all__ = [
    "CompositeArtifacts",
    "PipelineRun",
    "PlacementSettings",
    "Point",
    "create_composite",
    "run_pipeline",
]

__version__ = "0.2.0"
