.class public Lcom/wowmancode/customfx/PreviewFpsUi;
.super Ljava/lang/Object;
.implements Landroid/view/View$OnClickListener;
.implements Ljava/lang/Runnable;

.field private view:Landroid/widget/TextView;
.field private enabled:Z
.field private active:Z
.field private lastTime:J
.field private lastFrames:J

.method private constructor <init>(Landroid/widget/TextView;)V
    .locals 3
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    invoke-virtual {p1}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    const-string v1, "preview_metrics"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "enabled"
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    iput-boolean v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->enabled:Z
    invoke-direct {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->updateLabel()V
    return-void
.end method

.method public static attach(Landroid/app/Activity;)V
    .locals 10
    const v0, 0x7f0a7ff0
    invoke-virtual {p0, v0}, Landroid/app/Activity;->findViewById(I)Landroid/view/View;
    move-result-object v1
    if-nez v1, :done
    const v1, 0x1020002
    invoke-virtual {p0, v1}, Landroid/app/Activity;->findViewById(I)Landroid/view/View;
    move-result-object v1
    instance-of v2, v1, Landroid/widget/FrameLayout;
    if-eqz v2, :done
    check-cast v1, Landroid/widget/FrameLayout;
    new-instance v2, Landroid/widget/TextView;
    invoke-direct {v2, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    invoke-virtual {v2, v0}, Landroid/view/View;->setId(I)V
    const/16 v0, 0x11
    invoke-virtual {v2, v0}, Landroid/widget/TextView;->setGravity(I)V
    const/high16 v0, 0x41400000    # 12sp
    invoke-virtual {v2, v0}, Landroid/widget/TextView;->setTextSize(F)V
    const/4 v0, 0x1
    invoke-virtual {v2, v0}, Landroid/widget/TextView;->setSingleLine(Z)V
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v3
    invoke-virtual {v3}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;
    move-result-object v3
    iget v3, v3, Landroid/util/DisplayMetrics;->density:F
    const/high16 v4, 0x41000000    # 8dp
    mul-float/2addr v4, v3
    float-to-int v4, v4
    const/high16 v5, 0x42300000    # 44dp
    mul-float/2addr v5, v3
    float-to-int v5, v5
    const/high16 v6, 0x42480000    # 50dp, just below the editor toolbar
    mul-float/2addr v6, v3
    float-to-int v6, v6
    const/4 v7, 0x0
    invoke-virtual {v2, v4, v7, v4, v7}, Landroid/view/View;->setPadding(IIII)V
    new-instance v7, Landroid/graphics/drawable/GradientDrawable;
    invoke-direct {v7}, Landroid/graphics/drawable/GradientDrawable;-><init>()V
    const v8, -0x33eee7d9    # translucent dark slate
    invoke-virtual {v7, v8}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V
    const/high16 v8, 0x41400000
    mul-float/2addr v8, v3
    invoke-virtual {v7, v8}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V
    invoke-virtual {v2, v7}, Landroid/view/View;->setBackground(Landroid/graphics/drawable/Drawable;)V
    new-instance v3, Lcom/wowmancode/customfx/PreviewFpsUi;
    invoke-direct {v3, v2}, Lcom/wowmancode/customfx/PreviewFpsUi;-><init>(Landroid/widget/TextView;)V
    invoke-virtual {v2, v3}, Landroid/view/View;->setTag(Ljava/lang/Object;)V
    invoke-virtual {v2, v3}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V
    const-string v0, "Preview FPS. Tap to show or hide the live preview frame rate."
    invoke-virtual {v2, v0}, Landroid/view/View;->setContentDescription(Ljava/lang/CharSequence;)V
    new-instance v9, Landroid/widget/FrameLayout$LayoutParams;
    const/4 v0, -0x2
    invoke-direct {v9, v0, v5}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V
    const v0, 0x800035
    iput v0, v9, Landroid/widget/FrameLayout$LayoutParams;->gravity:I
    iput v6, v9, Landroid/view/ViewGroup$MarginLayoutParams;->topMargin:I
    iput v4, v9, Landroid/view/ViewGroup$MarginLayoutParams;->rightMargin:I
    invoke-virtual {v1, v2, v9}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    :done
    return-void
.end method

.method private static get(Landroid/app/Activity;)Lcom/wowmancode/customfx/PreviewFpsUi;
    .locals 2
    const v0, 0x7f0a7ff0
    invoke-virtual {p0, v0}, Landroid/app/Activity;->findViewById(I)Landroid/view/View;
    move-result-object v0
    if-eqz v0, :missing
    invoke-virtual {v0}, Landroid/view/View;->getTag()Ljava/lang/Object;
    move-result-object v0
    instance-of v1, v0, Lcom/wowmancode/customfx/PreviewFpsUi;
    if-eqz v1, :missing
    check-cast v0, Lcom/wowmancode/customfx/PreviewFpsUi;
    return-object v0
    :missing
    const/4 v0, 0x0
    return-object v0
.end method

.method public static resume(Landroid/app/Activity;)V
    .locals 1
    invoke-static {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->get(Landroid/app/Activity;)Lcom/wowmancode/customfx/PreviewFpsUi;
    move-result-object v0
    if-eqz v0, :done
    const/4 p0, 0x1
    iput-boolean p0, v0, Lcom/wowmancode/customfx/PreviewFpsUi;->active:Z
    invoke-direct {v0}, Lcom/wowmancode/customfx/PreviewFpsUi;->restart()V
    :done
    return-void
.end method

.method public static pause(Landroid/app/Activity;)V
    .locals 2
    invoke-static {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->get(Landroid/app/Activity;)Lcom/wowmancode/customfx/PreviewFpsUi;
    move-result-object v0
    if-eqz v0, :done
    const/4 v1, 0x0
    iput-boolean v1, v0, Lcom/wowmancode/customfx/PreviewFpsUi;->active:Z
    iget-object v1, v0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    invoke-virtual {v1, v0}, Landroid/view/View;->removeCallbacks(Ljava/lang/Runnable;)Z
    :done
    return-void
.end method

.method private frames()J
    .locals 2
    iget-object v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    invoke-virtual {v0}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    check-cast v0, Lcom/alightcreative/app/motion/activities/EditActivity;
    invoke-static {v0}, Lcom/alightcreative/app/motion/activities/EditActivity;->C0(Lcom/alightcreative/app/motion/activities/EditActivity;)Lcom/alightcreative/app/motion/scene/ScenePlayer;
    move-result-object v0
    if-eqz v0, :missing
    iget-wide v0, v0, Lcom/alightcreative/app/motion/scene/ScenePlayer;->previewFrameCount:J
    return-wide v0
    :missing
    const-wide/16 v0, 0x0
    return-wide v0
.end method

.method private updateLabel()V
    .locals 3
    iget-object v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    iget-boolean v1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->enabled:Z
    invoke-virtual {v0, v1}, Landroid/view/View;->setSelected(Z)V
    if-eqz v1, :off
    const-string v1, "Preview FPS: ..."
    const v2, -0x861c42
    goto :label
    :off
    const-string v1, "Preview FPS"
    const/4 v2, -0x1
    :label
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    invoke-virtual {v0, v2}, Landroid/widget/TextView;->setTextColor(I)V
    return-void
.end method

.method private restart()V
    .locals 3
    iget-object v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    invoke-virtual {v0, p0}, Landroid/view/View;->removeCallbacks(Ljava/lang/Runnable;)Z
    invoke-direct {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->updateLabel()V
    iget-boolean v1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->enabled:Z
    if-eqz v1, :done
    iget-boolean v1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->active:Z
    if-eqz v1, :done
    invoke-direct {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->frames()J
    move-result-wide v1
    iput-wide v1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->lastFrames:J
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J
    move-result-wide v1
    iput-wide v1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->lastTime:J
    const-wide/16 v1, 0x1f4
    invoke-virtual {v0, p0, v1, v2}, Landroid/view/View;->postDelayed(Ljava/lang/Runnable;J)Z
    :done
    return-void
.end method

.method public onClick(Landroid/view/View;)V
    .locals 4
    iget-boolean v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->enabled:Z
    xor-int/lit8 v0, v0, 0x1
    iput-boolean v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->enabled:Z
    invoke-virtual {p1}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v1
    const-string v2, "preview_metrics"
    const/4 v3, 0x0
    invoke-virtual {v1, v2, v3}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v1
    invoke-interface {v1}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    const-string v2, "enabled"
    invoke-interface {v1, v2, v0}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v1
    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->apply()V
    invoke-direct {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->restart()V
    return-void
.end method

.method public run()V
    .locals 10
    iget-boolean v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->active:Z
    if-eqz v0, :done
    iget-boolean v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->enabled:Z
    if-eqz v0, :done
    invoke-direct {p0}, Lcom/wowmancode/customfx/PreviewFpsUi;->frames()J
    move-result-wide v0
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J
    move-result-wide v2
    iget-wide v4, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->lastTime:J
    sub-long v4, v2, v4
    iget-wide v6, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->lastFrames:J
    sub-long v6, v0, v6
    iput-wide v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->lastFrames:J
    iput-wide v2, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->lastTime:J
    const-wide/16 v8, 0x0
    cmp-long v0, v4, v8
    if-lez v0, :schedule
    invoke-static {v6, v7, v8, v9}, Ljava/lang/Math;->max(JJ)J
    move-result-wide v6
    const-wide/16 v8, 0x2710
    mul-long/2addr v6, v8
    div-long/2addr v6, v4
    long-to-int v2, v6
    div-int/lit8 v3, v2, 0xa
    rem-int/lit8 v2, v2, 0xa
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "Preview FPS: "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, v3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    const-string v1, "."
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    iget-object v1, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    invoke-virtual {v1, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    :schedule
    iget-object v0, p0, Lcom/wowmancode/customfx/PreviewFpsUi;->view:Landroid/widget/TextView;
    const-wide/16 v1, 0x1f4
    invoke-virtual {v0, p0, v1, v2}, Landroid/view/View;->postDelayed(Ljava/lang/Runnable;J)Z
    :done
    return-void
.end method
