#!/usr/bin/env python3
"""Run compiled axis paths through the APK's actual reference-parser smali.

Bounded interpreter with mocked Kotlin reflection/model objects, not a device
test. Native parser control flow and compiled axis serialization/restoration run
unchanged. Unknown instructions/APIs fail closed. Also exercises native nested
animator paths, as those share the same reference parser as easing controls.
"""
import ast
from pathlib import Path
import re
import sys
from types import SimpleNamespace as Obj

SCENE = 'com.alightcreative.app.motion.scene.SceneElement'
UI = 'com/wowmancode/customfx/Transform3dUi'
AXIS = UI + '$AxisLens'
PARAMETERS = ['rotateX', 'rotateY', 'depth']


class VM:
    def __init__(self, decoded):
        self.sources = {str(p.relative_to(base))[:-6]: p.read_text()
                        for base in decoded.glob('smali*') if base.is_dir()
                        for p in base.rglob('*.smali')}
        self.parameters = None
        self.run(UI, '<clinit>')
        assert self.parameters == PARAMETERS
        self.properties = {
            SCENE: {'transform': 'Transform'},
            'Transform': {'rotation': 'Keyable', 'location': 'Keyable'},
            'Keyable': {'animators': 'List'},
            'Animator': {'amount': 'Keyable'},
        }

    def method(self, owner, name):
        match = re.search(r'^\.method [^\n]* '+re.escape(name)+r'\([^\n]*\n(.*?)^\.end method',
                          self.sources[owner], re.M | re.S)
        assert match, (owner, name)
        return match[1]

    def run(self, owner, name, *arguments):
        body = self.method(owner, name)
        # Ignore annotations/debug directives; tested methods have no payloads.
        body = re.sub(r'    \.annotation .*?    \.end annotation', '', body, flags=re.S)
        code = [s.strip() for s in body.splitlines() if s.strip() and not s.strip().startswith(('.', '#'))]
        labels = {s: i for i, s in enumerate(code) if s.startswith(':')}
        registers = {'p'+str(i): v for i, v in enumerate(arguments)}
        result, pc = None, 0
        for _ in range(20000):
            line = code[pc]; pc += 1
            if line.startswith(':'): continue
            op, _, args = line.partition(' ')
            parts = args.split(', ')
            if op == 'const-string': registers[parts[0]] = ast.literal_eval(args.split(', ', 1)[1])
            elif op.startswith('const/') or op == 'const': registers[parts[0]] = int(parts[1], 0)
            elif op == 'const-class': registers[parts[0]] = parts[1][1:-1].replace('/', '.')
            elif op.startswith('move-result'): registers[parts[0]] = result
            elif op.startswith('move-object') or op == 'move': registers[parts[0]] = registers[parts[1]]
            elif op.startswith('iget'): registers[parts[0]] = getattr(registers[parts[1]], parts[2].split('->')[1].split(':')[0])
            elif op.startswith('iput'): setattr(registers[parts[1]], parts[2].split('->')[1].split(':')[0], registers[parts[0]])
            elif op == 'sget-object':
                assert parts[1] == 'L'+UI+';->PARAMETERS:[Ljava/lang/String;'
                registers[parts[0]] = self.parameters
            elif op == 'sput-object':
                assert parts[1] == 'L'+UI+';->PARAMETERS:[Ljava/lang/String;'
                self.parameters = registers[parts[0]]
            elif op == 'instance-of': registers[parts[0]] = getattr(registers[parts[1]], 'owner', None) == parts[2][1:-1]
            elif op == 'array-length': registers[parts[0]] = len(registers[parts[1]])
            elif op == 'aget-object': registers[parts[0]] = registers[parts[1]][registers[parts[2]]]
            elif op == 'filled-new-array': result = [registers[s] for s in args.split('}')[0][1:].split(', ')]
            elif op == 'new-instance': registers[parts[0]] = Obj(owner=parts[1][1:-1], text='')
            elif op.startswith('invoke-'):
                match = re.fullmatch(r'\{([^}]*)\}, L([^;]+);->([^ (]+)\(.*', args)
                assert match, line
                names, target, method = match.groups()
                if ' .. ' in names:
                    first, last = names.split(' .. ')
                    names = ', '.join(first[0]+str(i) for i in range(int(first[1:]), int(last[1:])+1))
                values = [registers[s] for s in names.split(', ')] if names else []
                result = self.invoke(target, method, values, op)
            elif op.startswith('if-'):
                a = registers[parts[0]]
                b = registers[parts[1]] if len(parts) == 3 else 0
                condition = {'if-eqz': lambda: not a, 'if-nez': lambda: bool(a),
                             'if-eq': lambda: a == b, 'if-ne': lambda: a != b,
                             'if-ge': lambda: a >= b}[op]()
                if condition: pc = labels[parts[-1]]
            elif op.startswith('goto'): pc = labels[args]
            elif op == 'add-int/lit8': registers[parts[0]] = registers[parts[1]] + int(parts[2], 0)
            elif op == 'sub-int/2addr': registers[parts[0]] -= registers[parts[1]]
            elif op == 'check-cast': pass
            elif op == 'return-void': return None
            elif op.startswith('return'): return registers[args]
            elif op == 'throw': raise ValueError('unresolvable reference')
            else: raise AssertionError('unsupported instruction: '+line)
        raise AssertionError('reference parser did not terminate')

    def invoke(self, owner, name, v, op):
        if owner in (UI, AXIS) or owner == 'n2/f' and name == 'b':
            return self.run(owner, name, *v)
        if owner == 'kotlin/jvm/internal/Intrinsics':
            if name == 'areEqual': return v[0] == v[1]
            assert name.startswith('checkNotNull'), name
            assert v[0] is not None
            return None
        if owner == 't2/b': assert name == 'c'; return None
        if owner.startswith('n2/f$') and name == '<init>': return None  # debug lambdas
        if owner == 'java/lang/Object' and name == '<init>': return None
        if owner == 'java/lang/StringBuilder':
            if name == '<init>': return None
            if name == 'append': v[0].text += str(v[1]); return v[0]
            if name == 'toString': return v[0].text
        if owner == 'java/lang/String':
            if name == 'equals': return v[0] == v[1]
            if name == 'startsWith': return v[0].startswith(v[1])
            if name == 'length': return len(v[0])
            if name == 'substring': return v[0][v[1]:v[2]]
        if owner == 'java/lang/Class' and name == 'forName':
            if v[0] not in self.properties: raise ValueError('unknown class: '+v[0])
            return v[0]
        if owner == 'kotlin/jvm/internal/Reflection': assert name == 'getOrCreateKotlinClass'; return v[0]
        if owner == 'kotlin/jvm/JvmClassMappingKt': assert name == 'getKotlinClass'; return v[0]
        if owner == 'kotlin/reflect/full/KClasses':
            assert name == 'getMemberProperties'
            return [Obj(name=n, type=t) for n, t in self.properties[v[0]].items()]
        if owner == 'kotlin/reflect/KCallable':
            return v[0].name if name == 'getName' else v[0].type
        if owner == 'kotlin/reflect/KType' and name == 'getClassifier': return v[0]
        if owner == 'kotlin/reflect/KType' and name == 'getArguments': return ['Animator']
        if owner == 'kotlin/reflect/KTypeProjection': assert name == 'getType'; return v[0]
        if owner == 'kotlin/text/StringsKt':
            if name in ('split$default', 'splitToSequence$default'): return v[0].split(v[1][0], v[4]-1 if name == 'split$default' else -1)
            if name == 'startsWith$default': return v[0].startswith(chr(v[1]))
            if name == 'endsWith$default': return v[0].endswith(chr(v[1]) if isinstance(v[1], int) else v[1])
            if name == 'firstOrNull': return ord(v[0][0]) if v[0] else None
        if owner == 'kotlin/sequences/SequencesKt':
            if name == 'first': return v[0][0]
            if name == 'drop': return v[0][v[1]:]
        if name == 'get' and isinstance(v[0], list): return v[0][v[1]]
        if name == 'iterator': return iter(v[0])
        if name == 'hasNext':
            # Buffered iterator avoids consuming the next item.
            if not isinstance(v[0], Buffered):
                raise AssertionError('iterator must be buffered')
            return v[0].has_next()
        if name == 'next': return next(v[0])
        if owner == 'java/lang/Character' and name == 'charValue': return v[0]
        if owner == 'java/lang/Integer' and name == 'parseInt': return int(v[0])
        if owner == 'n2/b' and name == '<init>':
            v[0].type, v[0].path = v[2], SCENE+'::'+v[3].name
            return None
        if owner == 'n2/h' and name == '<init>':
            v[0].type, v[0].path = v[2], self.serialize(v[3])+'.'+v[4].name
            return None
        if owner == 'n2/c' and name == '<init>':
            v[0].type, v[0].path = v[2], self.serialize(v[3])+'.['+str(v[4])+']'
            return None
        if owner == 'n2/a' and name == 'e':
            return self.run(AXIS, 'e', v[0]) if v[0].owner == AXIS else v[0].type
        raise AssertionError(('unsupported API', owner, name))

    def serialize(self, lens):
        return self.run(AXIS, 'toString', lens) if lens.owner == AXIS else lens.path


