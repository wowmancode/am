.class public Lcom/wowmancode/customfx/TransitionUi;
.super Ljava/lang/Object;
.source "TransitionUi.java"

.implements Landroid/view/View$OnClickListener;
.implements Landroid/content/DialogInterface$OnClickListener;

.field private static current:Ljava/lang/ref/WeakReference;
.field private mode:I

.method public constructor <init>()V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    const/4 v0, -0x1
    iput v0, p0, Lcom/wowmancode/customfx/TransitionUi;->mode:I
    return-void
.end method

# The Effects fragment owns the selection and the standard add-effect action.
.method public static bind(Li1/k;)V
    .registers 2
    new-instance v0, Ljava/lang/ref/WeakReference;
    invoke-direct {v0, p0}, Ljava/lang/ref/WeakReference;-><init>(Ljava/lang/Object;)V
    sput-object v0, Lcom/wowmancode/customfx/TransitionUi;->current:Ljava/lang/ref/WeakReference;
    return-void
.end method

# Wrap the normal Add Effect row with a second, full-width Transitions row.
# This runs only for effect_list_add (0x7f0d007a).
.method public static wrapAddRow(Landroid/view/View;I)Landroid/view/View;
    .registers 9
    const v0, 0x7f0d007a
    if-ne p1, v0, :done

    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    new-instance v1, Landroid/widget/LinearLayout;
    invoke-direct {v1, v0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V
    const/4 v2, 0x1
    invoke-virtual {v1, v2}, Landroid/widget/LinearLayout;->setOrientation(I)V

    invoke-virtual {p0}, Landroid/view/View;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;
    move-result-object v2
    iget v3, v2, Landroid/view/ViewGroup$LayoutParams;->height:I
    # The wrapper contains two rows, so the RecyclerView item must measure both.
    # Keeping the original fixed height clips the Transitions row entirely.
    const/4 v6, -0x2
    iput v6, v2, Landroid/view/ViewGroup$LayoutParams;->height:I
    invoke-virtual {v1, v2}, Landroid/view/View;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V
    new-instance v4, Landroid/widget/LinearLayout$LayoutParams;
    const/4 v5, -0x1
    invoke-direct {v4, v5, v3}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V
    invoke-virtual {v1, p0, v4}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    new-instance v4, Landroid/widget/TextView;
    invoke-direct {v4, v0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    const-string v6, "Transitions  ›"
    invoke-virtual {v4, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    const/16 v6, 0x11
    invoke-virtual {v4, v6}, Landroid/widget/TextView;->setGravity(I)V
    const/4 v6, -0x1
    invoke-virtual {v4, v6}, Landroid/widget/TextView;->setTextColor(I)V
    const/high16 v6, 0x41600000
    invoke-virtual {v4, v6}, Landroid/widget/TextView;->setTextSize(F)V
    const v6, -0xd3b9a8
    invoke-virtual {v4, v6}, Landroid/view/View;->setBackgroundColor(I)V
    new-instance v6, Lcom/wowmancode/customfx/TransitionUi;
    invoke-direct {v6}, Lcom/wowmancode/customfx/TransitionUi;-><init>()V
    invoke-virtual {v4, v6}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V
    new-instance v6, Landroid/widget/LinearLayout$LayoutParams;
    invoke-direct {v6, v5, v3}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V
    invoke-virtual {v1, v4, v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    return-object v1

    :done
    return-object p0
.end method

.method private getFragment()Li1/k;
    .registers 2
    sget-object v0, Lcom/wowmancode/customfx/TransitionUi;->current:Ljava/lang/ref/WeakReference;
    if-eqz v0, :missing
    invoke-virtual {v0}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;
    move-result-object v0
    check-cast v0, Li1/k;
    return-object v0
    :missing
    const/4 v0, 0x0
    return-object v0
.end method

.method public onClick(Landroid/view/View;)V
    .registers 5
    invoke-direct {p0}, Lcom/wowmancode/customfx/TransitionUi;->getFragment()Li1/k;
    move-result-object v0
    if-eqz v0, :done
    invoke-virtual {v0}, Landroidx/fragment/app/Fragment;->getActivity()Landroidx/fragment/app/e;
    move-result-object v0
    if-eqz v0, :done
    const/4 v1, -0x1
    iput v1, p0, Lcom/wowmancode/customfx/TransitionUi;->mode:I
    new-instance v1, Landroid/app/AlertDialog$Builder;
    invoke-direct {v1, v0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V
    const-string v0, "Transitions"
    invoke-virtual {v1, v0}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    const-string v0, "In|Out"
    const-string v2, "\\|"
    invoke-virtual {v0, v2}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0, p0}, Landroid/app/AlertDialog$Builder;->setItems([Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v1}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    :done
    return-void
.end method

.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 10
    invoke-direct {p0}, Lcom/wowmancode/customfx/TransitionUi;->getFragment()Li1/k;
    move-result-object v0
    if-eqz v0, :done
    iget v1, p0, Lcom/wowmancode/customfx/TransitionUi;->mode:I
    const/4 v2, -0x1
    if-ne v1, v2, :apply

    iput p2, p0, Lcom/wowmancode/customfx/TransitionUi;->mode:I
    invoke-virtual {v0}, Landroidx/fragment/app/Fragment;->getActivity()Landroidx/fragment/app/e;
    move-result-object v0
    if-eqz v0, :done
    new-instance v1, Landroid/app/AlertDialog$Builder;
    invoke-direct {v1, v0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V
    const-string v0, "AMV Transitions"
    invoke-virtual {v1, v0}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    const-string v0, "Beat Zoom|Whip Pan|RGB Split|Glitch Tear|Spin Burst|Shake Impact|Fisheye Punch|Pixel Burst|Mirror Swipe|Radial Blur|Flash Cut|Vortex Twist"
    const-string v2, "\\|"
    invoke-virtual {v0, v2}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v1, v0, p0}, Landroid/app/AlertDialog$Builder;->setItems([Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v1}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    goto :done

    :apply
    const-string v3, "beatzoom|whippan|rgbsplit|glitchtear|spinburst|shakeimpact|fisheyepunch|pixelburst|mirrorswipe|radialblur|flashcut|vortex"
    const-string v4, "\\|"
    invoke-virtual {v3, v4}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;
    move-result-object v3
    if-ltz p2, :done
    array-length v4, v3
    if-ge p2, v4, :done
    aget-object v3, v3, p2
    new-instance v4, Ljava/lang/StringBuilder;
    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V
    const-string v5, "com.wowmancode.transitions."
    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const/4 v5, 0x0
    if-ne v1, v5, :out
    const-string v1, ".in"
    goto :lookup
    :out
    const-string v1, ".out"
    :lookup
    invoke-virtual {v4, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v4
    invoke-static {v4}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt;->visualEffectById(Ljava/lang/String;)Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffect;
    move-result-object v4
    if-eqz v4, :done
    invoke-virtual {v0, v4, v5}, Li1/k;->C0(Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffect;Lcom/alightcreative/app/motion/scene/visualeffect/EffectPreset;)V
    :done
    return-void
.end method
