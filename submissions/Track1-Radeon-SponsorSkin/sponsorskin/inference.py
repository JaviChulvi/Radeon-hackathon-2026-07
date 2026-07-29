"""Refinement backend contract shared by local and future Radeon execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

from PIL import Image

from sponsorskin.schemas import MaterialPreset


@dataclass(frozen=True)
class RefinementResult:
    """Image and provenance returned by a refinement backend."""

    image: Image.Image
    backend: str
    model_id: str | None
    latency_seconds: float
    metadata: dict[str, Any] = field(default_factory=dict)


class RefinementBackend(Protocol):
    """Interface implemented by local preview and Radeon model backends."""

    name: str
    model_id: str | None

    def refine(
        self,
        rough_composite: Image.Image,
        edit_mask: Image.Image,
        *,
        material: MaterialPreset,
        seed: int,
    ) -> RefinementResult:
        """Refine one rough composite while respecting the edit mask."""


class PassthroughRefiner:
    """Local backend that exercises the pipeline without claiming AI inference."""

    name = "local-passthrough"
    model_id = None

    def refine(
        self,
        rough_composite: Image.Image,
        edit_mask: Image.Image,
        *,
        material: MaterialPreset,
        seed: int,
    ) -> RefinementResult:
        del edit_mask
        started_at = perf_counter()
        image = rough_composite.copy()
        elapsed = perf_counter() - started_at
        return RefinementResult(
            image=image,
            backend=self.name,
            model_id=self.model_id,
            latency_seconds=elapsed,
            metadata={
                "material": material.value,
                "seed": seed,
                "notice": "Deterministic local preview; no generative model was executed.",
            },
        )
