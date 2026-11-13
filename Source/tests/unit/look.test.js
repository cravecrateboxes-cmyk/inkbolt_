// Tactical look data (src/data/looks.js): every campaign theme resolves to a known family and scene type, every
// number is finite and inside a sane range, resolve() returns every default key, and a theme with no entry (a future
// map) still gets a complete look from its env.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
require('../../src/data/looks.js');
const IB = globalThis.IB;
const L = IB.LOOKS;
const TYPES = ['ext-day', 'ext-snow', 'ext-dusk', 'ext-night', 'int-lit', 'int-ind', 'int-dark'];

function walk(o, path, fn) {
  for (const k of Object.keys(o)) {
    const v = o[k], p = path + '.' + k;
    if (v && typeof v === 'object' && !Array.isArray(v)) walk(v, p, fn); else fn(p, v);
  }
}

test('every campaign theme has a look entry naming a known family and type', () => {
  const src = fs.readFileSync(path.join(__dirname, '../../src/data/levelplans.js'), 'utf8');
  const ids = JSON.parse(/var ORDER = (\[[^\]]+\])/.exec(src)[1].replace(/'/g, '"'));
  assert.ok(ids.length >= 45, 'campaign list loaded');
  for (const id of ids) {
    const t = L.themes[id];
    assert.ok(t, 'look entry for ' + id);
    assert.ok(L.families[t.family], id + ': family ' + t.family);
    assert.ok(TYPES.includes(t.type), id + ': type ' + t.type);
  }
});

test('resolve returns every default key with sane numbers', () => {
  for (const id of Object.keys(L.themes)) {
    const r = L.resolve(id, {});
    walk(L.defaults, '', (p) => {
      const get = p.slice(1).split('.').reduce((o, k) => o && o[k], r);
      assert.notStrictEqual(get, undefined, id + ' misses ' + p);
    });
    walk(r, '', (p, v) => {
      if (typeof v === 'number') assert.ok(Number.isFinite(v) && v >= 0 && v <= 5000, id + p + ' = ' + v);
      if (Array.isArray(v)) v.forEach((x) => assert.ok(typeof x !== 'number' || (Number.isFinite(x) && x >= 0 && x <= 500), id + p));
    });
    assert.ok(r.albCeil > 0.5 && r.albCeil <= 0.9, id + ' albCeil');
    assert.ok(r.albSat >= 0.85 && r.albSat <= 1, id + ' albSat (section 1.1: do not grey the game out)');
    assert.ok(r.fog.length >= 20, id + ' fog length');
    assert.ok(r.ink.px > 0.5 && r.ink.px < 3, id + ' ink px');
  }
});

test('a theme with no entry gets a complete look from its env (future maps)', () => {
  const dark = L.resolve('nosuchmap', { sky: null, fog: { color: '#20242A' } });
  assert.equal(dark.family, 'dark-int'); assert.equal(dark.guessed, true);
  const lit = L.resolve('nosuchmap', { sky: null, fog: { color: '#F0E8DA' } });
  assert.equal(lit.family, 'civic-int');
  const day = L.resolve('nosuchmap', { sky: ['#82C1F0', '#F2F7FC'], sun: [0.4, 0.85, 0.3] });
  assert.equal(day.type, 'ext-day');
  const dusk = L.resolve('nosuchmap', { sky: ['#4B78C2', '#FFB27C'], sun: [-0.62, 0.42, 0.52] });
  assert.equal(dusk.type, 'ext-dusk');
  for (const r of [dark, lit, day, dusk]) assert.ok(r.ink && r.fog && r.grade && r.grid, 'complete');
});

test('every tier names the same keys', () => {
  const keys = Object.keys(L.tiers.high).sort().join();
  for (const t of ['medium', 'low', 'potato']) assert.equal(Object.keys(L.tiers[t]).sort().join(), keys, t);
});
