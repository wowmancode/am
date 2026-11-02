# Unlocked native license benefits

The injector discovers every concrete `LicenseBenefit` enum constant in the
source APK and adds the complete set to each local `PurchaseState` snapshot.
It uses the app's immutable Kotlin set-union API, preserving the incoming
benefits and every unrelated account, license, and purchase field. The hook
runs in the purchase-state constructor, so the initial offline/default state
and later account refreshes use the same exhaustive entitlement set.

The enum is read from the exact APK being built rather than hardcoded. The build
fails if the purchase-state constructor, immutable union method, or enum shape
changes, or if no concrete benefits are found. This unlocks everything gated by
native `LicenseBenefit` values, including every easing graph and the other
premium feature gates that consult the same purchase state.

The patch cannot fabricate server-owned records, cloud storage quotas, remote
content, or services that require an authenticated network entitlement. Those
features remain limited by the server even though every native license benefit
is present locally.
