#!/usr/bin/env python3
"""Reject native API linkage errors in the compiled 3D UI helper classes."""
import re
import sys
from pathlib import Path


def check(decoded):
    index={str(p.relative_to(base))[:-6]:p for base in decoded.glob('smali*')
           if base.is_dir() for p in base.rglob('*.smali')}
    helpers=[p for name,p in index.items() if name.startswith('com/wowmancode/customfx/Transform3d')]
    assert len(helpers)>=9, 'missing compiled 3D helpers'
    count=0
    for path in helpers:
        for opcode,owner,signature in re.findall(r'(invoke-[\w/]+) \{[^}]*\}, L([^;]+);->([^\n]+)',path.read_text()):
            if not owner.startswith(('com/alightcreative/','i1/','l1/','n2/','f3/')):continue
            cls=owner
            while cls in index:
                source=index[cls].read_text()
                match=re.search(r'^\.method ([^\n]*?) '+re.escape(signature)+r'$',source,re.M)
                if match:
                    assert 'public' in match[1], (path.name,owner,signature,'inaccessible API')
                    assert ('static' in match[1])==opcode.startswith('invoke-static'),(owner,signature,'static mismatch')
                    assert ('.class public interface' in source)==opcode.startswith('invoke-interface'),(owner,signature,'interface mismatch')
                    count+=1
                    break
                parent=re.search(r'^\.super L([^;]+);',source,re.M)
                cls=parent[1] if parent else ''
            else:raise AssertionError((path.name,owner,signature,'missing native API'))
    print(f'PASS 3D UI native linkage: {len(helpers)} helper classes, {count} native calls',file=sys.stderr)


if __name__=='__main__':check(Path(sys.argv[1]))
