"""Strict rectangle authoring for the standard Minecraft 64×64 skin atlas.

Left/right name the character's sides. Vertical faces are viewed from outside,
head upward; top's upper edge is the back, bottom's upper edge is the front.
These are the standard unfolded cube orientations; no atlas flips are needed.
"""

import re
from collections.abc import Mapping

from PIL import Image

PARTS = ("head", "body", "right_arm", "left_arm", "right_leg", "left_leg")
LAYERS = ("base", "overlay")
FACES = ("front", "back", "left", "right", "top", "bottom")
MAX_PALETTE = 256
MAX_PAINT = 4096
_COLOR = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\Z")


def uv_faces(model):
    """Return fresh ``(part, layer, face): (x, y, width, height)`` mapping."""
    if model not in ("classic", "slim"):
        raise ValueError("model must be 'classic' or 'slim'")
    arm = 4 if model == "classic" else 3
    # Origin, width, height, depth; overlay origins follow the same cube net.
    cubes = {
        "head": ((0, 0), (32, 0), 8, 8, 8),
        "body": ((16, 16), (16, 32), 8, 12, 4),
        "right_arm": ((40, 16), (40, 32), arm, 12, 4),
        "left_arm": ((32, 48), (48, 48), arm, 12, 4),
        "right_leg": ((0, 16), (0, 32), 4, 12, 4),
        "left_leg": ((16, 48), (0, 48), 4, 12, 4),
    }
    result = {}
    for part, (base, overlay, width, height, depth) in cubes.items():
        for layer, (x, y) in zip(LAYERS, (base, overlay)):
            faces = {
                "right": (x, y + depth, depth, height),
                "front": (x + depth, y + depth, width, height),
                "left": (x + depth + width, y + depth, depth, height),
                "back": (x + 2 * depth + width, y + depth, width, height),
                "top": (x + depth, y, width, depth),
                "bottom": (x + depth + width, y, width, depth),
            }
            result.update({(part, layer, face): rect for face, rect in faces.items()})
    return result


def _fields(value, required, optional, label):
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f"{label}: missing fields {sorted(missing)}; unknown fields {sorted(map(str, extra))}")


def build_skin(design):
    """Validate a design and render it. Malformed designs raise ValueError.

    Rectangles replace RGBA pixels, including alpha; they do not blend. Base
    paint must be opaque, so generated skins always have fully opaque bodies.
    """
    _fields(design, ("model", "palette", "base"), ("paint",), "design")
    faces = uv_faces(design["model"])
    palette = design["palette"]
    if not isinstance(palette, Mapping) or not 1 <= len(palette) <= MAX_PALETTE:
        raise ValueError(f"palette must contain 1..{MAX_PALETTE} colors")
    colors = {}
    for name, value in palette.items():
        if not isinstance(name, str) or not 1 <= len(name) <= 64:
            raise ValueError("palette names must be strings of 1..64 characters")
        if not isinstance(value, str) or not _COLOR.fullmatch(value):
            raise ValueError(f"palette color {name!r} must be #RRGGBB or #RRGGBBAA")
        channels = tuple(int(value[i:i + 2], 16) for i in range(1, len(value), 2))
        colors[name] = channels if len(channels) == 4 else channels + (255,)

    def color(name):
        if not isinstance(name, str) or name not in colors:
            raise ValueError("color must name an existing palette entry")
        return colors[name]

    base = design["base"]
    _fields(base, PARTS, (), "base")
    image = Image.new("RGBA", (64, 64))
    for part in PARTS:
        rgba = color(base[part])
        if rgba[3] != 255:
            raise ValueError(f"base color for {part} must be opaque")
        for face in FACES:
            x, y, w, h = faces[part, "base", face]
            image.paste(rgba, (x, y, x + w, y + h))
    paint = design.get("paint", [])
    if not isinstance(paint, list) or len(paint) > MAX_PAINT:
        raise ValueError(f"paint must be a list of at most {MAX_PAINT} rectangles")
    for index, operation in enumerate(paint):
        _fields(operation, ("part", "layer", "face", "rect", "color"), (), f"paint[{index}]")
        part, layer, face = (operation[k] for k in ("part", "layer", "face"))
        if part not in PARTS or layer not in LAYERS or face not in FACES:
            raise ValueError(f"paint[{index}] has an unknown part, layer, or face")
        rect = operation["rect"]
        if not isinstance(rect, list) or len(rect) != 4 or any(type(v) is not int for v in rect):
            raise ValueError(f"paint[{index}].rect must be four integers")
        x, y, w, h = rect
        u, v, fw, fh = faces[part, layer, face]
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > fw or y + h > fh:
            raise ValueError(f"paint[{index}].rect is outside the {fw}×{fh} face")
        rgba = color(operation["color"])
        if layer == "base" and rgba[3] != 255:
            raise ValueError(f"paint[{index}] base paint must be opaque")
        image.paste(rgba, (u + x, v + y, u + x + w, v + y + h))
    return image


def validate_skin(image, model):
    """Check dimensions and every required face; model must be supplied.

    Accepts any Pillow mode and checks its RGBA conversion (including palette
    transparency). PNG encoding is the caller's responsibility. No pixel-based
    model detection is attempted because the model is separate skin metadata.
    """
    faces = uv_faces(model)
    errors, warnings = [], []
    report = {"valid": False, "errors": errors, "warnings": warnings, "model": model,
              "size": None, "coverage": {}}
    if not isinstance(image, Image.Image):
        errors.append("image must be a Pillow image")
        return report
    report["size"] = list(image.size)
    if image.size != (64, 64):
        errors.append("skin dimensions must be 64×64 pixels")
        return report
    rgba = image.convert("RGBA")
    coverage = report["coverage"]
    alpha = rgba.getchannel("A")
    for part in PARTS:
        for layer in LAYERS:
            pixels = []
            for face in FACES:
                x, y, w, h = faces[part, layer, face]
                alphas = list(alpha.crop((x, y, x + w, y + h)).tobytes())
                pixels.extend(alphas)
                if layer == "base" and any(a != 255 for a in alphas):
                    errors.append(f"{part}/base/{face} contains non-opaque pixels")
            coverage[f"{part}/{layer}"] = {"total_pixels": len(pixels),
                "visible_pixels": sum(a > 0 for a in pixels),
                "opaque_pixels": sum(a == 255 for a in pixels)}
    if all(coverage[f"{part}/overlay"]["visible_pixels"] == 0 for part in PARTS):
        warnings.append("All overlays are transparent")
    report["valid"] = not errors
    return report
