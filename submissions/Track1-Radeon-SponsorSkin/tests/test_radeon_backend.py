from __future__ import annotations

from types import SimpleNamespace

import pytest
from PIL import Image

from sponsorskin.inference import (
    BackendUnavailableError,
    Flux2KleinRefiner,
    model_safe_size,
    validate_rocm_runtime,
)
from sponsorskin.prompts import material_prompt
from sponsorskin.schemas import Flux2Settings, MaterialPreset


class FakeCuda:
    def __init__(self, available: bool) -> None:
        self.available = available

    def is_available(self) -> bool:
        return self.available

    def device_count(self) -> int:
        return 1 if self.available else 0

    def get_device_name(self, index: int) -> str:
        assert index == 0
        return "Fake Radeon"

    def get_device_properties(self, index: int) -> SimpleNamespace:
        assert index == 0
        return SimpleNamespace(total_memory=48 * 1024**3)

    def is_bf16_supported(self) -> bool:
        return True

    def reset_peak_memory_stats(self) -> None:
        pass

    def synchronize(self) -> None:
        pass

    def max_memory_allocated(self) -> int:
        return 12 * 1024**3


class FakeGenerator:
    def __init__(self, *, device: str) -> None:
        assert device == "cuda"

    def manual_seed(self, seed: int) -> FakeGenerator:
        assert seed == 42
        return self


class FakePipeline:
    def __call__(self, **arguments):
        assert arguments["mask_image"].mode == "L"
        assert arguments["height"] % 16 == 0
        assert arguments["width"] % 16 == 0
        return SimpleNamespace(images=[arguments["image"].copy()])


def fake_torch(*, hip: str | None, available: bool) -> SimpleNamespace:
    return SimpleNamespace(
        __version__="2.9.0+rocm",
        version=SimpleNamespace(hip=hip),
        cuda=FakeCuda(available),
        Generator=FakeGenerator,
    )


def test_rocm_validation_records_measured_device() -> None:
    report = validate_rocm_runtime(fake_torch(hip="7.2.0", available=True))

    assert report["rocm_version"] == "7.2.0"
    assert report["device_name"] == "Fake Radeon"
    assert report["total_memory_bytes"] == 48 * 1024**3


@pytest.mark.parametrize(
    ("hip", "available"),
    [(None, True), ("7.2.0", False)],
)
def test_rocm_validation_fails_closed(hip: str | None, available: bool) -> None:
    with pytest.raises(BackendUnavailableError):
        validate_rocm_runtime(fake_torch(hip=hip, available=available))


def test_model_size_is_divisible_and_bounded() -> None:
    width, height = model_safe_size((4032, 3024), maximum_pixels=1024 * 1024)

    assert width % 16 == 0
    assert height % 16 == 0
    assert width * height <= 1024 * 1024


def test_material_prompt_contains_brand_preservation_contract() -> None:
    prompt = material_prompt(MaterialPreset.FABRIC_PRINT)

    assert "exact logo lettering" in prompt
    assert "pixels outside the white mask" in prompt
    assert "fabric" in prompt


def test_flux_adapter_is_locally_testable_with_injected_pipeline() -> None:
    backend = Flux2KleinRefiner(Flux2Settings(maximum_pixels=256 * 256, padding_mask_crop=None))
    backend._pipeline = FakePipeline()
    backend._torch = fake_torch(hip="7.2.0", available=True)
    backend._runtime = {"device_name": "Fake Radeon"}
    backend._diffusers_version = "0.40.0.dev0"
    rough = Image.new("RGB", (321, 193), (20, 30, 40))
    mask = Image.new("L", rough.size, 255)

    result = backend.refine(
        rough,
        mask,
        material=MaterialPreset.BILLBOARD,
        seed=42,
    )

    assert result.image.size == rough.size
    assert result.backend == "flux2-klein-inpaint-rocm"
    assert result.metadata["peak_allocated_bytes"] == 12 * 1024**3
    assert result.metadata["inference_size"] == [320, 192]
