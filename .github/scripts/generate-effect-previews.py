#!/usr/bin/env python3
"""Render native animated filter thumbnails; --check needs only the stdlib.

Generation requires moderngl, numpy, Pillow, and EGL/Mesa. Preview presets
demonstrate each effect; they do not change the filter's default controls.
"""

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "patch/previews"
IMAGES = LIBRARY / "thumb"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inputs():
    presets = json.loads((LIBRARY / "settings.json").read_text())
    effects = [path for path in sorted((ROOT / "patch/effects").glob("*.xml"))
               if ET.parse(path).getroot().get("internal") != "true"]
    if set(presets) != {path.name for path in effects}:
        raise ValueError("preview settings must cover every bundled filter exactly once")
    if any(path.name.startswith("amv-") for path in effects):
        raise ValueError("AMV transitions must not be bundled")
    script = Path(__file__).read_bytes()
    records = []
    for path in effects:
        root = ET.parse(path).getroot()
        name = root.find('./strings/locale[@lang="en"]/string[@name="name"]').text
        slug = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_").lower()
        thumb = slug + ".webp"
        if root.get("thumb") != "thumb/" + thumb:
            raise ValueError(f"{path.name}: thumbnail must match the native English-name slug")
        parameters = {p.get("id") for p in root.findall("./params/*")}
        if set(presets[path.name]) - parameters:
            raise ValueError(f"{path.name}: unknown preview parameter")
        fingerprint = digest(path.read_bytes() + json.dumps(presets[path.name], sort_keys=True).encode() + script)
        records.append(dict(effect=path.name, id=root.get("id"), name=name,
                            thumb=thumb, background=slug + "_bg.webp",
                            source_sha256=fingerprint, controls=presets[path.name]))
    return records


def check(records):
    index = json.loads((LIBRARY / "index.json").read_text())
    actual = {record["effect"]: record for record in index}
    if len(actual) != len(index) or set(actual) != {r["effect"] for r in records}:
        raise ValueError("preview index does not match the bundled filters")
    expected = set()
    for record in records:
        saved = actual[record["effect"]]
        if any(saved.get(key) != value for key, value in record.items()):
            raise ValueError(f"{record['effect']}: stale preview; regenerate")
        for field in ("thumb", "background"):
            path = IMAGES / record[field]
            data = path.read_bytes()
            if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
                raise ValueError(f"{path.name}: invalid WebP")
            if digest(data) != saved[field + "_sha256"]:
                raise ValueError(f"{path.name}: preview checksum changed")
            if field == "thumb" and (b"ANIM" not in data or b"ANMF" not in data):
                raise ValueError(f"{path.name}: thumbnail must be animated")
            expected.add(path.name)
    if {p.name for p in IMAGES.glob("*.webp")} != expected:
        raise ValueError("unexpected or missing preview images")
    print(f"Checked animated thumbnails and detail previews for all {len(records)} filters")


