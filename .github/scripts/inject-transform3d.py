#!/usr/bin/env python3
"""Bind 3D axes into the existing Move & Transform fragment and controls."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys


def main(decoded):
    def find(relative):
        paths=list(decoded.glob('smali*/'+relative+'.smali'))
        if len(paths)!=1:raise SystemExit('Native 3D hook target changed: '+relative)
        return paths[0]
    def method(text,name):
        match=re.search(r'^\.method [^\n]* '+re.escape(name)+r'\([^\n]*\n.*?^\.end method',text,re.M|re.S)
        if not match:raise SystemExit('Native 3D hook method changed: '+name)
        return match
    fragment=find('i1/z');text=fragment.read_text()
    for name,action in [('onViewCreated','attach'),('K','refresh'),('L','refresh')]:
        match=method(text,name);body=match.group()
        hook='    invoke-static {p0}, Lcom/wowmancode/customfx/Transform3dUi;->'+action+'(Li1/z;)V\n\n    '
        if hook.strip() not in body:
            at=body.rfind('return-void')
            if at<0:raise SystemExit('No return in '+name)
            body=body[:at]+hook+body[at:]
            text=text[:match.start()]+body+text[match.end():]
    match=method(text,'a0');body=match.group()
    if 'Transform3dUi;->bindings' not in body:
        anchor='    return-object v0'
        if body.count(anchor)!=1:raise SystemExit('Native transform bindings changed')
        body=body.replace(anchor,'    invoke-static {p0, v0}, Lcom/wowmancode/customfx/Transform3dUi;->bindings(Li1/z;Ljava/util/List;)Ljava/util/List;\n    move-result-object v0\n\n'+anchor)
        text=text[:match.start()]+body+text[match.end():]
    if 'custom3dMode()I' not in text:
        text+='\n.method public custom3dMode()I\n    .locals 1\n    invoke-virtual {p0}, Li1/b0;->y()I\n    move-result v0\n    return v0\n.end method\n'
    fragment.write_text(text)
    angle=find('i1/z$n');text=angle.read_text()
    if 'Transform3dUi;->onAngle' not in text:
        anchor='    invoke-static {v1}, Ll1/e;->z(Landroidx/fragment/app/Fragment;)Lcom/alightcreative/app/motion/scene/SceneElement;'
        if text.count(anchor)!=1:raise SystemExit('Native rotate callback changed')
        text=text.replace(anchor,'    move/from16 v2, p1\n'
            '    invoke-static {v1, v2}, Lcom/wowmancode/customfx/Transform3dUi;->onAngle(Li1/z;F)Z\n'
            '    move-result v2\n    if-eqz v2, :transform3d_native_z\n    return-void\n'
            '    :transform3d_native_z\n\n'+anchor)
        angle.write_text(text)
    motion=find('i1/z$t');text=motion.read_text()
    if 'Transform3dUi;->depthDrag' not in text:
        anchor='    const-string v4, "scene"'
        if text.count(anchor)!=1:raise SystemExit('Native move callback changed')
        text=text.replace(anchor,'    move-object/from16 v4, p0\n'
            '    iget-object v4, v4, Li1/z$t;->c:Li1/z;\n'
            '    invoke-static {v4, v0, v2, v3}, Lcom/wowmancode/customfx/Transform3dUi;->depthDrag(Li1/z;Lcom/alightcreative/app/motion/scene/Scene;Lcom/alightcreative/app/motion/scene/SceneElement;Lcom/alightcreative/app/motion/scene/Vector2D;)Lcom/alightcreative/app/motion/scene/SceneElement;\n'
            '    move-result-object v4\n    if-eqz v4, :transform3d_native_xy\n    return-object v4\n'
            '    :transform3d_native_xy\n\n'+anchor)
        motion.write_text(text)
    snaps=find('i1/z$s');text=snaps.read_text()
    if 'Transform3dUi;->isDepth' not in text:
        anchor='    const-string v3, "scene"'
        if text.count(anchor)!=1:raise SystemExit('Native move snapping changed')
        text=text.replace(anchor,'    iget-object v3, v0, Li1/z$s;->c:Li1/z;\n'
            '    invoke-static {v3}, Lcom/wowmancode/customfx/Transform3dUi;->isDepth(Li1/z;)Z\n'
            '    move-result v3\n    if-eqz v3, :transform3d_native_snaps\n'
            '    invoke-static {}, Ljava/util/Collections;->emptyList()Ljava/util/List;\n'
            '    move-result-object v3\n    return-object v3\n    :transform3d_native_snaps\n\n'+anchor)
        snaps.write_text(text)
    loader=importlib.util.spec_from_file_location('transform3d_build',Path(__file__).with_name('build-transform3d-ui.py'))
    build=importlib.util.module_from_spec(loader);loader.loader.exec_module(build)
    target=find('com/wowmancode/customfx/CustomEffectsUi').parents[3]
    build.compile_ui(decoded,target)
    subprocess.run([sys.executable, str(Path(__file__).with_name('check-transform3d-bindings.py')), str(decoded)], check=True, stdout=sys.stderr)
    print('  Added native Move & Transform XYZ controls and keyframe bindings',file=sys.stderr)


if __name__=='__main__':main(Path(sys.argv[1]))
