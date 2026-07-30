# Four-Minute Demo Script

Replace every bracketed cloud placeholder only after recording a real,
successful Radeon run. Do not hide a failed or remote execution path.

## 0:00-0:20 - Problem and promise

"Generic image generation can produce beautiful sponsorship ideas, but it can
also rewrite the logo. SponsorSkin keeps brand geometry deterministic and asks
the model only to integrate material, light, and texture."

Show the exact source logo and final candidate result side by side.

## 0:20-0:45 - Radeon evidence

In the terminal:

```bash
python scripts/doctor.py --require-rocm
```

Read the actual device, ROCm, PyTorch, and VRAM values on screen. Say:
"These values are measured on this Radeon Cloud instance."

## 0:45-1:30 - Inputs and placement

Launch `SPONSORSKIN_BACKEND=flux2 python app.py`. Upload one rights-cleared
target and the exact logo. Click four surface corners. Change the material
preset and briefly show scale, opacity, mask padding, strength, steps, and
seed.

## 1:30-2:05 - Deterministic preview

Click "Build deterministic preview." Show the rough composite, exact warped
logo layer, and edit mask. Explain that the undilated alpha preserves the brand
while the larger feathered mask gives the model room to modify contact edges.

## 2:05-2:50 - Real Radeon refinement

Click "Run Radeon FLUX.2 pipeline." Keep the interface and terminal visible.
State the cold or warm context honestly. When complete, show the measured
latency and manifest.

Cloud fill-ins:

- Device: `[MEASURED GPU]`
- ROCm: `[MEASURED ROCM]`
- Warm inference: `[MEASURED SECONDS]`
- Peak allocated VRAM: `[MEASURED GIB]`

## 2:50-3:30 - Why restoration matters

Open Pipeline Comparison. Move through original, rough, model-only, and final.
Point out that the final restores the exact logo while transferring smooth
illumination. In Quality & Downloads, show outside-mask change, SSIM, logo
color drift, warnings, final PNG, and manifest.

## 3:30-3:50 - Diverse value

Show already-prepared Porsche 911, bus, truck, hoodie, cap, billboard, and
bus-shelter examples with their source credits and manifests. Mention
designers, motorsport and fleet teams, event/brand teams, and apparel creators.

## 3:50-4:00 - Close

"Exact brand in. Realistic mockup out - locally on Radeon, with every setting,
metric, and hardware fact recorded."

Show repository and Track 1 title.
