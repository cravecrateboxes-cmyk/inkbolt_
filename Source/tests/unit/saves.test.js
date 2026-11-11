'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
['core/rng', 'data/weapons', 'data/enemies', 'data/upgrades', 'data/skills', 'data/unlocks', 'data/levels',
  'core/damage', 'core/gems', 'core/upgrades', 'core/skills', 'core/saves', 'core/levelgen']
  .forEach((f) => require('../../src/' + f + '.js'));
const IB = globalThis.IB;
const S = IB.Saves;

function setup(start) {
  let t = start || 1730800000000;
  const be = S.memoryBackend();
  const clock = () => t;
  const store = S.create(be, clock);
  return { be, store, tick: (ms) => { t += ms; }, now: () => t };
}

test('new slot matches the 5.14 schema defaults', () => {
  const { store, now } = setup();
  const s = store.newSlot(2, 918273);
  assert.deepEqual(s, {
    v: 1, id: 2, level: 1, highest: 0, xp: 0, gems: 0, upgrades: {}, arsenal: [], loadout: [], skills: {},
    stats: { kills: 0, deaths: 0, time: 0, coreHits: 0 }, best: {}, gear: { inv: [], shield: null, armor: null, attach: {}, next: 1, found: 0 },
    seed: 918273, saved: now()
  });
  assert.equal(typeof store.newSlot(1).seed, 'number');
});

test('create, load, overwrite, delete', () => {
  const { be, store, tick } = setup();
  assert.deepEqual(store.listSlots(), [null, null, null]);
  const s = store.newSlot(1, 5);
  s.gems = 182; s.upgrades = { dmg: 2, hp: 1 };
  store.save(s);
  assert.ok(be.getItem('inkbolt.slot1'));
  assert.equal(be.getItem('inkbolt.slot1.bak'), null, 'no backup before a second write');
  assert.deepEqual(store.load(1), s);
  tick(5000);
  s.gems = 200; s.level = 2;
  store.save(s);
  assert.equal(store.load(1).gems, 200);
  assert.equal(JSON.parse(be.getItem('inkbolt.slot1.bak')).gems, 182, 'previous version kept as .bak');
  store.remove(1);
  assert.equal(store.load(1), null);
  assert.equal(be.getItem('inkbolt.slot1'), null);
  assert.equal(be.getItem('inkbolt.slot1.bak'), null);
  assert.throws(() => store.save({ id: 4 }));
  assert.equal(store.load(4), null);
});

test('3-slot limit, replacement and newest', () => {
  const { store, tick } = setup();
  assert.equal(store.freeSlot(), 1);
  store.save(store.newSlot(1, 1)); tick(1000);
  assert.equal(store.freeSlot(), 2);
  store.save(store.newSlot(2, 2)); tick(1000);
  store.save(store.newSlot(3, 3)); tick(1000);
  assert.equal(store.freeSlot(), null, 'all three full');
  assert.equal(store.listSlots().filter(Boolean).length, 3);
  assert.equal(store.newest().id, 3);
  // replace slot 2 with a new game
  const fresh = store.newSlot(2, 77);
  store.save(fresh);
  assert.equal(store.load(2).seed, 77);
  assert.equal(store.newest().id, 2);
  assert.equal(store.listSlots().filter(Boolean).length, 3);
  store.remove(1);
  assert.equal(store.freeSlot(), 1);
});

test('corrupted JSON falls back to the backup; both corrupt -> null', () => {
  const { be, store, tick } = setup();
  const s = store.newSlot(1, 9);
  s.gems = 50; store.save(s); tick(10);
  s.gems = 60; store.save(s);
  be.setItem('inkbolt.slot1', '{"v":1,"gems":6'); // torn write
  assert.equal(store.load(1).gems, 50, 'backup used');
  // saving over a corrupt main must not clobber the good backup
  s.gems = 70; store.save(s);
  assert.equal(JSON.parse(be.getItem('inkbolt.slot1.bak')).gems, 50);
  assert.equal(store.load(1).gems, 70);
  be.setItem('inkbolt.slot1', 'garbage'); be.setItem('inkbolt.slot1.bak', '{nope');
  assert.equal(store.load(1), null);
  be.setItem('inkbolt.slot1', '42');
  be.setItem('inkbolt.slot1.bak', 'null');
  assert.equal(store.load(1), null, 'non-object JSON treated as corrupt');
});

