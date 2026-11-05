#!/usr/bin/env python3
"""Print a GLB's nodes, meshes (attributes, triangles), skins, animations and byte size.
    python3 tools/glb_info.py assets/fps-bots.glb [--json]"""
import json, struct, sys


def read_glb(path):
    data = open(path, 'rb').read()
    magic, ver, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF', path
    off, js, binc = 12, None, None
    while off < length:
        clen, ctype = struct.unpack_from('<I4s', data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == b'JSON':
            js = json.loads(chunk)
        elif ctype == b'BIN\x00':
            binc = chunk
        off += 8 + clen
    return js, binc, len(data)


def summary(path):
    g, _, size = read_glb(path)
    acc = g.get('accessors', [])
    meshes = {}
    for m in g.get('meshes', []):
        tris, attrs = 0, set()
        for p in m['primitives']:
            attrs |= set(p['attributes'])
            if 'indices' in p:
                tris += acc[p['indices']]['count'] // 3
        meshes[m['name']] = {'tris': tris, 'attributes': sorted(attrs)}
    return {
        'bytes': size,
        'nodes': [n.get('name') for n in g.get('nodes', [])],
        'meshes': meshes,
        'skins': [len(s['joints']) for s in g.get('skins', [])],
        'animations': [a.get('name') for a in g.get('animations', [])],
        'extensions': g.get('extensionsUsed', []),
    }


if __name__ == '__main__':
    s = summary(sys.argv[1])
    if '--json' in sys.argv:
        print(json.dumps(s, indent=1))
    else:
        print('%s  %.1f KB  ext=%s' % (sys.argv[1], s['bytes'] / 1024, s['extensions']))
        for k, v in s['meshes'].items():
            print('  %-40s %6d tris  %s' % (k, v['tris'], ','.join(v['attributes'])))
        print('  nodes:', ', '.join(n for n in s['nodes'] if n))
        if s['skins']:
            print('  skins (joints):', s['skins'])
        if s['animations']:
            print('  animations:', ', '.join(s['animations']))
