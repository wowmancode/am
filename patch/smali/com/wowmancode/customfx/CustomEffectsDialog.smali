.class public Lcom/wowmancode/customfx/CustomEffectsDialog;
.super Landroid/app/Dialog;
.source "CustomEffectsDialog.java"


# A full-screen dialog over the effect browser that hosts the editor in a
# WebView. Being a dialog rather than an activity, it needs no manifest entry.

.field private final act:Landroid/app/Activity;
.field private webView:Landroid/webkit/WebView;


.method public constructor <init>(Landroid/app/Activity;)V
    .registers 3
    # android.R.style.Theme_Black_NoTitleBar
    const v0, 0x1030009
    invoke-direct {p0, p1, v0}, Landroid/app/Dialog;-><init>(Landroid/content/Context;I)V
    iput-object p1, p0, Lcom/wowmancode/customfx/CustomEffectsDialog;->act:Landroid/app/Activity;
    return-void
.end method


.method protected onCreate(Landroid/os/Bundle;)V
    .registers 6

    invoke-super {p0, p1}, Landroid/app/Dialog;->onCreate(Landroid/os/Bundle;)V

    invoke-virtual {p0}, Landroid/app/Dialog;->getWindow()Landroid/view/Window;
    move-result-object v0
    if-eqz v0, :no_window
    const/4 v1, -0x1
    invoke-virtual {v0, v1, v1}, Landroid/view/Window;->setLayout(II)V
    # SOFT_INPUT_ADJUST_RESIZE so the keyboard doesn't cover the code
    const/16 v1, 0x10
    invoke-virtual {v0, v1}, Landroid/view/Window;->setSoftInputMode(I)V

    :no_window
    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsDialog;->act:Landroid/app/Activity;

    new-instance v1, Landroid/webkit/WebView;
    invoke-direct {v1, v0}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V
    iput-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsDialog;->webView:Landroid/webkit/WebView;

    invoke-virtual {v1}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;
    move-result-object v2
    const/4 v3, 0x1
    invoke-virtual {v2, v3}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V
    invoke-virtual {v2, v3}, Landroid/webkit/WebSettings;->setDomStorageEnabled(Z)V
    invoke-virtual {v2, v3}, Landroid/webkit/WebSettings;->setAllowFileAccess(Z)V

    new-instance v2, Lcom/wowmancode/customfx/CustomEffectsBridge;
    invoke-direct {v2, v0, p0}, Lcom/wowmancode/customfx/CustomEffectsBridge;-><init>(Landroid/app/Activity;Landroid/app/Dialog;)V
    const-string v3, "Android"
    invoke-virtual {v1, v2, v3}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    const-string v2, "file:///android_asset/custom_effects_editor.html"
    invoke-virtual {v1, v2}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V

    invoke-virtual {p0, v1}, Landroid/app/Dialog;->setContentView(Landroid/view/View;)V
    return-void
.end method


# Back goes from the editor to the list, and from the list closes the dialog.
.method public onBackPressed()V
    .registers 4

    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsDialog;->webView:Landroid/webkit/WebView;
    if-nez v0, :has_view
    invoke-virtual {p0}, Landroid/app/Dialog;->dismiss()V
    return-void

    :has_view
    const-string v1, "if(document.getElementById('panelEditor').style.display==='flex'){backToList();}else{Android.close();}"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/webkit/WebView;->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V
    return-void
.end method


.method protected onStop()V
    .registers 2

    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsDialog;->webView:Landroid/webkit/WebView;
    if-eqz v0, :done
    invoke-virtual {v0}, Landroid/webkit/WebView;->destroy()V
    const/4 v0, 0x0
    iput-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsDialog;->webView:Landroid/webkit/WebView;

    :done
    invoke-super {p0}, Landroid/app/Dialog;->onStop()V
    return-void
.end method