test('version migration from v:1', () => {
  const { be, store } = setup();
  be.setItem('inkbolt.slot2', JSON.stringify({ v: 1, id: 2, level: 7, highest: 6, gems: 182, upgrades: { dmg: 2 }, stats: { kills: 4 } }));
  const s = store.load(2);
  assert.equal(s.v, 1); assert.equal(s.level, 7); assert.equal(s.gems, 182);
  assert.deepEqual(s.upgrades, { dmg: 2 });
  assert.deepEqual(s.loadout, []); assert.deepEqual(s.arsenal, []); assert.deepEqual(s.skills, {});
  assert.deepEqual(s.stats, { kills: 4, deaths: 0, time: 0, coreHits: 0 });
  assert.deepEqual(s.best, {});
  assert.equal(s.xp, IB.Skills.xpForLevel(7), 'a save from before XP starts at LV 1 + highest');
  // the full brief example keeps every field; its class-keyed loadout becomes the ordered list + arsenal
  const ex = { v: 1, id: 1, level: 7, highest: 6, gems: 182, upgrades: { dmg: 2, hp: 1 },
    loadout: { pistol: 'pip', smg: 'buzz', rifle: 'rivet', melee: 'katana', grenade: 'frag' },
    stats: { kills: 412, deaths: 3, time: 1835, coreHits: 120 }, seed: 918273, saved: 1730800000000, best: {} };
  const list = ['pip', 'buzz', 'rivet', 'katana', 'frag'];
  assert.deepEqual(S.migrate(JSON.parse(JSON.stringify(ex))), Object.assign({}, ex, { loadout: list, arsenal: list, skills: {}, gear: S.defaultGear(), xp: IB.Skills.xpForLevel(7) }));
  // a current save passes through unchanged (gear included)
  const curGear = { inv: [{ id: 'g1', type: 'grip' }], shield: null, armor: null, attach: { rivet: ['g1'] }, next: 2, found: 1, starter: true, starterVest: true };
  const cur = Object.assign({}, ex, { loadout: ['rivet', 'pip'], arsenal: ['pip', 'rivet', 'buzz'], skills: { overload: 2, heavyink: 1 }, gear: curGear, xp: 12345 });
  assert.deepEqual(S.migrate(JSON.parse(JSON.stringify(cur))), cur);
  // the old 'owned' list fills the arsenal and the loadout
  const old = S.migrate({ v: 1, id: 1, highest: 2, owned: ['pip', 'rivet'] });
  assert.deepEqual(old.arsenal, ['pip', 'rivet']); assert.deepEqual(old.loadout, ['pip', 'rivet']);
  // gear (loot inventory) gets its default shape; stored items are kept
  const withGear = S.migrate({ v: 1, id: 1, gear: { inv: [{ id: 'g1', type: 'grip' }], shield: 'g1' } });
  assert.equal(withGear.gear.inv.length, 1); assert.equal(withGear.gear.shield, 'g1'); assert.deepEqual(withGear.gear.attach, {});
  assert.deepEqual(S.migrate({ v: 1, id: 1, gear: 'junk' }).gear, S.defaultGear());
  // a save from before armour vests: the gear keeps everything and gains an empty vest slot
  const preVest = S.migrate({ v: 1, id: 1, highest: 7, gear: { inv: [{ id: 'g1', type: 'shield', rarity: 'epic', level: 6, stats: { capacity: 40, delay: 3.5, rate: 15 } }], shield: 'g1', attach: {}, next: 2, found: 1, starter: true } });
  assert.equal(preVest.gear.armor, null); assert.equal(preVest.gear.shield, 'g1'); assert.equal(preVest.gear.starter, true); assert.equal(preVest.gear.starterVest, undefined, 'the starter vest is still to come');
  // no version field -> treated as v1
  assert.equal(S.migrate({ id: 1, level: 3 }).v, 1);
  // unknown future version kept as-is
  const fut = { v: 9, id: 3, weird: true };
  assert.deepEqual(S.migrate(fut), fut);
  assert.equal(S.migrate(null), null);
  assert.equal(S.migrate('x'), null);
  // garbage numbers repaired
  assert.equal(S.migrate({ v: 1, level: -3, gems: 'lots' }).level, 1);
  assert.equal(S.migrate({ v: 1, level: -3, gems: 'lots' }).gems, 0);
});

test('settings defaults, save, backup', () => {
  const { be, store } = setup();
  assert.deepEqual(store.loadSettings(), { sfx: true, mouseSens: 1.0, touchSens: 1.0, fov: 100, invertY: false,
    graphics: 'auto', shake: true, headBob: true, reduceFlash: false });
  store.saveSettings({ fov: 100, sfx: false });
  assert.equal(store.loadSettings().fov, 100);
  assert.equal(store.loadSettings().sfx, false);
  assert.equal(store.loadSettings().mouseSens, 1.0);
  store.saveSettings(Object.assign(store.loadSettings(), { fov: 90 }));
  assert.equal(JSON.parse(be.getItem('inkbolt.settings.bak')).fov, 100);
  be.setItem('inkbolt.settings', '{bad');
  assert.equal(store.loadSettings().fov, 100, 'falls back to the backup');
  be.setItem('inkbolt.settings', JSON.stringify({ fov: 'wide' }));
  assert.equal(store.loadSettings().fov, 100, 'wrong-typed value ignored');
});

