# Unlocked easing graphs

All built-in graph presets use the native `AdvancedEasing` benefit. The patch adds that benefit when each local `PurchaseState` snapshot is constructed, including the initial offline/default snapshot and later account updates. The graph editor and account benefit getter both read that same state, so preset selection, handles, lock badges, clipboard actions, existing projects, and preview/export checks agree.

The constructor uses the app's existing Kotlin set union API to copy the incoming benefits and add `AdvancedEasing` once. It preserves the caller's set, other benefit flags, license records, and purchase/account fields. This avoids allocating a new set on every benefit read. Native graph math, serialization, keyframe interpolation, and the 3D axis binding fix are retained.

The injector validates the exact constructor and native union API before patching, and repeated injection is idempotent. The normal build assembles all DEX files and runs the existing 3D keyframe, shader, and encoder checks. Actual graph touch interactions and phone exports still need device testing.
