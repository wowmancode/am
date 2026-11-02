package com.wowmancode.customfx;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.alightcreative.app.motion.scene.*;
import com.alightcreative.app.motion.scene.animators.AnimatorOf;
import com.alightcreative.app.motion.scene.userparam.KeyableUserParameterValue;
import com.alightcreative.app.motion.scene.visualeffect.KeyableVisualEffectRef;
import com.alightcreative.app.motion.scene.visualeffect.VisualEffectKt;
import java.util.*;
import kotlin.jvm.functions.Function1;
import kotlin.reflect.KType;

/** Move & Transform controls backed by native project effect/keyframe values. */
public final class Transform3dUi {
    public static final String EFFECT = "com.wowmancode.internal.transform3d";
    private static final String[] PARAMETERS = {"rotateX", "rotateY", "depth"};
    private static final String AXIS_PATH = "com.alightcreative.app.motion.scene.SceneElement::transform.__custom3d_";
    private static final int MOVE = 0x7f0a0604, ROTATE = 0x7f0a0608, STATE = 0x7f0a7ff1;
    private static final int X = 0x7f0a03ea, Y = 0x7f0a03ec, XL = 0x7f0a03eb, YL = 0x7f0a03ed;
    private static final int PAD = 0x7f0a0524, GUIDE = 0x7f0a0674;
    private Transform3dUi() {}