test('reset clears all inkbolt keys only', () => {
  const { be, store } = setup();
  store.save(store.newSlot(1, 1)); store.save(store.newSlot(1, 1));
  store.save(store.newSlot(2, 2)); store.save(store.newSlot(3, 3));
  store.saveSettings({ fov: 70 }); store.saveSettings({ fov: 71 });
  be.setItem('inkbolt.misc', 'x');
  be.setItem('othergame.save', 'keep');
  store.resetAll();
  assert.deepEqual(be.keys(), ['othergame.save']);
  assert.deepEqual(store.listSlots(), [null, null, null]);
  assert.equal(store.loadSettings().fov, 100);
});

test('backend that throws does not crash', () => {
  const bad = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('quota'); }, removeItem() { throw new Error('x'); }, keys() { throw new Error('x'); } };
  const store = S.create(bad, () => 1);
  assert.deepEqual(store.listSlots(), [null, null, null]);
  assert.doesNotThrow(() => store.save(store.newSlot(1, 1)));
  assert.equal(store.loadSettings().fov, 100);
  assert.doesNotThrow(() => store.resetAll());
});

test('ago()', () => {
  assert.equal(S.ago(0), 'just now');
  assert.equal(S.ago(59 * 1000), 'just now');
  assert.equal(S.ago(12 * 60 * 1000), '12 min ago');
  assert.equal(S.ago(3 * 3600 * 1000 + 5), '3 h ago');
  assert.equal(S.ago(26 * 3600 * 1000), '1 day ago');
  assert.equal(S.ago(2 * 86400 * 1000), '2 days ago');
  assert.equal(S.ago(-5000), 'just now');
});

test('skills are validated against progress on load (spent <= earned, gates, one endgame skill)', () => {
  const { be, store } = setup();
  // LV 2 (highest 1) has 2 points: 2 ranks are fine, 3 are not
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 1, skills: { overload: 2 } }));
  assert.deepEqual(store.load(1).skills, { overload: 2 });
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 1, skills: { overload: 3 } }));
  assert.deepEqual(store.load(1).skills, {}, 'overspent tree is reset (points refunded)');
  // a row-3 skill without the 5 points below it, unknown (or retired) ids, bad ranks, non-objects: all reset
  for (const bad of [{ hazard: 1 }, { nope: 1 }, { overboard: 2 }, { overload: 4 }, { overload: -1 }, { overload: 1.5 }, [1, 2], 'x']) {
    be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 17, skills: bad }));
    assert.deepEqual(store.load(1).skills, {}, JSON.stringify(bad));
  }
  // an endgame skill is kept once it is paid for (18 points below it, LV 30 has 30); both at once is not allowed
  const both = { overload: 3, heavyink: 3, electrify: 1, stream: 2, healthy: 3, boom: 3, undercover: 1, tank: 2, handyhelpers: 1 };
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 99, skills: both }));
  assert.deepEqual(store.load(1).skills, both);
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 99, skills: Object.assign({ chainreaction: 1 }, both) }));
  assert.deepEqual(store.load(1).skills, {}, 'both endgame skills: reset');
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 8, skills: both }));
  assert.deepEqual(store.load(1).skills, {}, 'not enough points yet');
  // a tree that spends more than the level has earned (23 spent, 20 earned at LV 21): reset, every point back
  const old = { overload: 3, heavyink: 3, stream: 3, electrify: 1, rapid: 3, hazard: 3, ricochet: 3, healthy: 3, undercover: 1 };
  be.setItem('inkbolt.slot1', JSON.stringify({ v: 1, id: 1, highest: 19, skills: old }));
  assert.deepEqual(store.load(1).skills, {}, 'more points spent than earned');
});

test('settings v2: old 85 default becomes 100, a chosen field of view is kept, range 60-130', () => {
  const be = IB.Saves.memoryBackend();
  be.setItem('inkbolt.settings', JSON.stringify({ fov: 85 }));
  assert.equal(IB.Saves.create(be).loadSettings().fov, 100);
  be.setItem('inkbolt.settings', JSON.stringify({ fov: 92 }));
  assert.equal(IB.Saves.create(be).loadSettings().fov, 92);
  be.setItem('inkbolt.settings', JSON.stringify({ fov: 85, sv: 2 }));
  assert.equal(IB.Saves.create(be).loadSettings().fov, 85, 'an 85 saved after v2 is a choice');
  be.setItem('inkbolt.settings', JSON.stringify({ fov: 200, sv: 2 }));
  assert.equal(IB.Saves.create(be).loadSettings().fov, 130);
});
