# Live editor preview performance

These changes affect the Alight Motion editor canvas and timeline playback.

- Skip the per-frame scene traversal used only to attach statistics to Firebase performance traces, and disable those preview traces.
- Remove debug callback allocations on frame requests, pending-frame updates, and preview queue iterations. Remove the string formatting and Android log write performed on every EGL surface swap.
- Move Earthquake's time-dependent motion history (up to 4096 steps) from each fragment into the vertex stage. Every vertex receives identical inputs, so the motion is constant across the image. Sampling, animation, and blur remain in the fragment shader.
- Reuse Shadow's 65 blur weights across all 65 rows, preserving sample positions and accumulation order.
- Bypass the FX computation when its mix control is zero or negative. Return the input texture directly in its native premultiplied format.

The shader changes also apply during export. The native preview changes preserve the existing frame scheduler, media caching, resolution settings, and output quality. The original pinned FX sources are unchanged; the importer generates the optimized host shaders.

## Preview FPS

Tap **Preview FPS** below the editor toolbar to enable the display; tap again to disable it. It starts disabled and remembers your preference. It measures the current editor player's completed surface-swap count over elapsed wall-clock time, updating twice per second. It reads neither the configured project FPS nor the screen refresh rate. When idle it can show zero.

Polling runs only while enabled and the editor is resumed. Pausing the activity or disabling the display removes its scheduled callback; resuming resets the measurement interval. The Android overlay is not part of the rendered scene or exported video. The render path adds a per-player volatile frame counter, with no GPU fence, readback, or forced synchronization.

## Validation

All 28 effects compile and link as GLSL ES 1.00 with the native vertex and fragment preambles. The GPU comparison tool checks 216 source-versus-host cases, plus 20 Earthquake comparisons against its original fragment-only adaptation, including late timeline positions around the 4096-step boundary and control extremes. These comparisons preserve the host's existing float32 layer-local timing behavior. All 236 comparisons produced identical RGBA output on the test GPU.

The native hook was applied to a fresh `am-2` disassembly, applied a second time to check idempotency, and reassembled successfully. The full APK is built and signed by the existing workflow with the persistent update certificate.

For a reproducible offline shader benchmark, run:

```sh
python3 .github/scripts/benchmark-fx-preview.py
```

Requires `moderngl`, `numpy`, and an EGL implementation. On this workspace's Mesa llvmpipe software renderer at 192×108, five-draw medians were about 28.15 → 0.24 ms for Earthquake and 190.09 → 100.59 ms for Shadow. These are individual shader timings on a desktop software GPU, not Android playback FPS. Actual phone playback, FPS UI interaction, and export still need device testing; gains depend on the project, effects, resolution, and hardware.
