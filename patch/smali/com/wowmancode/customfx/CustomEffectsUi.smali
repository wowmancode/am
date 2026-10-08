.class public final Lcom/wowmancode/customfx/CustomEffectsUi;
.super Ljava/lang/Object;
.source "CustomEffectsUi.java"

# implements
.implements Ljava/lang/Runnable;
.implements Landroid/view/View$OnClickListener;


# One small object does all main-thread work for the editor:
#   op 0: show a toast with arg
#   op 1: close the editor dialog
#   op 2: close the dialog and add effect arg through the browser's own
#         pick method, exactly as if a built-in effect had been tapped
#   op 3: (click listener) open the editor dialog
.field private final op:I
.field private final act:Landroid/app/Activity;
.field private final dlg:Landroid/app/Dialog;
.field private final arg:Ljava/lang/String;


.method public constructor <init>(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    .registers 5
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput p1, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->op:I
    iput-object p2, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->act:Landroid/app/Activity;
    iput-object p3, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->dlg:Landroid/app/Dialog;
    iput-object p4, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->arg:Ljava/lang/String;
    return-void
.end method


# Run op on the activity's main thread. JavaScript bridge calls arrive on a
# background thread, where touching views or showing a toast would crash.
.method public static post(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    .registers 5
    new-instance v0, Lcom/wowmancode/customfx/CustomEffectsUi;
    invoke-direct {v0, p0, p1, p2, p3}, Lcom/wowmancode/customfx/CustomEffectsUi;-><init>(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    invoke-virtual {p1, v0}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    return-void
.end method


.method public run()V
    .registers 8

    :try_start
    iget v0, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->op:I
    iget-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->act:Landroid/app/Activity;
    iget-object v2, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->dlg:Landroid/app/Dialog;
    iget-object v3, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->arg:Ljava/lang/String;

    if-nez v0, :not_toast
    const/4 v4, 0x0
    invoke-static {v1, v3, v4}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v4
    invoke-virtual {v4}, Landroid/widget/Toast;->show()V
    goto :done

    :not_toast
    if-eqz v2, :no_dialog
    invoke-virtual {v2}, Landroid/app/Dialog;->dismiss()V

    :no_dialog
    const/4 v4, 0x2
    if-ne v0, v4, :done

    # Effect ids are passed as "<effect>/<preset>"; no preset here.
    new-instance v4, Ljava/lang/StringBuilder;
    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v5, "/"
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v4

    check-cast v1, Lcom/alightcreative/app/motion/activities/effectbrowser/EffectBrowserActivity;
    const/4 v5, 0x0
    const-string v6, "custom"
    invoke-virtual {v1, v4, v5, v6}, Lcom/alightcreative/app/motion/activities/effectbrowser/EffectBrowserActivity;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    :done
    return-void

    :catch_0
    move-exception v0
    const-string v1, "CustomFX"
    const-string v2, "UI action failed"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    return-void
.end method


.method public onClick(Landroid/view/View;)V
    .registers 5

    :try_start
    new-instance v0, Lcom/wowmancode/customfx/CustomEffectsDialog;
    iget-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsUi;->act:Landroid/app/Activity;
    invoke-direct {v0, v1}, Lcom/wowmancode/customfx/CustomEffectsDialog;-><init>(Landroid/app/Activity;)V
    invoke-virtual {v0}, Landroid/app/Dialog;->show()V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    return-void

    :catch_0
    move-exception v0
    const-string v1, "CustomFX"
    const-string v2, "Could not open the editor"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    return-void
.end method


# Called from the patched EffectBrowserActivity.onCreate right after
# setContentView: adds a floating "+ Custom" pill at the bottom right.
.method public static attachButton(Landroid/app/Activity;)V
    .registers 8
    # p0 = activity (v7)

    :try_start
    invoke-virtual {p0}, Landroid/app/Activity;->getResources()Landroid/content/res/Resources;
    move-result-object v1
    invoke-virtual {v1}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;
    move-result-object v1
    iget v1, v1, Landroid/util/DisplayMetrics;->density:F

    # v2 = 16dp, v3 = 10dp, v4 = 24dp (all px ints)
    const/high16 v2, 0x41800000
    mul-float/2addr v2, v1
    float-to-int v2, v2
    const/high16 v3, 0x41200000
    mul-float/2addr v3, v1
    float-to-int v3, v3
    const/high16 v4, 0x41c00000
    mul-float/2addr v4, v1
    float-to-int v4, v4

    new-instance v0, Landroid/widget/TextView;
    invoke-direct {v0, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    const-string v5, "+ Custom"
    invoke-virtual {v0, v5}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    const/4 v5, -0x1
    invoke-virtual {v0, v5}, Landroid/widget/TextView;->setTextColor(I)V
    const/high16 v5, 0x41600000
    invoke-virtual {v0, v5}, Landroid/widget/TextView;->setTextSize(F)V
    invoke-virtual {v0, v2, v3, v2, v3}, Landroid/view/View;->setPadding(IIII)V

    new-instance v5, Landroid/graphics/drawable/GradientDrawable;
    invoke-direct {v5}, Landroid/graphics/drawable/GradientDrawable;-><init>()V
    # 0xFFE94560, the editor's accent color
    const v6, -0x16baa0
    invoke-virtual {v5, v6}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V
    const/high16 v6, 0x42c80000
    invoke-virtual {v5, v6}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V
    invoke-virtual {v0, v5}, Landroid/view/View;->setBackground(Landroid/graphics/drawable/Drawable;)V

    # 8dp elevation keeps it above the effect grid.
    const/high16 v5, 0x41000000
    mul-float/2addr v5, v1
    invoke-virtual {v0, v5}, Landroid/view/View;->setElevation(F)V

    new-instance v5, Lcom/wowmancode/customfx/CustomEffectsUi;
    const/4 v6, 0x3
    const/4 v1, 0x0
    invoke-direct {v5, v6, p0, v1, v1}, Lcom/wowmancode/customfx/CustomEffectsUi;-><init>(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    invoke-virtual {v0, v5}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    # WRAP_CONTENT x WRAP_CONTENT, gravity BOTTOM|END
    new-instance v5, Landroid/widget/FrameLayout$LayoutParams;
    const/4 v6, -0x2
    const v1, 0x800055
    invoke-direct {v5, v6, v6, v1}, Landroid/widget/FrameLayout$LayoutParams;-><init>(III)V
    invoke-virtual {v5, v2, v2, v2, v4}, Landroid/widget/FrameLayout$LayoutParams;->setMargins(IIII)V

    # android.R.id.content
    const v1, 0x1020002
    invoke-virtual {p0, v1}, Landroid/app/Activity;->findViewById(I)Landroid/view/View;
    move-result-object v1
    check-cast v1, Landroid/view/ViewGroup;
    invoke-virtual {v1, v0, v5}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    return-void

    :catch_0
    move-exception v0
    const-string v1, "CustomFX"
    const-string v2, "Could not add the Custom button"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    return-void
.end method
