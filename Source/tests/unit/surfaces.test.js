// Surface table (src/data/surfaces.gen.js, written by tools/gen_surfaces.py): one class per palette cell for every
// model family, names equal to blender/palettes.gen.json (trap T19: regenerate both when a palette changes), and
// every kit family has at least one light-emitting cell or is listed as having none.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/surfaces.gen.js');
const IB = globalThis.IB;
const PAL = JSON.parse(fs.readFileSync(path.join(__dirname, '../../blender/palettes.gen.json'), 'utf8'));
const ASSETS = fs.readdirSync(path.join(__dirname, '../../assets')).filter((f) => /^fps-.*\.glb$/.test(f)).map((f) => f.slice(4, -4));

test('every model family has a surface table that matches its palette', () => {
  for (const fam of ASSETS) {
    const s = IB.SURFACES[fam];
    assert.ok(s, 'surface table for ' + fam);
    assert.ok(PAL[fam], 'palette for ' + fam);
    assert.deepEqual(s.names, PAL[fam].map((c) => c[0]), fam + ': names match palettes.gen.json (re-run tools/gen_surfaces.py)');
    assert.equal(s.cls.length, s.names.length); assert.equal(s.emit.length, s.names.length);
    assert.ok(s.names.length <= 64, fam + ' has at most 64 cells');
    s.cls.forEach((c, i) => {
      assert.ok(Number.isInteger(c) && c >= 0 && c <= 15, fam + ' ' + s.names[i]);
      assert.ok(s.emit[i] >= 0 && s.emit[i] <= 2, fam + ' emit ' + s.names[i]);
      if (s.emit[i] > 0) assert.equal(c, 15, fam + ' ' + s.names[i] + ' emits but is not class 15');
    });
  }
});

test('class table has 16 classes with gloss and metal in 0..1', () => {
  assert.equal(IB.SURFACE_CLASSES.length, 16);
  for (const c of IB.SURFACE_CLASSES) { assert.ok(c.gloss >= 0 && c.gloss <= 1); assert.ok(c.metal >= 0 && c.metal <= 1); }
});
