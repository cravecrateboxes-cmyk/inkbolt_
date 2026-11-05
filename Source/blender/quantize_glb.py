#!/usr/bin/env python3
"""KHR_mesh_quantization pass for INKBOLT GLBs (brief 3.4). Pure Python, no dependencies.

    python3 quantize_glb.py in.glb [out.glb]      (default: in place)

  NORMAL      float32 x3 -> int8 normalized (stride 4)
  TEXCOORD_0  float32 x2 -> uint16 normalized          (palette UVs live in [0,1])
  COLOR_0     any       -> uint8 normalized x4
  WEIGHTS_0   float32 x4 -> uint8 normalized
  _HULL       float32 x3 -> int8 normalized of v/3 (stride 4); the game multiplies by 3 on load
  POSITION, indices, animation and skin data are kept as they are.
Supported by the three.js r128 GLTFLoader.
"""
import json, struct, sys

HULL_SCALE = 3.0
FMT = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read(path):
    data = open(path, 'rb').read()
    off, js, binc = 12, None, b''
    while off < len(data):
        clen, ctype = struct.unpack_from('<I4s', data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == b'JSON':
            js = json.loads(chunk)
        else:
            binc = chunk
        off += 8 + clen
    return js, binc


def acc_values(g, binc, a):
    bv = g['bufferViews'][a['bufferView']]
    fmt = FMT[a['componentType']]
    n = NCOMP[a['type']]
    esize = struct.calcsize('<' + fmt) * n
    stride = bv.get('byteStride', esize)
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    out = []
    for i in range(a['count']):
        vals = struct.unpack_from('<%d%s' % (n, fmt), binc, base + i * stride)
        if a.get('normalized'):
            ct = a['componentType']
            vals = tuple(max(-1.0, v / 127.0) if ct == 5120 else v / 255.0 if ct == 5121 else max(-1.0, v / 32767.0) if ct == 5122 else v / 65535.0 if ct == 5123 else v for v in vals)
        out.append(vals)
    return out


def raw_bytes(g, binc, a):
    bv = g['bufferViews'][a['bufferView']]
    fmt = FMT[a['componentType']]
    n = NCOMP[a['type']]
    esize = struct.calcsize('<' + fmt) * n
    stride = bv.get('byteStride', esize)
    base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    if stride == esize:
        return binc[base: base + esize * a['count']]
    return b''.join(binc[base + i * stride: base + i * stride + esize] for i in range(a['count']))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def quantize(src, dst=None):
    dst = dst or src
    g, binc = read(src)
    roles = {}
    for m in g.get('meshes', []):
        for p in m['primitives']:
            for k, i in p['attributes'].items():
                roles[i] = k
            if 'indices' in p:
                roles[p['indices']] = '_INDEX'
    out = bytearray()
    views = []

    def add_view(blob, stride=None, target=None):
        while len(out) % 4:
            out.append(0)
        v = {'buffer': 0, 'byteOffset': len(out), 'byteLength': len(blob)}
        if stride:
            v['byteStride'] = stride
        if target:
            v['target'] = target
        out.extend(blob)
        views.append(v)
        return len(views) - 1

    for i, a in enumerate(g.get('accessors', [])):
        if 'bufferView' not in a:
            continue
        role = roles.get(i)
        if role in ('NORMAL', '_HULL'):
            vals = acc_values(g, binc, a)
            s = HULL_SCALE if role == '_HULL' else 1.0
            blob = b''.join(struct.pack('<3bx', *(int(round(clamp(c / s, -1, 1) * 127)) for c in v[:3])) for v in vals)
            a.update(componentType=5120, normalized=True, bufferView=add_view(blob, 4, 34962))
            a.pop('byteOffset', None)
            for k in ('min', 'max'):
                a.pop(k, None)
        elif role == 'TEXCOORD_0':
            vals = acc_values(g, binc, a)
            blob = b''.join(struct.pack('<2H', *(int(round(clamp(c, 0, 1) * 65535)) for c in v)) for v in vals)
            a.update(componentType=5123, normalized=True, bufferView=add_view(blob, 4, 34962))
            a.pop('byteOffset', None)
            for k in ('min', 'max'):
                a.pop(k, None)
        elif role in ('COLOR_0', 'WEIGHTS_0'):
            vals = acc_values(g, binc, a)
            n = NCOMP[a['type']]
            blob = b''.join(struct.pack('<4B', *([int(round(clamp(c, 0, 1) * 255)) for c in v] + [255] * (4 - n))) for v in vals)
            a.update(componentType=5121, normalized=True, type='VEC4', bufferView=add_view(blob, 4, 34962))
            a.pop('byteOffset', None)
            for k in ('min', 'max'):
                a.pop(k, None)
        else:
            blob = raw_bytes(g, binc, a)
            vertex = role is not None and role != '_INDEX'
            esize = struct.calcsize('<' + FMT[a['componentType']]) * NCOMP[a['type']]
            stride = esize if (vertex and esize % 4 == 0 and False) else None
            a['bufferView'] = add_view(blob, stride, 34963 if role == '_INDEX' else (34962 if vertex else None))
            a.pop('byteOffset', None)
    # images stored in buffer views
    for img in g.get('images', []):
        if 'bufferView' in img:
            bv = g['bufferViews'][img['bufferView']]
            blob = binc[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
            img['bufferView'] = add_view(blob)
    g['bufferViews'] = views
    while len(out) % 4:
        out.append(0)
    g['buffers'] = [{'byteLength': len(out)}]
    for key in ('extensionsUsed', 'extensionsRequired'):
        lst = g.setdefault(key, [])
        if 'KHR_mesh_quantization' not in lst:
            lst.append('KHR_mesh_quantization')
    js = json.dumps(g, separators=(',', ':')).encode()
    while len(js) % 4:
        js += b' '
    total = 12 + 8 + len(js) + 8 + len(out)
    with open(dst, 'wb') as f:
        f.write(struct.pack('<4sII', b'glTF', 2, total))
        f.write(struct.pack('<I4s', len(js), b'JSON')); f.write(js)
        f.write(struct.pack('<I4s', len(out), b'BIN\x00')); f.write(out)
    return total


if __name__ == '__main__':
    n = quantize(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print('quantized', sys.argv[1], n, 'bytes')
