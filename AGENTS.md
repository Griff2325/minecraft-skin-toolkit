# Minecraft Skin Toolkit

Original local tools for agents to author standard Minecraft skins. No PMCSkin3D code or assets are included.

- Keep the raster/UV core shared by CLI and MCP. Use Pillow for images and the official Python MCP SDK for transport.
- Scope: standard 64×64 classic/slim skins, face-local rectangles, validation, previews. No account access, telemetry, skin downloads, or launcher modification.
- Core API: `uv_faces(model)` returns `(part, layer, face) -> (x,y,w,h)`; `build_skin(design)` returns Pillow RGBA image; `validate_skin(image, model)` returns JSON-safe report with `valid`, `errors`, `warnings`.
- Design schema: `model` classic/slim; `palette` mapping color names to #RRGGBB or #RRGGBBAA; `base` mapping each of head/body/right_arm/left_arm/right_leg/left_leg to a palette color; `paint` ordered rectangles `{part, layer: base|overlay, face: front|back|left|right|top|bottom, rect:[x,y,w,h], color}`. Rectangles use top-left face-local coordinates, as viewed looking straight at that face. Right/left refer to the character. Transparent overlays by default, all base parts required and opaque.
- Reject malformed or out-of-bounds input. Never silently clip, overwrite an existing file, or access outside a configured output root through MCP.
- Run `uv run python -m unittest discover -s tests` and protocol smoke tests before release. Inspect generated previews and import PNG in PMCSkin3D. In-game compatibility must be reported separately until tested.
- Keep user portraits and private paths out of public examples. Use a generic example in the repository.
