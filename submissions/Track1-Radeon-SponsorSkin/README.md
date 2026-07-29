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

## Radeon status

No Radeon/ROCm claim is made from local macOS testing. GPU inference,
performance measurements, and LoRA training require the designated Radeon
Cloud environment.
