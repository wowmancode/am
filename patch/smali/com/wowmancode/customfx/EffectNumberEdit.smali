.class public Lcom/wowmancode/customfx/EffectNumberEdit;
.super Ljava/lang/Object;
.source "EffectNumberEdit.java"
.implements Landroid/view/View$OnClickListener;
.implements Landroid/content/DialogInterface$OnClickListener;
.implements Ljava/lang/Runnable;

.field private parameter:Lcom/alightcreative/app/motion/scene/userparam/UserParameter;
.field private valueView:Landroid/widget/TextView;
.field private control:Landroid/view/View;
.field private editor:Landroid/widget/EditText;

.method private constructor <init>(Lcom/alightcreative/app/motion/scene/userparam/UserParameter;Landroid/widget/TextView;Landroid/view/View;)V
    .registers 4
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->parameter:Lcom/alightcreative/app/motion/scene/userparam/UserParameter;
    iput-object p2, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->valueView:Landroid/widget/TextView;
    iput-object p3, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->control:Landroid/view/View;
    return-void
.end method

.method public static bind(Lcom/alightcreative/app/motion/scene/userparam/UserParameter;Landroid/widget/TextView;Landroid/view/View;)V
    .registers 4
    if-eqz p1, :done
    if-eqz p2, :done
    new-instance v0, Lcom/wowmancode/customfx/EffectNumberEdit;
    invoke-direct {v0, p0, p1, p2}, Lcom/wowmancode/customfx/EffectNumberEdit;-><init>(Lcom/alightcreative/app/motion/scene/userparam/UserParameter;Landroid/widget/TextView;Landroid/view/View;)V
    invoke-virtual {p1, v0}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V
    :done
    return-void
.end method

.method private displayScale()F
    .registers 4
    const/high16 v0, 0x3f800000
    iget-object v1, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->parameter:Lcom/alightcreative/app/motion/scene/userparam/UserParameter;
    instance-of v2, v1, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;
    if-eqz v2, :slider
    check-cast v1, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;->getMultiplier()F
    move-result v0
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;->getSliderType()Lcom/alightcreative/app/motion/scene/userparam/SliderType;
    move-result-object v1
    goto :type
    :slider
    check-cast v1, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Slider;
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Slider;->getSliderType()Lcom/alightcreative/app/motion/scene/userparam/SliderType;
    move-result-object v1
    :type
    sget-object v2, Lcom/alightcreative/app/motion/scene/userparam/SliderType;->PERCENT:Lcom/alightcreative/app/motion/scene/userparam/SliderType;
    if-eq v1, v2, :percent
    sget-object v2, Lcom/alightcreative/app/motion/scene/userparam/SliderType;->RELATIVE_PERCENT:Lcom/alightcreative/app/motion/scene/userparam/SliderType;
    if-eq v1, v2, :percent
    sget-object v2, Lcom/alightcreative/app/motion/scene/userparam/SliderType;->KELVIN:Lcom/alightcreative/app/motion/scene/userparam/SliderType;
    if-ne v1, v2, :nonzero
    const/high16 v1, 0x447a0000
    mul-float/2addr v0, v1
    goto :nonzero
    :percent
    const/high16 v1, 0x42c80000
    mul-float/2addr v0, v1
    :nonzero
    const/4 v1, 0x0
    cmpl-float v1, v0, v1
    if-nez v1, :done
    const/high16 v0, 0x3f800000
    :done
    return v0
.end method

.method private rawValue()F
    .registers 4
    iget-object v0, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->control:Landroid/view/View;
    instance-of v1, v0, Lcom/alightcreative/widget/AlightSlider;
    if-eqz v1, :spinner
    check-cast v0, Lcom/alightcreative/widget/AlightSlider;
    invoke-virtual {v0}, Lcom/alightcreative/widget/AlightSlider;->getValue()I
    move-result v0
    int-to-float v0, v0
    const/high16 v1, 0x447a0000
    div-float/2addr v0, v1
    return v0
    :spinner
    check-cast v0, Lcom/alightcreative/widget/ValueSpinner;
    invoke-virtual {v0}, Lcom/alightcreative/widget/ValueSpinner;->getLastSentPos()I
    move-result v0
    int-to-float v0, v0
    iget-object v1, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->parameter:Lcom/alightcreative/app/motion/scene/userparam/UserParameter;
    check-cast v1, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;->getStep()F
    move-result v1
    mul-float/2addr v0, v1
    return v0
.end method

