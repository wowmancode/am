.class public Lcom/wowmancode/customfx/CustomEffectsBridge;
.super Ljava/lang/Object;
.source "CustomEffectsBridge.java"


# instance fields
.field private ctx:Landroid/content/Context;
.field private act:Landroid/app/Activity;
.field private dlg:Landroid/app/Dialog;


# direct methods
.method public constructor <init>(Landroid/app/Activity;Landroid/app/Dialog;)V
    .registers 3
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->ctx:Landroid/content/Context;
    iput-object p1, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->act:Landroid/app/Activity;
    iput-object p2, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->dlg:Landroid/app/Dialog;
    return-void
.end method

.method private getStorageDir()Ljava/io/File;
    .registers 4
    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->ctx:Landroid/content/Context;
    invoke-virtual {v0}, Landroid/content/Context;->getFilesDir()Ljava/io/File;
    move-result-object v0
    new-instance v1, Ljava/io/File;
    const-string v2, "custom_effects"
    invoke-direct {v1, v0, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/io/File;->mkdirs()Z
    return-object v1
.end method

.method private buildEffectXml(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 6
    # p1=id, p2=name, p3=glsl code
    # Build a complete effect XML string

    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "<?xml version=\'1.0\' encoding=\'UTF-8\' ?>\n<effect id=\""
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v1, "\" name=\""
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    # Escape name for XML
    invoke-static {p2}, Lcom/wowmancode/customfx/CustomEffectsBridge;->xmlEscape(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v1
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v1, "\" category=\"color\" tags=\"custom\">\n    <params>\n        <texture id=\"inputImg\" srcType=\"content\" />\n    </params>\n    <shader type=\"fragment\" precision=\"high\"><![CDATA[\n"
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v1, "\n    ]]></shader>\n</effect>\n"
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method

.method private static xmlEscape(Ljava/lang/String;)Ljava/lang/String;
    .registers 3
    const-string v0, "&"
    const-string v1, "&amp;"
    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object p0
    const-string v0, "\""
    const-string v1, "&quot;"
    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object p0
    const-string v0, "<"
    const-string v1, "&lt;"
    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object p0
    const-string v0, ">"
    const-string v1, "&gt;"
    invoke-virtual {p0, v0, v1}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;
    move-result-object p0
    return-object p0
.end method


# ---- JavaScript Interface Methods ----

.method public loadEffects()Ljava/lang/String;
    .registers 9
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    # Read all .json files from custom_effects directory
    invoke-direct {p0}, Lcom/wowmancode/customfx/CustomEffectsBridge;->getStorageDir()Ljava/io/File;
    move-result-object v0

    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    const-string v2, "["
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/io/File;->listFiles()[Ljava/io/File;
    move-result-object v2

    if-eqz v2, :cond_done

    const/4 v3, 0x0
    array-length v4, v2
    # v5: whether an entry has been written (for commas)
    const/4 v5, 0x0

    :loop_start
    if-ge v3, v4, :cond_done

    aget-object v6, v2, v3

    invoke-virtual {v6}, Ljava/io/File;->getName()Ljava/lang/String;
    move-result-object v7
    const-string v6, ".json"
    invoke-virtual {v7, v6}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v6
    if-eqz v6, :cond_next

    # Read the file
    :try_start
    aget-object v6, v2, v3
    invoke-static {v6}, Lcom/wowmancode/customfx/CustomEffectsBridge;->readFile(Ljava/io/File;)Ljava/lang/String;
    move-result-object v6

    if-eqz v6, :cond_next

    if-eqz v5, :no_comma
    const-string v7, ","
    invoke-virtual {v1, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    :no_comma
    invoke-virtual {v1, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const/4 v5, 0x1
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :cond_next

    :cond_next
    add-int/lit8 v3, v3, 0x1
    goto :loop_start

    :cond_done
    const-string v2, "]"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method


.method public saveEffect(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Z
    .registers 10
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation
    # p1=id, p2=name, p3=editable code, p4=generated effect XML

    :try_start
    # Save the metadata JSON
    invoke-direct {p0}, Lcom/wowmancode/customfx/CustomEffectsBridge;->getStorageDir()Ljava/io/File;
    move-result-object v0

    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v2, ".json"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v1

    new-instance v2, Ljava/io/File;
    invoke-direct {v2, v0, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    # Store both the editable source and generated XML. Keeping the XML makes
    # detected slider parameters survive an app restart.
    new-instance v3, Lorg/json/JSONObject;
    invoke-direct {v3}, Lorg/json/JSONObject;-><init>()V
    const-string v4, "id"
    invoke-virtual {v3, v4, p1}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    const-string v4, "name"
    invoke-virtual {v3, v4, p2}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    const-string v4, "code"
    invoke-virtual {v3, v4, p3}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;
    const-string v4, "xml"
    invoke-virtual {v3, v4, p4}, Lorg/json/JSONObject;->put(Ljava/lang/String;Ljava/lang/Object;)Lorg/json/JSONObject;

    invoke-virtual {v3}, Lorg/json/JSONObject;->toString()Ljava/lang/String;
    move-result-object v3
    invoke-static {v2, v3}, Lcom/wowmancode/customfx/CustomEffectsBridge;->writeFile(Ljava/io/File;Ljava/lang/String;)V

    # Register the generated effect, including any detected slider params.
    invoke-static {p1, p4}, Lcom/wowmancode/customfx/CustomEffectsLoader;->registerEffect(Ljava/lang/String;Ljava/lang/String;)Z
    move-result v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    return v0

    :catch_0
    move-exception v0
    const-string v1, "CustomFX"
    const-string v2, "Failed to save custom effect"
    invoke-static {v1, v2, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    const/4 v0, 0x0
    return v0
.end method


.method public deleteEffect(Ljava/lang/String;)V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    :try_start
    invoke-direct {p0}, Lcom/wowmancode/customfx/CustomEffectsBridge;->getStorageDir()Ljava/io/File;
    move-result-object v0

    # Delete .json file
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v2, ".json"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v1

    new-instance v2, Ljava/io/File;
    invoke-direct {v2, v0, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V
    invoke-virtual {v2}, Ljava/io/File;->delete()Z

    # Unregister from effect map
    invoke-static {p1}, Lcom/wowmancode/customfx/CustomEffectsLoader;->unregisterEffect(Ljava/lang/String;)V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    :catch_0
    return-void
.end method


.method public applyEffect(Ljava/lang/String;)V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    const/4 v0, 0x2
    iget-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->act:Landroid/app/Activity;
    iget-object v2, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->dlg:Landroid/app/Dialog;
    invoke-static {v0, v1, v2, p1}, Lcom/wowmancode/customfx/CustomEffectsUi;->post(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    return-void
.end method




.method public exportPack(Ljava/lang/String;)V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    # Share via Android share intent
    :try_start
    new-instance v0, Landroid/content/Intent;
    const-string v1, "android.intent.action.SEND"
    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    const-string v1, "text/plain"
    invoke-virtual {v0, v1}, Landroid/content/Intent;->setType(Ljava/lang/String;)Landroid/content/Intent;

    const-string v1, "android.intent.extra.TEXT"
    invoke-virtual {v0, v1, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const-string v1, "android.intent.extra.SUBJECT"
    const-string v2, "Custom Effects Pack"
    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const-string v1, "Share Effect Pack"
    invoke-static {v0, v1}, Landroid/content/Intent;->createChooser(Landroid/content/Intent;Ljava/lang/CharSequence;)Landroid/content/Intent;
    move-result-object v0

    iget-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->ctx:Landroid/content/Context;
    invoke-virtual {v1, v0}, Landroid/content/Context;->startActivity(Landroid/content/Intent;)V
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    :catch_0
    return-void
.end method


.method public importPack()Ljava/lang/String;
    .registers 4
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    # Try to read from clipboard
    :try_start
    iget-object v0, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->ctx:Landroid/content/Context;
    const-string v1, "clipboard"
    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;
    move-result-object v0
    check-cast v0, Landroid/content/ClipboardManager;

    invoke-virtual {v0}, Landroid/content/ClipboardManager;->hasPrimaryClip()Z
    move-result v1
    if-eqz v1, :ret_null

    invoke-virtual {v0}, Landroid/content/ClipboardManager;->getPrimaryClip()Landroid/content/ClipData;
    move-result-object v0
    if-eqz v0, :ret_null

    invoke-virtual {v0}, Landroid/content/ClipData;->getItemCount()I
    move-result v1
    if-lez v1, :ret_null

    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/content/ClipData;->getItemAt(I)Landroid/content/ClipData$Item;
    move-result-object v0

    invoke-virtual {v0}, Landroid/content/ClipData$Item;->getText()Ljava/lang/CharSequence;
    move-result-object v0
    if-eqz v0, :ret_null

    invoke-virtual {v0}, Ljava/lang/Object;->toString()Ljava/lang/String;
    move-result-object v0

    # Check if it looks like JSON
    const-string v1, "{"
    invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :ret_null

    return-object v0
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :ret_null

    :ret_null
    const/4 v0, 0x0
    return-object v0
.end method


.method public getPreviewImage()Ljava/lang/String;
    .registers 2
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation
    # Return null — the HTML will generate a test pattern
    const/4 v0, 0x0
    return-object v0
.end method


.method public showToast(Ljava/lang/String;)V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    const/4 v0, 0x0
    iget-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->act:Landroid/app/Activity;
    const/4 v2, 0x0
    invoke-static {v0, v1, v2, p1}, Lcom/wowmancode/customfx/CustomEffectsUi;->post(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    return-void
.end method


.method public close()V
    .registers 5
    .annotation runtime Landroid/webkit/JavascriptInterface;
    .end annotation

    const/4 v0, 0x1
    iget-object v1, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->act:Landroid/app/Activity;
    iget-object v2, p0, Lcom/wowmancode/customfx/CustomEffectsBridge;->dlg:Landroid/app/Dialog;
    const/4 v3, 0x0
    invoke-static {v0, v1, v2, v3}, Lcom/wowmancode/customfx/CustomEffectsUi;->post(ILandroid/app/Activity;Landroid/app/Dialog;Ljava/lang/String;)V
    return-void
.end method


# ---- Static file helpers ----

.method private static readFile(Ljava/io/File;)Ljava/lang/String;
    .registers 5

    new-instance v0, Ljava/io/BufferedReader;
    new-instance v1, Ljava/io/FileReader;
    invoke-direct {v1, p0}, Ljava/io/FileReader;-><init>(Ljava/io/File;)V
    invoke-direct {v0, v1}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V

    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    :loop
    invoke-virtual {v0}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;
    move-result-object v2
    if-eqz v2, :done
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v3, "\n"
    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    goto :loop

    :done
    invoke-virtual {v0}, Ljava/io/BufferedReader;->close()V
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method


.method private static writeFile(Ljava/io/File;Ljava/lang/String;)V
    .registers 4

    new-instance v0, Ljava/io/FileWriter;
    invoke-direct {v0, p0}, Ljava/io/FileWriter;-><init>(Ljava/io/File;)V
    invoke-virtual {v0, p1}, Ljava/io/Writer;->write(Ljava/lang/String;)V
    invoke-virtual {v0}, Ljava/io/Writer;->flush()V
    invoke-virtual {v0}, Ljava/io/Writer;->close()V
    return-void
.end method
