package com.wowmancode.customfx;

import android.app.Activity;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.alightcreative.app.motion.scene.ElementGroupingKt;
import com.alightcreative.app.motion.scene.Scene;
import com.alightcreative.app.motion.scene.SceneHolder;
import java.util.Set;

/** Project-backed null layer implemented as a native transform group. */
public final class NullLayerUi implements View.OnClickListener {
    private static final String BUTTON_TAG = "wowmancode-null-button";
    private final Activity activity;

    private NullLayerUi(Activity activity) { this.activity = activity; }

    public static void attach(Activity activity) {
        View content = activity.findViewById(android.R.id.content);
        if (!(content instanceof FrameLayout)) return;
        if (content.findViewWithTag(BUTTON_TAG) != null) return;
        TextView button = new TextView(activity);
        button.setId(View.generateViewId());
        button.setTag(BUTTON_TAG);
        button.setText("Null");
        button.setGravity(Gravity.CENTER);
        button.setTextColor(0xffffffff);
        button.setTextSize(12);
        int padH = dp(activity, 14), padV = dp(activity, 8);
        button.setPadding(padH, padV, padH, padV);
        GradientDrawable background = new GradientDrawable();
        background.setColor(0xff2a7fff);
        background.setCornerRadius(dp(activity, 18));
        button.setBackground(background);
        button.setElevation(dp(activity, 6));
        button.setContentDescription("Make Null. Select layers first; moving the Null group moves them.");
        button.setOnClickListener(new NullLayerUi(activity));
        FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(-2, dp(activity, 40), Gravity.TOP | Gravity.START);
        layout.leftMargin = dp(activity, 12);
        layout.topMargin = dp(activity, 50);
        ((FrameLayout) content).addView(button, layout);
    }

    public void onClick(View ignored) {
        try {
            SceneHolder holder = l1.e.u(activity);
            if (holder == null) return;
            Set<Long> selected = holder.getSelection().getSelectedElements();
            if (selected == null || selected.isEmpty()) {
                Toast.makeText(activity, "Select one or more layers, then tap Null", Toast.LENGTH_SHORT).show();
                return;
            }
            f3.b.a undo = l1.e.c(activity);
            try {
                Scene scene = holder.getScene();
                Scene grouped = ElementGroupingKt.groupElementsById$default(
                    scene, selected, "Null", null, null, 12, null);
                holder.setScene(grouped);
            } finally {
                if (undo != null) undo.b();
            }
            Toast.makeText(activity, "Null created. Move it to move its linked layers.", Toast.LENGTH_SHORT).show();
        } catch (Throwable error) {
            Toast.makeText(activity, "Could not create Null: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private static int dp(Activity activity, int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }
}
