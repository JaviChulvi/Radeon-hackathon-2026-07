# Radeon SponsorSkin

## Exact brand in. Realistic mockup out.

Track 1 - Development of Multimodal Content Creation Tools

Status as of 2026-07-30: the complete local development workflow, deterministic
computer-vision stack, exact-logo restoration, evaluation, manifests, Gradio
UI, and Radeon backend contract are implemented and tested. Real FLUX.2 output,
latency, peak VRAM, and ROCm evidence remain pending access to the assigned
Radeon Cloud instance.

## 1. Project background

Generic image generators can create attractive sponsorship concepts, but they
often rewrite lettering, alter proportions, move symbols, or change brand
colors. Manual mockups preserve the logo but take time and demand design
expertise. SponsorSkin combines both strengths: deterministic computer vision
places the exact supplied logo, while a masked generative stage is responsible
only for local material, light, reflection, and texture integration.

The result is a practical creation tool for quickly testing sponsor placements
without handing brand identity to the generative model.

## 2. Target users and application scenarios

- Freelance designers preparing client-ready sponsorship concepts.
- Small motorsport teams visualizing sponsor inventory on vehicles.
- Event and brand teams testing billboard or venue signage.
- Apparel creators previewing print placement on fabric.
- Small businesses evaluating paint, vinyl, and sign concepts before
  fabrication.

The primary scenarios are billboard/signage, vehicle-panel vinyl, printed
fabric, and painted wall graphics.

## 3. User workflow

1. Upload a target JPEG, PNG, or WebP photograph.
2. Upload an authorized safe SVG or transparent PNG logo.
3. Click four corners on the target surface in any order.
4. Choose material and placement settings.
5. Build the exact deterministic rough preview and edit mask.
6. Run local passthrough or masked FLUX.2 Klein refinement on Radeon.
7. Restore the exact logo using the generated illumination field.
8. Compare original, rough, model-only, and final outputs.
9. Inspect preservation and fidelity metrics.
10. Download the final PNG and reproducibility manifest.

## 4. System architecture

The validation, geometry, compositing, inference, restoration, evaluation,
telemetry, and UI layers are independent. This keeps the scored workflow
testable on CPU and allows the refinement backend to switch without duplicating
brand logic.

The deterministic path rasterizes safe SVG, preserves alpha, validates and
orders the quadrilateral, computes an OpenCV homography, warps the exact RGBA
logo, creates the rough composite, and derives both an undilated exact alpha and
a dilated feathered edit mask.

## 5. Model and algorithm introduction

The intended Radeon backend is
`black-forest-labs/FLUX.2-klein-4B`, the Apache-2.0 distilled 4B model, through
Diffusers `Flux2KleinInpaintPipeline`. The rough exact-logo composite is the
source image; the feathered mask identifies only the local editable region.
Four conservative material prompts cover vinyl, fabric print, billboard, and
painted wall.

Initial settings are BF16, four distilled steps, strength 0.65, guidance 1.0,
and a maximum model area of 1,048,576 pixels. Inputs are resized to dimensions
divisible by 16 for inference and returned to the original size before exact
restoration.

## 6. Exact-logo restoration

Generated lettering cannot be trusted. SponsorSkin estimates the refined-to-
rough luminance ratio inside stable logo pixels in linear RGB, clamps and
smooths the field, applies it to the exact warped logo, composites with the
original alpha geometry, and locks pixels outside the edit mask back to the
source. Passthrough refinement is explicitly idempotent and does not
re-composite or shift colors.

## 7. AMD Radeon GPU / ROCm adaptation

- Retain the Radeon Cloud platform PyTorch build; never install a CUDA wheel.
- Verify `torch.version.hip`, device availability, device name, BF16 support,
  and total VRAM before model download.
- Use the PyTorch `torch.cuda` compatibility namespace exposed by ROCm.
- Start with BF16 and standard PyTorch attention; avoid xFormers,
  bitsandbytes, FP8, compile mode, and CUDA-only kernels.
- Fail closed when ROCm or a device is missing.
- Record cold wall time, warm inference, peak allocated VRAM, model and source
  revisions, device, ROCm, PyTorch, seed, and resolution in raw JSON.

This adaptation is implemented but not yet measured on the assigned device.

## 8. Quality and reproducibility

Every run stores original, source logo, exact warped layer, rough composite,
edit mask, exact alpha, refined result, final image, shading visualization,
metrics, and manifest in a unique timestamped directory.

Automated signals include exact outside-mask changed-pixel ratio, outside SSIM
and mean absolute error, logo Delta E 2000, variance-of-Laplacian sharpness,
mask coverage, and warnings. The local passthrough benchmark measures only the
CPU-safe artifact path and is never presented as model or Radeon performance.

## 9. Local evidence

- 35 passing CPU-safe tests at artifact-build time.
- Three fictional procedural scenarios with committed inputs, logos, masks,
  exact warped layers, and rough previews.
- Local passthrough preservation: outside changed-pixel ratio 0 and outside
  SSIM 1 on the committed benchmark fixture.
- Interactive Gradio workflow verified through real browser operation.
- Machine-readable local environment and timing JSON committed under
  `benchmarks/`.

## 10. Optional LoRA experiment

The optional Sponsor Edit LoRA learns rough exact-logo composite to polished
surface integration. Canonical pairs remain trainer-independent and require
source/logo rights metadata. The experiment starts with 12-20 pairs at 512 px
and is accepted only if a loadable Radeon-trained checkpoint improves at least
60 percent of held-out comparisons without worsening preservation or logo
fidelity. It is not a release blocker.

## 11. Limitations and honest status

Current demo images are procedural development fixtures, not real photos. Local
outputs are deterministic rough previews, not generated refinements. Radeon
model compatibility, visual improvement, cold/warm latency, and peak VRAM must
be filled from real cloud runs. A model revision must be pinned after the first
passing smoke test. LoRA remains experimental.

## 12. Practical value

SponsorSkin turns an exact brand asset plus an ordinary photo into an auditable
creative workflow. It reduces the time and expertise needed for early sponsor,
signage, and apparel decisions while keeping geometry, provenance, licensing,
and hardware evidence visible.

## References

- AMD AI DevMaster Hackathon: https://luma.com/amd-4dhi
- FLUX.2 Klein 4B model card:
  https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- Diffusers FLUX.2 documentation:
  https://huggingface.co/docs/diffusers/api/pipelines/flux2
- Project repository:
  https://github.com/JaviChulvi/Radeon-hackathon-2026-07
