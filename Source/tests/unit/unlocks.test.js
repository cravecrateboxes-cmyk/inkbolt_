'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;

const L1 = ['pip'];
const L3 = [...L1, 'buzz'];
const L4 = [...L3, 'frag'];
const L5 = [...L4, 'rivet'];
const L6 = [...L5, 'popflash'];
const L7 = [...L6, 'katana'];
const L8 = [...L7, 'handcannon'];
const L9 = [...L8, 'needle'];
const L10 = [...L9, 'whisk'];
const L11 = [...L10, 'triplet'];
const L12 = [...L11, 'cancannon'];
const L13 = [...L12, 'longtom'];
const L14 = [...L13, 'fireaxe'];
const L16 = [...L14, 'twintap'];
const L17 = [...L16, 'hornet'];
const L18 = [...L17, 'brick'];
const L25 = [...L18, 'scrapper'];
const EXPECTED = {
  1: L1, 2: L1, 3: L3, 4: L4, 5: L5, 6: L6, 7: L7, 8: L8, 9: L9, 10: L10, 11: L11, 12: L12, 13: L13,
  14: L14, 15: L14, 16: L16, 17: L17, 18: L18, 19: L18, 20: L18, 21: L18, 22: L18, 23: L18, 24: L18, 25: L25
};

test('unlock table matches the brief exactly', () => {
  assert.deepEqual(IB.UNLOCKS, {1: ['pip'], 3: ['buzz'], 4: ['frag'], 5: ['rivet'], 6: ['popflash'], 7: ['katana'],
    8: ['handcannon'], 9: ['needle'], 10: ['whisk'], 11: ['triplet'], 12: ['cancannon'], 13: ['longtom'],
    14: ['fireaxe'], 16: ['twintap'], 17: ['hornet'], 18: ['brick'], 25: ['scrapper']});
});

test('owned weapons for each level 1 to 25', () => {
  assert.deepEqual(IB.ownedWeapons(0), []);
  for (let l = 1; l <= 25; l++) assert.deepEqual(IB.ownedWeapons(l), EXPECTED[l], 'level ' + l);
  assert.deepEqual(IB.ownedWeapons(99), L25);
  assert.equal(L25.length, 17);
});

test('unlocksAt', () => {
  assert.deepEqual(IB.unlocksAt(1), ['pip']);
  assert.deepEqual(IB.unlocksAt(2), []);
  assert.deepEqual(IB.unlocksAt(25), ['scrapper']);
  assert.deepEqual(IB.unlocksAt(15), []);
  IB.unlocksAt(1).push('x');
  assert.deepEqual(IB.unlocksAt(1), ['pip'], 'returns a copy');
  assert.equal(IB.unlockLevelOf('needle'), 9);
  assert.equal(IB.unlockLevelOf('nope'), null);
});

test('no weapon unlocks twice; ids exist in weapon table and GLB name list', () => {
  const all = Object.values(IB.UNLOCKS).flat();
  assert.equal(new Set(all).size, all.length);
  for (const id of all) {
    assert.ok(IB.WEAPONS[id], id + ' in WEAPONS');
    assert.ok(IB.GLB_WEAPON_NAMES.includes('WPN_' + id.toUpperCase()), id + ' in GLB names');
    assert.equal(IB.WEAPONS[id].unlock, IB.unlockLevelOf(id), id + ' unlock field matches table');
  }
  assert.deepEqual(new Set(all), new Set(Object.keys(IB.WEAPONS)), 'every weapon is unlockable');
});
