# 3D layer controls in Move & Transform

Move now has X, Y, and Z value boxes in the existing panel. Select Z, then swipe left/right on the normal trackpad to adjust depth; select X or Y to return to normal planar movement. Rotate now has X/Y/Z selectors above the existing dial. Select an axis to use the dial, then tap that axis again (or hold it) to enter a number. Z rotation remains the original native rotation property. Numeric dialogs include Reset and validate finite values.

The new boxes copy the native field background, typeface, text size, colors, 63×25 dp sizing, 15 dp top offset, and 5 dp gaps. Axis labels use the existing small label style; selected axes have a thin native accent border. The controls appear only in Move and Rotate. Existing Scale, Pivot, and Skew panels keep their controls.

Depth, X rotation, and Y rotation use native float keyables in an internal layer projection effect. Selecting one replaces the active keyframe binding with that axis, using the existing keyframe, easing, and animator machinery. Z rotation keeps its native keyable. Updates copy the immutable layer/effect records and use the existing scene holder and undo transactions. Projects and project XML use the app's ordinary effect/keyframe serialization; no preferences or sidecar state store the transform values. Opening Move & Transform alone adds no effect to the layer.

The trackpad's existing undo grouping is retained for depth movement, and its XY snapping is disabled while Z is selected. The rotation dial keeps its normal gesture/undo handlers. Numeric updates use an explicit native undo transaction. The axis selector itself is view state and does not mutate the project.

## Projection and scope

This is a perspective transform of a flat layer, including images, shapes, text, and rendered groups. Positive Z moves the layer away; negative Z brings it closer. The fixed focal distance is 1000 layer units. X/Y tilt is applied about the native layer pivot, with native Z rotation and planar movement preserved. Camera/plane intersection clips points behind the camera and handles edge-on planes without divisions by zero. Back faces are visible. Alpha stays premultiplied.

Orientation is calculated in the vertex shader, with one source sample per fragment. With depth and tilt at zero the shader returns the original pixel directly. No projection effect is attached until a 3D value/keyframe is changed. Preview and export use the same projection independent of framebuffer resolution.

The existing timeline layer order determines stacking. This does not introduce a shared scene camera, mesh extrusion, depth-buffer intersections, or automatic sorting of layers by Z. Selection outlines and XY motion paths remain the native planar guides.

## Build and validation

The helper is maintained as Java in `patch/java/com/wowmancode/customfx/Transform3dUi.java`. The build generates compile-time stubs from the source APK's exact public method descriptors, builds only the helper classes with Java 8 bytecode, then converts them to smali in the smallest DEX. App, Android, and Kotlin stubs are never packaged. Tool downloads have pinned SHA-256 values. The immutable copy adapters are generated from the native method signatures, using Kotlin masks to preserve unrelated fields.

Every build checks the helper's native method references against the actual APK, including inheritance, access, static calls, and interface dispatch. The current nine helpers resolve 71 native calls. Hook anchors reject changed native callbacks instead of guessing. Repeated injection is checked locally, and the complete DEX is reassembled from the original APK.

The internal shader compiles and links as GLSL ES 1.00. A separate GPU check compares its output against an independent homography derived by projecting plane corners. Its 96 cases cover positive/negative depth, combined tilts, back faces, pivot offsets, native Z/XY transforms, premultiplied transparency, camera clipping, edge-on planes, and two preview/export raster sizes. Maximum observed RGBA difference was 0.00003064. Existing FX filters retain their 356 passing GPU comparisons and all 56 applied preview assets.

The internal projection is excluded from the public effect gallery and its preview-coverage list. It is bundled and integrity-hashed with the other effects. The signed workflow runs the GPU checks and validates the resulting APK. There is no attached Android device/emulator, so actual touch interactions, native keyframe/undo interaction, project reopening, and phone export still need device testing.
