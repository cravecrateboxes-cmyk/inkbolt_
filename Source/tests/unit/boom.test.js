'use strict';
// VFX escalation rules (src/game/boom.js pure helpers; no THREE needed): intensity curve, canisters per zone,
// scrap chain chance, word rate, the canister safety patch and canister balance.
const test = require('node:test');
const assert = require('node:assert/strict');
require('../../src/game/boom.js');
const B = globalThis.IB.Boom;

test('intensity starts at 1, rises every level, caps at 2.2', () => {
  assert.equal(B.intensity(1), 1);
  assert.equal(B.intensity(0), 1);
  assert.equal(B.intensity(undefined), 1);
  for (let L = 2; L <= 9; L++) assert.ok(B.intensity(L) > B.intensity(L - 1), 'level ' + L);
  assert.ok(Math.abs(B.intensity(8) - 2.05) < 1e-9);
  assert.equal(B.intensity(9), 2.2);
  assert.equal(B.intensity(40), 2.2);
});

test('canisters: none on the first two levels, then 1..4 per zone', () => {
  assert.equal(B.canistersPerZone(1), 0);
  assert.equal(B.canistersPerZone(2), 0);
  assert.deepEqual([3, 4, 5, 6, 7, 8, 9, 20].map(B.canistersPerZone), [1, 1, 2, 2, 3, 3, 4, 4]);
});

test('scrap chains and words grow with the level and stay bounded', () => {
  assert.equal(B.chainChance(1), 0);
  for (let L = 2; L <= 30; L++) { assert.ok(B.chainChance(L) >= B.chainChance(L - 1)); assert.ok(B.chainChance(L) <= 0.55); }
  assert.ok(B.wordChance(1) >= 0.4 && B.wordChance(1) < B.wordChance(8));
  assert.ok(B.wordChance(50) <= 0.85);
  assert.equal(B.wordChance(1, true), 1);
});

test('clearPatch only accepts a fully open disc of cells', () => {
  const blocked = new Set(['5,9']);
  const open = (i, j) => i >= 0 && j >= 0 && i < 20 && j < 20 && !blocked.has(i + ',' + j);
  assert.equal(B.clearPatch(open, 10, 10, 3), true);
  assert.equal(B.clearPatch(open, 6, 9, 3), false);    // the blocked cell is inside the disc
  assert.equal(B.clearPatch(open, 1, 10, 3), false);   // runs off the grid
  assert.equal(B.clearPatch(open, 10, 10, 0), true);
});

test('canister balance: telegraphed, not a one-shot, needs a couple of hits', () => {
  assert.ok(B.CAN.fuse >= 0.5, 'player-set fuse long enough to see the red ring');
  assert.ok(B.CAN.dmgPlayer <= 35, 'a canister never takes more than a third of base health');
  assert.ok(B.CAN.hp > 18, 'one pistol bullet does not set it off');
  assert.ok(B.CAN.gap >= 5 && B.CAN.fromEntry >= 6 && B.CAN.fromSpawn >= 2.5, 'spaced out, away from the entry and the spawn cans');
});
