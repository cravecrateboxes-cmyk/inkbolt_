# INKBOLT loot glow review: filmstrips per scene and a before / after comparison sheet from two runs of
# lootglow-shots.js.
#   python3 Source/tests/e2e/lootglow-sheet.py <beforeDir> <afterDir> <sheet.png>
# Writes <dir>/strip-<scene>.png in both folders (the frames side by side, labelled) and the sheet: per scene a
# 'before' row over an 'after' row, at the same frame times / distances.
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

TW, TH = 240, 135
ORDER = ['dist', 'near', 'spawn', 'idle', 'walk', 'pickup', 'overlap', 'calls']
TITLE = {'dist': 'five tiers at distance', 'near': 'close up / in the beam / up / down', 'spawn': 'a blue and an orange gun land',
         'idle': 'idle pulse (orange)', 'walk': 'walking up to a purple gun', 'pickup': 'E on the green gun (purple stays)',
         'overlap': 'three drops on one spot, strafing', 'calls': 'draw calls: 0 / 5 / 20 drops'}


def font(sz):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


F, FB = font(13), font(16)


def frames(d, scene, meta):
    out = []
    for e in meta['scenes'].get(scene, []):
        im = Image.open(os.path.join(d, e['file'])).convert('RGB').resize((TW, TH), Image.LANCZOS)
        lab = e['label'] + ('  ·  %d calls' % e['calls'] if scene == 'calls' else '')
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, TH - 18, TW, TH], fill=(16, 14, 22))
        dr.text((5, TH - 17), lab, fill=(240, 236, 228), font=F)
        out.append(im)
    return out


def strip(ims):
    s = Image.new('RGB', (max(1, len(ims)) * (TW + 4) + 4, TH + 8), (16, 14, 22))
    for i, im in enumerate(ims):
        s.paste(im, (4 + i * (TW + 4), 4))
    return s


def main():
    bdir, adir, sheet = sys.argv[1:4]
    B = json.load(open(os.path.join(bdir, 'shots.json')))
    A = json.load(open(os.path.join(adir, 'shots.json')))
    rows = []
    for sc in ORDER:
        fb, fa = frames(bdir, sc, B), frames(adir, sc, A)
        if not fb and not fa:
            continue
        sb, sa = strip(fb), strip(fa)
        sb.save(os.path.join(bdir, 'strip-%s.png' % sc)); sa.save(os.path.join(adir, 'strip-%s.png' % sc))
        rows.append((sc, sb, sa))
    LW = 70
    W = LW + max(max(r[1].width, r[2].width) for r in rows)
    H = 40 + sum(26 + r[1].height + r[2].height for r in rows)
    out = Image.new('RGB', (W, H), (28, 25, 36))
    dr = ImageDraw.Draw(out)
    dr.text((10, 10), 'Weapon loot glow: before (top row) / after (bottom row) · plan %s · look %s · tier %s' % (A['plan'], A['look'], A['tier']), fill=(255, 220, 150), font=FB)
    y = 40
    for sc, sb, sa in rows:
        dr.text((10, y + 4), TITLE.get(sc, sc), fill=(255, 255, 255), font=FB)
        y += 26
        dr.text((10, y + TH // 2), 'before', fill=(200, 190, 180), font=F); out.paste(sb, (LW, y)); y += sb.height
        dr.text((10, y + TH // 2), 'after', fill=(150, 230, 160), font=F); out.paste(sa, (LW, y)); y += sa.height
    out.save(sheet)
    print('sheet', sheet, out.size)


main()
