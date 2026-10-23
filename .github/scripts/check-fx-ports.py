#!/usr/bin/env python3
"""GPU smoke checks against the pinned FX shaders, using desktop EGL/Mesa.

Requires moderngl and numpy. This checks the host adaptation, including alpha,
dimensions, local time, defaults, changed controls, and bypass. It does not
compare against Vegas or establish performance on an Android device.
"""

import importlib.util
import json
import re
from pathlib import Path

import moderngl
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("shader_check", Path(__file__).with_name("check-shaders.py"))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)
PORT_SPEC = importlib.util.spec_from_file_location("fx_import", Path(__file__).with_name("import-fx-filters.py"))
PORT = importlib.util.module_from_spec(PORT_SPEC)
PORT_SPEC.loader.exec_module(PORT)
VERTEX = """#version 330
out vec2 vTexSamplingCoord;
out vec2 acScreenNorm;
void main() {
    vec2 p = vec2(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0);
    gl_Position = vec4(p, 0.0, 1.0);
    vTexSamplingCoord = acScreenNorm = 0.5 * p + vec2(0.5);
}
"""

SAMPLING_CASES = {
    "vegas_glow": [[1, 0, 0, 0, 0, 0, 0], [1, 1, 1, 0, 0, 0, 0],
                   [1, 2, 2, 2, -2, 1, 2], [0.35, 0.5, 0.25, 1, 0, 0, 0],
                   [1, 2, -2, 0, 0, 0, 0]],
    "vegas_light_rays": [[1, 0, 0, 0, 0, 0, 0, 0], [1, 2, 2, 2, -2, -2, -2, 2],
                         [1, 2, -2, 0, 0, 2, 2, 2], [1, 0, 0, 0, 0, 0, 0, -2],
                         [0.35, 1, 1, -2, 2, 0.5, -0.5, 1]],
    "vegas_radial_blur": [[1, -2, 0, 0, 0], [1, 2, 2, -2, 0],
                          [1, 2, -2, 2, 1], [0.35, 0.5, 0, 0, 1], [1, 0, 0, 0, 0]],
    "vegas_unsharp_mask": [[1, 2, 2, 0], [1, -2, 1, 0.5], [1, 1, 1, 2],
                           [0.35, 0.75, 0.5, 0.1], [1, 0, 0, 0]],
}


def desktop(source):
    source = re.sub(r"^#version[^\n]*\n", "", source)
    source = re.sub(r"precision\s+\w+\s+\w+\s*;", "", source)
    source = re.sub(r"\bvarying\b", "in", source)
    source = re.sub(r"\btexture2D\b", "texture", source)
    source = re.sub(r"\bgl_FragColor\b", "fragment", source)
    return "#version 330\nout vec4 fragment;\n" + source


def vertex_for(path):
    source = CHECK.assemble(path, "vertex")
    source = re.sub(r"^#version[^\n]*\n", "", source)
    source = re.sub(r"precision\s+\w+\s+\w+\s*;", "", source)
    source = re.sub(r"\b(highp|mediump|lowp)\b", "", source)
    source = re.sub(r"attribute vec4 ac_internal_position;", "", source)
    source = re.sub(r"attribute vec2 ac_internal_texcoord;", "", source)
    source = source.replace("varying", "out")
    source = source.replace("gl_Position = ac_internal_position;",
        "vec2 p = vec2(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0);\n"
        "    vec2 ac_internal_texcoord = 0.5 * p + vec2(0.5);\n"
        "    gl_Position = vec4(p, 0.0, 1.0);")
    return "#version 330\n" + source


