"""Shared artifact I/O. New builds never overwrite an existing design."""
import json
import re
from pathlib import Path
from PIL import Image
from .core import build_skin, validate_skin
from .preview import preview_skin


def load_skin(path: Path) -> Image.Image:
    if path.stat().st_size > 1024*1024:
        raise ValueError("Skin PNG must be at most 1 MiB")
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != (64,64):
            raise ValueError("Expected a standard 64x64 PNG")
        image.load()
        return image.copy()


def output_path(root: Path, relative: str) -> Path:
    candidate = (root/relative).resolve()
    if candidate == root or not candidate.is_relative_to(root):
        raise ValueError("Path must stay inside the configured output root")
    return candidate


def build_artifacts(design: dict, root: Path, name: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError("Name must be 1-64 letters, digits, underscores or hyphens")
    image = build_skin(design)
    model = design.get("model", "classic")
    report = validate_skin(image, model)
    if not report["valid"]:
        raise ValueError(json.dumps(report))
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    folder = root/name
    folder.mkdir()  # Exclusive new revision: existing designs are never replaced.
    (folder/"design.json").write_text(json.dumps(design, indent=2)+"\n")
    image.save(folder/"skin.png", format="PNG")
    preview_skin(image, model).save(folder/"preview.png", format="PNG")
    return {"model":model,"skin":str(folder/"skin.png"),"design":str(folder/"design.json"),"preview":str(folder/"preview.png"),"validation":report}
