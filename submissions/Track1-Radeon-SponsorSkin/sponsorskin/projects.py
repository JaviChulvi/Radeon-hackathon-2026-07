"""Versioned run directories, environment capture, and JSON serialization."""

from __future__ import annotations

import platform
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path

from sponsorskin.schemas import EnvironmentSnapshot


def create_run_directory(root: str | Path) -> tuple[str, Path]:
    """Create a collision-resistant, chronological run directory."""

    output_root = Path(root)
    output_root.mkdir(parents=True, exist_ok=True)
    for _ in range(10):
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{timestamp}-{secrets.token_hex(3)}"
        run_directory = output_root / run_id
        try:
            run_directory.mkdir()
        except FileExistsError:
            continue
        return run_id, run_directory
    raise RuntimeError("Could not allocate a unique run directory")


def capture_environment() -> EnvironmentSnapshot:
    """Capture local or Radeon runtime facts without making PyTorch mandatory."""

    torch_version: str | None = None
    rocm_version: str | None = None
    gpu_name: str | None = None
    try:
        import torch

        torch_version = torch.__version__
        rocm_version = torch.version.hip
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return EnvironmentSnapshot(
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        machine=platform.machine(),
        torch_version=torch_version,
        rocm_version=rocm_version,
        gpu_name=gpu_name,
    )