def main():
    ctx = moderngl.create_standalone_context(backend="egl")
    width, height = 24, 16  # Nonsquare to catch swapped/constant dimensions.
    y, x = np.mgrid[:height, :width]
    gradient = np.stack((x / (width - 1), y / (height - 1),
                         ((x + y) % 5) / 4, np.ones_like(x)), axis=-1).astype("f4")
    checker = np.ones_like(gradient)
    checker[..., :3] = (((x // 3 + y // 2) % 2) * 0.8 + 0.1)[..., None]
    cutout = gradient.copy()
    cutout[..., 3] = np.where((x - 12)**2 + (y - 8)**2 < 40, 0.5, 0.0)
    cutout[cutout[..., 3] == 0, :3] = 0
    cases = {"defaults": [1, 0, 0, 0, 0, 0, 0, 0],
             "adjusted": [1, -0.75, 0.5, 0.75, -0.25, 1, -0.5, 0.5],
             "bypass": [0, -0.75, 0.5, 0.75, -0.25, 1, -0.5, 0.5]}
    texture = ctx.texture((width, height), 4, dtype="f4")
    # Nearest gives the two hosts identical samples at cutout boundaries.
    # Linear filtering in the app operates on premultiplied samples.
    texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
    texture.repeat_x = texture.repeat_y = False
    target = ctx.texture((width, height), 4, dtype="f4")
    fbo = ctx.framebuffer(color_attachments=[target])
    fbo.use()
    ctx.viewport = (0, 0, width, height)

    def render(program, image, controls, time=1.5):
        texture.write(np.ascontiguousarray(image).tobytes())
        texture.use(0)
        values = {"uTexSampler": 0, "inputImg.texture": 0,
                  # Match the host's float32 layer-local time, particularly
                  # at exact frame boundaries late in a project.
                  "uWidth": width, "uHeight": height,
                  "uTime": float(np.float32(np.float32(time + 5.0) - np.float32(5.0))),
                  "acScreenSize": (width, height), "acTime": time + 5.0, "acStartTime": 5.0}
        values.update({f"uControl{i}": value for i, value in enumerate(controls, 1)})
        for name, value in values.items():
            if name in program:
                program[name].value = value
        vao = ctx.vertex_array(program, [])
        vao.render(vertices=3)
        vao.release()
        return np.frombuffer(fbo.read(components=4, dtype="f4"), dtype="f4").reshape(height, width, 4)

    manifest = json.loads((ROOT / "patch/fx/manifest.json").read_text())
    total = 0
    worst = 0.0

    def fragment_reference(raw, entry):
        source, names = PORT.convert(raw, entry["controls"])
        return ctx.program(vertex_shader=VERTEX, fragment_shader=desktop(
            CHECK.PREAMBLE.replace("{precision}", "highp") +
            "\nuniform AC_ImageInfo inputImg;\n" +
            "\n".join(f"uniform float {name};" for name in names) + "\n" + source))

    for entry in manifest["filters"]:
        stem = Path(entry["source"]).stem
        raw = (ROOT / "patch/fx/shaders" / entry["source"]).read_text()
        xml = ROOT / "patch/effects" / ("fx-" + stem.replace("_", "-") + ".xml")
        reference = ctx.program(vertex_shader=VERTEX, fragment_shader=desktop(raw))
        port = ctx.program(vertex_shader=vertex_for(xml), fragment_shader=desktop(CHECK.assemble(xml)))
        error = 0.0
        for image in (gradient, checker, cutout):
            premultiplied = image.copy()
            premultiplied[..., :3] *= premultiplied[..., 3:4]
            for label, controls in cases.items():
                expected = render(reference, image, controls).copy()
                expected[..., :3] *= expected[..., 3:4]
                actual = render(port, premultiplied, controls)
                assert np.all(np.isfinite(actual)), (stem, label, "nonfinite output")
                assert actual.min() >= -1e-6 and actual.max() <= 1.000001, stem
                assert np.all(actual[..., :3] <= actual[..., 3:4] + 1e-6), (stem, "alpha")
                delta = float(np.max(np.abs(actual - expected)))
                assert delta <= 1 / 255, (stem, label, delta)
                if label == "bypass":
                    assert np.max(np.abs(actual - premultiplied)) < 1e-5, stem
                error = max(error, delta)
                total += 1
        if stem == "newblue_earthquake":
            # Includes the 4096-step history boundary, fractional time, zero
            # velocity, control extremes, and a nonzero layer start time.
            # Compare against the original fragment-only host adaptation:
            # host-local time arithmetic at exact frame boundaries must be
            # preserved, including float32 rounding of (time - startTime).
            baseline = fragment_reference(raw, entry)
            for time in (0.0, 1 / 30, 10.125, 4096 / 30, 140.0):
                for controls in (cases["defaults"], cases["adjusted"],
                                 [1, 2, -2], [1, -2, 2]):
                    expected = render(baseline, gradient, controls, time)
                    actual = render(port, gradient, controls, time)
                    delta = float(np.max(np.abs(actual - expected)))
                    assert np.all(np.isfinite(actual)) and delta <= 1 / 255, (stem, time, controls, delta)
                    error = max(error, delta)
                    total += 1
            baseline.release()
        if stem in SAMPLING_CASES:
            baseline = fragment_reference(raw, entry)
            for filtering in (moderngl.NEAREST, moderngl.LINEAR):
                texture.filter = (filtering, filtering)
                for image in (gradient, checker, cutout):
                    premultiplied = image.copy()
                    premultiplied[..., :3] *= premultiplied[..., 3:4]
                    for controls in SAMPLING_CASES[stem]:
                        expected = render(baseline, premultiplied, controls)
                        actual = render(port, premultiplied, controls)
                        delta = float(np.max(np.abs(actual - expected)))
                        assert np.all(np.isfinite(actual)) and delta <= 1 / 255, (stem, filtering, controls, delta)
                        error = max(error, delta)
                        total += 1
            texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            baseline.release()
        reference.release()
        port.release()
        worst = max(worst, error)
        print(f"PASS {stem}: max premultiplied RGBA difference {error:.8f}", flush=True)
    print(f"Passed {total} GPU comparisons; maximum difference {worst:.8f}")


if __name__ == "__main__":
    main()
