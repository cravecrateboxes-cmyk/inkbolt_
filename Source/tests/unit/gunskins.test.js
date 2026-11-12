'use strict';
// gun rarity skins (src/core/gunskins.js): palette cell order matches Blender, every gun has a colourway, names, feel
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
['data/weapons', 'data/assets', 'core/gunskins'].forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const S = IB.GunSkinData;
const GUNS = IB.MODELLED_WEAPONS.filter((id) => IB.WEAPONS[id] && IB.WEAPONS[id].cls !== 'melee');

test('palette cells mirror blender/ib_lib BASE + wpn_core palette order', () => {
  const lib = fs.readFileSync(path.join(__dirname, '../../blender/ib_lib.py'), 'utf8');
  const fam = fs.readFileSync(path.join(__dirname, '../../blender/wpn_core.py'), 'utf8');
  const base = lib.slice(lib.indexOf('BASE = ['), lib.indexOf(']\n', lib.indexOf('BASE = [')));
  const list = fam.slice(fam.indexOf("ib_lib.PALETTES['weapons']"), fam.indexOf(']\n', fam.indexOf("('gun2'")));
  const names = (s) => [...s.matchAll(/\('(\w+)', '#[0-9A-Fa-f]{6}'\)/g)].map((m) => m[1]);
  assert.deepEqual(names(base).concat(names(list)), S.CELLS);
  assert.ok(S.CELLS.length <= 64);
});

test('every gun has its own colourway and a skin at every tier', () => {
  const seen = new Set();
  GUNS.forEach((id) => {
    assert.ok(S.GUNS[id], id + ' colourway');
    seen.add(S.GUNS[id].body + S.GUNS[id].frame + S.GUNS[id].acc);
    S.TIER_IDS.forEach((t) => {
      const sk = S.skin(id, t);
      Object.keys(sk.cells).forEach((c) => {
        assert.ok(S.CELLS.includes(c), c);
        assert.match(sk.cells[c].hex, /^#[0-9A-F]{6}$/);
      });
      assert.ok(S.PATTERNS[sk.pat.type] !== undefined);
    });
  });
  assert.equal(seen.size, GUNS.length, 'colourways are distinct');
  // the progression: Epic and Legendary glow, Legendary shimmers
  assert.equal(S.skin('rivet', 'gray').glow, '#000000');
  assert.notEqual(S.skin('rivet', 'purple').glow, '#000000');
  assert.equal(S.skin('rivet', 'orange').shimmer, 1);
  // Legendary: a premium finish per gun, several kinds, gold only on some; every one glows and shimmers
  const legs = GUNS.map((id) => S.skin(id, 'orange'));
  legs.forEach((k, i) => {
    assert.ok(S.LEGEND[S.GUNS[GUNS[i]].leg], GUNS[i] + ' legendary finish');
    assert.equal(k.shimmer, 1); assert.notEqual(k.glow, '#000000');
    assert.ok(S.PATTERNS[k.pat.type] > 0, GUNS[i] + ' finish pattern');
    assert.ok(S.LEGEND[k.legend].word.includes(S.word(GUNS[i], 'orange')));
  });
  const kinds = new Set(legs.map((k) => k.legend));
  assert.ok(kinds.size >= 6, 'at least six legendary finishes');
  assert.ok(legs.filter((k) => k.legend === 'gold').length <= GUNS.length / 3, 'gold only on some');
});

test('rarity names and feel', () => {
  assert.equal(S.name('rivet', 'gray', 'AR-22 Rivet'), 'AR-22 Rivet');
  S.TIER_IDS.slice(1).forEach((t) => {
    const n = S.name('rivet', t, 'AR-22 Rivet');
    assert.match(n, /^\w+ Rivet$/);
    assert.ok(S.WORDS[t].includes(n.split(' ')[0]));
  });
  assert.equal(S.name('hothead', 'blue', 'Volt Hothead').split(' ').slice(1).join(' '), 'Volt Hothead');
  let prev = 2;
  S.TIER_IDS.forEach((t) => { const f = S.feel(t); assert.ok(f.pitch <= prev); prev = f.pitch; assert.match(f.tracer, /^#/); });
});
