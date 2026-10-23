# Preview and export performance

These changes affect the Alight Motion editor canvas and timeline playback.

- Skip the per-frame scene traversal used only to attach statistics to Firebase performance traces, and disable those preview traces.
- Remove debug callback allocations on frame requests, pending-frame updates, and preview queue iterations. Remove the string formatting and Android log write performed on every EGL surface swap.
- Move Earthquake's time-dependent motion history (up to 4096 steps) from each fragment into the vertex stage. Every vertex receives identical inputs, so the motion is constant across the image. Sampling, animation, and blur remain in the fragment shader.
- Reuse Shadow's 65 blur weights across all 65 rows, preserving sample positions and accumulation order.
- Bypass the FX computation when its mix control is zero or negative. Return the input texture directly in its native premultiplied format.
- Skip Light Rays texture samples whose radius weight is exactly zero, and reuse its original pixel for the first ray sample. Skip Glow's 24 additional samples when its intensity is zero. Reuse the original pixel in Radial Blur's first sample and Unsharp Mask's center sample.
- Remove diagnostic allocations inside the shared scene renderer, including its per-layer loop. This applies to nested scenes, live preview, and exports.

The shader changes also apply during export. The native preview changes preserve the existing frame scheduler, media caching, resolution settings, and output quality. The original pinned FX sources are unchanged; the importer generates the optimized host shaders.

## Video export scheduling

The surface encoder previously passed a 10,000 µs timeout to every `dequeueOutputBuffer` call, including the final empty poll before rendering the next frame. During normal rendering, drain all currently available output with a zero timeout, then submit the next frame. This allows GPU rendering and encoding to overlap without an extra wait for future output.

At end of stream, the existing 10,000 µs wait/retry loop remains: signal EOS, continue consuming delayed output until an EOS-marked buffer arrives, and release every acquired buffer. Codec configuration handling, format changes, sample timestamps, bitrate, output resolution, pending audio, muxer writes, and error handling retain their existing behavior.

Per-frame export Firebase traces and encoder debug callback allocations are also removed. Texture cleanup and GPU error handling remain enabled.

## Preview FPS

Tap **Preview FPS** below the editor toolbar to enable the display; tap again to disable it. It starts disabled and remembers your preference. It measures the current editor player's completed surface-swap count over elapsed wall-clock time, updating twice per second. It reads neither the configured project FPS nor the screen refresh rate. When idle it can show zero.

Polling runs only while enabled and the editor is resumed. Pausing the activity or disabling the display removes its scheduled callback; resuming resets the measurement interval. The Android overlay is not part of the rendered scene or exported video. The render path adds a per-player volatile frame counter, with no GPU fence, readback, or forced synchronization.

## Validation

All 28 effects compile and link as GLSL ES 1.00 with the native vertex and fragment preambles. The GPU comparison tool checks 216 source-versus-host cases, 20 Earthquake comparisons against its original fragment-only adaptation, and 120 sampling comparisons across opaque/transparent images, nearest/linear filtering, and active/neutral/extreme controls. These comparisons preserve the host's existing float32 layer-local timing behavior, including the late-timeline history boundary. All 356 comparisons produced identical RGBA output on the test GPU.

`check-export-drain.py` executes the actual patched drain method in a bounded smali interpreter with mocked Android codec/muxer APIs. It verifies zero-timeout normal polls, available-buffer draining, codec configuration skipping, pending-audio order, delayed EOS output, buffer release, and duplicate-format errors. The injection hook runs this check on every build. This models queue behavior; it does not emulate Android hardware or driver backpressure.

The native hook was applied to a fresh `am-2` disassembly, applied a second time to check idempotency, and reassembled successfully. The full APK is built and signed by the existing workflow with the persistent update certificate.

For a reproducible offline shader benchmark, run:

```sh
python3 .github/scripts/benchmark-fx-preview.py
```

Requires `moderngl`, `numpy`, and an EGL implementation. On Mesa llvmpipe at 192×108, five-draw medians for this revision versus the original fragment-only adapters were:

| Shader / controls | Before | After |
| --- | ---: | ---: |
| Earthquake motion history | 45.774 ms | 0.264 ms |
| Shadow blur | 210.014 ms | 100.982 ms |
| Glow, zero intensity | 0.364 ms | 0.145 ms |
| Glow, active | 0.465 ms | 0.443 ms |
| Light Rays, default radius | 0.402 ms | 0.281 ms |
| Light Rays, wide radius | 0.393 ms | 0.419 ms |
| Radial Blur | 0.281 ms | 0.277 ms |
| Unsharp Mask, active | 0.432 ms | 0.443 ms |

Culling helps the default Light Rays case but adds overhead when its wide radius covers the entire image. Radial Blur and Unsharp Mask changes remove redundant source samples; these desktop timings show little difference. These are individual shader timings on a desktop software GPU, not Android playback FPS. Actual phone playback, FPS UI interaction, and export still need device testing; gains depend on the project, effects, resolution, and hardware.
