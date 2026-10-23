#!/usr/bin/env python3
"""Compile the reviewable 3D UI Java source against exact APK method stubs.

Only helper classes are dexed; app/Android/Kotlin stubs are compile-time only.
All tools are downloaded by pinned SHA-256 into a temporary build cache.
"""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
TOOLS = {
    'android.jar': ('https://repo.maven.apache.org/maven2/com/google/android/android/4.1.1.4/android-4.1.1.4.jar', '84072541cbb711eff89f7277100ff854929a446dba7ceb1b195c340e0b4fd3cb'),
    'kotlin.jar': ('https://repo.maven.apache.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/1.5.31/kotlin-stdlib-1.5.31.jar', '4800ceacb2ec0bb9959a087154b8e35318ead1ea4eba32d4bb1b9734222a7e68'),
    'r8.jar': ('https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.3.37/r8-8.3.37.jar', '59753e70a74f918389cc87f1b7d66b5c0862932559167425708ded159e3de439'),
    'apktool.jar': ('https://github.com/iBotPeaches/Apktool/releases/download/v2.10.0/apktool_2.10.0.jar', 'c0350abbab5314248dfe2ee0c907def4edd14f6faef1f5d372d3d4abd28f0431'),
}
SCENE = 'com/alightcreative/app/motion/scene/'
METHODS = {
    SCENE+'SceneElement': {'getVisualEffects','getVisualEffectOrder','getTransform','copy$default'},
    SCENE+'KeyableTransform': {'getRotation','valueAtTime','copy$default'},
    SCENE+'Transform': {'getLocation','getRotation'},
    SCENE+'Vector2D': {'getX','getY'},
    SCENE+'SceneElementKt': {'fractionalTime'},
    SCENE+'KeyableKt': {'keyable','valueAtTime','copyWithValueForTime'},
    SCENE+'SceneHolder': {'update'},
    SCENE+'userparam/KeyableUserParameterValue': {'<init>','getFloatValue'},
    SCENE+'visualeffect/KeyableVisualEffectRef': {'<init>','getId','getInstanceId','getParameters','getRenderGroup','getLocallyApplied','getHidden','getDisabledRenderGroups'},
    SCENE+'visualeffect/VisualEffectKt': {'nextEffectInstanceId'},
    'com/alightcreative/widget/RotateView': {'setAngle'},
    'i1/z': set(), 'i1/v': {'<init>','b','c'},
    'n2/a': {'a','b','c','d','e','get'},
    'l1/e': {'z','t','w','o','p','c'},
}
PRIMITIVES = {'V':'void','Z':'boolean','B':'byte','S':'short','I':'int','J':'long','F':'float','D':'double','C':'char'}


def types(descriptor):
    return re.findall(r'\[*L[^;]+;|\[*[VZBSIJFDC]', descriptor)


def java_type(descriptor):
    if descriptor.startswith('['): return java_type(descriptor[1:])+'[]'
    return PRIMITIVES.get(descriptor, descriptor[1:-1].replace('/', '.').replace('$', '.'))


