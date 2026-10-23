"""Local stdio MCP adapter for Codex, Claude Code, and other MCP clients."""
import argparse
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Image as MCPImage
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from .core import uv_faces, validate_skin
from .io import build_artifacts, load_skin, output_path
from .models import Design, Model
from .preview import preview_skin
from io import BytesIO


def create_server(root: Path) -> FastMCP:
    root = root.resolve()
    server = FastMCP("Minecraft Skin Toolkit", instructions="Create original standard Minecraft skins locally. Call skin_schema to learn face dimensions; build using named colors and face-local rectangles. Inspect the returned preview and revise under a new name. No account, web access, or launcher access. All file paths are relative to the configured output root.")
    read = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

    @server.tool(annotations=read)
    def skin_schema(model: Model = "classic") -> dict:
        """Return complete design JSON schema and canonical UV face sizes. Faces are viewed externally; left/right name the character's side. Top face local top is back edge; bottom local top is front edge."""
        return {"design_schema":Design.model_json_schema(),"faces":[{"part":p,"layer":l,"face":f,"uv":[x,y,w,h],"size":[w,h]} for (p,l,f),(x,y,w,h) in uv_faces(model).items()]}

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False))
    def skin_build(design: Design, name: str) -> CallToolResult:
        """Build a 64x64 PNG, editable design.json, and front/back/side preview in a NEW named folder. All six base parts require opaque palette colors. Paint is ordered rectangles within a face. Return paths, validation and the actual preview image. Use a new name for each revision; existing files are never overwritten."""
        result = build_artifacts(design.model_dump(), root, name)
        return CallToolResult(content=[TextContent(type="text",text=json.dumps(result)), MCPImage(path=result["preview"]).to_image_content()])

    @server.tool(annotations=read)
    def skin_validate(path: str, model: Model = "classic") -> dict:
        """Validate a PNG inside the output root. Model must be supplied correctly; PNG alone cannot reliably distinguish classic/slim geometry. Checks technical compatibility, not artistic quality or in-game acceptance."""
        return validate_skin(load_skin(output_path(root,path)),model)

    @server.tool(annotations=read)
    def skin_preview(path: str, model: Model = "classic") -> CallToolResult:
        """Return a front/back/right/left orthographic image of a PNG inside the output root. Outer layers composite at native texel scale; this is an inspection sheet, not an in-game 3D rendering."""
        image = preview_skin(load_skin(output_path(root,path)),model)
        data=BytesIO(); image.save(data,format="PNG")
        return CallToolResult(content=[MCPImage(data=data.getvalue(),format="png").to_image_content()])

    return server


def main():
    parser=argparse.ArgumentParser(description="Local Minecraft skin MCP server (stdio)")
    parser.add_argument("--output-root",type=Path,default=Path.cwd()/".skin-output",help="Only folder the MCP server may read/write")
    args=parser.parse_args()
    create_server(args.output_root).run(transport="stdio")

if __name__ == "__main__":
    main()
