import copy
import io
import unittest

from PIL import Image
from minecraft_skin_toolkit.core import PARTS, MAX_PAINT, build_skin, uv_faces, validate_skin


def design(model="classic"):
    return {"model": model, "palette": {"skin": "#AABBCC", "red": "#FF000080"},
            "base": dict.fromkeys(PARTS, "skin"), "paint": []}


class CoreTests(unittest.TestCase):
    def test_known_classic_uv(self):
        uv = uv_faces("classic")
        expected = {
            ("head", "base", "front"): (8, 8, 8, 8),
            ("head", "overlay", "back"): (56, 8, 8, 8),
            ("body", "base", "right"): (16, 20, 4, 12),
            ("body", "overlay", "left"): (28, 36, 4, 12),
            ("right_arm", "base", "back"): (52, 20, 4, 12),
            ("left_arm", "base", "front"): (36, 52, 4, 12),
            ("left_arm", "overlay", "bottom"): (56, 48, 4, 4),
            ("right_leg", "overlay", "top"): (4, 32, 4, 4),
            ("left_leg", "base", "front"): (20, 52, 4, 12),
            ("left_leg", "overlay", "front"): (4, 52, 4, 12),
        }
        for key, value in expected.items():
            self.assertEqual(uv[key], value)
        self.assertEqual(len(uv), 72)

    def test_slim_uv(self):
        uv = uv_faces("slim")
        self.assertEqual(uv["right_arm", "base", "front"], (44, 20, 3, 12))
        self.assertEqual(uv["right_arm", "base", "left"], (47, 20, 4, 12))
        self.assertEqual(uv["right_arm", "base", "back"], (51, 20, 3, 12))
        self.assertEqual(uv["left_arm", "overlay", "bottom"], (55, 48, 3, 4))
        self.assertEqual(uv["left_arm", "base", "back"], (43, 52, 3, 12))

    def test_atlas_faces_do_not_overlap(self):
        for model, area in (("classic", 3264), ("slim", 3136)):
            occupied = set()
            for x, y, w, h in uv_faces(model).values():
                pixels = {(u, v) for u in range(x, x+w) for v in range(y, y+h)}
                self.assertFalse(pixels & occupied)
                self.assertTrue(all(0 <= u < 64 and 0 <= v < 64 for u, v in pixels))
                occupied |= pixels
            self.assertEqual(len(occupied), area)

    def test_png_round_trip_and_overlay_alpha(self):
        d = design("slim")
        d["paint"] = [{"part": "head", "layer": "overlay", "face": "front", "rect": [0, 1, 2, 3], "color": "red"}]
        image = build_skin(d)
        self.assertEqual(image.getpixel((40, 9)), (255, 0, 0, 128))
        self.assertEqual(image.getpixel((42, 9)), (0, 0, 0, 0))
        self.assertEqual(image.getpixel((8, 9)), (170, 187, 204, 255))
        data = io.BytesIO()
        image.save(data, format="PNG")
        data.seek(0)
        decoded = Image.open(data)
        self.assertEqual(decoded.format, "PNG")
        self.assertEqual(decoded.tobytes(), image.tobytes())
        report = validate_skin(decoded, "slim")
        self.assertTrue(report["valid"])
        self.assertEqual(report["coverage"]["head/overlay"]["visible_pixels"], 6)

    def test_face_local_corners_preserve_cube_net_orientation(self):
        d = design()
        d["palette"]["mark"] = "#112233"
        # Independent atlas sentinels for top-left corners on every head face.
        for face, point in (("front", (8, 8)), ("back", (24, 8)),
                            ("right", (0, 8)), ("left", (16, 8)),
                            ("top", (8, 0)), ("bottom", (16, 0))):
            d["paint"] = [{"part": "head", "layer": "base", "face": face,
                           "rect": [0, 0, 1, 1], "color": "mark"}]
            self.assertEqual(build_skin(d).getpixel(point), (17, 34, 51, 255))

    def test_palette_transparency_is_validated(self):
        image = build_skin(design()).convert("P")
        # Marking the base fill's palette index transparent must not bypass alpha checks.
        image.info["transparency"] = image.getpixel((8, 8))
        self.assertFalse(validate_skin(image, "classic")["valid"])

    def test_rejected_designs(self):
        cases = []
        d = design(); del d["base"]["left_leg"]; cases.append(d)
        d = design(); d["base"]["head"] = "red"; cases.append(d)
        d = design(); d["unexpected"] = 1; cases.append(d)
        d = design(); d["palette"]["skin"] = "red"; cases.append(d)
        d = design(); d["model"] = "auto"; cases.append(d)
        d = design(); d["paint"] = [{}] * (MAX_PAINT + 1); cases.append(d)
        for rect in ([True, 0, 1, 1], [0, 0, 9, 1], [-1, 0, 1, 1], [0, 0, 0, 1], [0, 0, 1.0, 1]):
            d = design()
            d["paint"] = [{"part": "head", "layer": "overlay", "face": "front", "rect": rect, "color": "red"}]
            cases.append(d)
        d = copy.deepcopy(cases[-1]); d["paint"][0].update(rect=[0, 0, 1, 1], layer="base"); cases.append(d)
        for d in cases:
            with self.subTest(d=d), self.assertRaises(ValueError):
                build_skin(d)

    def test_validation_rejects_transparent_base_and_wrong_size(self):
        image = build_skin(design())
        image.putpixel((8, 8), (1, 2, 3, 254))
        report = validate_skin(image, "classic")
        self.assertFalse(report["valid"])
        self.assertIn("head/base/front contains non-opaque pixels", report["errors"])
        self.assertFalse(validate_skin(Image.new("RGBA", (64, 32)), "classic")["valid"])
        self.assertFalse(validate_skin(None, "classic")["valid"])
        with self.assertRaises(ValueError):
            validate_skin(image, "auto")


if __name__ == "__main__":
    unittest.main()
