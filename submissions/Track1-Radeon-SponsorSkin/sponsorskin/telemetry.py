"""Measured system and accelerator telemetry without mandatory PyTorch."""

from __future__ import annotations

import importlib.metadata
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PACKAGE_DISTRIBUTIONS = (
    "radeon-sponsorskin",
    "numpy",
    "opencv-python-headless",
    "Pillow",
    "scikit-image",
    "gradio",
)


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for distribution in PACKAGE_DISTRIBUTIONS:
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return versions


def _tool_version(executable: str, arguments: list[str]) -> dict[str, Any]:
    path = shutil.which(executable)
    if not path:
        return {"available": False, "path": None, "output": None}
    try:
        result = subprocess.run(
            [path, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = (result.stdout or result.stderr).strip()
        return {
            "available": True,
            "path": path,
            "return_code": result.returncode,
            "output": output[:4000] or None,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "available": True,
            "path": path,
            "return_code": None,
            "output": f"{type(exc).__name__}: {exc}",
        }


def _torch_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "installed": False,
        "version": None,
        "rocm_version": None,
        "cuda_api_available": False,
        "device_count": 0,
        "device_name": None,
        "total_memory_bytes": None,
        "bf16_supported": None,
    }
    try:
        import torch
    except ImportError:
        return snapshot

    snapshot["installed"] = True
    snapshot["version"] = torch.__version__
    snapshot["rocm_version"] = torch.version.hip
    snapshot["cuda_api_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        snapshot["device_count"] = torch.cuda.device_count()
        snapshot["device_name"] = torch.cuda.get_device_name(0)
        snapshot["total_memory_bytes"] = torch.cuda.get_device_properties(0).total_memory
        snapshot["bf16_supported"] = bool(torch.cuda.is_bf16_supported())
    return snapshot


def collect_telemetry() -> dict[str, Any]:
    """Collect measured runtime facts suitable for JSON evidence."""

    torch_snapshot = _torch_snapshot()
    rocm_ready = bool(
        torch_snapshot["rocm_version"]
        and torch_snapshot["cuda_api_available"]
        and torch_snapshot["device_count"]
    )
    return {
        "schema_version": "1.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "system": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
        },
        "packages": _package_versions(),
        "torch": torch_snapshot,
        "tools": {
            "amd-smi": _tool_version("amd-smi", ["version"]),
            "rocm-smi": _tool_version("rocm-smi", ["--version"]),
        },
        "rocm_ready": rocm_ready,
        "scope": (
            "Measured Radeon/ROCm runtime"
            if rocm_ready
            else "Local development runtime; Radeon/ROCm inference not verified"
        ),
    }


def write_json_report(report: dict[str, Any], destination: str | Path) -> Path:
    """Write a telemetry-style dictionary with stable formatting."""

    import json

    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path
