"""Canonical paired-dataset validation independent of any LoRA trainer."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sponsorskin.schemas import MaterialPreset
from sponsorskin.validation import InputValidationError, load_logo_image

REQUIRED_SAMPLE_FILES = {
    "source.png",
    "rough_composite.png",
    "target.png",
    "mask.png",
    "logo.png",
    "instruction.txt",
    "metadata.json",
}


class DatasetMetadata(BaseModel):
    """Rights and split metadata required for every canonical sample."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    split: Literal["train", "validation", "test"]
    material: MaterialPreset
    source_creator: str = Field(min_length=1)
    source_license: str = Field(min_length=1)
    source_url: str | None = None
    logo_creator: str = Field(min_length=1)
    logo_license: str = Field(min_length=1)
    notes: str | None = None


class SampleValidation(BaseModel):
    """Validation outcome for one sample directory."""

    sample_id: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    split: str | None = None
    material: str | None = None
    image_size: tuple[int, int] | None = None


class DatasetValidationReport(BaseModel):
    """Machine-readable aggregate dataset validation report."""

    schema_version: Literal["1.0"] = "1.0"
    root: str
    valid: bool
    sample_count: int
    valid_sample_count: int
    split_counts: dict[str, int]
    material_counts: dict[str, int]
    samples: list[SampleValidation]


def _open_png(path: Path, *, mode: str) -> Image.Image:
    try:
        with Image.open(path) as candidate:
            candidate.verify()
        with Image.open(path) as candidate:
            encoding = candidate.format
            image = candidate.copy()
    except (FileNotFoundError, UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError(f"{path.name} is not a valid PNG image") from exc
    if encoding != "PNG":
        raise ValueError(f"{path.name} must use PNG encoding")
    return image.convert(mode)


def validate_sample(sample_directory: str | Path) -> SampleValidation:
    """Validate one canonical source/condition/target pair."""

    directory = Path(sample_directory)
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(name for name in REQUIRED_SAMPLE_FILES if not (directory / name).is_file())
    if missing:
        errors.append(f"Missing required files: {', '.join(missing)}")

    metadata: DatasetMetadata | None = None
    metadata_path = directory / "metadata.json"
    if metadata_path.is_file():
        try:
            metadata = DatasetMetadata.model_validate_json(
                metadata_path.read_text(encoding="utf-8")
            )
            if metadata.sample_id != directory.name:
                errors.append("metadata.sample_id must match the sample directory name")
        except (OSError, ValidationError, ValueError) as exc:
            errors.append(f"Invalid metadata.json: {exc}")

    instruction_path = directory / "instruction.txt"
    if instruction_path.is_file():
        try:
            instruction = instruction_path.read_text(encoding="utf-8").strip()
            if not instruction:
                errors.append("instruction.txt must not be empty")
            elif len(instruction) > 1000:
                warnings.append("instruction.txt exceeds 1,000 characters")
        except (OSError, UnicodeError) as exc:
            errors.append(f"instruction.txt could not be read as UTF-8: {exc}")

    image_size: tuple[int, int] | None = None
    image_names = ("source.png", "rough_composite.png", "target.png")
    images: dict[str, Image.Image] = {}
    for name in image_names:
        if not (directory / name).is_file():
            continue
        try:
            images[name] = _open_png(directory / name, mode="RGB")
        except ValueError as exc:
            errors.append(str(exc))
    if images:
        sizes = {name: image.size for name, image in images.items()}
        image_size = next(iter(sizes.values()))
        if len(set(sizes.values())) > 1:
            errors.append(f"source, rough composite, and target sizes differ: {sizes}")
        if image_size[0] % 16 or image_size[1] % 16:
            warnings.append("image dimensions are not divisible by 16")

    mask_path = directory / "mask.png"
    if mask_path.is_file():
        try:
            mask = _open_png(mask_path, mode="L")
            if image_size and mask.size != image_size:
                errors.append("mask.png size must match source.png")
            mask_values = np.asarray(mask, dtype=np.uint8)
            if not np.any(mask_values > 0):
                errors.append("mask.png contains no editable pixels")
            if np.all(mask_values > 0):
                warnings.append("mask.png marks the entire image as editable")
        except ValueError as exc:
            errors.append(str(exc))

    logo_path = directory / "logo.png"
    if logo_path.is_file():
        try:
            load_logo_image(logo_path)
        except InputValidationError as exc:
            errors.append(f"logo.png: {exc}")

    return SampleValidation(
        sample_id=directory.name,
        valid=not errors,
        errors=errors,
        warnings=warnings,
        split=metadata.split if metadata else None,
        material=metadata.material.value if metadata else None,
        image_size=image_size,
    )


def validate_dataset(dataset_root: str | Path) -> DatasetValidationReport:
    """Validate every immediate sample directory under a canonical dataset root."""

    root = Path(dataset_root)
    if not root.is_dir():
        raise ValueError(f"Dataset root does not exist: {root}")
    sample_directories = sorted(path for path in root.iterdir() if path.is_dir())
    samples = [validate_sample(path) for path in sample_directories]
    split_counts = Counter(sample.split for sample in samples if sample.split)
    material_counts = Counter(sample.material for sample in samples if sample.material)
    valid_count = sum(sample.valid for sample in samples)
    return DatasetValidationReport(
        root=str(root.resolve()),
        valid=bool(samples) and valid_count == len(samples),
        sample_count=len(samples),
        valid_sample_count=valid_count,
        split_counts=dict(sorted(split_counts.items())),
        material_counts=dict(sorted(material_counts.items())),
        samples=samples,
    )


def write_dataset_report(report: DatasetValidationReport, output_path: str | Path) -> Path:
    """Persist a canonical validation report."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return destination
