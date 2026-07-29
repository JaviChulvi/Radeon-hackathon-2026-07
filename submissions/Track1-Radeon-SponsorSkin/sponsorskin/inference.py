"""Refinement backend contract shared by local and future Radeon execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol

from PIL import Image

from sponsorskin.prompts import material_prompt
from sponsorskin.schemas import Flux2Settings, MaterialPreset

DIFFUSERS_REVISION = "9e969b6cf0588fd75fbacee9a39d16a3f5c56fc4"


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


class BackendUnavailableError(RuntimeError):
    """Raised when a selected refinement backend cannot run in this environment."""


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


def model_safe_size(
    image_size: tuple[int, int],
    *,
    maximum_pixels: int,
    multiple: int = 16,
) -> tuple[int, int]:
    """Fit an image to an area budget and model-compatible dimensions."""

    width, height = image_size
    scale = min(1.0, (maximum_pixels / (width * height)) ** 0.5)
    safe_width = max(multiple, int(width * scale) // multiple * multiple)
    safe_height = max(multiple, int(height * scale) // multiple * multiple)
    return safe_width, safe_height


def validate_rocm_runtime(torch_module: Any) -> dict[str, Any]:
    """Fail closed unless PyTorch exposes a real ROCm accelerator."""

    rocm_version = getattr(torch_module.version, "hip", None)
    cuda_available = bool(torch_module.cuda.is_available())
    device_count = torch_module.cuda.device_count() if cuda_available else 0
    if not rocm_version:
        raise BackendUnavailableError(
            "The FLUX.2 backend requires the platform ROCm PyTorch build; "
            "torch.version.hip is empty."
        )
    if not cuda_available or device_count < 1:
        raise BackendUnavailableError(
            "ROCm PyTorch is installed, but no accelerator is available through torch.cuda."
        )
    return {
        "torch_version": torch_module.__version__,
        "rocm_version": rocm_version,
        "device_count": device_count,
        "device_name": torch_module.cuda.get_device_name(0),
        "total_memory_bytes": torch_module.cuda.get_device_properties(0).total_memory,
        "bf16_supported": bool(getattr(torch_module.cuda, "is_bf16_supported", lambda: False)()),
    }


class Flux2KleinRefiner:
    """Lazy FLUX.2 Klein masked-refinement backend intended for Radeon Cloud."""

    name = "flux2-klein-inpaint-rocm"

    def __init__(self, settings: Flux2Settings | None = None) -> None:
        self.settings = settings or Flux2Settings()
        self.model_id = self.settings.model_id
        self._pipeline: Any | None = None
        self._torch: Any | None = None
        self._runtime: dict[str, Any] | None = None
        self._diffusers_version: str | None = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        try:
            import torch
        except ImportError as exc:
            raise BackendUnavailableError(
                "PyTorch is not installed. Keep and use the Radeon Cloud platform ROCm build."
            ) from exc

        runtime = validate_rocm_runtime(torch) if self.settings.require_rocm else {}
        if not self.settings.require_rocm and not torch.cuda.is_available():
            raise BackendUnavailableError("No accelerator is available through torch.cuda.")
        try:
            import diffusers
            from diffusers import Flux2KleinInpaintPipeline
        except (ImportError, RuntimeError) as exc:
            raise BackendUnavailableError(
                "The pinned Radeon inference dependencies are missing. "
                "Install requirements-radeon.txt without replacing platform PyTorch."
            ) from exc

        load_arguments: dict[str, Any] = {"torch_dtype": torch.bfloat16}
        if self.settings.model_revision:
            load_arguments["revision"] = self.settings.model_revision
        pipeline = Flux2KleinInpaintPipeline.from_pretrained(
            self.settings.model_id,
            **load_arguments,
        )
        if self.settings.enable_cpu_offload:
            pipeline.enable_model_cpu_offload()
        else:
            pipeline.to("cuda")
        self._pipeline = pipeline
        self._torch = torch
        self._runtime = runtime
        self._diffusers_version = diffusers.__version__

    def refine(
        self,
        rough_composite: Image.Image,
        edit_mask: Image.Image,
        *,
        material: MaterialPreset,
        seed: int,
    ) -> RefinementResult:
        """Run masked BF16 inference and return measured Radeon provenance."""

        self._load()
        torch = self._torch
        pipeline = self._pipeline
        if torch is None or pipeline is None:
            raise BackendUnavailableError("FLUX.2 pipeline initialization did not complete.")

        original_size = rough_composite.size
        inference_size = model_safe_size(
            original_size,
            maximum_pixels=self.settings.maximum_pixels,
        )
        model_image = rough_composite.convert("RGB").resize(
            inference_size,
            Image.Resampling.LANCZOS,
        )
        model_mask = edit_mask.convert("L").resize(
            inference_size,
            Image.Resampling.BILINEAR,
        )
        generator = torch.Generator(device="cuda").manual_seed(seed)
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started_at = perf_counter()
        output = pipeline(
            prompt=material_prompt(material),
            image=model_image,
            mask_image=model_mask,
            height=inference_size[1],
            width=inference_size[0],
            padding_mask_crop=self.settings.padding_mask_crop,
            strength=self.settings.strength,
            num_inference_steps=self.settings.num_inference_steps,
            guidance_scale=self.settings.guidance_scale,
            generator=generator,
        )
        torch.cuda.synchronize()
        latency = perf_counter() - started_at
        refined = output.images[0].convert("RGB")
        if refined.size != original_size:
            refined = refined.resize(original_size, Image.Resampling.LANCZOS)

        return RefinementResult(
            image=refined,
            backend=self.name,
            model_id=self.model_id,
            latency_seconds=latency,
            metadata={
                "material": material.value,
                "prompt": material_prompt(material),
                "model_revision": self.settings.model_revision,
                "input_size": list(original_size),
                "inference_size": list(inference_size),
                "num_inference_steps": self.settings.num_inference_steps,
                "strength": self.settings.strength,
                "guidance_scale": self.settings.guidance_scale,
                "padding_mask_crop": self.settings.padding_mask_crop,
                "seed": seed,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                "diffusers_version": self._diffusers_version,
                "diffusers_revision": DIFFUSERS_REVISION,
                **(self._runtime or {}),
            },
        )
