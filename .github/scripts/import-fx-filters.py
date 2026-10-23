#!/usr/bin/env python3
"""Generate bundled Alight Motion effects from the pinned FX shader sources.

Run without arguments to regenerate patch/effects/fx-*.xml, or pass --check
to reject missing, stale, or unexpected generated effects without editing files.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parents[2]
UNIFORM = re.compile(r"^uniform\s+(\w+)\s+(\w+)\s*;\s*$", re.M)
VARYING = "varying vec2 vTexSamplingCoord;"
HOST_INPUTS = {
    "uTexSampler": "inputImg.texture",
    "vTexSamplingCoord": "acScreenNorm",
    "uWidth": "acScreenSize.x",
    "uHeight": "acScreenSize.y",
    "uTime": "(acTime - acStartTime)",
}

# Alight Motion textures and outputs are premultiplied. The source FX math
# operates on straight RGBA, including effects that change the alpha channel.
SAMPLE = """vec4 fxPortOutput;

vec4 fxPortSample(sampler2D image, vec2 uv) {
    vec4 color = texture2D(image, uv);
    if (color.a > 0.0) color.rgb /= color.a;
    else color.rgb = vec3(0.0);
    return color;
}

"""
MAIN = """
void main() {
    if (uControl1 <= 0.0) {
        gl_FragColor = texture2D(inputImg.texture, clamp(acScreenNorm, 0.0, 1.0));
        return;
    }
    fxPortMain();
    gl_FragColor = vec4(fxPortOutput.rgb * fxPortOutput.a, fxPortOutput.a);
}
"""


def convert(source: str, labels: list[str]) -> tuple[str, list[str]]:
    declarations = UNIFORM.findall(source)
    uniforms = dict((name, kind) for kind, name in declarations)
    allowed = set(HOST_INPUTS) - {"vTexSamplingCoord"}
    allowed.update(f"uControl{i}" for i in range(1, 9))
    if len(uniforms) != len(declarations) or set(uniforms) - allowed:
        raise ValueError("duplicate or unsupported source uniforms")
    if uniforms.get("uTexSampler") != "sampler2D" or any(
        kind != "float" for name, kind in uniforms.items() if name != "uTexSampler"
    ):
        raise ValueError("unexpected source uniform types")
    controls = [f"uControl{i}" for i in range(1, 9) if f"uControl{i}" in uniforms]
    if not controls or controls[0] != "uControl1" or len(labels) != len(controls):
        raise ValueError("control labels do not match the shader uniforms")
    if source.count(VARYING) != 1 or source.count("void main()") != 1:
        raise ValueError("unexpected shader entry point or texture coordinates")
    if "#version" in source or "#extension" in source or "fxPort" in source:
        raise ValueError("unsupported shader directives or reserved identifiers")

    body = UNIFORM.sub("", source).replace(VARYING, "")
    body = re.sub(r"^precision highp float;\s*", "", body)
    body = body.replace("void main()", "void fxPortMain()")
    replacements = dict(HOST_INPUTS, texture2D="fxPortSample", gl_FragColor="fxPortOutput")
    body = re.sub(r"\b(" + "|".join(replacements) + r")\b",
                  lambda match: replacements[match.group()], body)
    return SAMPLE + body.strip() + "\n" + MAIN, controls


def replace_once(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError("optimized shader source anchor changed: " + before[:70])
    return source.replace(before, after)


def render(source: str, entry: dict, provenance: dict) -> str:
    shader, controls = convert(source, entry["controls"])
    name = entry["source"]
    vertex_xml = ""
    if name == "vegas_light_rays.glsl":
        # A sample outside the light's radius is multiplied by exactly zero.
        # Determine its coverage before fetching/unpremultiplying the texture.
        shader = replace_once(shader,
            "    vec4 rays = vec4(0.0);",
            "    if (blend <= 0.0 || power <= 0.0) { fxPortOutput = original; return; }\n"
            "    vec4 rays = vec4(0.0);")
        shader = replace_once(shader,
            "        vec4 sampleColor = fxPortSample(inputImg.texture, clamp(p, 0.0, 1.0));",
            "        float bound = clamp(1.0 - length((p - light) / radius), 0.0, 1.0);\n"
            "        if (bound > 0.0) {\n"
            "        vec4 sampleColor = i == 0 ? original : fxPortSample(inputImg.texture, clamp(p, 0.0, 1.0));")
        shader = replace_once(shader,
            "        float bound = clamp(1.0 - length((p - light) / radius), 0.0, 1.0);\n"
            "        rays += sampleColor * bright * bound * (1.0 - 0.5 * t);",
            "        rays += sampleColor * bright * bound * (1.0 - 0.5 * t);\n        }")
    if name == "vegas_glow.glsl":
        shader = replace_once(shader,
            "    float suppression = clamp(0.5 * uControl4, 0.0, 1.0);",
            "    if (intensity <= 0.0) { fxPortOutput = original; return; }\n"
            "    float suppression = clamp(0.5 * uControl4, 0.0, 1.0);")
    if name == "vegas_radial_blur.glsl":
        shader = replace_once(shader,
            "    vec4 sum = vec4(0.0);\n    for (int i = 0; i < 13; ++i)",
            "    vec4 sum = original;\n    for (int i = 1; i < 13; ++i)")
    if name == "vegas_unsharp_mask.glsl":
        shader = replace_once(shader,
            "            blur += wx * wy * fxPortSample(inputImg.texture, tapUv);",
            "            vec4 sampleColor = (x == 0 && y == 0) ? original : fxPortSample(inputImg.texture, tapUv);\n"
            "            blur += wx * wy * sampleColor;")
    if name == "vegas_2d_shadow.glsl":
        # The same 65 weights were evaluated for each of the 65 rows.
        # Keep the sampling and accumulation order, but reuse those weights.
        anchor = "        for (int row = 0; row < 65; ++row) {"
        if shader.count(anchor) != 1:
            raise ValueError("Shadow sampling loop changed")
        shader = shader.replace(anchor,
            "        float weights[65];\n"
            "        for (int tap = 0; tap < 65; ++tap) {\n"
            "            weights[tap] = impulse((float(tap) - 32.0) * spacing, sigma) * spacing;\n"
            "        }\n" + anchor)
        shader = shader.replace("float wy = impulse(y, sigma) * spacing;", "float wy = weights[row];")
        shader = shader.replace("float wx = impulse(x, sigma) * spacing;", "float wx = weights[column];")
    if name == "newblue_earthquake.glsl":
        # Motion depends only on time and controls. Replaying up to 4096
        # historical steps for every pixel made real editor playback costly.
        # Evaluate it at the vertices and interpolate the identical result.
        start, end = shader.index("vec4 frameBytes("), shader.index("vec4 pixelColor(")
        helpers = shader[start:end]
        calculation = re.search(r"    float bound = .*?    nativeMotion\(frame, bound, velocity, motion, previous, blur\);", shader, re.S)
        if calculation is None:
            raise ValueError("Earthquake motion calculation changed")
        varyings = ("varying highp vec3 fxMotion;\n"
                    "varying highp vec2 fxPrevious;\n"
                    "varying highp float fxBlur;\n")
        vertex = ("precision highp float;\nuniform float acTime;\nuniform float acStartTime;\n" +
                  varyings + helpers + "void main() {\n    vertShaderInit();\n" +
                  "    fxMotion = vec3(0.0);\n    fxPrevious = vec2(0.0);\n    fxBlur = 0.0;\n"
                  "    if (uControl1 <= 0.0) return;\n" + calculation.group() +
                  "\n    fxMotion = motion;\n    fxPrevious = previous;\n    fxBlur = blur;\n}\n")
        shader = shader.replace(calculation.group(),
                                "    vec3 motion = fxMotion;\n    vec2 previous = fxPrevious;\n    float blur = fxBlur;")
        shader = varyings + shader.replace(helpers, "")
        vertex_xml = f'    <shader type="vertex"><![CDATA[\n{vertex}    ]]></shader>\n'
    description = entry["description"]
    strings = [("name", entry["name"]), ("desc", description)]
    strings += list(zip(controls, entry["controls"]))
    string_xml = "\n".join(
        f"        <string name={quoteattr(key)}>{escape(value)}</string>"
        for key, value in strings
    )
    params = ['        <texture id="inputImg" srcType="content" />']
    for control in controls:
        default = "1.0" if control == "uControl1" else "0.0"
        params.append(
            f'        <spinner id="{control}" default="{default}" min="-2.0" '
            f'max="2.0" step="0.01" label="@string/{control}" />'
        )
    param_xml = "\n".join(params)
    stem = Path(name).stem
    thumb = re.sub(r"[^A-Za-z0-9]+", "_", entry["name"].strip()).strip("_").lower()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated by .github/scripts/import-fx-filters.py; edit patch/fx sources.
     Source: {provenance["repository"]} @ {provenance["commit"]}, shaders/{name} -->
<effect id="com.wowmancode.fx.{stem}" name="@string/name" desc="@string/desc" category={quoteattr(entry["category"])} tags="custom,fx,vegas,newblue,raster" thumb="thumb/{thumb}.webp">
    <strings><locale lang="en">
{string_xml}
    </locale></strings>
    <params>
{param_xml}
    </params>
{vertex_xml}    <shader type="fragment" precision="high"><![CDATA[
{shader}    ]]></shader>
</effect>
'''


def generate(root: Path, check: bool) -> int:
    library = root / "patch" / "fx"
    manifest = json.loads((library / "manifest.json").read_text(encoding="utf-8"))
    sources = library / "shaders"
    output = root / "patch" / "effects"
    entries = manifest["filters"]
    names = [entry["source"] for entry in entries]
    if (len(names) != len(set(names)) or
            any(Path(name).name != name or not name.endswith(".glsl") for name in names)):
        raise ValueError("duplicate or invalid shader filenames")
    if set(names) != {path.name for path in sources.glob("*.glsl")}:
        raise ValueError("manifest must cover every bundled source shader exactly once")
    expected = {}
    for entry in entries:
        path = sources / entry["source"]
        target = output / ("fx-" + path.stem.replace("_", "-") + ".xml")
        if target in expected:
            raise ValueError("generated effect filename collision")
        expected[target] = render(path.read_text(encoding="utf-8"), entry, manifest)
    extra = set(output.glob("fx-*.xml")) - set(expected)
    if extra:
        raise ValueError(f"unexpected generated effects: {sorted(p.name for p in extra)}")
    stale = [path for path, text in expected.items()
             if not path.is_file() or path.read_text(encoding="utf-8") != text]
    if check and stale:
        for path in stale:
            print(f"::error file={path.relative_to(root)}::FX filter needs regeneration")
        return 1
    if not check:
        output.mkdir(parents=True, exist_ok=True)
        for path, text in expected.items():
            path.write_text(text, encoding="utf-8")
    print(f"{'Checked' if check else 'Generated'} {len(expected)} FX filters")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        return generate(ROOT, args.check)
    except (ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
