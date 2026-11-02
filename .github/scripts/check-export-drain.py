#!/usr/bin/env python3
"""Execute the patched encoder-drain smali with deterministic Android API mocks.

Checks queue scheduling, delayed EOS, muxer ordering, pending audio, codec config,
and buffer release. This is a bounded interpreter for this method's instruction
set, not an Android codec/device test. Unknown instructions fail closed.
"""

import re
import sys
from pathlib import Path
from types import SimpleNamespace as Object


class Iterator:
    def __init__(self, values):
        self.values, self.index = values, 0

    def hasNext(self):
        return self.index < len(self.values)

    def next(self):
        value = self.values[self.index]
        self.index += 1
        return value


class Codec:
    def __init__(self, events):
        self.events = list(events)
        self.timeouts, self.released = [], []
        self.signaled = 0

    def signalEndOfInputStream(self):
        self.signaled += 1

    def dequeueOutputBuffer(self, info, timeout, _wide_high):
        self.timeouts.append(timeout)
        assert self.events, 'drain kept waiting after all scripted output was consumed'
        event = self.events.pop(0)
        if isinstance(event, int):
            return event
        index, size, flags = event
        info.offset, info.size, info.flags = 0, size, flags
        return index

    def getOutputFormat(self):
        return Object()

    def getOutputBuffer(self, index):
        return Object(index=index)

    def releaseOutputBuffer(self, index, render):
        assert render == 0
        self.released.append(index)


class Muxer:
    def __init__(self):
        self.started, self.writes = False, []

    def addTrack(self, _format):
        return 7

    def start(self):
        assert not self.started
        self.started = True

    def writeSampleData(self, track, buffer, info):
        assert self.started
        self.writes.append((track, buffer.index, info.size))


def context(events):
    return Object(videoEncoder=Codec(events), muxer=Muxer(), muxerStarted=False,
                  videoTrackIndex=-1, audioTrackIndex=3,
                  pendingAudioEncoderOutputBuffers=[(Object(size=12), Object(index=99))],
                  bufferInfo=Object(offset=0, size=0, flags=0))


def execute(source, state, eos):
    method = re.search(r'^\.method private final drainEncoder\(Z\)V\n.*?^\.end method', source, re.M | re.S)
    assert method, 'missing encoder drain method'
    code = [line.strip() for line in method.group().splitlines()
            if line.strip() and not line.strip().startswith(('.', '#'))]
    labels = {line: index for index, line in enumerate(code) if line.startswith(':')}
    registers = {'p0': state, 'p1': int(eos)}
    pc, result = 0, None
    for _ in range(10000):
        line = code[pc]
        pc += 1
        if line.startswith(':'):
            continue
        op, _, args = line.partition(' ')
        parts = args.split(', ')
        if op.startswith('const'):
            registers[parts[0]] = args.split(', ', 1)[1].strip('"') if op == 'const-string' else int(parts[1], 0)
        elif op in ('move-object', 'move-result', 'move-result-object'):
            registers[parts[0]] = result if op.startswith('move-result') else registers[parts[1]]
        elif op.startswith('iget'):
            registers[parts[0]] = getattr(registers[parts[1]], parts[2].split('->')[1].split(':')[0])
        elif op.startswith('iput'):
            setattr(registers[parts[1]], parts[2].split('->')[1].split(':')[0], registers[parts[0]])
        elif op in ('new-instance', 'sget-object'):
            registers[parts[0]] = Object(type=parts[1])
        elif op.startswith('invoke-'):
            match = re.fullmatch(r'\{([^}]*)\}, (.+)->([^ (]+)\(.*', args)
            assert match, line
            names, owner, name = match.groups()
            values = [registers.get(n) for n in names.split(', ')] if names else []
            if op == 'invoke-static':
                assert owner in ('Lt2/b;', 'Lkotlin/jvm/internal/Intrinsics;'), line
                assert not name.startswith('throw'), line
            elif op == 'invoke-direct':
                if 'RuntimeException' in values[0].type:
                    values[0].message = values[1]
            else:
                receiver, *arguments = values
                if name == 'iterator':
                    result = Iterator(receiver)
                elif name == 'clear':
                    receiver.clear()
                elif name in ('component1', 'component2'):
                    result = receiver[int(name[-1]) - 1]
                elif name in ('position', 'limit'):
                    setattr(receiver, name, arguments[0])
                    result = receiver
                else:
                    result = getattr(receiver, name)(*arguments)
        elif op.startswith('if-'):
            value = registers[parts[0]]
            condition = {'if-eqz': lambda: value == 0,
                         'if-nez': lambda: value != 0,
                         'if-ltz': lambda: value < 0,
                         'if-ne': lambda: value != registers[parts[1]]}[op]()
            if condition:
                pc = labels[parts[-1]]
        elif op.startswith('goto'):
            pc = labels[args]
        elif op == 'and-int/lit8':
            registers[parts[0]] = registers[parts[1]] & int(parts[2], 0)
        elif op == 'add-int/2addr':
            registers[parts[0]] += registers[parts[1]]
        elif op == 'check-cast':
            pass
        elif op == 'throw':
            raise RuntimeError(registers[args].message)
        elif op == 'return-void':
            return
        else:
            raise AssertionError('unsupported instruction: ' + line)
    raise AssertionError('drain did not terminate')


def main():
    files = list(Path(sys.argv[1]).glob('smali*/**/MediaCodecExportContext.smali'))
    assert len(files) == 1
    source = files[0].read_text()
    state = context([-1])
    execute(source, state, False)
    assert state.videoEncoder.timeouts == [0] and state.videoEncoder.signaled == 0

    state = context([-2, -3, (0, 20, 2), (1, 40, 0), (2, 50, 0), -1])
    execute(source, state, False)
    assert state.videoEncoder.timeouts == [0] * 6
    assert state.videoEncoder.released == [0, 1, 2]
    assert state.muxer.writes == [(3, 99, 12), (7, 1, 40), (7, 2, 50)]
    assert state.pendingAudioEncoderOutputBuffers == []

    state = context([-2, -1, (0, 40, 0), -1, (1, 50, 4)])
    execute(source, state, True)
    assert state.videoEncoder.signaled == 1
    assert state.videoEncoder.timeouts == [10000] * 5
    assert state.videoEncoder.released == [0, 1]
    assert state.muxer.writes == [(3, 99, 12), (7, 0, 40), (7, 1, 50)]

    state = context([-2, (0, 40, 0), -1, (1, 50, 0), -1, (2, 0, 4)])
    execute(source, state, False)
    assert state.videoEncoder.released == [0]
    execute(source, state, True)
    assert state.videoEncoder.timeouts == [0] * 3 + [10000] * 3
    assert state.videoEncoder.released == [0, 1, 2]
    assert state.muxer.writes == [(3, 99, 12), (7, 0, 40), (7, 1, 50)]

    try:
        execute(source, context([-2, -2]), False)
    except RuntimeError as error:
        assert str(error) == 'format changed twice'
    else:
        raise AssertionError('duplicate format change must fail')
    print('PASS encoder scheduling: nonblocking frames, ready buffers, audio ordering, delayed EOS, release and format errors')


if __name__ == '__main__':
    main()
