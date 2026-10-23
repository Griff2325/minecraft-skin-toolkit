"""Orthographic inspection sheet made from the actual exported UV texture."""
from PIL import Image, ImageDraw, ImageFont
from .core import uv_faces


def preview_skin(skin: Image.Image, model: str = "classic") -> Image.Image:
    faces = uv_faces(model)
    skin = skin.convert("RGBA")
    if skin.size != (64, 64):
        raise ValueError("Preview requires a 64x64 skin")
    sheet = Image.new("RGB", (936, 452), "#15201e")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    d.text((24, 16), f"MINECRAFT SKIN / {model.upper()}", font=font, fill="#e9e4d3")
    arm = 4 if model == "classic" else 3
    for index, face in enumerate(("front", "back", "right", "left")):
        view = Image.new("RGBA", (16, 32))
        if face in ("front", "back"):
            # Front: character right appears on the left. Back: reverse it.
            a, b = ("right", "left") if face == "front" else ("left", "right")
            positions = [("head", (4,0)), ("body", (4,8)),
                         (a+"_arm", (4-arm,8)), (b+"_arm", (12,8)),
                         (a+"_leg", (4,20)), (b+"_leg", (8,20))]
        else:
            side = "right" if face == "right" else "left"
            positions = [("head", (4,0)), ("body", (6,8)),
                         (side+"_leg", (6,20)), (side+"_arm", (6,8))]
        for part, pos in positions:
            for layer in ("base", "overlay"):
                x,y,w,h = faces[part,layer,face]
                view.alpha_composite(skin.crop((x,y,x+w,y+h)), pos)
        x = 24+index*228
        d.rounded_rectangle((x,55,x+204,405), radius=12, fill="#22352f")
        sheet.paste(view.resize((160,320),Image.Resampling.NEAREST),(x+22,67),view.resize((160,320),Image.Resampling.NEAREST))
        d.text((x+20,416),face.upper(),font=font,fill="#c5d5c8")
    return sheet
