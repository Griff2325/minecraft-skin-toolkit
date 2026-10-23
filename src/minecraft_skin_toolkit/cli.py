"""CLI using exactly the same core and artifacts as MCP."""
import argparse
import json
from pathlib import Path
from .core import uv_faces, validate_skin
from .io import build_artifacts, load_skin
from .models import Design
from .preview import preview_skin


def main():
    parser=argparse.ArgumentParser(description="Build, validate and preview standard Minecraft skins")
    commands=parser.add_subparsers(dest="command",required=True)
    build=commands.add_parser("build")
    build.add_argument("design",type=Path)
    build.add_argument("--name",required=True)
    build.add_argument("--output-root",type=Path,default=Path.cwd()/".skin-output")
    for name in ("validate","preview"):
        cmd=commands.add_parser(name)
        cmd.add_argument("skin",type=Path)
        cmd.add_argument("--model",choices=("classic","slim"),default="classic")
        if name=="preview":cmd.add_argument("--output",required=True,type=Path)
    schema=commands.add_parser("schema")
    schema.add_argument("--model",choices=("classic","slim"),default="classic")
    args=parser.parse_args()
    try:
        if args.command=="build":
            if args.design.stat().st_size>2*1024*1024:raise ValueError("Design JSON must be at most 2 MiB")
            design=Design.model_validate_json(args.design.read_text()).model_dump()
            result=build_artifacts(design,args.output_root,args.name)
        elif args.command=="validate":
            result=validate_skin(load_skin(args.skin),args.model)
        elif args.command=="preview":
            image=preview_skin(load_skin(args.skin),args.model)
            with args.output.open("xb") as output:image.save(output,format="PNG")
            result={"preview":str(args.output.resolve())}
        else:
            result={"design_schema":Design.model_json_schema(),"faces":[{"part":p,"layer":l,"face":f,"uv":[x,y,w,h]} for (p,l,f),(x,y,w,h) in uv_faces(args.model).items()]}
        print(json.dumps(result,indent=2))
        if args.command=="validate" and not result["valid"]:raise SystemExit(1)
    except (ValueError,OSError) as error:
        parser.exit(2,f"Error: {error}\n")

if __name__=="__main__":main()
