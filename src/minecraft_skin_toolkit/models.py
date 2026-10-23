"""Discoverable MCP input schema; core also validates direct Python/CLI callers."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictInt

Part = Literal["head", "body", "right_arm", "left_arm", "right_leg", "left_leg"]
Model = Literal["classic", "slim"]

class Paint(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    part: Part
    layer: Literal["base", "overlay"] = "base"
    face: Literal["front", "back", "left", "right", "top", "bottom"]
    rect: list[StrictInt] = Field(min_length=4, max_length=4, description="[x,y,width,height] in face-local texels, viewed externally; no clipping")
    color: str = Field(min_length=1, max_length=64, description="Existing palette key")

class Design(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    model: Model = "classic"
    palette: dict[str, str] = Field(max_length=256, description="Named #RRGGBB or #RRGGBBAA colors")
    base: dict[Part, str] = Field(description="Required opaque fill color for all six body parts")
    paint: list[Paint] = Field(default_factory=list, max_length=4096, description="Ordered face-local rectangle operations; overlays start transparent")
