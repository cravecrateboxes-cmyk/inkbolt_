#!/usr/bin/env python3
"""Before/after look sheets (tactical look plan, Stage 0.3).

    python3 look-sheet.py <classicDir> <onDir> <out.jpg> [plan]

Pairs files with the same name in both folders (optionally only <plan>-*.png), two columns (classic | on),
960 px wide cells, a label strip on each row, JPEG quality 88. Rows with a missing side show a grey cell.
"""
import os, sys
from PIL import Image, ImageDraw

CELL_W = int(os.environ.get('CELL_W', '640'))   # 960 for close review


def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(2)
    a, b, out = sys.argv[1:4]
    plan = sys.argv[4] if len(sys.argv) > 4 else None
    names = sorted(set(os.listdir(a)) | set(os.listdir(b)))
    names = [n for n in names if n.endswith('.png') and (not plan or n.startswith(plan + '-'))]
    if not names:
        print('no shots'); sys.exit(1)
    cell_h = CELL_W * 9 // 16
    lab = 26
    sheet = Image.new('RGB', (CELL_W * 2, (cell_h + lab) * len(names)), (24, 22, 28))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        y = i * (cell_h + lab)
        d.text((8, y + 6), n[:-4] + '   |   left: classic   right: look', fill=(235, 235, 235))
        for j, folder in enumerate((a, b)):
            f = os.path.join(folder, n)
            if os.path.exists(f):
                im = Image.open(f).convert('RGB').resize((CELL_W, cell_h), Image.LANCZOS)
            else:
                im = Image.new('RGB', (CELL_W, cell_h), (90, 90, 90))
            sheet.paste(im, (j * CELL_W, y + lab))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out, quality=84)
    print('sheet', out, len(names), 'rows')


if __name__ == '__main__':
    main()