def compile_ui(decoded, destination):
    cache = Path(tempfile.gettempdir())/'am-java-tools'
    cache.mkdir(exist_ok=True)
    for name,(url,digest) in TOOLS.items():
        path = cache/name
        if not path.exists(): urllib.request.urlretrieve(url,path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise SystemExit('Tool checksum mismatch: '+name)
    with tempfile.TemporaryDirectory() as temporary:
        work=Path(temporary); stubs=work/'stubs'; classes=work/'classes'; helper=work/'helper'
        classes.mkdir();helper.mkdir()
        required=set(METHODS); sources={}; declarations={}; copies={}
        for cls,names in METHODS.items():
            paths=list(decoded.glob('smali*/'+cls+'.smali'))
            if len(paths)!=1: raise SystemExit('Missing native API: '+cls)
            source=paths[0].read_text(); sources[cls]=source
            interface='.class public interface' in source
            lines=[]
            for flags,name,args,result in re.findall(r'^\.method ([^\n]*?) ([\w$<>]+)\(([^)]*)\)([^\n]+)',source,re.M):
                if name not in names or 'private' in flags or 'synthetic' in flags and name!='copy$default':continue
                if name=='<init>' and ('DefaultConstructorMarker' in args or cls.endswith('KeyableUserParameterValue') and args != 'L'+SCENE+'KeyableFloat;'):continue
                if cls==SCENE+'KeyableKt' and (name=='keyable' and args!='F' or name=='valueAtTime' and args!='L'+SCENE+'Keyable;F'):continue
                descriptors=types(args); alltypes=descriptors+[result]
                required.update(t.lstrip('[')[1:-1] for t in alltypes if t.lstrip('[').startswith('L') and not t.lstrip('[').startswith(('Ljava/','Landroid/','Lkotlin/')))
                params=', '.join(java_type(t)+' p'+str(i) for i,t in enumerate(descriptors))
                method='public '+('static ' if 'static' in flags else '')
                method+=(cls.split('/')[-1] if name=='<init>' else java_type(result)+' '+name)+'('+params+')'
                lines.append(method+(';' if interface else ' { throw new UnsupportedOperationException(); }'))
                if name=='copy$default': copies[cls]=descriptors
            declarations[cls]=('interface' if interface else 'class',lines)
        # Two stable Fragment APIs and the injected public mode bridge.
        declarations['androidx/fragment/app/Fragment']=('class',[
            'public android.view.View getView(){throw new UnsupportedOperationException();}',
            'public android.content.Context getContext(){throw new UnsupportedOperationException();}'])
        declarations['i1/z'][1].extend(['public int custom3dMode(){throw new UnsupportedOperationException();}',
                                        'public void u(){throw new UnsupportedOperationException();}'])
        required.add('androidx/fragment/app/Fragment')
        for cls in sorted(required):
            if cls.startswith(('java/','android/','kotlin/')):continue
            if '$' in cls: continue
            kind,lines=declarations.get(cls,('class',[]))
            parent=' extends androidx.fragment.app.Fragment' if cls=='i1/z' else ''
            if cls=='com/alightcreative/widget/RotateView':
                parent=' extends android.view.View';lines.append('public RotateView(){super(null);}')
            parent+=' implements '+SCENE.replace('/','.')+'Keyable' if cls==SCENE+'KeyableFloat' else ''
            if cls==SCENE+'Keyable':kind='interface'
            if cls==SCENE+'animators/AnimatorOf':
                kind='enum';lines=['Float, Rotate;']
            path=stubs/(cls+'.java');path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text('package '+cls.rsplit('/',1)[0].replace('/','.')+';\npublic '+kind+' '+cls.rsplit('/',1)[-1]+parent+' {\n'+'\n'.join(lines)+'\n}')
        # The native undo transaction is a nested interface.
        path=stubs/'f3/b.java';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('package f3; public class b { public interface a { boolean a(); void b(); } }')
        # Generate immutable copies using the real constructor descriptors,
        # preserving all unrelated fields through Kotlin's default masks.
        def copy(cls,expressions,changed):
            args=copies[cls]; values=[]
            for index,typ in enumerate(args):
                values.append(expressions.get(index, 'false' if typ=='Z' else '0f' if typ=='F' else '0L' if typ=='J' else '0' if typ in PRIMITIVES else 'null'))
            values[-2]=str(~sum(1<<(field-1) for field in changed))
            return cls.replace('/','.')+'.copy$default('+', '.join(values)+')'
        effect_copy=copy(SCENE+'SceneElement',{0:'element',24:'effects',25:'order'},[24,25])
        transform_copy=copy(SCENE+'KeyableTransform',{0:'element.getTransform()',4:'rotation'},[4])
        rotation_copy=copy(SCENE+'SceneElement',{0:'element',6:transform_copy},[6])
        native=work/'Transform3dCopies.java'
        native.write_text('package com.wowmancode.customfx;\nimport com.alightcreative.app.motion.scene.*;\n'
            'final class Transform3dCopies {\nstatic SceneElement effects(SceneElement element, java.util.Map effects, java.util.List order) {return '+effect_copy+';}\n'
            'static SceneElement rotation(SceneElement element, Keyable rotation) {return '+rotation_copy+';}\n}')
        classpath=os.pathsep.join(str(cache/n) for n in ('android.jar','kotlin.jar'))
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-Xlint:-options','-classpath',classpath,'-d',str(classes),*[str(p) for p in stubs.rglob('*.java')]],check=True)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-source','8','-target','8','-Xlint:-options','-classpath',classpath+os.pathsep+str(classes),'-d',str(helper),str(native),str(ROOT/'patch/java/com/wowmancode/customfx/Transform3dUi.java')],check=True)
        dex=work/'dex';dex.mkdir()
        subprocess.run(['java','-cp',str(cache/'r8.jar'),'com.android.tools.r8.D8','--min-api','21','--lib',str(cache/'android.jar'),'--classpath',str(classes),'--classpath',str(cache/'kotlin.jar'),'--output',str(dex),*[str(p) for p in helper.rglob('*.class')]],check=True)
        smali=work/'smali'
        wrapper=work/'Disassemble.java'
        wrapper.write_text('import java.io.File; import com.android.tools.smali.dexlib2.*; import com.android.tools.smali.dexlib2.iface.*; import com.android.tools.smali.baksmali.*; public class Disassemble { public static void main(String[] args) { MultiDexContainer dex= DexFileFactory.loadDexContainer(new File(args[0]),new Opcodes(21,-1)); BaksmaliOptions options=new BaksmaliOptions(); options.parameterRegisters=true; options.localsDirective=true; Baksmali.disassembleDexFile(dex.getEntry((String)dex.getDexEntryNames().get(0)).getDexFile(),new File(args[1]),2,options); }}')
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(cache/'apktool.jar'),'-d',str(classes),str(wrapper)],check=True)
        subprocess.run(['java','-cp',str(classes)+os.pathsep+str(cache/'apktool.jar'),'Disassemble',str(dex/'classes.dex'),str(smali)],check=True)
        import shutil
        for p in smali.rglob('*.smali'):
            target=destination/p.relative_to(smali);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        print('  Compiled 3D transform UI helpers against the native APK API',file=sys.stderr)


if __name__=='__main__':compile_ui(Path(sys.argv[1]),Path(sys.argv[2]))
