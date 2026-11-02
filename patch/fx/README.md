# Imported FX filters

All 24 active visual shaders from
[`wowmancode/fx`, `codex/rollback-wave-spherize`](https://github.com/wowmancode/fx/tree/codex/rollback-wave-spherize)
are bundled here at commit `05050c0380fa9d5418599be616692e073dd4f40b`.
The source files are unchanged. `manifest.json` supplies effect names, categories,
and labels for every declared control. The separate audio DSP sources are not
part of this visual filter import.

Regenerate the XML bundled in the APK with:

```sh
python3 .github/scripts/import-fx-filters.py
python3 .github/scripts/import-fx-filters.py --check
python3 .github/scripts/check-shaders.py patch/effects/*.xml
```

The build checks regeneration and compiles every shader. The existing APK
pipeline includes the generated effects, updates their integrity signature,
and verifies their packaged bytes. No additional runtime download is needed.
Effect names start with **Vegas** or **NewBlue** in the corresponding effect
categories. Each control supports the app's normal numeric editing and animation.
Animated applied previews and larger detail images are bundled for these and
all other custom filters; see [the preview instructions](../previews/README.md).

Mix defaults to 1; all other controls default to 0. Controls keep the source
range of -2 to 2 and its original nonlinear mappings. Mix is clamped to 0–1
by the shader; 0 bypasses it. Some source defaults are neutral: for example,
Unsharp Mask needs Amount and Radius raised, and Starburst needs Star Intensity.
See the source repository's parameter guides for the exact mappings.

The adapter binds texture coordinates to `acScreenNorm`, image dimensions to
`acScreenSize`, and animation time to `acTime - acStartTime`, so moving a layer
does not change the animation's time origin. It converts Alight Motion's
premultiplied samples to straight RGBA for the original FX math, then
premultiplies the final output. Texture interpolation remains the app's native
premultiplied interpolation.

Optional GPU smoke checks require `moderngl`, `numpy`, and EGL/Mesa:

```sh
python3 .github/scripts/check-fx-ports.py
```

These compare each adapted shader with its pinned standalone source on an
opaque gradient, checkerboard, and transparent cutout, using default, changed,
and bypass controls. Nearest sampling isolates the host adaptation from
differences in alpha interpolation. They also check finite output and valid
premultiplied RGBA. The shader compiler separately checks the GLSL ES 1.00
format used by the app.

The original shaders are draft recreations with the accuracy limits documented
in the source repository; importing them does not establish Vegas equivalence.
Height Map uses one layer for both inputs. Wave uses an approximate sine warp.
The shadow's blur can use 4,225 samples per pixel, and Earthquake reconstructs
up to 4,096 motion steps per pixel; these can be expensive on phones. Android
device playback and export still need testing.
