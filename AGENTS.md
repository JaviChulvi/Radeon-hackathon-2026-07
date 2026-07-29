# Repository Guidelines

## Project Structure & Module Organization

This repository is a fork of the official AMD contest repository. Preserve the root `README.md` and `Radeon-Cloud-User Guide/`. Read `PLAN.md` before changing scope.

Place SponsorSkin work under `submissions/Track1-Radeon-SponsorSkin/`. Keep application code in `sponsorskin/`, entrypoints in `app.py` and `scripts/`, tests in `tests/`, rights-cleared examples in `demo_assets/`, measurements in `benchmarks/`, and submission artifacts in `docs/`. Do not commit generated `runs/`, model weights, or caches.

## Build, Test, and Development Commands

Use the local Python 3.12 environment:

```bash
conda activate radeon-sponsorskin
cd submissions/Track1-Radeon-SponsorSkin
python app.py
python -m pytest tests -q
python scripts/doctor.py
python scripts/benchmark.py
```

`app.py` starts Gradio. `doctor.py` reports Python, PyTorch, GPU, and ROCm details. `benchmark.py` writes reproducible timing and memory results. Keep these entrypoints stable.

## Coding Style & Naming Conventions

Use four-space indentation, explicit type hints on public functions, and small modules with one clear responsibility. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes and Pydantic models; and `UPPER_SNAKE_CASE` for constants. Keep UI callbacks thin and put geometry, compositing, inference, restoration, and evaluation logic in services. Run `ruff format .` and `ruff check .` before committing.

## Testing Guidelines

Use pytest and name files `test_*.py`. CPU-safe tests must cover input validation, homography, masks, alpha handling, restoration invariants, manifests, and metrics. Mark Radeon-only tests explicitly and skip them when ROCm is unavailable. Use fixed seeds and never describe GPU behavior as verified without committed Radeon output.

## Commit & Pull Request Guidelines

History uses concise imperative summaries such as `Update tunnel guide`. Keep commits focused and runnable, for example `Add deterministic logo homography`.

PRs should explain the user-visible change, list verification commands, and include UI screenshots or representative outputs. Track 1 submission PRs must use:

```text
Track 1, <Team name>, Radeon SponsorSkin
```

Link the profile PDF, poster, demo video, and raw benchmark JSON.

## Security & Asset Policy

Never commit credentials, cloud tokens, private images, or unlicensed brand assets. Use fictional or authorized logos and record asset licenses in `demo_assets/CREDITS.md`. On Radeon Cloud, retain the platform ROCm PyTorch build; do not install a CUDA wheel over it.
