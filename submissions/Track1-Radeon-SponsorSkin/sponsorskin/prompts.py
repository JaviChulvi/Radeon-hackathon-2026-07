"""Conservative material prompts for exact-logo-aware refinement."""

from __future__ import annotations

from sponsorskin.schemas import MaterialPreset

MATERIAL_DESCRIPTIONS = {
    MaterialPreset.VINYL: (
        "a professionally applied vinyl decal on glossy painted metal, with subtle local "
        "reflections and physically plausible contact edges"
    ),
    MaterialPreset.FABRIC_PRINT: (
        "a high-quality print embedded in fabric, following the existing folds, weave, "
        "illumination, and soft self-shadowing"
    ),
    MaterialPreset.BILLBOARD: (
        "professionally installed billboard or signage graphics, following the panel texture, "
        "ambient light, and existing perspective"
    ),
    MaterialPreset.PAINTED_WALL: (
        "carefully painted wall graphics, inheriting the wall texture, surface irregularities, "
        "lighting, and restrained edge wear"
    ),
}


def material_prompt(material: MaterialPreset) -> str:
    """Return the release prompt for a selected surface material."""

    description = MATERIAL_DESCRIPTIONS[material]
    return (
        f"Integrate the supplied exact logo as {description}. Preserve the exact logo lettering, "
        "geometry, proportions, colors, position, and orientation. Preserve the object, camera, "
        "background, and all pixels outside the white mask. Change only local material response, "
        "lighting, reflections, texture, and contact edges inside the mask. Do not invent, "
        "rewrite, remove, or add any text or logo elements."
    )