def generate(records):
    import moderngl
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    spec = importlib.util.spec_from_file_location("fx_gpu", Path(__file__).with_name("check-fx-ports.py"))
    gpu = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gpu)
    ctx = moderngl.create_standalone_context(backend="egl")
    IMAGES.mkdir(parents=True, exist_ok=True)

    # A shared, original test scene makes geometry, color, detail, and alpha
    # changes comparable across filters. The border is transparent for shadows.
    n = 720
    y, x = np.mgrid[:n, :n]
    pixels = np.zeros((n, n, 4), dtype=np.uint8)
    pixels[..., 0] = np.clip(25 + x * 0.10 + y * 0.045, 0, 255)
    pixels[..., 1] = np.clip(35 + y * 0.08, 0, 255)
    pixels[..., 2] = np.clip(125 + x * 0.07 - y * 0.07, 0, 255)
    pixels[..., 3] = 255
    scene = Image.fromarray(pixels, "RGBA")
    draw = ImageDraw.Draw(scene)
    for row in range(50, 680, 36):
        draw.line((40, row, 680, row), fill=(110, 170, 240, 255), width=1)
    for column in range(50, 680, 36):
        draw.line((column, 40, column, 680), fill=(110, 170, 240, 255), width=1)
    draw.ellipse((400, 100, 620, 320), fill=(255, 185, 55, 255))
    draw.polygon(((20, 580), (220, 210), (405, 580)), fill=(246, 60, 125, 255))
    draw.polygon(((130, 690), (415, 355), (710, 690)), fill=(35, 210, 200, 255))
    draw.ellipse((83, 375, 280, 572), fill=(90, 60, 220, 255), outline=(255, 255, 255, 255), width=8)
    for sx, sy in ((335, 130), (615, 395), (145, 145)):
        draw.line((sx - 16, sy, sx + 16, sy), fill="white", width=5)
        draw.line((sx, sy - 16, sx, sy + 16), fill="white", width=5)
    draw.text((320, 480), "FX", font=ImageFont.load_default(size=140), fill="white", stroke_width=2)
    for i, color in enumerate(("#ff4d64", "#ffbd39", "#e4ed63", "#41d8b8", "#4b98fa", "#a478f0")):
        draw.rectangle((92 + i * 90, 605, 167 + i * 90, 637), fill=color)
    mask = Image.new("L", (n, n))
    ImageDraw.Draw(mask).rounded_rectangle((42, 42, 678, 678), radius=42, fill=255)
    scene.putalpha(mask)
    scene.save(LIBRARY / "source.png")

    def uniforms(root):
        result = {}
        for param in root.findall("./params/*"):
            kind, name, value = param.tag, param.get("id"), param.get("default")
            if kind in ("texture", "section", "tip"):
                continue
            if kind == "color":
                argb = int(value.lstrip("#"), 16)
                result[name] = tuple(((argb >> bit) & 255) / 255 for bit in (16, 8, 0, 24))
            elif kind == "switch":
                result[name] = value == "true"
            elif kind == "selector":
                result[name] = int(value)
            else:
                result[name] = float(value)
        return result

    def renderer(path, size, recipe):
        root = ET.parse(path).getroot()
        program = ctx.program(vertex_shader=gpu.vertex_for(path),
                              fragment_shader=gpu.desktop(gpu.CHECK.assemble(path)))
        image = scene.resize((size, size), Image.Resampling.LANCZOS)
        src = np.asarray(image.transpose(Image.Transpose.FLIP_TOP_BOTTOM), dtype="f4") / 255
        src[..., :3] *= src[..., 3:4]
        texture = ctx.texture((size, size), 4, src.tobytes(), dtype="f4")
        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        texture.repeat_x = texture.repeat_y = False
        target = ctx.texture((size, size), 4, dtype="f4")
        fbo = ctx.framebuffer(color_attachments=[target])
        vao = ctx.vertex_array(program, [])
        yy, xx = np.mgrid[:size, :size]
        checker = np.where(((xx // max(size // 15, 1) + yy // max(size // 15, 1)) % 2)[..., None], 0.84, 0.94)
        values = {**uniforms(root), **recipe, "inputImg.texture": 0,
                  "inputImg.size": (size, size), "acScreenSize": (size, size),
                  "acPreviewSize": (size, size), "acLayerSize": (size, size),
                  "acStartTime": 0.0, "acEndTime": 2.0}
        for name, value in values.items():
            if name in program:
                program[name].value = value

        def render(time, mix=1.0):
            fbo.use()
            ctx.viewport = (0, 0, size, size)
            texture.use(0)
            if "acTime" in program:
                program["acTime"].value = time
            vao.render(vertices=3)
            result = np.frombuffer(fbo.read(components=4, dtype="f4"), dtype="f4").reshape(size, size, 4)
            if not np.all(np.isfinite(result)):
                raise ValueError(f"{path.name}: nonfinite preview pixels")
            result = np.clip(result, 0, 1) * mix + src * (1 - mix)
            rgb = result[..., :3] + checker * (1 - result[..., 3:4])
            return Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255 + 0.5), "RGB").transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        def release():
            for resource in (vao, fbo, target, texture, program):
                resource.release()
        return render, release

    for record in records:
        path = ROOT / "patch/effects" / record["effect"]
        render, release = renderer(path, 180, record["controls"])
        blend = (0, 0, 0.25, 0.5, 0.75, 1, 1, 1, 1, 0.75, 0.5, 0.25)
        frames = [render(i * 0.1, amount) for i, amount in enumerate(blend)]
        frames[0].save(IMAGES / record["thumb"], save_all=True, append_images=frames[1:],
                       duration=100, loop=0, quality=75, method=4)
        release()
        render, release = renderer(path, 720, record["controls"])
        render(0.7).save(IMAGES / record["background"], quality=84, method=4)
        release()
        for field in ("thumb", "background"):
            record[field + "_sha256"] = digest((IMAGES / record[field]).read_bytes())
        print(f"Rendered {record['name']}", flush=True)
    (LIBRARY / "index.json").write_text(json.dumps(records, indent=2) + "\n")
    ctx.release()
    check(inputs())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    records = inputs()
    if args.check:
        check(records)
    else:
        generate(records)


if __name__ == "__main__":
    main()
