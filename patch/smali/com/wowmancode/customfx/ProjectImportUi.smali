.class public Lcom/wowmancode/customfx/ProjectImportUi;
.super Ljava/lang/Object;
.implements Landroid/view/View$OnClickListener;
.source "ProjectImportUi.java"

.field private static final REQUEST_XML:I = 0x4a4d

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static attachButton(Landroid/app/Activity;)V
    .registers 11
    const v0, 0x1020002
    invoke-virtual {p0, v0}, Landroid/app/Activity;->findViewById(I)Landroid/view/View;
    move-result-object v0
    instance-of v1, v0, Landroid/widget/FrameLayout;
    if-eqz v1, :done
    check-cast v0, Landroid/widget/FrameLayout;

    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;
    move-result-object v1
    invoke-virtual {v1}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;
    move-result-object v1
    iget v1, v1, Landroid/util/DisplayMetrics;->density:F
    const/high16 v2, 0x42400000
    mul-float v2, v2, v1
    float-to-int v2, v2
    const/high16 v3, 0x41800000
    mul-float v3, v3, v1
    float-to-int v3, v3
    const/high16 v4, 0x42c00000
    mul-float v4, v4, v1
    float-to-int v4, v4

    new-instance v5, Landroid/widget/TextView;
    invoke-direct {v5, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    const-string v6, "Import Project XML"
    invoke-virtual {v5, v6}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    const/16 v6, 0x11
    invoke-virtual {v5, v6}, Landroid/widget/TextView;->setGravity(I)V
    const/4 v6, -0x1
    invoke-virtual {v5, v6}, Landroid/widget/TextView;->setTextColor(I)V
    const/high16 v6, 0x41600000
    invoke-virtual {v5, v6}, Landroid/widget/TextView;->setTextSize(F)V
    const v6, -0x5cd27b
    invoke-virtual {v5, v6}, Landroid/view/View;->setBackgroundColor(I)V
    invoke-virtual {v5, v3, v3, v3, v3}, Landroid/view/View;->setPadding(IIII)V
    new-instance v6, Lcom/wowmancode/customfx/ProjectImportUi;
    invoke-direct {v6}, Lcom/wowmancode/customfx/ProjectImportUi;-><init>()V
    invoke-virtual {v5, v6}, Landroid/view/View;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    new-instance v6, Landroid/widget/FrameLayout$LayoutParams;
    const/4 v7, -0x2
    invoke-direct {v6, v7, v2}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V
    const v7, 0x800055
    iput v7, v6, Landroid/widget/FrameLayout$LayoutParams;->gravity:I
    iput v3, v6, Landroid/view/ViewGroup$MarginLayoutParams;->rightMargin:I
    iput v4, v6, Landroid/view/ViewGroup$MarginLayoutParams;->bottomMargin:I
    invoke-virtual {v0, v5, v6}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    :done
    return-void
.end method

.method public onClick(Landroid/view/View;)V
    .registers 5
    invoke-virtual {p1}, Landroid/view/View;->getContext()Landroid/content/Context;
    move-result-object v0
    check-cast v0, Landroid/app/Activity;
    new-instance v1, Landroid/content/Intent;
    const-string v2, "android.intent.action.OPEN_DOCUMENT"
    invoke-direct {v1, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V
    const-string v2, "android.intent.category.OPENABLE"
    invoke-virtual {v1, v2}, Landroid/content/Intent;->addCategory(Ljava/lang/String;)Landroid/content/Intent;
    const-string v2, "*/*"
    invoke-virtual {v1, v2}, Landroid/content/Intent;->setType(Ljava/lang/String;)Landroid/content/Intent;
    const v2, 0x4a4d
    invoke-virtual {v0, v1, v2}, Landroid/app/Activity;->startActivityForResult(Landroid/content/Intent;I)V
    return-void
.end method

# The app's ImportActivity already parses native project XML. Force text/xml
# because document providers often report application/xml or octet-stream.
.method public static onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)Z
    .registers 7
    const v0, 0x4a4d
    if-ne p1, v0, :not_ours
    const/4 v0, -0x1
    if-ne p2, v0, :handled
    if-eqz p3, :handled
    invoke-virtual {p3}, Landroid/content/Intent;->getData()Landroid/net/Uri;
    move-result-object v0
    if-eqz v0, :handled
    new-instance v1, Landroid/content/Intent;
    const-class v2, Lcom/alightcreative/app/motion/activities/ImportActivity;
    invoke-direct {v1, p0, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    const-string v2, "text/xml"
    invoke-virtual {v1, v0, v2}, Landroid/content/Intent;->setDataAndType(Landroid/net/Uri;Ljava/lang/String;)Landroid/content/Intent;
    const/4 v0, 0x1
    invoke-virtual {v1, v0}, Landroid/content/Intent;->addFlags(I)Landroid/content/Intent;
    invoke-virtual {p0, v1}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V
    :handled
    const/4 v0, 0x1
    return v0
    :not_ours
    const/4 v0, 0x0
    return v0
.end method
