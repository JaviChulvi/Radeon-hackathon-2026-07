# Radeon / ROCm Handoff Notes

## Current status

The Mac development path is complete and tested, but no Radeon inference claim
is made yet. The assigned cloud instance must supply the platform ROCm PyTorch
build. Never replace it with a CUDA or generic PyPI wheel.

## Cloud execution order

From the submission directory:

```bash
python scripts/doctor.py --require-rocm \
  --json benchmarks/radeon-environment.json
python -m pip install -e ".[dev,ui]"
python -m pip install -r requirements-radeon.txt
```

Run the doctor again after dependency installation. Confirm that
`torch.version.hip`, `torch.cuda.is_available()`, the device name, BF16 support,
and total VRAM are populated. PyTorch intentionally exposes ROCm devices
through its `torch.cuda` compatibility API.

Then run one 512–1024 px smoke edit with `scripts/smoke_flux.py`. Only after it
passes:

1. Pin the exact Hugging Face model commit in `configs/inference.yaml`.
2. Set `SPONSORSKIN_MODEL_REVISION` to that commit for the UI.
3. Run `scripts/benchmark_flux.py` with at least four iterations.
4. Commit `benchmarks/radeon-environment.json`,
   `benchmarks/radeon-results.json`, and representative run manifests.
5. Launch the UI with `SPONSORSKIN_BACKEND=flux2`.

## Conservative defaults

- BF16, standard PyTorch attention, no compile mode.
- Four distilled inference steps, strength 0.65, guidance 1.0.
- Maximum model area 1,048,576 pixels.
- No xFormers, bitsandbytes, FP8, or CUDA-only kernels.
- CPU offload disabled unless measured VRAM requires it.

## Evidence gate

Radeon claims require raw output showing GPU name, ROCm and PyTorch versions,
model and source revisions, seed, input/inference size, cold wall time, warm
inference time, peak allocated VRAM, quality metrics, and final images. A
missing model revision, non-ROCm wheel, OOM, NaN/Inf, or visibly worse output
blocks the claim and keeps the passthrough UI as the honest fallback.
