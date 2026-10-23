#!/usr/bin/env python3
"""Compare old fragment-only and optimized FX costs on the current EGL GPU.

Requires the dependencies of check-fx-ports.py. This is an offline benchmark,
not an Android FPS estimate. GPU synchronization is used only in this tool.
"""

import importlib.util
import json
import statistics
import time
from pathlib import Path

import moderngl
import numpy as np

SPEC = importlib.util.spec_from_file_location("gpu", Path(__file__).with_name("check-fx-ports.py"))
GPU = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GPU)


def main():
    ctx = moderngl.create_standalone_context(backend="egl")
    width, height = 192, 108
    y, x = np.mgrid[:height, :width]
    image = np.stack((x / (width - 1), y / (height - 1), ((x + y) % 5) / 4,
                      np.full_like(x, 0.5, dtype="f4")), axis=-1).astype("f4")
    image[..., :3] *= image[..., 3:4]
    texture = ctx.texture((width, height), 4, image.tobytes(), dtype="f4")
    texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
    texture.repeat_x = texture.repeat_y = False
    texture.use(0)
    target = ctx.simple_framebuffer((width, height), components=4, dtype="f4")
    target.use()
    manifest = json.loads((GPU.ROOT / "patch/fx/manifest.json").read_text())
    print(f"{ctx.info['GL_RENDERER']}; {width}x{height}; median of five draws")
    scenarios = [("newblue_earthquake.glsl", "motion history", {}),
                 ("vegas_2d_shadow.glsl", "blur", {}),
                 ("vegas_glow.glsl", "zero intensity", {}),
                 ("vegas_glow.glsl", "active", {"uControl2": 1, "uControl3": 1}),
                 ("vegas_light_rays.glsl", "default radius", {}),
                 ("vegas_light_rays.glsl", "wide radius", {"uControl6": 2, "uControl7": 2}),
                 ("vegas_radial_blur.glsl", "radial", {}),
                 ("vegas_unsharp_mask.glsl", "active", {"uControl2": 1, "uControl3": 1})]
    for name, label, controls_override in scenarios:
        entry = next(e for e in manifest["filters"] if e["source"] == name)
        raw = (GPU.ROOT / "patch/fx/shaders" / name).read_text()
        old, controls = GPU.PORT.convert(raw, entry["controls"])
        header = (GPU.CHECK.PREAMBLE.replace("{precision}", "highp") +
                  "\nuniform AC_ImageInfo inputImg;\n" +
                  "\n".join(f"uniform float {n};" for n in controls) + "\n")
        path = GPU.ROOT / "patch/effects" / ("fx-" + Path(name).stem.replace("_", "-") + ".xml")
        programs = [ctx.program(vertex_shader=GPU.VERTEX, fragment_shader=GPU.desktop(header + old)),
                    ctx.program(vertex_shader=GPU.vertex_for(path),
                                fragment_shader=GPU.desktop(GPU.CHECK.assemble(path)))]
        times = []
        for program in programs:
            values = {"inputImg.texture": 0, "acScreenSize": (width, height),
                      "acTime": 10.125, "acStartTime": 0}
            values.update({name: 1 if name == "uControl1" else 0 for name in controls})
            values.update(controls_override)
            for name, value in values.items():
                if name in program:
                    program[name].value = value
            vao = ctx.vertex_array(program, [])
            vao.render(vertices=3)
            ctx.finish()
            samples = []
            for _ in range(5):
                start = time.perf_counter()
                vao.render(vertices=3)
                ctx.finish()
                samples.append((time.perf_counter() - start) * 1000)
            times.append(statistics.median(samples))
            vao.release()
            program.release()
        print(f"{path.stem} ({label}): {times[0]:.3f} ms -> {times[1]:.3f} ms ({times[0] / times[1]:.2f}x)", flush=True)
    target.release()
    texture.release()
    ctx.release()


if __name__ == "__main__":
    main()
