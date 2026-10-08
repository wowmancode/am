.class public Lcom/wowmancode/customfx/CustomEffectsLoader;
.super Ljava/lang/Object;
.source "CustomEffectsLoader.java"


# direct methods
.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method


# Called from the patched VisualEffectKt$initVisualEffects$1 during startup,
# just before the "effects loaded" latch opens. Reads all saved custom
# effects from internal storage and registers them.
.method public static loadAll(Landroid/content/Context;)V
    .registers 12
    # p0 = Context; v10 = loadedVisualEffects map

    :try_start
    invoke-static {}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt;->access$getLoadedVisualEffects$p()Ljava/util/Map;
    move-result-object v10

    invoke-virtual {p0}, Landroid/content/Context;->getFilesDir()Ljava/io/File;
    move-result-object v0
    new-instance v1, Ljava/io/File;
    const-string v2, "custom_effects"
    invoke-direct {v1, v0, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    invoke-virtual {v1}, Ljava/io/File;->exists()Z
    move-result v0
    if-eqz v0, :cond_done

    invoke-virtual {v1}, Ljava/io/File;->listFiles()[Ljava/io/File;
    move-result-object v0
    if-eqz v0, :cond_done

    array-length v2, v0
    const/4 v3, 0x0

    :loop_start
    if-ge v3, v2, :cond_done

    aget-object v4, v0, v3

    invoke-virtual {v4}, Ljava/io/File;->getName()Ljava/lang/String;
    move-result-object v5
    const-string v6, ".json"
    invoke-virtual {v5, v6}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z
    move-result v5
    if-eqz v5, :cond_next

    :try_inner_start
    # Read JSON file
    invoke-static {v4}, Lcom/wowmancode/customfx/CustomEffectsLoader;->readFile(Ljava/io/File;)Ljava/lang/String;
    move-result-object v5
    if-eqz v5, :cond_next

    new-instance v6, Lorg/json/JSONObject;
    invoke-direct {v6, v5}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    const-string v7, "id"
    invoke-virtual {v6, v7}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v7

    const-string v8, "name"
    invoke-virtual {v6, v8}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v8

    const-string v5, "code"
    invoke-virtual {v6, v5}, Lorg/json/JSONObject;->getString(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v5

    # Build effect XML
    invoke-static {v7, v8, v5}, Lcom/wowmancode/customfx/CustomEffectsLoader;->buildEffectXml(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v5

    # Parse it into a VisualEffect
    const/4 v6, 0x0
    invoke-static {v5, v6}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectParserKt;->visualEffectFromXml(Ljava/lang/String;Landroid/net/Uri;)Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffect;
    move-result-object v5

    # Put it in the map
    invoke-interface {v10, v7, v5}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v6, "CustomFX"
    new-instance v8, Ljava/lang/StringBuilder;
    invoke-direct {v8}, Ljava/lang/StringBuilder;-><init>()V
    const-string v9, "Loaded custom effect: "
    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v8, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v7
    invoke-static {v6, v7}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    :try_inner_end
    .catch Ljava/lang/Exception; {:try_inner_start .. :try_inner_end} :catch_inner

    goto :cond_next

    :catch_inner
    move-exception v5
    const-string v6, "CustomFX"
    new-instance v7, Ljava/lang/StringBuilder;
    invoke-direct {v7}, Ljava/lang/StringBuilder;-><init>()V
    const-string v8, "Failed to load custom effect: "
    invoke-virtual {v7, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v4}, Ljava/io/File;->getName()Ljava/lang/String;
    move-result-object v4
    invoke-virtual {v7, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v7}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v4
    invoke-static {v6, v4, v5}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    :cond_next
    add-int/lit8 v3, v3, 0x1
    goto :loop_start

    :cond_done
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_outer

    :catch_outer
    return-void
.end method


# Register a single effect at runtime (called from the JS bridge when saving)
.method public static registerEffect(Ljava/lang/String;Ljava/lang/String;)V
    .registers 6
    # p0 = id, p1 = effect XML string

    :try_start
    const/4 v0, 0x0
    invoke-static {p1, v0}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectParserKt;->visualEffectFromXml(Ljava/lang/String;Landroid/net/Uri;)Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffect;
    move-result-object v0

    invoke-static {}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt;->access$getLoadedVisualEffects$p()Ljava/util/Map;
    move-result-object v1

    invoke-interface {v1, p0, v0}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    const-string v1, "CustomFX"
    new-instance v2, Ljava/lang/StringBuilder;
    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V
    const-string v3, "Registered effect: "
    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v2
    invoke-static {v1, v2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    :catch_0
    return-void
.end method


# Unregister an effect (called when deleting)
.method public static unregisterEffect(Ljava/lang/String;)V
    .registers 3
    # p0 = id

    :try_start
    invoke-static {}, Lcom/alightcreative/app/motion/scene/visualeffect/VisualEffectKt;->access$getLoadedVisualEffects$p()Ljava/util/Map;
    move-result-object v0
    invoke-interface {v0, p0}, Ljava/util/Map;->remove(Ljava/lang/Object;)Ljava/lang/Object;
    :try_end
    .catch Ljava/lang/Exception; {:try_start .. :try_end} :catch_0

    :catch_0
    return-void
.end method


# ---- Helpers ----

.method private static buildEffectXml(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
    .registers 5
    # p0=id, p1=name, p2=glsl code

    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "<?xml version=\'1.0\' encoding=\'UTF-8\' ?>\n<effect id=\""
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v1, "\" name=\""
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    # Escape name
    invoke-static {p1}, Lcom/wowmancode/customfx/CustomEffectsLoader;->xmlEscape(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v1
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v1, "\" category=\"color\" tags=\"custom\">\n    <params>\n        <texture id=\"inputImg\" srcType=\"content\" />\n    </params>\n    <shader type=\"fragment\" precision=\"high\"><![CDATA[\n"
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
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
