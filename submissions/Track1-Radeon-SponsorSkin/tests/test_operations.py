from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sponsorskin.benchmarking import benchmark_local_pipeline
from sponsorskin.telemetry import collect_telemetry, write_json_report


def test_telemetry_is_truthful_without_assuming_rocm() -> None:
    report = collect_telemetry()

    assert report["schema_version"] == "1.0"
    assert report["system"]["python_version"] == sys.version.split()[0]
    assert report["rocm_ready"] is bool(
        report["torch"]["rocm_version"]
        and report["torch"]["cuda_api_available"]
        and report["torch"]["device_count"]
    )
    if not report["rocm_ready"]:
        assert "not verified" in report["scope"]


def test_json_report_has_stable_trailing_newline(tmp_path: Path) -> None:
    output_path = write_json_report({"value": 3}, tmp_path / "report.json")

    assert output_path.read_text(encoding="utf-8") == '{\n  "value": 3\n}\n'


def test_small_local_benchmark_reports_warm_runs() -> None:
    report = benchmark_local_pipeline(iterations=2, width=320, height=192)

    assert report["backend"] == "local-passthrough"
    assert report["iterations"] == 2
    assert len(report["timings_seconds"]["warm_runs"]) == 1
    assert report["quality_metrics"]["outside_changed_ratio"] == 0
    assert "no generative model" in report["scope"]


def test_doctor_cli_writes_json(tmp_path: Path) -> None:
    output_path = tmp_path / "doctor.json"

    result = subprocess.run(
        [sys.executable, "scripts/doctor.py", "--json", str(output_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "Scope:" in result.stdout
    assert report["system"]["python_version"] == sys.version.split()[0]
