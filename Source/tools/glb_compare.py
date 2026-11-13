#!/usr/bin/env python3
"""Compare rebuilt GLBs with saved copies (tactical look plan, Stage 5D.3).

    python3 Source/tools/glb_compare.py <old.glb> <new.glb> [...pairs]
    python3 Source/tools/glb_compare.py --dirs <oldDir> <newDir>     every fps-*.glb present in both

Per mesh (matched by name): POSITION, NORMAL, TEXCOORD_0, _HULL, indices must be byte-identical and node transforms
equal; only COLOR_0 may differ, and its R channel on at most 1.5% of vertices (Cycles noise at the two-step
threshold). Prints one line per file; exits 1 on any other difference.
"""
import json, os, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'blender'))
from quantize_glb import read, raw_bytes  # noqa: E402

STRICT = ('POSITION', 'NORMAL', 'TEXCOORD_0', '_HULL')


def meshes(path):
    g, b = read(path)
    out = {}
    for m in g.get('meshes', []):
        prims = []
        for p in m['primitives']:
            d = {k: raw_bytes(g, b, g['accessors'][i]) for k, i in p['attributes'].items()}
            d['_type'] = {k: (g['accessors'][i]['componentType'], g['accessors'][i]['type']) for k, i in p['attributes'].items()}
            if 'indices' in p:
                d['indices'] = raw_bytes(g, b, g['accessors'][p['indices']])
                d['_isz'] = 2 if g['accessors'][p['indices']]['componentType'] == 5123 else 4
            prims.append(d)
        out[m['name']] = prims
    nodes = {n.get('name'): (n.get('translation'), n.get('rotation'), n.get('scale'), n.get('mesh') is not None) for n in g.get('nodes', [])}
    return out, nodes


def corners(d):
    """order-independent triangle set: each corner = position (0.1 mm grid) + normal + uv + hull bytes; each triangle
    rotated to a canonical first corner; the triangles sorted. Returns (signature, per-corner R values sorted)."""
    import numpy as np
    n = len(d['POSITION']) // 12
    pos = np.round(np.frombuffer(d['POSITION'], dtype='<f4').reshape(n, 3) * 1e4).astype(np.int64)
    parts = [pos]
    for k in ('NORMAL', 'TEXCOORD_0', '_HULL'):
        if k in d:
            parts.append(np.frombuffer(d[k], dtype=np.uint8).reshape(n, -1).astype(np.int64))
    v = np.concatenate(parts, axis=1)
    idx = np.frombuffer(d['indices'], dtype='<u2' if d.get('_isz', 2) == 2 else '<u4').reshape(-1, 3) if 'indices' in d else np.arange(n).reshape(-1, 3)
    keys = [tuple(r) for r in v]
    tris = []
    for t in idx:
        c = [keys[t[0]], keys[t[1]], keys[t[2]]]
        k = c.index(min(c)); tris.append(tuple(c[k:] + c[:k]))
    tris.sort()
    reds = sorted(np.frombuffer(d['COLOR_0'], dtype=np.uint8).reshape(n, 4)[idx.reshape(-1), 0].tolist()) if 'COLOR_0' in d else []
    return tuple(tris), reds


def compare(a, b):
    ma, na = meshes(a); mb, nb = meshes(b)
    errs = []
    if set(ma) != set(mb):
        errs.append('mesh names differ: -%s +%s' % (sorted(set(ma) - set(mb))[:5], sorted(set(mb) - set(ma))[:5]))
    if na != nb:
        bad = [k for k in set(na) | set(nb) if na.get(k) != nb.get(k)]
        errs.append('node transforms differ: %s' % bad[:5])
    rdiff = rtotal = 0
    for name in sorted(set(ma) & set(mb)):
        pa, pb = ma[name], mb[name]
        if len(pa) != len(pb):
            errs.append(name + ': primitive count'); continue
        for x, y in zip(pa, pb):
            same = all((k in x) == (k in y) and (k not in x or x[k] == y[k]) for k in STRICT + ('indices',))
            if not same:
                # Cycles noise at the R threshold can change how corners weld (trap T20): then compare the
                # triangles corner by corner (position, normal, uv, hull), which welding cannot change
                cx_, cy_ = corners(x), corners(y)
                if cx_[0] != cy_[0]:
                    errs.append('%s: triangle corners differ' % name)
                else:
                    rtotal += len(cx_[1]); rdiff += sum(1 for u, v in zip(cx_[1], cy_[1]) if u != v)
                continue
            if 'COLOR_0' in x and 'COLOR_0' in y:
                cx, cy = x['COLOR_0'], y['COLOR_0']
                if len(cx) != len(cy):
                    errs.append(name + ': COLOR_0 size'); continue
                n = len(cx) // 4
                rtotal += n
                rdiff += sum(1 for i in range(n) if cx[i * 4] != cy[i * 4])
    share = rdiff / rtotal if rtotal else 0
    if share > 0.015:
        errs.append('COLOR_0 R differs on %.2f%% of vertices' % (share * 100))
    return errs, share


def main(argv):
    pairs = []
    if argv and argv[0] == '--dirs':
        for f in sorted(os.listdir(argv[2])):
            if f.startswith('fps-') and f.endswith('.glb') and os.path.exists(os.path.join(argv[1], f)):
                pairs.append((os.path.join(argv[1], f), os.path.join(argv[2], f)))
    else:
        pairs = list(zip(argv[0::2], argv[1::2]))
    bad = 0
    for a, b in pairs:
        errs, share = compare(a, b)
        print(('ok   ' if not errs else 'FAIL ') + os.path.basename(b) + '  R differs on %.2f%%  size %d -> %d' % (share * 100, os.path.getsize(a), os.path.getsize(b)) + ('  ' + '; '.join(errs[:4]) if errs else ''))
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
