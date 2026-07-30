# Cloud Evidence Checklist

## Eligibility and access

- [ ] Luma registration approved.
- [ ] AMD Developer Program membership confirmed.
- [ ] Team name and member registrations match.
- [ ] Persistent Radeon Cloud storage created.

## Environment gate

- [ ] `scripts/doctor.py --require-rocm` passes.
- [ ] GPU name, VRAM, ROCm, PyTorch, Python, and BF16 support captured.
- [ ] Platform PyTorch retained; no CUDA/generic wheel installed.
- [ ] `benchmarks/radeon-environment.json` committed.

## Model gate

- [ ] FLUX.2 Klein 4B access/download succeeds.
- [ ] One masked 512-1024 px smoke edit completes.
- [ ] Exact model commit pinned in config and manifests.
- [ ] Diffusers commit matches `requirements-radeon.txt`.
- [ ] Fixed-seed repeat produces stable execution.

## Quality and performance

- [ ] Billboard, real vehicle panel, and third real/photo scenario pass review.
- [ ] Original, rough, model-only, and final images retained.
- [ ] Outside-mask changed-pixel ratio and SSIM inspected.
- [ ] Logo readability, geometry, color, and halos reviewed.
- [ ] Cold wall time, warm inference, and peak VRAM measured.
- [ ] `benchmarks/radeon-results.json` committed.

## Final deliverables

- [ ] Project profile updated with real Radeon table and result images.
- [ ] Poster replaces pending-Radeon label with supported measurements.
- [ ] 3-5 minute video records the actual command/UI path.
- [ ] README links PDF, poster, video, and raw JSON.
- [ ] Clean-clone test passes on a fresh cloud instance.
- [ ] No tokens, caches, weights, private photos, or unclear assets committed.
