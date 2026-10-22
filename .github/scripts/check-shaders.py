#!/usr/bin/env python3
"""Compile and link effect shaders the way Alight Motion 3.10.0 does.

The app prepends a fixed preamble (from l2.j1.d) plus one uniform per
parameter, then the effect's shader source. Custom vertex shaders receive
the native vertex preamble and nontexture parameters. A shader that doesn't compile
fails at runtime, so this runs the same assembly through glslangValidator.

Usage: check-shaders.py patch/effects/*.xml
"""

import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PREAMBLE = """#version 100
precision {precision} float;
uniform vec2 acScreenSize;
uniform vec2 acPreviewSize;
uniform vec2 acLayerScale;
uniform vec2 acLayerCenter;
uniform vec2 acLayerCenterNorm;
uniform vec2 acLayerPivot;
uniform vec2 acLayerSize;
uniform vec2 acLayerSizeNorm;
uniform vec2 acVelocity;
uniform float acAngularVelocity;
uniform float acScaleVelocity;
uniform float acTime;
uniform float acStartTime;
uniform float acEndTime;
uniform int acPass;
uniform int acIter;
uniform mat3 acLayerTransform;
uniform mat4 acScreenToLayer;
uniform mat4 acLayerToScreen;
uniform bool acShowGuides;

varying vec2 acScreenNorm;
varying vec2 acLayerNorm;

struct AC_ImageInfo {
    sampler2D texture;
    vec2 size;
};"""

# Parameter element -> GLSL uniform type (DataType.getGlslType).
GLSL_TYPES = {
    "texture": "AC_ImageInfo",
    "color": "vec4",
    "switch": "bool",
    "spinner": "float",
    "slider": "float",
    "selector": "int",
    "point": "vec2",
}
# Parameters that produce no uniform.
NO_UNIFORM = {"tip", "section"}

PRECISION = {"high": "highp", "low": "lowp"}

VERTEX_PREAMBLE = """#version 100
attribute vec4 ac_internal_position;
attribute vec2 ac_internal_texcoord;
varying vec2 acScreenNorm;
varying vec2 acLayerNorm;
uniform mat4 acScreenToLayer;
void vertShaderInit() {
    gl_Position = ac_internal_position;
    acScreenNorm = ac_internal_texcoord;
    acLayerNorm = (vec4(ac_internal_texcoord, 0.0, 1.0) * acScreenToLayer).xy;
}
"""


def assemble(path: Path, stage: str = "fragment") -> str:
    root = ET.parse(path).getroot()
    shaders = [s for s in root.findall("shader") if s.get("type") == stage]
    if stage == "vertex" and not shaders:
        return VERTEX_PREAMBLE + "void main() { vertShaderInit(); }\n"
    if len(shaders) != 1:
        raise ValueError(f"expected one {stage} shader, found {len(shaders)}")
    shader = shaders[0]

    uniforms = []
    params = root.find("params")
    for param in params if params is not None else []:
        if param.tag in NO_UNIFORM:
            continue
        if param.tag not in GLSL_TYPES:
            raise ValueError(f"unknown parameter type <{param.tag}>")
        # AM excludes texture parameters from the vertex stage.
        if stage != "vertex" or param.tag != "texture":
            uniforms.append(f"uniform {GLSL_TYPES[param.tag]} {param.get('id')};")

    precision = PRECISION.get(shader.get("precision"), "mediump")
    preamble = VERTEX_PREAMBLE if stage == "vertex" else PREAMBLE.replace("{precision}", precision)
    return (preamble + "\n" + "\n".join(uniforms)
            + "\n\n" + (shader.text or ""))


def main() -> None:
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        for arg in sys.argv[1:]:
            path = Path(arg)
            try:
                fragment, vertex = assemble(path), assemble(path, "vertex")
            except (ValueError, ET.ParseError) as error:
                print(f"::error file={path}::{error}")
                failed = True
                continue

            out = Path(tmp) / (path.stem + ".frag")
            out.write_text(fragment)
            vert = Path(tmp) / (path.stem + ".vert")
            vert.write_text(vertex)
            result = subprocess.run(["glslangValidator", "-l", str(vert), str(out)],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print(f"OK    {path.name}")
            else:
                print(f"FAIL  {path.name}\n{result.stdout.strip()}")
                print(f"::error file={path}::shader does not compile")
                failed = True

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