    private static State state(i1.z fragment) {
        View root = fragment.getView();
        View holder = root == null ? null : root.findViewById(STATE);
        return holder != null && holder.getTag() instanceof State ? (State) holder.getTag() : null;
    }
    public static void attach(i1.z fragment) {
        if (state(fragment) != null || !(fragment.getView() instanceof ViewGroup)) return;
        ViewGroup root = (ViewGroup) fragment.getView();
        View anchor = root.findViewById(X);
        if (anchor == null || !(anchor.getParent() instanceof ViewGroup)) return;
        ViewGroup panel = (ViewGroup) anchor.getParent();
        State state = new State(fragment, panel);
        state.overlay.setId(STATE);
        state.overlay.setTag(state);
        panel.addView(state.overlay, new ViewGroup.LayoutParams(-1, -1));
        refresh(fragment);
    }
    public static void refresh(i1.z fragment) {
        State state = state(fragment);
        if (state != null) state.refresh();
    }
    public static boolean isDepth(i1.z fragment) {
        State state = state(fragment);
        return state != null && fragment.custom3dMode() == MOVE && state.moveAxis == 2;
    }
    public static boolean onAngle(i1.z fragment, float angle) {
        State state = state(fragment);
        if (state == null || fragment.custom3dMode() != ROTATE || state.rotationAxis == 2) return false;
        state.setValue(state.rotationAxis, angle, false);
        return true;
    }
    public static SceneElement depthDrag(i1.z fragment, Scene scene, SceneElement element, Vector2D delta) {
        if (!isDepth(fragment)) return null;
        float time = l1.e.p(fragment);
        Keyable keyable = keyable(element, 2);
        float value = Math.max(-100000, Math.min(100000, ((Number) KeyableKt.valueAtTime(keyable, time)).floatValue() + delta.getX()));
        return withKeyable(element, 2, KeyableKt.copyWithValueForTime(keyable, scene, element, time, value));
    }
    public static List bindings(i1.z fragment, List original) {
        State state = state(fragment);
        if (state == null) return original;
        int mode = fragment.custom3dMode();
        int axis = mode == MOVE && state.moveAxis == 2 ? 2 : mode == ROTATE && state.rotationAxis < 2 ? state.rotationAxis : -1;
        if (axis < 0) return original;
        if (state.lenses == null) {
            KType type = ((i1.v) original.get(1)).b().e();
            state.lenses = new AxisLens[]{new AxisLens(0, type), new AxisLens(1, type), new AxisLens(2, type)};
        }
        ArrayList result = new ArrayList(original);
        int index = mode == MOVE ? 0 : 1;
        i1.v previous = (i1.v) original.get(index);
        result.set(index, new i1.v(mode == MOVE ? AnimatorOf.Float : AnimatorOf.Rotate,
                                  state.lenses[axis], previous.c()));
        return result;
    }
    /** Restore our synthetic property, then let the native parser compose any suffix. */
    public static n2.a restoreAxis(String path, String segment) {
        for (int axis = 0; axis < PARAMETERS.length; axis++) {
            String base = AXIS_PATH + PARAMETERS[axis];
            if ((path.equals(base) || path.startsWith(base + "."))
                    && segment.equals("__custom3d_" + PARAMETERS[axis])) {
                KType type = n2.f.b("com.alightcreative.app.motion.scene.SceneElement::transform.rotation").e();
                return new AxisLens(axis, type);
            }
        }
        return null;
    }
    static KeyableVisualEffectRef effect(SceneElement element) {
        for (Object item : element.getVisualEffects().values()) {
            KeyableVisualEffectRef reference = (KeyableVisualEffectRef) item;
            if (EFFECT.equals(reference.getId())) return reference;
        }
        return null;
    }
    static Keyable keyable(SceneElement element, int axis) {
        KeyableVisualEffectRef effect = effect(element);
        KeyableUserParameterValue value = effect == null ? null : (KeyableUserParameterValue) effect.getParameters().get(PARAMETERS[axis]);
        return value == null ? KeyableKt.keyable(0f) : value.getFloatValue();
    }
    static SceneElement withKeyable(SceneElement element, int axis, Keyable value) {
        KeyableVisualEffectRef old = effect(element);
        Map parameters = new LinkedHashMap(old == null ? Collections.emptyMap() : old.getParameters());
        parameters.put(PARAMETERS[axis], new KeyableUserParameterValue((KeyableFloat) value));
        long id = old == null ? VisualEffectKt.nextEffectInstanceId() : old.getInstanceId();
        KeyableVisualEffectRef next = new KeyableVisualEffectRef(EFFECT, id, parameters,
            old == null ? 0 : old.getRenderGroup(), old != null && old.getLocallyApplied(),
            old != null && old.getHidden(), old == null ? Collections.emptySet() : old.getDisabledRenderGroups());
        Map effects = new LinkedHashMap(element.getVisualEffects());
        effects.put(id, next);
        List order = new ArrayList(element.getVisualEffectOrder());
        if (old == null) order.add(id);
        return Transform3dCopies.effects(element, effects, order);
    }
    private static final class AxisLens implements n2.a {
        private final int axis;
        private final KType type;
        AxisLens(int axis, KType type) { this.axis = axis; this.type = type; }
        public Object get(Object element) { return keyable((SceneElement) element, axis); }
        public Object c(Object element) { return get(element); }
        public Object a(Object element) { return withKeyable((SceneElement) element, axis, (Keyable) get(element)); }
        public Object b(Object element, Object value) { return withKeyable((SceneElement) element, axis, (Keyable) value); }
        public Object d(Object element, Function1 update) { return b(element, update.invoke(get(element))); }
        public KType e() { return type; }
        public String toString() { return AXIS_PATH + PARAMETERS[axis]; }
        public boolean equals(Object other) { return other instanceof AxisLens && ((AxisLens) other).axis == axis; }
        public int hashCode() { return EFFECT.hashCode() * 31 + axis; }
    }
    private static final class State {
        final i1.z fragment;
        final ViewGroup root;
        final FrameLayout overlay;
        final LinearLayout row;
        final TextView[] values = new TextView[3], labels = new TextView[3];
        final CharSequence originalGuide;
        int moveAxis = -1, rotationAxis = 2;
        AxisLens[] lenses;
        State(i1.z fragment, ViewGroup root) {
            this.fragment = fragment; this.root = root;
            overlay = new FrameLayout(root.getContext());
            row = new LinearLayout(root.getContext());
            row.setOrientation(LinearLayout.HORIZONTAL);
            TextView nativeValue = (TextView) root.findViewById(X);
            TextView guide = (TextView) root.findViewById(GUIDE);
            originalGuide = guide.getText();
            for (int index = 0; index < 3; index++) {
                final int axis = index;
                LinearLayout cell = new LinearLayout(root.getContext());
                cell.setOrientation(LinearLayout.VERTICAL);
                values[index] = new TextView(root.getContext());
                values[index].setGravity(Gravity.CENTER);
                values[index].setTypeface(nativeValue.getTypeface());
                values[index].setTextSize(TypedValue.COMPLEX_UNIT_PX, nativeValue.getTextSize());
                values[index].setSingleLine(true);
                Drawable background = nativeValue.getBackground();
                if (background != null && background.getConstantState() != null)
                    values[index].setBackground(background.getConstantState().newDrawable().mutate());
                labels[index] = new TextView(root.getContext());
                labels[index].setText(new String[]{"X", "Y", "Z"}[index]);
                labels[index].setGravity(Gravity.CENTER);
                labels[index].setTextSize(TypedValue.COMPLEX_UNIT_DIP, 6);
                labels[index].setTextColor(root.getResources().getColor(0x7f06003d));
                cell.addView(values[index], new LinearLayout.LayoutParams(dp(63), dp(25)));
                cell.addView(labels[index], new LinearLayout.LayoutParams(-1, dp(16)));
                LinearLayout.LayoutParams layout = new LinearLayout.LayoutParams(dp(63), dp(44));
                if (index != 2) layout.rightMargin = dp(5);
                row.addView(cell, layout);
                cell.setFocusable(true);
                cell.setOnClickListener(new View.OnClickListener() {
                    public void onClick(View ignored) {
                        boolean moving = fragment.custom3dMode() == MOVE;
                        boolean selected = moving ? moveAxis == axis : rotationAxis == axis;
                        if (moving) moveAxis = axis; else rotationAxis = axis;
                        fragment.u();
                        if (moving && axis < 2) root.findViewById(axis == 0 ? X : Y).performClick();
                        else if (selected) edit(axis);
                    }
                });
                cell.setOnLongClickListener(new View.OnLongClickListener() {
                    public boolean onLongClick(View ignored) {
                        if (fragment.custom3dMode() == MOVE) moveAxis = axis; else rotationAxis = axis;
                        fragment.u();
                        if (fragment.custom3dMode() == MOVE && axis < 2) root.findViewById(axis == 0 ? X : Y).performClick();
                        else edit(axis);
                        return true;
                    }
                });
                cell.setContentDescription(new String[]{"X", "Y", "Z"}[index] + " axis. Tap to select; tap again or hold to edit.");
            }
            FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(-2, dp(44), Gravity.TOP | Gravity.CENTER_HORIZONTAL);
            layout.topMargin = dp(15);
            overlay.addView(row, layout);
        }
        int dp(float value) { return Math.round(value * root.getResources().getDisplayMetrics().density); }
        float current(int axis) {
            SceneElement element = l1.e.z(fragment);
            if (element == null) return 0;
            float time = SceneElementKt.fractionalTime(element, l1.e.o(fragment));
            boolean moving = fragment.custom3dMode() == MOVE;
            if (moving && axis < 2) {
                Vector2D location = element.getTransform().valueAtTime(time).getLocation();
                return axis == 0 ? location.getX() : location.getY();
            }
            if (!moving && axis == 2) return element.getTransform().valueAtTime(time).getRotation();
            return ((Number) KeyableKt.valueAtTime(keyable(element, moving ? 2 : axis), time)).floatValue();
        }
        void refresh() {
            int mode = fragment.custom3dMode();
            boolean moving = mode == MOVE;
            row.setVisibility(moving || mode == ROTATE ? View.VISIBLE : View.GONE);
            if (!moving && mode != ROTATE) return;
            if (moving) {
                for (int id : new int[]{X, Y, XL, YL}) root.findViewById(id).setVisibility(View.INVISIBLE);
            }
            for (int index = 0; index < 3; index++) {
                values[index].setText(String.format(Locale.US, moving ? "%.1f" : "%.1f°", current(index)));
                boolean selected = moving ? moveAxis == index : rotationAxis == index;
                values[index].setTextColor(root.getResources().getColor(selected ? 0x7f060017 : 0x7f06005f));
                Drawable background = values[index].getBackground();
                if (background instanceof GradientDrawable)
                    ((GradientDrawable) background).setStroke(dp(selected ? 1 : 0), root.getResources().getColor(0x7f060017));
            }
            ((TextView) root.findViewById(GUIDE)).setText(moving && moveAxis == 2 ? "Swipe left or right to move layer in Z" : originalGuide);
            if (mode == ROTATE) ((com.alightcreative.widget.RotateView) root.findViewById(PAD)).setAngle(current(rotationAxis));
        }
        void setValue(int axis, float value, boolean transaction) {
            if (Float.isNaN(value) || Float.isInfinite(value)) return;
            value = Math.max(-100000, Math.min(100000, value));
            SceneElement element = l1.e.z(fragment);
            Scene scene = l1.e.t(fragment);
            SceneHolder holder = l1.e.w(fragment);
            if (element == null || scene == null || holder == null) return;
            f3.b.a undo = transaction ? l1.e.c(fragment) : null;
            try {
                float time = SceneElementKt.fractionalTime(element, l1.e.o(fragment));
                boolean moving = fragment.custom3dMode() == MOVE;
                if (!moving && axis == 2) {
                    Keyable next = KeyableKt.copyWithValueForTime(element.getTransform().getRotation(), scene, element, time, value);
                    holder.update(Transform3dCopies.rotation(element, next));
                } else {
                    int parameter = moving ? 2 : axis;
                    Keyable next = KeyableKt.copyWithValueForTime(keyable(element, parameter), scene, element, time, value);
                    holder.update(withKeyable(element, parameter, next));
                }
                fragment.u();
            } finally { if (undo != null) undo.b(); }
        }
        void edit(final int axis) {
            final EditText input = new EditText(root.getContext());
            input.setSingleLine(true);
            input.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_SIGNED | InputType.TYPE_NUMBER_FLAG_DECIMAL);
            input.setText(String.format(Locale.US, "%.2f", current(axis)));
            input.selectAll();
            FrameLayout container = new FrameLayout(root.getContext());
            container.setPadding(dp(20), dp(8), dp(20), 0);
            container.addView(input, new FrameLayout.LayoutParams(-1, -2));
            final AlertDialog dialog = new AlertDialog.Builder(root.getContext())
                .setTitle((fragment.custom3dMode() == MOVE ? "Position " : "Rotation ") + new String[]{"X", "Y", "Z"}[axis])
                .setView(container).setPositiveButton("Set", null)
                .setNegativeButton("Cancel", null).setNeutralButton("Reset", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int which) { setValue(axis, 0, true); }
                }).create();
            dialog.setOnShowListener(new DialogInterface.OnShowListener() {
                public void onShow(DialogInterface ignored) {
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(new View.OnClickListener() {
                        public void onClick(View ignored) {
                            try {
                                float value = Float.parseFloat(input.getText().toString().trim());
                                if (Float.isNaN(value) || Float.isInfinite(value) || Math.abs(value) > 100000) throw new NumberFormatException();
                                setValue(axis, value, true); dialog.dismiss();
                            } catch (NumberFormatException error) { input.setError("Enter a finite number from −100000 to 100000"); }
                        }
                    });
                    input.requestFocus();
                    dialog.getWindow().setSoftInputMode(5);
                }
            });
            dialog.show();
        }
    }
}
