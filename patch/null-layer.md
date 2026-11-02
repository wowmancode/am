# Null transform layer

Tap **Null** in the editor after selecting one or more layers. The button uses
Alight Motion's native `groupElementsById` operation to move the selected layer
IDs into a scene-backed group labeled `Null`. Moving that group moves every
child layer, so it behaves as a transform parent. The group is ordinary project
data and is serialized with the project.

The operation runs through the existing scene holder and an undo transaction.
Each tap produces a numbered native group label (`Null 1`, `Null 2`, and so on)
through the same label helper used by the built-in Group command. Selection
controls, transform keyframes, easing, effects, and export render the children
through the app's unchanged nested-scene path.

If nothing is selected, the button explains that layers must be selected first.
Null is therefore a link/group operation rather than an invisible standalone
object with no children. Ungrouping or editing the nested scene remains available
through Alight Motion's native group controls.
