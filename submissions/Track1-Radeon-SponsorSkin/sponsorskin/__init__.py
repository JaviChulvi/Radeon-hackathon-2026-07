"""Radeon SponsorSkin application package."""

from sponsorskin.compositing import CompositeArtifacts, create_composite
from sponsorskin.pipeline import PipelineRun, run_pipeline
from sponsorskin.schemas import PlacementSettings, Point
from sponsorskin.version import __version__

__all__ = [
    "CompositeArtifacts",
    "PipelineRun",
    "PlacementSettings",
    "Point",
    "__version__",
    "create_composite",
    "run_pipeline",
]
