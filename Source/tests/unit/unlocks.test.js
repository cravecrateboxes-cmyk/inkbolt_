'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;

// campaign level -> weapons on stands at its start; melee weapons and frag cans are all in hand by level 5
const TABLE = {1: ['pip', 'buzz'], 2: ['rivet', 'handcannon'], 3: ['triplet', 'whisk', 'dagger'], 4: ['longtom', 'hornet', 'frag', 'nunchucks'],
  5: ['brick', 'twintap', 'katana', 'eaxe'], 6: ['needle'], 7: ['scrapper'], 8: ['vanguard'], 9: ['thunder'], 11: ['railspike']};

test('unlock table: the campaign plan', () => {
  assert.deepEqual(IB.UNLOCKS, TABLE);
});

test('by level 5 every melee weapon and the frag cans are unlocked', () => {
  const at5 = IB.ownedWeapons(5);
  for (const id of IB.MELEE_WEAPONS) assert.ok(at5.includes(id), id);
  assert.ok(at5.includes('frag'));
  assert.equal(IB.MELEE_WEAPONS.length, 4);
  assert.deepEqual(IB.MELEE_WEAPONS.map((id) => IB.WEAPONS[id].cls), ['melee', 'melee', 'melee', 'melee']);
});

test('owned weapons grow level by level', () => {
  assert.deepEqual(IB.ownedWeapons(0), []);
  let prev = [];
  for (let l = 1; l <= 13; l++) {
    const o = IB.ownedWeapons(l);
    assert.deepEqual(o.slice(0, prev.length), prev, 'level ' + l + ' keeps what came before');
    assert.deepEqual(o.slice(prev.length), TABLE[l] || [], 'level ' + l);
    prev = o;
  }
});

test('unlocksAt', () => {
  assert.deepEqual(IB.unlocksAt(1), ['pip', 'buzz']);
  assert.deepEqual(IB.unlocksAt(10), []);
  IB.unlocksAt(1).push('x');
  assert.deepEqual(IB.unlocksAt(1), ['pip', 'buzz'], 'returns a copy');
  assert.equal(IB.unlockLevelOf('needle'), 6);
  assert.equal(IB.unlockLevelOf('katana'), 5);
  assert.equal(IB.unlockLevelOf('nope'), null);
});

test('no weapon unlocks twice; ids exist in the weapon table; unlock fields match', () => {
  const all = Object.values(IB.UNLOCKS).flat();
  assert.equal(new Set(all).size, all.length);
  for (const id of all) {
    assert.ok(IB.WEAPONS[id], id + ' in WEAPONS');
    assert.ok(IB.GLB_WEAPON_NAMES.includes('WPN_' + id.toUpperCase()), id + ' in GLB names');
    assert.equal(IB.WEAPONS[id].unlock, IB.unlockLevelOf(id), id + ' unlock field matches table');
  }
  for (const w of Object.values(IB.WEAPONS)) if (!all.includes(w.id)) assert.equal(w.unlock, 0, w.id + ' not in the campaign');
});
