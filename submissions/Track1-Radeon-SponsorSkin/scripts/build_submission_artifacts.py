#!/usr/bin/env python3
"""Build and validate the SponsorSkin project-profile and poster PDFs."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"
ASSETS_ROOT = PROJECT_ROOT / "demo_assets"

INK = colors.HexColor("#0B0F16")
PANEL = colors.HexColor("#161C27")
PANEL_2 = colors.HexColor("#222A38")
PAPER = colors.HexColor("#F4F1EA")
MUTED = colors.HexColor("#AAB4C4")
RED = colors.HexColor("#D91E36")
ORANGE = colors.HexColor("#F27622")
TEAL = colors.HexColor("#31D0AA")
WHITE = colors.white
STATUS = "LOCAL DEVELOPMENT CANDIDATE - RADEON VALIDATION PENDING"


def _draw_image(
    pdf: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    width: float,
    height: float,
) -> None:
    image = ImageReader(path)
    source_width, source_height = image.getSize()
    scale = min(width / source_width, height / source_height)
    rendered_width = source_width * scale
    rendered_height = source_height * scale
    pdf.drawImage(
        image,
        x + (width - rendered_width) / 2,
        y + (height - rendered_height) / 2,
        rendered_width,
        rendered_height,
        preserveAspectRatio=True,
        mask="auto",
    )


def _wrapped_lines(text: str, font: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if stringWidth(candidate, font, size) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _text(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: float = 9.5,
    color: colors.Color = WHITE,
    leading: float | None = None,
    max_lines: int | None = None,
) -> float:
    leading = leading or size * 1.35
    lines = _wrapped_lines(text, font, size, width)
    if max_lines:
        lines = lines[:max_lines]
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    cursor = y
    for line in lines:
        pdf.drawString(x, cursor, line)
        cursor -= leading
    return cursor


def _bullet_list(
    pdf: canvas.Canvas,
    items: list[str],
    x: float,
    y: float,
    width: float,
    *,
    size: float = 9,
    gap: float = 5,
) -> float:
    cursor = y
    for item in items:
        pdf.setFillColor(TEAL)
        pdf.circle(x + 2.5, cursor + 3, 2.2, fill=1, stroke=0)
        cursor = _text(
            pdf,
            item,
            x + 12,
            cursor,
            width - 12,
            size=size,
            leading=size * 1.32,
        )
        cursor -= gap
    return cursor


def _panel(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: colors.Color = PANEL,
    radius: float = 8,
) -> None:
    pdf.setFillColor(fill)
    pdf.roundRect(x, y, width, height, radius, fill=1, stroke=0)


def _tag(
    pdf: canvas.Canvas,
    label: str,
    x: float,
    y: float,
    *,
    color: colors.Color = TEAL,
) -> float:
    width = stringWidth(label, "Helvetica-Bold", 7.5) + 18
    pdf.setFillColor(color)
    pdf.roundRect(x, y, width, 18, 9, fill=1, stroke=0)
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 7.5)
    pdf.drawCentredString(x + width / 2, y + 5.5, label)
    return width


def _section_title(
    pdf: canvas.Canvas,
    kicker: str,
    title: str,
    subtitle: str | None = None,
) -> None:
    width, height = A4
    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(42, height - 74, kicker.upper())
    _text(
        pdf,
        title,
        42,
        height - 101,
        width - 84,
        font="Helvetica-Bold",
        size=22,
        leading=25,
    )
    if subtitle:
        _text(
            pdf,
            subtitle,
            42,
            height - 132,
            width - 84,
            size=9.5,
            color=MUTED,
        )


def _profile_page(pdf: canvas.Canvas, page_number: int) -> None:
    width, height = A4
    pdf.setFillColor(INK)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(RED)
    pdf.rect(0, height - 9, width, 9, fill=1, stroke=0)


def _profile_footer(pdf: canvas.Canvas, page_number: int) -> None:
    width, _ = A4
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 6.5)
    pdf.drawString(42, 25, "RADEON SPONSORSKIN")
    pdf.drawRightString(width - 42, 25, f"PROJECT PROFILE  /  {page_number:02d}")


def _profile_cover(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 1)
    _tag(pdf, "TRACK 1 - MULTIMODAL CONTENT CREATION", 42, height - 70, color=ORANGE)
    _text(
        pdf,
        "Exact brand in.\nRealistic mockup out.",
        42,
        height - 125,
        width - 84,
        font="Helvetica-Bold",
        size=34,
        leading=38,
    )
    _text(
        pdf,
        "SponsorSkin combines deterministic computer vision, masked generative "
        "refinement, and exact-logo restoration for auditable sponsorship mockups.",
        42,
        height - 215,
        width - 84,
        size=12,
        color=MUTED,
        leading=17,
    )

    image_y = 266
    image_height = 285
    gap = 12
    image_width = (width - 84 - gap) / 2
    for index, (label, path) in enumerate(
        [
            ("ORIGINAL", ASSETS_ROOT / "local_previews/billboard/original.png"),
            (
                "LOCAL ROUGH COMPOSITE",
                ASSETS_ROOT / "local_previews/billboard/rough_composite.png",
            ),
        ]
    ):
        x = 42 + index * (image_width + gap)
        _panel(pdf, x, image_y, image_width, image_height, fill=PANEL_2)
        _draw_image(pdf, path, x + 7, image_y + 25, image_width - 14, image_height - 34)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawString(x + 9, image_y + 10, label)

    card_y = 118
    card_width = (width - 84 - 24) / 3
    cards = [
        ("EXACT", "logo geometry retained"),
        ("LOCAL", "editable region isolated"),
        ("AUDITABLE", "artifacts + manifests"),
    ]
    for index, (headline, copy) in enumerate(cards):
        x = 42 + index * (card_width + 12)
        _panel(pdf, x, card_y, card_width, 95)
        pdf.setFillColor(TEAL)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(x + 14, card_y + 60, headline)
        _text(pdf, copy, x + 14, card_y + 37, card_width - 28, size=8.5, color=MUTED)
    _tag(pdf, STATUS, 42, 72, color=RED)


def _profile_background(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 2)
    _section_title(
        pdf,
        "01 / Opportunity",
        "Brand-safe ideation without the manual mockup bottleneck",
    )
    left_x, right_x = 42, 311
    column_width = 242

    _panel(pdf, left_x, 438, column_width, 245)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(left_x + 18, 647, "The problem")
    _text(
        pdf,
        "Generic generators can produce attractive concepts, but often rewrite "
        "lettering, alter proportions, move symbols, or shift brand colors. "
        "Traditional mockups preserve the asset but cost time and specialist effort.",
        left_x + 18,
        621,
        column_width - 36,
        size=10,
        color=MUTED,
        leading=15,
    )
    _text(
        pdf,
        "SponsorSkin divides the job: computer vision owns logo identity; a masked "
        "model owns only local material, lighting, reflection, and texture.",
        left_x + 18,
        520,
        column_width - 36,
        font="Helvetica-Bold",
        size=10,
        color=WHITE,
        leading=15,
    )

    _panel(pdf, right_x, 438, column_width, 245, fill=PANEL_2)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(right_x + 18, 647, "Target users")
    _bullet_list(
        pdf,
        [
            "Freelance and in-house designers",
            "Small motorsport and event teams",
            "Brand, venue, and signage planners",
            "Apparel creators and fabric printers",
            "Small businesses planning fabrication",
        ],
        right_x + 18,
        620,
        column_width - 36,
        size=9.5,
        gap=9,
    )

    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(42, 399, "APPLICATION SCENARIOS")
    scenario_width = (width - 84 - 24) / 3
    scenarios = [
        ("BILLBOARD", "Signage concepts before media production."),
        ("VEHICLE", "Sponsor inventory and vinyl placement."),
        ("FABRIC", "Print scale and position on apparel."),
    ]
    for index, (title, copy) in enumerate(scenarios):
        x = 42 + index * (scenario_width + 12)
        _panel(pdf, x, 205, scenario_width, 170)
        pdf.setFillColor(TEAL)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x + 15, 338, title)
        _text(pdf, copy, x + 15, 313, scenario_width - 30, size=9, color=MUTED)
        pdf.setFillColor(PANEL_2)
        pdf.roundRect(x + 15, 226, scenario_width - 30, 52, 6, fill=1, stroke=0)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(x + scenario_width / 2, 257, "UPLOAD + 4 CLICKS")
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 7.5)
        pdf.drawCentredString(x + scenario_width / 2, 241, "preview, compare, export")
    _tag(pdf, "PRACTICAL VALUE: FASTER EARLY CREATIVE DECISIONS", 42, 157)


def _profile_workflow(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 3)
    _section_title(
        pdf,
        "02 / Workflow and architecture",
        "One interface, explicit boundaries, reproducible outputs",
    )

    steps = [
        ("01", "UPLOAD", "target + authorized logo"),
        ("02", "PLACE", "four surface corners"),
        ("03", "REFINE", "local or Radeon backend"),
        ("04", "RESTORE", "exact asset + illumination"),
        ("05", "VERIFY", "metrics + manifest"),
    ]
    step_width = (width - 84 - 32) / 5
    for index, (number, title, copy) in enumerate(steps):
        x = 42 + index * (step_width + 8)
        _panel(pdf, x, 605, step_width, 100, fill=PANEL_2)
        pdf.setFillColor(ORANGE)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(x + 10, 681, number)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x + 10, 657, title)
        _text(pdf, copy, x + 10, 638, step_width - 20, size=6.9, color=MUTED, leading=9)

    architecture = [
        ("VALIDATE", "safe SVG / raster limits"),
        ("GEOMETRY", "ordered quad + homography"),
        ("COMPOSITE", "exact layer + two masks"),
        ("INFERENCE", "passthrough / FLUX.2"),
        ("RESTORE", "lighting transfer + lock"),
        ("EVALUATE", "fidelity + preservation"),
        ("DELIVER", "PNG + JSON evidence"),
    ]
    pdf.setStrokeColor(colors.HexColor("#354054"))
    pdf.setLineWidth(2)
    pdf.line(105, 495, 105, 252)
    for index, (title, copy) in enumerate(architecture):
        y = 500 - index * 39
        pdf.setFillColor(TEAL if index in (0, 6) else ORANGE)
        pdf.circle(105, y, 5, fill=1, stroke=0)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(126, y - 1, title)
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(211, y - 1, copy)

    _panel(pdf, 335, 240, 218, 290)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(353, 495, "System invariants")
    _bullet_list(
        pdf,
        [
            "Inputs are never overwritten.",
            "Exact undilated alpha is retained.",
            "Black mask pixels return to source.",
            "Passthrough is pixel-idempotent.",
            "Radeon mode fails closed without ROCm.",
            "Every run gets a unique manifest.",
        ],
        353,
        465,
        182,
        size=8.8,
        gap=9,
    )

    _panel(pdf, 42, 128, width - 84, 76, fill=PANEL_2)
    _text(
        pdf,
        "Design decision",
        58,
        178,
        115,
        font="Helvetica-Bold",
        size=10,
        color=ORANGE,
    )
    _text(
        pdf,
        "The refinement backend can change without duplicating validation, geometry, "
        "brand restoration, metrics, or evidence logic.",
        174,
        178,
        width - 232,
        size=9.5,
        color=WHITE,
        leading=14,
    )


def _profile_geometry(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 4)
    _section_title(
        pdf,
        "03 / Core algorithm",
        "Deterministic placement before and after generation",
    )

    image_size = 222
    image_y = 438
    cards = [
        (
            "EXACT RGBA LAYER",
            ASSETS_ROOT / "local_previews/vehicle-panel/logo_layer.png",
        ),
        (
            "FEATHERED EDIT MASK",
            ASSETS_ROOT / "local_previews/vehicle-panel/edit_mask.png",
        ),
    ]
    for index, (label, path) in enumerate(cards):
        x = 42 + index * 270
        _panel(pdf, x, image_y, image_size + 38, 232, fill=PANEL_2)
        _draw_image(pdf, path, x + 8, image_y + 28, image_size + 22, 190)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawString(x + 12, image_y + 11, label)

    _panel(pdf, 42, 243, width - 84, 160)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(60, 369, "Geometry and masking")
    _bullet_list(
        pdf,
        [
            "Validate safe SVG or transparent PNG and preserve alpha.",
            "Order four clicks into a convex, non-self-intersecting quadrilateral.",
            "Compute an OpenCV perspective homography and warp exact RGBA pixels.",
            "Keep undilated exact alpha for restoration; dilate and feather only the edit mask.",
        ],
        60,
        341,
        width - 120,
        size=9.3,
        gap=7,
    )

    _panel(pdf, 42, 102, width - 84, 112, fill=PANEL_2)
    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(60, 180, "Exact-logo restoration")
    _text(
        pdf,
        "Estimate the refined-to-rough luminance ratio inside stable logo pixels in "
        "linear RGB. Clamp and smooth that illumination field, apply it to the exact "
        "warped logo, composite with original alpha geometry, then lock every pixel "
        "outside the edit mask back to the source.",
        60,
        154,
        width - 120,
        size=9.2,
        color=WHITE,
        leading=13.5,
    )


def _profile_model(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 5)
    _section_title(
        pdf,
        "04 / Model and AMD adaptation",
        "A conservative masked path designed for measurable Radeon execution",
    )

    _panel(pdf, 42, 485, width - 84, 190)
    _tag(pdf, "IMPLEMENTED", 60, 637)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(60, 608, "FLUX.2 Klein 4B inpaint backend")
    _text(
        pdf,
        "The local rough composite is the source image and the feathered mask limits "
        "the editable region. Four material presets cover vinyl, fabric print, "
        "billboard, and painted wall.",
        60,
        580,
        width - 120,
        size=9.8,
        color=MUTED,
        leading=14,
    )
    specs = [
        ("DTYPE", "BF16"),
        ("STEPS", "4 initial"),
        ("STRENGTH", "0.65"),
        ("GUIDANCE", "1.0"),
        ("MAX AREA", "1,048,576 px"),
    ]
    spec_width = (width - 120 - 32) / 5
    for index, (key, value) in enumerate(specs):
        x = 60 + index * (spec_width + 8)
        pdf.setFillColor(PANEL_2)
        pdf.roundRect(x, 509, spec_width, 45, 5, fill=1, stroke=0)
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica-Bold", 5.8)
        pdf.drawCentredString(x + spec_width / 2, 539, key)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.drawCentredString(x + spec_width / 2, 523, value)

    half_width = (width - 84 - 12) / 2
    _panel(pdf, 42, 206, half_width, 247, fill=PANEL_2)
    _panel(pdf, 42 + half_width + 12, 206, half_width, 247)
    pdf.setFillColor(TEAL)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(58, 420, "ROCm contract")
    _bullet_list(
        pdf,
        [
            "Retain the platform ROCm PyTorch build.",
            "Verify torch.version.hip and device.",
            "Use the torch.cuda compatibility API.",
            "Start with standard PyTorch attention.",
            "Avoid CUDA-only extension assumptions.",
            "Record device and dependency revisions.",
        ],
        58,
        393,
        half_width - 32,
        size=8.3,
        gap=6,
    )
    x2 = 42 + half_width + 28
    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x2, 420, "Cloud acceptance gate")
    _bullet_list(
        pdf,
        [
            "Doctor confirms real ROCm device.",
            "Smoke test completes one masked edit.",
            "Outside-mask preservation remains exact.",
            "Three warm runs are stable.",
            "Latency and peak VRAM are raw JSON.",
            "Model revision is pinned after success.",
        ],
        x2,
        393,
        half_width - 32,
        size=8.3,
        gap=6,
    )
    _tag(pdf, "PENDING REAL RADEON CLOUD EXECUTION", 42, 158, color=RED)
    _text(
        pdf,
        "No local macOS result is presented as model inference or AMD GPU performance.",
        42,
        136,
        width - 84,
        size=9,
        color=MUTED,
    )


def _profile_evidence(pdf: canvas.Canvas, benchmark: dict[str, object]) -> None:
    width, height = A4
    _profile_page(pdf, 6)
    _section_title(
        pdf,
        "05 / Quality and reproducibility",
        "Every claim maps to an artifact, metric, or explicit pending gate",
    )

    metric_width = (width - 84 - 24) / 3
    metrics = [
        ("35 / 35", "CPU-safe tests passing"),
        ("0.000", "outside changed ratio"),
        ("1.000", "outside SSIM"),
    ]
    for index, (value, label) in enumerate(metrics):
        x = 42 + index * (metric_width + 12)
        _panel(pdf, x, 578, metric_width, 110, fill=PANEL_2)
        pdf.setFillColor(TEAL)
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(x + 15, 645, value)
        _text(pdf, label, x + 15, 615, metric_width - 30, size=8.5, color=MUTED)

    _panel(pdf, 42, 317, 249, 230)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, 513, "Run artifact contract")
    _bullet_list(
        pdf,
        [
            "original and source logo",
            "exact warped RGBA layer",
            "rough composite and two masks",
            "refined and final images",
            "illumination visualization",
            "metrics.json and manifest.json",
        ],
        60,
        484,
        213,
        size=8.7,
        gap=7,
    )

    _panel(pdf, 303, 317, 250, 230, fill=PANEL_2)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(321, 513, "Measured local path")
    timings = benchmark["timings_seconds"]
    assert isinstance(timings, dict)
    warm_mean = float(timings["warm_mean"])
    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawString(321, 463, f"{warm_mean:.3f} s")
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawString(321, 443, "WARM MEAN - 1280 x 768 - 4 WARM RUNS")
    _text(
        pdf,
        "Complete deterministic passthrough artifact path on Apple M3 Pro. "
        "This measurement contains no generative model and no Radeon GPU.",
        321,
        410,
        214,
        size=8.8,
        color=WHITE,
        leading=13,
    )
    _tag(pdf, "LOCAL CPU EVIDENCE", 321, 342, color=ORANGE)

    _panel(pdf, 42, 149, width - 84, 135)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, 250, "Automated signals")
    _text(
        pdf,
        "Outside changed-pixel ratio  /  outside SSIM and mean absolute error  /  "
        "logo Delta E 2000  /  variance-of-Laplacian sharpness  /  mask coverage  /  "
        "warnings  /  latency  /  environment provenance",
        60,
        219,
        width - 120,
        size=9.3,
        color=MUTED,
        leading=15,
    )
    _tag(pdf, "RADEON LATENCY + VRAM PLACEHOLDER: CLOUD RUN REQUIRED", 42, 104, color=RED)


def _profile_scenarios(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 7)
    _section_title(
        pdf,
        "06 / Creative scenarios",
        "Fictional procedural fixtures make local behavior reproducible and rights-clear",
    )
    scenarios = [
        (
            "NOVA GRID / BILLBOARD",
            ASSETS_ROOT / "local_previews/billboard/rough_composite.png",
            "billboard",
        ),
        (
            "APEX ZERO / VEHICLE VINYL",
            ASSETS_ROOT / "local_previews/vehicle-panel/rough_composite.png",
            "vehicle-panel",
        ),
        (
            "KINETIQ / FABRIC PRINT",
            ASSETS_ROOT / "local_previews/fabric/rough_composite.png",
            "fabric",
        ),
    ]
    card_height = 158
    for index, (label, path, key) in enumerate(scenarios):
        y = 535 - index * 177
        _panel(pdf, 42, y, width - 84, card_height, fill=PANEL_2 if index % 2 else PANEL)
        _draw_image(pdf, path, 54, y + 12, 252, card_height - 24)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(326, y + 117, label)
        _text(
            pdf,
            "Committed input, fictional transparent logo, four corners, exact layer, "
            "mask, and deterministic rough preview.",
            326,
            y + 92,
            205,
            size=8.5,
            color=MUTED,
            leading=12,
        )
        _tag(pdf, "LOCAL PASSTHROUGH", 326, y + 28, color=ORANGE)
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 6.5)
        pdf.drawRightString(531, y + 33, key)

    _text(
        pdf,
        "Final judging examples should add rights-cleared real photographs and real "
        "Radeon refinements while retaining these fixtures as regression evidence.",
        42,
        91,
        width - 84,
        size=8.8,
        color=MUTED,
    )


def _profile_status(pdf: canvas.Canvas) -> None:
    width, height = A4
    _profile_page(pdf, 8)
    _section_title(
        pdf,
        "07 / Delivery status",
        "Local package ready; cloud evidence deliberately unfilled",
    )

    half_width = (width - 84 - 12) / 2
    _panel(pdf, 42, 435, half_width, 247, fill=PANEL_2)
    _panel(pdf, 42 + half_width + 12, 435, half_width, 247)
    pdf.setFillColor(TEAL)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(59, 647, "Ready locally")
    _bullet_list(
        pdf,
        [
            "Deterministic CV stack",
            "Exact-logo restoration",
            "Metrics and manifests",
            "Interactive Gradio app",
            "Radeon backend contract",
            "Doctor and benchmark tools",
            "Three demo fixtures",
            "35 passing tests",
        ],
        59,
        617,
        half_width - 34,
        size=8.5,
        gap=5,
    )
    x2 = 42 + half_width + 29
    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x2, 647, "Radeon Cloud gate")
    _bullet_list(
        pdf,
        [
            "Confirm ROCm environment",
            "Download and pin model revision",
            "Run masked smoke test",
            "Capture cold and warm timing",
            "Capture peak allocated VRAM",
            "Record real GPU and ROCm facts",
            "Export actual refined examples",
            "Record 3-5 minute demo video",
        ],
        x2,
        617,
        half_width - 34,
        size=8.5,
        gap=5,
    )

    _panel(pdf, 42, 259, width - 84, 139, fill=PANEL_2)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(60, 364, "Known limitations")
    _text(
        pdf,
        "Current examples are procedural development fixtures, not real photographs. "
        "Local outputs are deterministic rough previews, not model refinements. "
        "Radeon compatibility, visual improvement, latency, and peak VRAM require "
        "real cloud execution. LoRA remains an optional experiment.",
        60,
        335,
        width - 120,
        size=9.3,
        color=MUTED,
        leading=14,
    )

    _panel(pdf, 42, 130, width - 84, 93)
    pdf.setFillColor(ORANGE)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(60, 191, "REFERENCES")
    _text(
        pdf,
        "luma.com/amd-4dhi  |  huggingface.co/black-forest-labs/FLUX.2-klein-4B  |  "
        "huggingface.co/docs/diffusers/api/pipelines/flux2  |  "
        "github.com/JaviChulvi/Radeon-hackathon-2026-07",
        60,
        169,
        width - 120,
        size=7.5,
        color=MUTED,
        leading=11,
    )
    _tag(pdf, STATUS, 42, 86, color=RED)


def build_profile(output_path: Path) -> None:
    benchmark = json.loads((PROJECT_ROOT / "benchmarks/local-results.json").read_text())
    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    pdf.setTitle("Radeon SponsorSkin - Project Profile")
    pdf.setAuthor("Radeon SponsorSkin contributors")
    pages = [
        _profile_cover,
        _profile_background,
        _profile_workflow,
        _profile_geometry,
        _profile_model,
        lambda target: _profile_evidence(target, benchmark),
        _profile_scenarios,
        _profile_status,
    ]
    for page_number, draw_page in enumerate(pages, start=1):
        draw_page(pdf)
        _profile_footer(pdf, page_number)
        pdf.showPage()
    pdf.save()


def build_poster(output_path: Path) -> None:
    width, height = landscape(A3)
    pdf = canvas.Canvas(str(output_path), pagesize=(width, height))
    pdf.setTitle("Radeon SponsorSkin - Track 1 Poster")
    pdf.setAuthor("Radeon SponsorSkin contributors")
    pdf.setFillColor(INK)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setFillColor(RED)
    pdf.rect(0, height - 12, width, 12, fill=1, stroke=0)

    _tag(pdf, "TRACK 1 - MULTIMODAL CONTENT CREATION", 46, height - 61, color=ORANGE)
    _text(
        pdf,
        "Radeon SponsorSkin",
        46,
        height - 108,
        650,
        font="Helvetica-Bold",
        size=33,
        leading=36,
    )
    _text(
        pdf,
        "Exact brand in. Realistic mockup out.",
        46,
        height - 145,
        650,
        font="Helvetica-Bold",
        size=17,
        color=TEAL,
    )
    _tag(pdf, "RADEON VALIDATION PENDING", width - 247, height - 61, color=RED)

    hero_y, hero_height = 255, 400
    hero_width = 495
    _panel(pdf, 46, hero_y, hero_width, hero_height, fill=PANEL_2)
    _draw_image(
        pdf,
        ASSETS_ROOT / "local_previews/billboard/rough_composite.png",
        58,
        hero_y + 47,
        hero_width - 24,
        hero_height - 67,
    )
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(61, hero_y + 24, "LOCAL DETERMINISTIC ROUGH COMPOSITE")

    x_right = 565
    right_width = width - x_right - 46
    _panel(pdf, x_right, 469, right_width, 186)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(x_right + 22, 620, "The workflow")
    steps = [
        ("01", "Upload target + exact logo"),
        ("02", "Click four surface corners"),
        ("03", "Masked material refinement"),
        ("04", "Restore exact logo geometry"),
        ("05", "Verify and export evidence"),
    ]
    for index, (number, copy) in enumerate(steps):
        y = 589 - index * 25
        pdf.setFillColor(ORANGE if index < 3 else TEAL)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(x_right + 22, y, number)
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(x_right + 50, y, copy)

    _panel(pdf, x_right, 255, right_width, 198, fill=PANEL_2)
    pdf.setFillColor(WHITE)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(x_right + 22, 419, "Local evidence")
    evidence = [
        ("35 / 35", "CPU-safe tests"),
        ("0.000", "outside changed ratio"),
        ("1.000", "outside SSIM"),
    ]
    evidence_width = (right_width - 56) / 3
    for index, (value, label) in enumerate(evidence):
        x = x_right + 22 + index * (evidence_width + 6)
        pdf.setFillColor(PANEL)
        pdf.roundRect(x, 334, evidence_width, 63, 6, fill=1, stroke=0)
        pdf.setFillColor(TEAL)
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawCentredString(x + evidence_width / 2, 370, value)
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica-Bold", 5.7)
        pdf.drawCentredString(x + evidence_width / 2, 350, label.upper())
    _text(
        pdf,
        "Real Radeon GPU latency, peak VRAM, and refined outputs will be inserted "
        "only after the cloud smoke and benchmark gates pass.",
        x_right + 22,
        306,
        right_width - 44,
        size=8.7,
        color=WHITE,
        leading=13,
    )
    _tag(pdf, "NO LOCAL GPU CLAIM", x_right + 22, 271, color=RED)

    scenario_y = 78
    scenario_height = 163
    scenario_width = (width - 92 - 24) / 3
    scenarios = [
        ("BILLBOARD", "billboard"),
        ("VEHICLE VINYL", "vehicle-panel"),
        ("FABRIC PRINT", "fabric"),
    ]
    for index, (label, key) in enumerate(scenarios):
        x = 46 + index * (scenario_width + 12)
        _panel(pdf, x, scenario_y, scenario_width, scenario_height)
        _draw_image(
            pdf,
            ASSETS_ROOT / f"local_previews/{key}/rough_composite.png",
            x + 8,
            scenario_y + 28,
            scenario_width - 16,
            scenario_height - 38,
        )
        pdf.setFillColor(WHITE)
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawString(x + 10, scenario_y + 11, label)

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6.5)
    pdf.drawRightString(width - 46, 35, "github.com/JaviChulvi/Radeon-hackathon-2026-07")
    pdf.save()


def build_poster_svg(output_path: Path) -> None:
    width, height = 1191, 842
    scenario_width = 355

    def png_data_uri(path: Path) -> str:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{payload}"

    hero_uri = png_data_uri(ASSETS_ROOT / "local_previews/billboard/rough_composite.png")
    items = [
        ("BILLBOARD", "billboard"),
        ("VEHICLE VINYL", "vehicle-panel"),
        ("FABRIC PRINT", "fabric"),
    ]
    scenario_markup = []
    for index, (label, key) in enumerate(items):
        x = 46 + index * (scenario_width + 16)
        image_uri = png_data_uri(ASSETS_ROOT / f"local_previews/{key}/rough_composite.png")
        scenario_markup.append(
            f"""
  <g id="scenario-{escape(key)}">
    <rect x="{x}" y="604" width="{scenario_width}" height="175" rx="10" fill="#161C27"/>
    <image href="{image_uri}" xlink:href="{image_uri}"
      x="{x + 10}" y="614" width="{scenario_width - 20}" height="135"
      preserveAspectRatio="xMidYMid meet"/>
    <text x="{x + 12}" y="766" class="label">{escape(label)}</text>
  </g>"""
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}"
  viewBox="0 0 {width} {height}">
  <title>Radeon SponsorSkin Track 1 poster</title>
  <style>
    .title {{ font: 700 48px Helvetica, Arial, sans-serif; fill: #F4F1EA; }}
    .subtitle {{ font: 700 23px Helvetica, Arial, sans-serif; fill: #31D0AA; }}
    .heading {{ font: 700 22px Helvetica, Arial, sans-serif; fill: #F4F1EA; }}
    .body {{ font: 16px Helvetica, Arial, sans-serif; fill: #F4F1EA; }}
    .muted {{ font: 14px Helvetica, Arial, sans-serif; fill: #AAB4C4; }}
    .label {{ font: 700 13px Helvetica, Arial, sans-serif; fill: #F4F1EA; }}
    .metric {{ font: 700 28px Helvetica, Arial, sans-serif; fill: #31D0AA; }}
    .small {{ font: 700 11px Helvetica, Arial, sans-serif; fill: #AAB4C4; }}
  </style>
  <rect width="{width}" height="{height}" fill="#0B0F16"/>
  <rect width="{width}" height="12" fill="#D91E36"/>
  <rect x="46" y="38" width="320" height="25" rx="13" fill="#F27622"/>
  <text x="206" y="55" text-anchor="middle" class="small" fill="#0B0F16">
    TRACK 1 - MULTIMODAL CONTENT CREATION
  </text>
  <text x="46" y="117" class="title">Radeon SponsorSkin</text>
  <text x="46" y="154" class="subtitle">Exact brand in. Realistic mockup out.</text>
  <rect x="919" y="38" width="226" height="25" rx="13" fill="#D91E36"/>
  <text x="1032" y="55" text-anchor="middle" class="small" fill="#0B0F16">
    RADEON VALIDATION PENDING
  </text>

  <g id="hero">
    <rect x="46" y="184" width="520" height="390" rx="12" fill="#222A38"/>
    <image href="{hero_uri}" xlink:href="{hero_uri}"
      x="58" y="198" width="496" height="335" preserveAspectRatio="xMidYMid meet"/>
    <text x="61" y="555" class="label">LOCAL DETERMINISTIC ROUGH COMPOSITE</text>
  </g>

  <g id="workflow">
    <rect x="590" y="184" width="555" height="186" rx="12" fill="#161C27"/>
    <text x="614" y="221" class="heading">The workflow</text>
    <text x="614" y="257" class="body">01  Upload target + exact logo</text>
    <text x="614" y="283" class="body">02  Click four surface corners</text>
    <text x="614" y="309" class="body">03  Masked material refinement</text>
    <text x="614" y="335" class="body">04  Restore exact logo, verify, export</text>
  </g>

  <g id="evidence">
    <rect x="590" y="386" width="555" height="188" rx="12" fill="#222A38"/>
    <text x="614" y="422" class="heading">Local evidence</text>
    <text x="614" y="466" class="metric">35 / 35</text>
    <text x="760" y="466" class="metric">0.000</text>
    <text x="900" y="466" class="metric">1.000</text>
    <text x="614" y="489" class="small">CPU-SAFE TESTS</text>
    <text x="760" y="489" class="small">OUTSIDE CHANGE</text>
    <text x="900" y="489" class="small">OUTSIDE SSIM</text>
    <text x="614" y="523" class="muted">
      Real Radeon latency, VRAM, and refined outputs remain pending.
    </text>
    <rect x="614" y="539" width="170" height="23" rx="12" fill="#D91E36"/>
    <text x="699" y="555" text-anchor="middle" class="small" fill="#0B0F16">
      NO LOCAL GPU CLAIM
    </text>
  </g>
{"".join(scenario_markup)}
  <text x="1145" y="814" text-anchor="end" class="small">
    github.com/JaviChulvi/Radeon-hackathon-2026-07
  </text>
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")


def validate_pdf(path: Path, expected_pages: int) -> None:
    reader = PdfReader(path)
    if len(reader.pages) != expected_pages:
        raise RuntimeError(
            f"{path.name}: expected {expected_pages} page(s), got {len(reader.pages)}"
        )
    for index, page in enumerate(reader.pages, start=1):
        extracted = (page.extract_text() or "").strip()
        if len(extracted) < 40:
            raise RuntimeError(f"{path.name}: page {index} has insufficient text")


def main() -> None:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    profile_path = DOCS_ROOT / "project-profile.pdf"
    poster_path = DOCS_ROOT / "poster.pdf"
    poster_svg_path = DOCS_ROOT / "poster.svg"
    build_profile(profile_path)
    build_poster(poster_path)
    build_poster_svg(poster_svg_path)
    validate_pdf(profile_path, expected_pages=8)
    validate_pdf(poster_path, expected_pages=1)
    print(f"Built and validated {profile_path.relative_to(PROJECT_ROOT)}")
    print(f"Built and validated {poster_path.relative_to(PROJECT_ROOT)}")
    print(f"Built editable {poster_svg_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
