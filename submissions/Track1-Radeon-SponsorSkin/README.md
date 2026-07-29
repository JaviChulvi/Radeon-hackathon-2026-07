# Radeon SponsorSkin

Radeon SponsorSkin creates realistic sponsorship mockups while preserving the
exact geometry of a user-provided SVG or transparent PNG logo.

The local development slice implements validated logo loading, four-corner
perspective placement, deterministic compositing, edit-mask generation, exact
logo restoration, objective quality metrics, and reproducible run manifests.
FLUX.2 refinement remains disabled until it is validated on Radeon Cloud.

## Local setup

```bash
conda activate radeon-sponsorskin
python -m pip install -e ".[dev,ui]"
```

To create or update the complete Conda environment, including the native Cairo
library required for SVG rendering:

```bash
mamba env update --file environment.yml --prune
```

## Interactive local app

```bash
python app.py
```

Open `http://127.0.0.1:7860`, upload a target and authorized logo, then click
four corners on the target surface. The UI supports deterministic preview,
versioned local runs, metric inspection, and final/manifest downloads. Its
local badge remains visible because this mode does not execute generative
inference.

## Deterministic composition

```bash
python scripts/compose.py \
  --target path/to/photo.png \
  --logo path/to/logo.png \
  --point 100,100 --point 500,110 --point 490,350 --point 110,340 \
  --output runs/example
```

The command writes `original.png`, `logo_layer.png`,
`rough_composite.png`, `edit_mask.png`, and `exact_alpha.png`.

## Complete local pipeline

Use the passthrough backend to verify the full artifact contract without a GPU:

```bash
python scripts/run_local.py \
  --target path/to/photo.png \
  --logo path/to/logo.svg \
  --point 100,100 --point 500,110 --point 490,350 --point 110,340 \
  --material billboard \
  --seed 42
```

Each invocation creates a new directory under `runs/`. It includes the source
and intermediate images, `final.png`, an illumination visualization,
`metrics.json`, and `manifest.json` with settings and environment provenance.
The local passthrough output is intentionally deterministic and does not claim
generative refinement.

## Test and lint

```bash
python -m pytest tests -q
ruff check .
ruff format --check .
```

## Environment doctor and local benchmark

```bash
python scripts/doctor.py --json benchmarks/local-environment.json
python scripts/benchmark.py --output benchmarks/local-results.json
```

`doctor.py` records Python, dependency, PyTorch, accelerator, ROCm, and AMD SMI
facts without assuming a GPU exists. Add `--require-rocm` in Radeon Cloud to
make missing ROCm/device detection fail fast. The local benchmark times the
complete passthrough artifact path; it is CPU development evidence, not a
generative-inference or Radeon benchmark.

## Radeon Cloud handoff

This code path is prepared but remains unverified until access to the assigned
Radeon Cloud instance is available. Keep the platform ROCm PyTorch build; do
not install or upgrade `torch` from PyPI.

```bash
python -m pip install -e ".[dev,ui]"
python -m pip install -r requirements-radeon.txt
python scripts/doctor.py --require-rocm \
  --json benchmarks/radeon-environment.json
```

`requirements-radeon.txt` pins the current Diffusers source revision that
contains `Flux2KleinInpaintPipeline`. The model revision stays unset until the
first successful cloud smoke test, when it must be pinned in the configuration
and captured in benchmark evidence.

Run one masked model smoke test:

```bash
python scripts/smoke_flux.py \
  --target path/to/photo.png \
  --logo path/to/logo.png \
  --point 100,100 --point 500,110 --point 490,350 --point 110,340 \
  --material billboard --steps 4 --strength 0.65
```

Measure one cold process path plus at least three warm inference runs:

```bash
python scripts/benchmark_flux.py \
  --target path/to/photo.png \
  --logo path/to/logo.png \
  --point 100,100 --point 500,110 --point 490,350 --point 110,340 \
  --material billboard --iterations 4 \
  --output benchmarks/radeon-results.json
```

After the smoke test passes, launch the same UI with the Radeon backend:

```bash
SPONSORSKIN_BACKEND=flux2 \
SPONSORSKIN_SERVER_NAME=0.0.0.0 \
python app.py
```

The backend lazily loads
`black-forest-labs/FLUX.2-klein-4B` in BF16, fails closed when
`torch.version.hip` or the device is missing, keeps output dimensions aligned
with restoration, and records latency, peak allocated VRAM, GPU, ROCm,
PyTorch, model, and dependency provenance in every manifest.

## Paired-dataset validation

The optional LoRA experiment uses a trainer-independent canonical format. See
`docs/dataset-methodology.md`, then validate every pair and rights record:

```bash
python scripts/validate_dataset.py path/to/canonical-dataset \
  --json benchmarks/dataset-validation.json
```

LoRA remains non-blocking and must not enter the demo unless it trains, reloads,
and passes the documented held-out acceptance gate on Radeon.

## Reproducible demo fixtures

Three fictional procedural fixtures cover billboard, vehicle-panel vinyl, and
fabric-print placement:

```bash
python scripts/generate_demo_assets.py --output demo_assets --force
```

The generated inputs, transparent wordmarks, corners, licenses, masks, and
rough composites are committed under `demo_assets/`. Their metadata explicitly
labels every existing preview as local passthrough output. These fixtures are
safe for development and documentation; final judging examples should add
rights-cleared real photographs and measured Radeon refinements when cloud
access is available.

## Radeon status

No Radeon/ROCm claim is made from local macOS testing. GPU inference,
performance measurements, and LoRA training require the designated Radeon
Cloud environment.
