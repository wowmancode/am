.class public Lcom/wowmancode/customfx/CustomEffectsActivity;
.super Landroid/app/Activity;
.source "CustomEffectsActivity.java"


# instance fields
.field private webView:Landroid/webkit/WebView;


# direct methods
.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V
    return-void
.end method


# virtual methods
.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6

    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    # Create a FrameLayout as root
    new-instance v0, Landroid/widget/FrameLayout;
    invoke-direct {v0, p0}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;)V

    # Create the WebView
    new-instance v1, Landroid/webkit/WebView;
    invoke-direct {v1, p0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsActivity;->webView:Landroid/webkit/WebView;

    # LayoutParams: MATCH_PARENT, MATCH_PARENT
    new-instance v2, Landroid/widget/FrameLayout$LayoutParams;
    const/4 v3, -0x1
    const/4 v4, -0x1
    invoke-direct {v2, v3, v4}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V
    invoke-virtual {v0, v1, v2}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    invoke-virtual {p0, v0}, Landroid/app/Activity;->setContentView(Landroid/view/View;)V

    # Configure WebView settings
    invoke-virtual {v1}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v2

    const/4 v3, 0x1
    invoke-virtual {v2, v3}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v2, v3}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    invoke-virtual {v2, v3}, Landroid/webkit/WebSettings;->setAllowFileAccess(Z)V

    # Add JavaScript interface bridge
    new-instance v2, Lcom/wowmancode/customfx/CustomEffectsBridge;
    invoke-direct {v2, p0}, Lcom/wowmancode/customfx/CustomEffectsBridge;-><init>(Landroid/content/Context;)V
    const-string v3, "Android"
    invoke-virtual {v1, v2, v3}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    # Load the editor HTML from assets
    const-string v2, "file:///android_asset/custom_effects_editor.html"
    invoke-virtual {v1, v2}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    return-void
.end method

.method public onBackPressed()V
    .registers 3

    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsActivity;->webView:Landroid/webkit/WebView;

    # Check if editor panel is visible; let JS handle back if so
    const-string v1, "javascript:if(document.getElementById('panelEditor').style.display==='flex'){backToList();}else{Android.finishActivity();}"
    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    return-void
.end method

.method public onDestroy()V
    .registers 2

    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsActivity;->webView:Landroid/webkit/WebView;
    if-eqz v0, :cond_0
    invoke-virtual {v0}, Landroid/webkit/WebView;->destroy()V

    :cond_0
    invoke-super {p0}, Landroid/app/Activity;->onDestroy()V
    return-void
.end method
