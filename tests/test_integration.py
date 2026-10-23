import asyncio
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from minecraft_skin_toolkit.io import build_artifacts, output_path
from minecraft_skin_toolkit.preview import preview_skin

PARTS=("head","body","right_arm","left_arm","right_leg","left_leg")
def design(model="classic"):
    return {"model":model,"palette":{"blue":"#2288CC","gold":"#EEAA44"},"base":{part:"blue" for part in PARTS},"paint":[{"part":"head","layer":"overlay","face":"front","rect":[1,1,2,2],"color":"gold"}]}

class IntegrationTests(unittest.TestCase):
    def test_artifacts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result=build_artifacts(design(),root,"sample")
            original=Path(result["skin"]).read_bytes()
            with self.assertRaises(FileExistsError):build_artifacts(design("slim"),root,"sample")
            self.assertEqual(original,Path(result["skin"]).read_bytes())
            with Image.open(result["preview"]) as preview:
                self.assertEqual(preview.size,(936,452))
            with self.assertRaises(ValueError):build_artifacts(design(),root,"../escape")
            with self.assertRaises(ValueError):output_path(root,"../escape.png")
            (root/"link").symlink_to(root.parent,target_is_directory=True)
            with self.assertRaises(ValueError):output_path(root,"link/escape.png")

    def test_cli_build_validate_and_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); source=root/"design.json"
            source.write_text(json.dumps(design("slim")))
            def cli(*args):
                return subprocess.run([sys.executable,"-m","minecraft_skin_toolkit.cli",*map(str,args)],capture_output=True,text=True,check=True)
            built=json.loads(cli("build",source,"--name","cli-test","--output-root",root).stdout)
            self.assertTrue(json.loads(cli("validate",built["skin"],"--model","slim").stdout)["valid"])
            cli("preview",built["skin"],"--model","slim","--output",root/"copy.png")
            self.assertTrue((root/"copy.png").is_file())

    def test_stdio_discovery_build_validation_and_images(self):
        async def run(root):
            params=StdioServerParameters(command=sys.executable,args=["-m","minecraft_skin_toolkit.server","--output-root",str(root)])
            async with stdio_client(params) as (read,write):
                async with ClientSession(read,write) as client:
                    await client.initialize()
                    tools=(await client.list_tools()).tools
                    self.assertEqual({t.name for t in tools},{"skin_schema","skin_build","skin_validate","skin_preview"})
                    schema=await client.call_tool("skin_schema",{"model":"slim"})
                    self.assertFalse(schema.isError)
                    build=await client.call_tool("skin_build",{"design":design("slim"),"name":"mcp-test"})
                    self.assertFalse(build.isError,build.content)
                    self.assertTrue(any(c.type=="image" for c in build.content))
                    valid=await client.call_tool("skin_validate",{"path":"mcp-test/skin.png","model":"slim"})
                    self.assertFalse(valid.isError)
                    self.assertTrue(json.loads(valid.content[0].text)["valid"])
                    preview=await client.call_tool("skin_preview",{"path":"mcp-test/skin.png","model":"slim"})
                    self.assertEqual(preview.content[0].type,"image")
                    for args in ({"path":"../secret.png"},{"path":"/tmp/secret.png"}):
                        self.assertTrue((await client.call_tool("skin_validate",args)).isError)
                    self.assertTrue((await client.call_tool("skin_build",{"design":design(),"name":"mcp-test"})).isError)
                    bad=design();bad["paint"][0]["rect"][0]=True
                    self.assertTrue((await client.call_tool("skin_build",{"design":bad,"name":"bad"})).isError)
                    self.assertFalse((root/"bad").exists())
        with tempfile.TemporaryDirectory() as temp:asyncio.run(run(Path(temp)))

if __name__=="__main__":unittest.main()