class Buffered:
    def __init__(self, values): self.values, self.index = list(values), 0
    def has_next(self): return self.index < len(self.values)
    def __next__(self):
        value = self.values[self.index]; self.index += 1
        return value


def main():
    vm = VM(Path(sys.argv[1]))
    original_invoke = vm.invoke
    def invoke(owner, name, values, op):
        if name == 'iterator': return Buffered(values[0])
        if owner == UI and name == 'access$000': return vm.parameters
        return original_invoke(owner, name, values, op)
    vm.invoke = invoke
    factory = vm.sources['i1/a$a']
    assert 'Ljava/lang/Object;->toString()Ljava/lang/String;' in factory
    assert 'Landroid/os/Bundle;->putStringArray' in factory
    assert 'Ln2/f;->b(Ljava/lang/String;)Ln2/a;' in vm.method('i1/a', 'onCreate')
    count = 0
    for axis in range(3):
        lens = Obj(owner=AXIS)
        vm.run(AXIS, '<init>', lens, axis, 'Keyable')
        path = vm.serialize(lens)
        for suffix in ('', '.animators.[0]', '.animators.[2].amount'):
            restored = vm.run('n2/f', 'b', path+suffix)
            assert vm.serialize(restored) == path+suffix
            if not suffix:
                assert restored.axis == axis and vm.run(AXIS, 'e', restored) == 'Keyable'
                assert vm.run(AXIS, 'equals', lens, restored)
            count += 1
    # Existing paths still take the original reflection branch.
    for path in (SCENE+'::transform.rotation', SCENE+'::transform.location',
                 SCENE+'::transform.rotation.animators.[0]'):
        assert vm.serialize(vm.run('n2/f', 'b', path)) == path
        count += 1
    # The previous Object.toString format reproduces the reported failure.
    try: vm.run('n2/f', 'b', 'com.wowmancode.customfx.Transform3dUi$AxisLens@1234')
    except (ValueError, IndexError): pass
    else: raise AssertionError('old nonserializable binding unexpectedly restored')
    for bad in (SCENE+'::transform.__custom3d_depthExtra', 'other::transform.__custom3d_depth'):
        assert not vm.run(UI, 'restoreAxis', bad, '__custom3d_depth')
    print(f'PASS 3D keyframe references: {count} native parser round trips, nested animators, axis identity, old crash and scope guards')


if __name__ == '__main__': main()
