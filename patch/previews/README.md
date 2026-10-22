# Applied filter previews

Every filter in `patch/effects/` has an animated 180 × 180 WebP thumbnail and
a 720 × 720 applied detail image. The app's existing effect browser discovers
them by the English effect name, plays the small animation, and uses the
`_bg.webp` image in its detail view. The same name convention is used by stock
Alight Motion previews.

The original sample card has color, fine detail, geometry, and transparent
edges. Every image is rendered through the actual bundled effect shader.
Animations alternate between the original and applied result; time-based
filters animate during the loop. `settings.json` chooses illustrative control
values, including nonzero settings for filters with neutral defaults. Applying
an effect still uses its original default controls.

To regenerate (requires `moderngl`, `numpy`, Pillow, and EGL/Mesa):

```sh
python3 .github/scripts/generate-effect-previews.py
```

To check the committed previews (Python standard library only):

```sh
python3 .github/scripts/generate-effect-previews.py --check
```

The index pins each filter XML, preview recipe, renderer source, and image
checksum. The build rejects missing, stale, or static thumbnails and verifies
that every committed preview is present in the output APK. The preview assets
do not enter the top-level effect XML integrity hash.
