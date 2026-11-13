// Every asset name the game asks for exists in the Blender GLBs; budgets and rig checks (brief 3.2 / 3.4).
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
require('../../src/data/assets.js');
require('../../src/data/assets.gen.js');
require('../../src/data/themes.js');
require('../../src/data/themes.gen.js');
const IB = globalThis.IB;
const ASSETS = path.join(__dirname, '../../assets');

function readGlb(file) {
  const d = fs.readFileSync(path.join(ASSETS, file));
  assert.strictEqual(d.toString('ascii', 0, 4), 'glTF', file + ' is not a GLB');
  const len = d.readUInt32LE(12);
  return JSON.parse(d.toString('utf8', 20, 20 + len));
}
const G = {};
for (const [fam, file] of Object.entries(IB.ASSET_FILES)) G[fam] = readGlb(file);
const names = g => new Set(g.nodes.map(n => n.name));
function tris(g, meshName) {
  const node = g.nodes.find(n => n.name === meshName && n.mesh !== undefined);
  assert.ok(node, 'mesh node ' + meshName);
  return g.meshes[node.mesh].primitives.reduce((t, p) => t + g.accessors[p.indices].count / 3, 0);
}

test('every name the game asks for exists in its GLB', () => {
  for (const [fam, list] of Object.entries(IB.ASSET_NAMES)) {
    const have = names(G[fam]);
    for (const n of list) assert.ok(have.has(n), fam + ' missing ' + n);
  }
  // every theme's pieces exist in its own kit (or fps-common)
  for (const th of Object.values(IB.THEME_DEFS)) {
    assert.ok(G[th.family], 'theme ' + th.id + ' has no GLB ' + th.family);
    const have = names(G[th.family]), common = names(G.common);
    for (const n of th.allPieces()) { const full = IB.themePiece(th, n); assert.ok(have.has(full) || common.has(full), th.family + ' missing ' + full); }
  }
});

test('every modelled weapon has a mesh, mag, sockets and all arm actions', () => {
  const anims = new Set(G.weapons.animations.map(a => a.name));
  for (const id of IB.MODELLED_WEAPONS) {
    const k = 'WPN_' + id.toUpperCase();
    for (const s of ['', '_Mag', '_MUZZLE', '_MAG', '_EJECT', '_SIGHT']) assert.ok(names(G.weapons).has(k + s), k + s);
    if (IB.SCOPED_WEAPONS.includes(id)) assert.ok(names(G.weapons).has(k + '_SCOPE'), k + '_SCOPE');
    for (const a of IB.ARM_ACTIONS) assert.ok(anims.has(id.toUpperCase() + '_' + a), 'action ' + id.toUpperCase() + '_' + a);
  }
  assert.ok(IB.ARM_ACTIONS.includes('Slide'));
});

test('sockets sit on their gun: MAG is the mag origin, SIGHT above the bore line, muzzle in front', () => {
  for (const id of IB.MODELLED_WEAPONS) {
    const k = 'WPN_' + id.toUpperCase();
    const gun = G.weapons.nodes.find(n => n.name === k);
    const kids = (gun.children || []).map(i => G.weapons.nodes[i]);
    const at = s => (kids.find(n => n.name === k + s) || {}).translation;
    for (const s of ['_MUZZLE', '_MAG', '_EJECT', '_SIGHT']) assert.ok(at(s), k + s + ' is a child of ' + k);
    // glTF is Y-up, forward -Z: the muzzle is ahead of the sight, the sight above the muzzle line
    assert.ok(at('_MUZZLE')[2] < at('_SIGHT')[2], k + ' muzzle ahead of sight');
    assert.ok(at('_SIGHT')[1] > at('_MUZZLE')[1], k + ' sight above the bore');
  }
});

test('arm action lengths follow the weapon table (reload, draw 0.3 s, holster 0.2 s, idle 2 s)', () => {
  require('../../src/data/weapons.js');
  const len = {};
  for (const a of G.weapons.animations) len[a.name] = Math.max(...a.samplers.map(s => G.weapons.accessors[s.input].max[0]));
  const near = (a, b, n) => assert.ok(Math.abs(a - b) <= 1 / 30 + 1e-4, n + ' ' + a + ' != ' + b);
  for (const id of IB.MODELLED_WEAPONS) {
    const K = id.toUpperCase(), w = IB.WEAPONS[id];
    near(len[K + '_Reload'], w.reload, K + '_Reload');
    near(len[K + '_Draw'], IB.WEAPON_RULES.draw, K + '_Draw');
    near(len[K + '_Holster'], IB.WEAPON_RULES.holster, K + '_Holster');
    near(len[K + '_Idle'], 2, K + '_Idle');
    assert.ok(len[K + '_Fire'] <= Math.max(w.cycle, 2 / 30) + 1 / 30 + 1e-4, K + '_Fire ' + len[K + '_Fire'] + ' > cycle ' + w.cycle);
  }
});

test('arms are one skinned mesh on a 22-bone rig', () => {
  assert.strictEqual(G.weapons.skins.length, 1);
  assert.strictEqual(G.weapons.skins[0].joints.length, 22);
});

test('GLBs are quantized (KHR_mesh_quantization) and carry the outline attribute', () => {
  for (const [fam, g] of Object.entries(G)) {
    assert.ok((g.extensionsUsed || []).includes('KHR_mesh_quantization'), fam);
    for (const m of g.meshes) for (const p of m.primitives) {
      for (const a of ['POSITION', 'NORMAL', 'TEXCOORD_0', 'COLOR_0', '_HULL']) assert.ok(a in p.attributes, fam + ' ' + m.name + ' ' + a);
    }
  }
});

test('triangle budgets hold (including the outline hull)', () => {
  const all = Object.assign({}, ...Object.values(G).map(g => Object.fromEntries(g.nodes.filter(n => n.mesh !== undefined).map(n => [n.name, g]))));
  for (const [n, max] of Object.entries(IB.TRI_BUDGET.meshes)) {
    // a weapon's budget covers the gun, its detachable mag and all of its rarity layers together
    const layers = Object.keys(all).filter(k => k.startsWith(n + '_') && /^(_Mag)?_L\d+$/.test(k.slice(n.length)));
    const t = tris(all[n], n) + (all[n + '_Mag'] ? tris(all[n + '_Mag'], n + '_Mag') : 0) + layers.reduce((s, k) => s + tris(all[k], k), 0);
    assert.ok(t <= max, n + ' ' + t + ' > ' + max);
  }
  for (const [id, r] of Object.entries(IB.TRI_BUDGET.robots)) {
    const t = Object.entries(r.parts).reduce((s, [n, k]) => s + tris(G.bots, n) * k, 0);
    assert.ok(t <= r.max, id + ' ' + t + ' > ' + r.max);
  }
  for (const th of Object.values(IB.THEME_DEFS)) {
    const B = th.budget || {}, g = G[th.family];
    let kit = 0;
    for (const n of new Set(th.allPieces().map(x => IB.themePiece(th, x)))) {
      if (!g.nodes.some(nd => nd.name === n && nd.mesh !== undefined)) continue;   // fps-common pieces are budgeted there
      const t = tris(g, n); kit += t;
      assert.ok(t <= (/Landmark|Backdrop/.test(n) ? (B.landmark || 4000) : (B.prop || 1200)), th.id + ' ' + n + ' ' + t);
    }
    assert.ok(kit <= (B.total || 40000), th.id + ' kit total ' + kit);
  }
});
