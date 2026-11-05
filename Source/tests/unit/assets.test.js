// Every asset name the game asks for exists in the Blender GLBs; budgets and rig checks (brief 3.2 / 3.4).
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
require('../../src/data/assets.js');
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
  const kitHave = names(G['kit-toytown']);
  for (const n of IB.kitAssetNames('toytown')) assert.ok(kitHave.has(n), 'kit-toytown missing ' + n);
});

test('every modelled weapon has a mesh, mag, sockets and all six arm actions', () => {
  const anims = new Set(G.weapons.animations.map(a => a.name));
  for (const id of IB.MODELLED_WEAPONS) {
    const k = 'WPN_' + id.toUpperCase();
    for (const s of ['', '_Mag', '_MUZZLE', '_MAG', '_EJECT']) assert.ok(names(G.weapons).has(k + s), k + s);
    for (const a of IB.ARM_ACTIONS) assert.ok(anims.has(id.toUpperCase() + '_' + a), 'action ' + id.toUpperCase() + '_' + a);
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
  for (const [n, max] of Object.entries(IB.TRI_BUDGET.meshes)) assert.ok(tris(all[n], n) <= max, n + ' ' + tris(all[n], n) + ' > ' + max);
  for (const [id, r] of Object.entries(IB.TRI_BUDGET.robots)) {
    const t = Object.entries(r.parts).reduce((s, [n, k]) => s + tris(G.bots, n) * k, 0);
    assert.ok(t <= r.max, id + ' ' + t + ' > ' + r.max);
  }
  let kit = 0;
  for (const n of IB.kitAssetNames('toytown')) {
    const t = tris(G['kit-toytown'], n); kit += t;
    if (!/Landmark/.test(n)) assert.ok(t <= IB.TRI_BUDGET.kitPropMax, n + ' ' + t);
  }
  assert.ok(kit <= IB.TRI_BUDGET.kitMax, 'kit total ' + kit);
});
