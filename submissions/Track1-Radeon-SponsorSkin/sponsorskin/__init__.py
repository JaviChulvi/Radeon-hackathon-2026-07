"""Radeon SponsorSkin application package."""

from sponsorskin.compositing import CompositeArtifacts, create_composite
from sponsorskin.schemas import PlacementSettings, Point

__all__ = [
    "CompositeArtifacts",
    "PlacementSettings",
    "Point",
    "create_composite",
]

__version__ = "0.1.0"
