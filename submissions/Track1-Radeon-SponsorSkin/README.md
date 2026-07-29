# Radeon SponsorSkin

Radeon SponsorSkin creates realistic sponsorship mockups while preserving the
exact geometry of a user-provided SVG or transparent PNG logo.

The local development slice currently implements validated logo loading,
four-corner perspective placement, deterministic compositing, edit-mask
generation, and exported intermediate artifacts. FLUX.2 refinement remains
disabled until it is validated on Radeon Cloud.

## Local setup

```bash
conda activate radeon-sponsorskin
python -m pip install -e ".[dev]"
```

To create or update the complete Conda environment, including the native Cairo
library required for SVG rendering:

```bash
mamba env update --file environment.yml --prune
```

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

## Test and lint

```bash
python -m pytest tests -q
ruff check .
ruff format --check .
```

## Radeon status

No Radeon/ROCm claim is made from local macOS testing. GPU inference,
performance measurements, and LoRA training require the designated Radeon
Cloud environment.
