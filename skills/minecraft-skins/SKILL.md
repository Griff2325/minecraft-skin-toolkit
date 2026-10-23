---
name: minecraft-skins
description: Create, validate, preview, and refine original Minecraft player skin PNGs using the local Minecraft Skin Toolkit CLI or MCP server. Use for standard classic/slim custom skins, including reference-inspired character designs.
---

Use the `minecraft-skins` MCP server when connected. Its four tools are `skin_schema`, `skin_build`, `skin_validate`, and `skin_preview`. Otherwise use the installed `minecraft-skin` CLI from this repository. Locate the checkout from the configured MCP launch command. Read its README for setup and `examples/cobalt-explorer.json` for a full design. Do not assume the installed skill folder is the checkout.

- Inspect any supplied reference before designing. Identify hair color/style, facial hair, skin tone, clothing, and distinctive details. Preserve the user's concrete choices. Do not promise photographic likeness from an 8×8 face.
- Call `skin_schema` for the intended classic/slim model. Write a palette, opaque base fills for all six parts, and ordered face-local rectangles. Left/right refer to the character; use the schema's face sizes instead of guessing UV offsets.
- Build under a new revision name. Inspect the returned image, especially face readability, moustache/beard distinction, clothing seams, and every visible side. A technically valid PNG can still be poor artwork. Revise when the preview misses the brief.
- Keep unwanted overlays transparent. Use outer-layer detail deliberately. Alpha is replaced, not blended. Base layers must remain opaque.
- Validate the exported PNG with the intended model. Classic/slim cannot reliably be detected from pixels alone. Preview sheets are orthographic and do not show outer-layer expansion or in-game lighting.
- Return the final PNG, preview and editable design. Keep personal references out of public examples unless the user asks to share them. The tool does not upload skins or equip them in-game.

CLI fallback:

```sh
uv run --directory /absolute/path/minecraft-skin-toolkit minecraft-skin build /absolute/path/design.json --name character-v1 --output-root /absolute/path/skin-output
uv run --directory /absolute/path/minecraft-skin-toolkit minecraft-skin validate /absolute/path/skin-output/character-v1/skin.png --model classic
```

MCP file paths are relative to its configured output root; it cannot read arbitrary files elsewhere. Put imported PNGs inside that folder before previewing. New builds never overwrite existing folders. This release supports only 64×64 skins; use a suitable editor for HD or legacy layouts. PMCSkin3D can be used for manual refinement, but this toolkit does not wrap or copy its editor.