.method public onClick(Landroid/view/View;)V
    .registers 7
    invoke-virtual {p1}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    new-instance v1, Landroid/widget/EditText;
    invoke-direct {v1, v0}, Landroid/widget/EditText;-><init>(Landroid/content/Context;)V
    iput-object v1, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->editor:Landroid/widget/EditText;
    const v2, 0x3002
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setInputType(I)V
    const/4 v2, 0x6
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setImeOptions(I)V
    invoke-direct {p0}, Lcom/wowmancode/customfx/EffectNumberEdit;->rawValue()F
    move-result v2
    invoke-direct {p0}, Lcom/wowmancode/customfx/EffectNumberEdit;->displayScale()F
    move-result v3
    mul-float/2addr v2, v3
    invoke-static {v2}, Ljava/lang/Float;->toString(F)Ljava/lang/String;
    move-result-object v2
    invoke-virtual {v1, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    new-instance v2, Landroid/app/AlertDialog$Builder;
    invoke-direct {v2, v0}, Landroid/app/AlertDialog$Builder;-><init>(Landroid/content/Context;)V
    const-string v3, "Edit effect value"
    invoke-virtual {v2, v3}, Landroid/app/AlertDialog$Builder;->setTitle(Ljava/lang/CharSequence;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v2, v1}, Landroid/app/AlertDialog$Builder;->setView(Landroid/view/View;)Landroid/app/AlertDialog$Builder;
    const-string v3, "Apply"
    invoke-virtual {v2, v3, p0}, Landroid/app/AlertDialog$Builder;->setPositiveButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    const-string v3, "Cancel"
    const/4 v4, 0x0
    invoke-virtual {v2, v3, v4}, Landroid/app/AlertDialog$Builder;->setNegativeButton(Ljava/lang/CharSequence;Landroid/content/DialogInterface$OnClickListener;)Landroid/app/AlertDialog$Builder;
    invoke-virtual {v2}, Landroid/app/AlertDialog$Builder;->show()Landroid/app/AlertDialog;
    move-result-object v2
    invoke-virtual {v2}, Landroid/app/Dialog;->getWindow()Landroid/view/Window;
    move-result-object v2
    if-eqz v2, :focus
    const/4 v3, 0x5
    invoke-virtual {v2, v3}, Landroid/view/Window;->setSoftInputMode(I)V
    :focus
    invoke-virtual {v1}, Landroid/view/View;->requestFocus()Z
    invoke-virtual {v1}, Landroid/widget/EditText;->selectAll()V
    invoke-virtual {v1, p0}, Landroid/view/View;->post(Ljava/lang/Runnable;)Z
    return-void
.end method

.method public run()V
    .registers 4
    iget-object v0, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->editor:Landroid/widget/EditText;
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v1
    const-string v2, "input_method"
    invoke-virtual {v1, v2}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v1
    instance-of v2, v1, Landroid/view/inputmethod/InputMethodManager;
    if-eqz v2, :done
    check-cast v1, Landroid/view/inputmethod/InputMethodManager;
    const/4 v2, 0x1
    invoke-virtual {v1, v0, v2}, Landroid/view/inputmethod/InputMethodManager;->showSoftInput(Landroid/view/View;I)Z
    :done
    return-void
.end method

.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 5
    iget-object v0, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->editor:Landroid/widget/EditText;
    invoke-virtual {v0}, Landroid/widget/EditText;->getText()Landroid/text/Editable;
    move-result-object v0
    invoke-interface {v0}, Landroid/text/Editable;->toString()Ljava/lang/String;
    move-result-object v0
    :try_start
    invoke-static {v0}, Ljava/lang/Float;->parseFloat(Ljava/lang/String;)F
    move-result v0
    :try_end
    .catch Ljava/lang/NumberFormatException; {:try_start .. :try_end} :invalid
    invoke-static {v0}, Ljava/lang/Float;->isNaN(F)Z
    move-result v1
    if-nez v1, :invalid
    invoke-static {v0}, Ljava/lang/Float;->isInfinite(F)Z
    move-result v1
    if-nez v1, :invalid
    invoke-direct {p0, v0}, Lcom/wowmancode/customfx/EffectNumberEdit;->apply(F)V
    return-void
    :invalid
    iget-object v0, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->valueView:Landroid/widget/TextView;
    invoke-virtual {v0}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    const-string v1, "Enter a valid number"
    const/4 p1, 0x0
    invoke-static {v0, v1, p1}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    return-void
.end method

.method private apply(F)V
    .registers 12
    invoke-direct {p0}, Lcom/wowmancode/customfx/EffectNumberEdit;->displayScale()F
    move-result v0
    div-float/2addr p1, v0
    iget-object v1, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->parameter:Lcom/alightcreative/app/motion/scene/userparam/UserParameter;
    iget-object v2, p0, Lcom/wowmancode/customfx/EffectNumberEdit;->control:Landroid/view/View;
    instance-of v3, v2, Lcom/alightcreative/widget/AlightSlider;
    if-eqz v3, :spinner
    check-cast v1, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Slider;
    check-cast v2, Lcom/alightcreative/widget/AlightSlider;
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Slider;->getMinValue()F
    move-result v3
    invoke-static {p1, v3}, Ljava/lang/Math;->max(FF)F
    move-result p1
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Slider;->getMaxValue()F
    move-result v3
    invoke-static {p1, v3}, Ljava/lang/Math;->min(FF)F
    move-result p1
    const/high16 v3, 0x447a0000
    mul-float/2addr p1, v3
    invoke-static {p1}, Ljava/lang/Math;->round(F)I
    move-result v4
    invoke-virtual {v2}, Lcom/alightcreative/widget/AlightSlider;->getValue()I
    move-result v5
    if-eq v4, v5, :done
    invoke-virtual {v2}, Lcom/alightcreative/widget/AlightSlider;->getOnSeekBarChangeListener()Landroid/widget/SeekBar$OnSeekBarChangeListener;
    move-result-object v5
    if-eqz v5, :done
    const/4 v6, 0x0
    invoke-interface {v5, v6}, Landroid/widget/SeekBar$OnSeekBarChangeListener;->onStartTrackingTouch(Landroid/widget/SeekBar;)V
    invoke-virtual {v2, v4}, Lcom/alightcreative/widget/AlightSlider;->setValue(I)V
    invoke-virtual {v2}, Lcom/alightcreative/widget/AlightSlider;->getValue()I
    move-result v4
    const/4 v7, 0x1
    invoke-interface {v5, v6, v4, v7}, Landroid/widget/SeekBar$OnSeekBarChangeListener;->onProgressChanged(Landroid/widget/SeekBar;IZ)V
    invoke-interface {v5, v6}, Landroid/widget/SeekBar$OnSeekBarChangeListener;->onStopTrackingTouch(Landroid/widget/SeekBar;)V
    goto :done

    :spinner
    check-cast v1, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;
    check-cast v2, Lcom/alightcreative/widget/ValueSpinner;
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;->getMinValue()F
    move-result v3
    invoke-static {p1, v3}, Ljava/lang/Math;->max(FF)F
    move-result p1
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;->getMaxValue()F
    move-result v3
    invoke-static {p1, v3}, Ljava/lang/Math;->min(FF)F
    move-result p1
    invoke-virtual {v1}, Lcom/alightcreative/app/motion/scene/userparam/UserParameter$Spinner;->getStep()F
    move-result v3
    const/4 v4, 0x0
    cmpl-float v4, v3, v4
    if-lez v4, :done
    div-float/2addr p1, v3
    invoke-static {p1}, Ljava/lang/Math;->round(F)I
    move-result v4
    invoke-virtual {v2}, Lcom/alightcreative/widget/ValueSpinner;->getLastSentPos()I
    move-result v5
    if-eq v4, v5, :done
    invoke-virtual {v2}, Lcom/alightcreative/widget/ValueSpinner;->getOnStartTrackingTouch()Lkotlin/jvm/functions/Function0;
    move-result-object v5
    invoke-virtual {v2}, Lcom/alightcreative/widget/ValueSpinner;->getOnSpinAbs()Lkotlin/jvm/functions/Function1;
    move-result-object v6
    invoke-virtual {v2}, Lcom/alightcreative/widget/ValueSpinner;->getOnStopTrackingTouch()Lkotlin/jvm/functions/Function0;
    move-result-object v7
    if-eqz v6, :done
    if-eqz v5, :skip_start
    invoke-interface {v5}, Lkotlin/jvm/functions/Function0;->invoke()Ljava/lang/Object;
    :skip_start
    invoke-virtual {v2, v4}, Lcom/alightcreative/widget/ValueSpinner;->setValue(I)V
    invoke-static {v4}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v8
    invoke-interface {v6, v8}, Lkotlin/jvm/functions/Function1;->invoke(Ljava/lang/Object;)Ljava/lang/Object;
    if-eqz v7, :done
    invoke-interface {v7}, Lkotlin/jvm/functions/Function0;->invoke()Ljava/lang/Object;
    :done
    return-void
.end method
