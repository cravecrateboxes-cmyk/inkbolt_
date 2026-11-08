// INKBOLT collision audit ("invisible walls"): for every zone of every campaign plan (IB.CAMPAIGN, so new maps are
// covered automatically) each collision box is compared with what is drawn there -- every static mesh of the scene
// near the zone (merged zone meshes, trails, hatch room, weapon stands), rasterised top-down on a 5 cm grid in the box's
// height band at player height (from the box base, at least 0.2 m above the ground, 1.6 m up).
// The player's capsule (radius R) is flooded in from standable spots inside the zone / trails, through every spot where
// it touches nothing drawn and no box. A FELT spot is one next to that reachable area where only this box stops the
// capsule although nothing drawn is within R + TOL (15 cm): the player bumps into air there. Felt spots are reached
// only through such open spots, so a pocket behind a drawn wall never counts, slots narrower than the capsule (between
// the bikes of a rack) never count, and a box sticking out up to TOL past what is drawn is fine. Per box, the felt area
// (capsule-centre m^2) must stay under LIMIT (0.3 m^2: e.g. a box 30 cm proud of the drawn prop along 2 m). Typical
// failures: a box over a whole prefab whose visual is a frame, an open booth, a round planter or ball, a skewed car,
// a full-cell fallback box (no _COL in the kit) round a drum or sack pile. Fix them in the kit (blender/col_fit.py
// re-cuts listed pieces' boxes to the drawn shape on export) or in the theme (`cols`).
// Skipped: movement-only bounds (kind 'bound', invisible by design), gates and elevator boxes (they move / toggle),
// walkable boxes (stair blocks and decks are solid to the floor for robot nav), boxes the player just steps onto, and
// ALLOW (the box over a moving line, whose riders are instanced meshes this audit does not sample).
// Run (after tools/build.py): node tests/e2e/collision-audit.spec.js   (PLANS=mall,police to pick plans; LIMIT=m^2;
// TOP=n offenders listed per plan; VERBOSE=1 lists the worst under the limit too; OUT=file.json writes every box over
// REPORT m^2 with hints). ~4 min for all plans.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const LIMIT = +(process.env.LIMIT || 0.3), TOP = +(process.env.TOP || 8), REPORT = +(process.env.REPORT || 0.08);
let fails = 0;
function check(name, ok, info) { console.log((ok ? 'PASS ' : 'FAIL ') + name + (info ? '  ' + info : '')); if (!ok) fails++; }
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

// ---- in-page audit of one zone: [{box, piece, kind, emptyArea, frac, at}] for boxes with > report m^2 empty ----
function auditZone(args) {
  const zi = args[0], report = args[1], dump = args[2];   // dump: a box id -> ASCII map of it
  const L = IB.Game.level, W = L.world, Z = L.zones[zi], M = IB.MOVE;
  const RES = 0.05, TOL = 0.15, PR = M.radius, MARGIN = 2 * PR + TOL + 0.1;
  // exact Euclidean distance transform (Felzenszwalb) of a 0/1 grid -> metres from each cell to the nearest 1
  function edt(mark, nx, nz, res) {
    const INF = 1e12, d = new Float64Array(nx * nz), n = Math.max(nx, nz), f = new Float64Array(n), o = new Float64Array(n), v = new Int32Array(n), zz = new Float64Array(n + 1);
    const pass = len => {
      let k = 0; v[0] = 0; zz[0] = -INF; zz[1] = INF;
      for (let q = 1; q < len; q++) {
        let s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]);
        while (s <= zz[k]) { k--; s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]); }
        k++; v[k] = q; zz[k] = s; zz[k + 1] = INF;
      }
      k = 0;
      for (let q = 0; q < len; q++) { while (zz[k + 1] < q) k++; o[q] = (q - v[k]) * (q - v[k]) + f[v[k]]; }
    };
    for (let k = 0; k < nz; k++) { for (let i = 0; i < nx; i++) f[i] = mark[k * nx + i] ? 0 : INF; pass(nx); for (let i = 0; i < nx; i++) d[k * nx + i] = o[i]; }
    for (let i = 0; i < nx; i++) { for (let k = 0; k < nz; k++) f[k] = d[k * nx + i]; pass(nz); for (let k = 0; k < nz; k++) d[k * nx + i] = Math.sqrt(o[k]) * res; }
    return d;
  }
  // deliberate: the box over a moving line (robots ride it, drawn by instanced meshes this audit does not sample)
  const ALLOW = [{ piece: /^KIT_FOUNDRY_Line_/, minY: 1.4 }];
  const skip = new Set();
  L.zones.forEach(z => [z.exitGate, z.entryGate].forEach(g => { if (g && g.box) skip.add(g.box); }));
  (Z.elevators || []).forEach(E => { E.moving.forEach(m => skip.add(m.b)); E.stop.forEach(s => skip.add(s.b)); skip.add(E.door); });
  // world-space triangles of the zone's static meshes, bucketed on a 1 m XZ grid
  // every static mesh in the scene near the zone (the zone's merged meshes, trails, the hatch, weapon-stand crates)
  let scene = L.root; while (scene.parent) scene = scene.parent;
  scene.updateMatrixWorld(true);
  const tris = [], v = new THREE.Vector3(), ZX0 = Z.ox - 12, ZX1 = Z.ox + Z.w + 12, ZZ0 = Z.oz - 12, ZZ1 = Z.oz + Z.h + 12;
  const robotRoots = new Set(((IB.AI && IB.AI.robots) || []).map(r => r.mesh || r.group || r.obj).filter(Boolean));
  scene.traverse(o => {
    if (!o.isMesh || o.isInstancedMesh || o.isSkinnedMesh || !o.geometry || !o.geometry.attributes.position) return;
    for (let q = o; q; q = q.parent) if (robotRoots.has(q)) return;
    if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
    const bb = o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
    if (bb.max.x < ZX0 || bb.min.x > ZX1 || bb.max.z < ZZ0 || bb.min.z > ZZ1) return;
    const g = o.geometry, p = g.attributes.position, P = new Float32Array(p.count * 3);
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
    const ix = g.index ? g.index.array : null, n = ix ? ix.length : p.count;
    for (let t = 0; t + 2 < n; t += 3) {
      const a = ix ? ix[t] : t, b = ix ? ix[t + 1] : t + 1, c = ix ? ix[t + 2] : t + 2;
      const T = [P[a * 3], P[a * 3 + 1], P[a * 3 + 2], P[b * 3], P[b * 3 + 1], P[b * 3 + 2], P[c * 3], P[c * 3 + 1], P[c * 3 + 2]];
      if (Math.max(T[1], T[4], T[7]) < 0.12) continue;   // floor / ground: below every audited band
      tris.push(T);
    }
  });
  const bucket = new Map(), key = (i, k) => i * 100003 + k;
  tris.forEach((T, ti) => {
    const i0 = Math.floor(Math.min(T[0], T[3], T[6])), i1 = Math.floor(Math.max(T[0], T[3], T[6]));
    const k0 = Math.floor(Math.min(T[2], T[5], T[8])), k1 = Math.floor(Math.max(T[2], T[5], T[8]));
    for (let i = i0; i <= i1; i++) for (let k = k0; k <= k1; k++) { const kk = key(i, k); let a = bucket.get(kk); if (!a) bucket.set(kk, a = []); a.push(ti); }
  });
  const tmpQ = [], trails = (L.trails || []).filter(t => t && t.x !== undefined);
  const inWalk = (x, z) => (x > Z.ox && x < Z.ox + Z.w && z > Z.oz && z < Z.oz + Z.h) ||
    trails.some(t => Math.abs(x - t.x) < 1.5 && z > Math.min(t.z0, t.z1) && z < Math.max(t.z0, t.z1));
  const out = [];
  let audited = 0;
  for (const b of W.boxes) {
    if (dump !== undefined && b.id !== dump) continue;
    if (b.zone !== zi || !b.on || b.kind === 'bound' || b.kind === 'canister' || b.noRay || b.walk || skip.has(b)) continue;
    if (ALLOW.some(a => a.piece.test(b.piece || '') && b.y0 >= a.minY)) continue;
    const ground = W.terrains.length ? W.groundAt((b.x0 + b.x1) / 2, (b.z0 + b.z1) / 2) : 0;
    if (b.y1 <= ground + (b.walk ? M.stepUpStair : M.stepUp) + 0.01) continue;   // stepped onto, never bumped into
    const yA = Math.max(b.y0, ground + 0.2), yB = Math.min(b.y1, yA + 1.6);
    if (yB <= yA) continue;
    audited++;
    const X0 = b.x0 - MARGIN, Z0 = b.z0 - MARGIN, nx = Math.ceil((b.x1 - b.x0 + 2 * MARGIN) / RES), nz = Math.ceil((b.z1 - b.z0 + 2 * MARGIN) / RES);
    if (nx * nz > 4e6) continue;
    const mark = new Uint8Array(nx * nz), ya = yA - 0.05, yb = yB + 0.05, X1 = X0 + nx * RES, Z1 = Z0 + nz * RES;
    const seen = new Set();
    const put = (x, y, z) => { if (y < ya || y > yb) return; const i = Math.floor((x - X0) / RES), k = Math.floor((z - Z0) / RES); if (i >= 0 && k >= 0 && i < nx && k < nz) mark[k * nx + i] = 1; };
    const raster = (T, depth) => {
      const mnx = Math.min(T[0], T[3], T[6]), mxx = Math.max(T[0], T[3], T[6]), mny = Math.min(T[1], T[4], T[7]), mxy = Math.max(T[1], T[4], T[7]);
      const mnz = Math.min(T[2], T[5], T[8]), mxz = Math.max(T[2], T[5], T[8]);
      if (mxx < X0 || mnx > X1 || mxz < Z0 || mnz > Z1 || mxy < ya || mny > yb) return;
      const e = Math.max(Math.hypot(T[0] - T[3], T[1] - T[4], T[2] - T[5]), Math.hypot(T[3] - T[6], T[4] - T[7], T[5] - T[8]), Math.hypot(T[6] - T[0], T[7] - T[1], T[8] - T[2]));
      if (e > 0.6 && depth < 14) {   // split big triangles, culling the parts away from this box
        const m = j => [(T[j[0]] + T[j[1]]) / 2, (T[j[0] + 1] + T[j[1] + 1]) / 2, (T[j[0] + 2] + T[j[1] + 2]) / 2];
        const A = T.slice(0, 3), B = T.slice(3, 6), C = T.slice(6, 9), ab = m([0, 3]), bc = m([3, 6]), ca = m([6, 0]);
        [[A, ab, ca], [ab, B, bc], [ca, bc, C], [ab, bc, ca]].forEach(q => raster([].concat(q[0], q[1], q[2]), depth + 1));
        return;
      }
      const n = Math.max(1, Math.ceil(e / (RES * 0.7)));
      for (let i = 0; i <= n; i++) for (let j = 0; i + j <= n; j++) {
        const u = i / n, w = j / n, s = 1 - u - w;
        put(T[0] * s + T[3] * u + T[6] * w, T[1] * s + T[4] * u + T[7] * w, T[2] * s + T[5] * u + T[8] * w);
      }
    };
    for (let i = Math.floor(X0); i <= Math.floor(X1); i++) for (let k = Math.floor(Z0); k <= Math.floor(Z1); k++) {
      const a = bucket.get(key(i, k)); if (!a) continue;
      for (const ti of a) { if (seen.has(ti)) continue; seen.add(ti); raster(tris[ti], 0); }
    }
    // dv: distance (m) from each cell centre to the nearest visible surface in the band (exact 2D EDT)
    const dv = edt(mark, nx, nz, RES);
    // reach: where the player's capsule centre gets to as things are -- clear of everything drawn and of every box (this
    // one too) -- flooding from standable border spots (inside the zone or a trail). FELT: spots next to that, within R
    // of this box, with nothing drawn within R + TOL, connected to the reached area through such spots only: the
    // capsule would fit there by the look of it, and only this box stops it (the player bumps into air). Going through
    // spots with nothing drawn near means a felt pocket never tunnels through a drawn wall to the box's far side.
    const others = new Uint8Array(nx * nz), nearB = new Uint8Array(nx * nz);
    W.query(X0, Z0, X1, Z1, tmpQ);
    for (const o of tmpQ.slice()) {
      if (o.y0 >= yB || o.y1 <= yA) continue;
      const i0 = Math.max(0, Math.floor((o.x0 - PR - X0) / RES)), i1 = Math.min(nx - 1, Math.floor((o.x1 + PR - X0) / RES));
      const k0 = Math.max(0, Math.floor((o.z0 - PR - Z0) / RES)), k1 = Math.min(nz - 1, Math.floor((o.z1 + PR - Z0) / RES));
      for (let k = k0; k <= k1; k++) for (let i = i0; i <= i1; i++) {
        const x = X0 + (i + 0.5) * RES, z = Z0 + (k + 0.5) * RES;
        const qx = Math.max(o.x0, Math.min(x, o.x1)), qz = Math.max(o.z0, Math.min(z, o.z1));
        if ((qx - x) * (qx - x) + (qz - z) * (qz - z) < PR * PR) (o === b ? nearB : others)[k * nx + i] = 1;
      }
    }
    const reach = new Uint8Array(nx * nz), free = c => dv[c] > PR && !others[c] && !nearB[c];
    const st = [], seed = c => {
      if (!free(c)) return;
      const i = c % nx, k = (c - i) / nx;
      if (inWalk(X0 + (i + 0.5) * RES, Z0 + (k + 0.5) * RES)) st.push(c);
    };
    for (let i = 0; i < nx; i++) { seed(i); seed(nx * (nz - 1) + i); }
    for (let k = 0; k < nz; k++) { seed(k * nx); seed(k * nx + nx - 1); }
    const flood = (ok, mark) => {
      while (st.length) {
        const c = st.pop(); if (mark[c] || !ok(c)) continue; mark[c] = 1;
        const i = c % nx, k = (c - i) / nx;
        if (i > 0) st.push(c - 1); if (i < nx - 1) st.push(c + 1); if (k > 0) st.push(c - nx); if (k < nz - 1) st.push(c + nx);
      }
    };
    flood(free, reach);
    const felt = new Uint8Array(nx * nz), open = c => nearB[c] && !others[c] && dv[c] > PR + TOL;
    for (let c = 0; c < nx * nz; c++) {
      if (!open(c)) continue;
      const i = c % nx;
      if ((i > 0 && reach[c - 1]) || (i < nx - 1 && reach[c + 1]) || (c >= nx && reach[c - nx]) || (c + nx < nx * nz && reach[c + nx])) st.push(c);
    }
    flood(open, felt);
    let empty = 0, tot = 0, sx = 0, sz = 0;
    for (let k = 0; k < nz; k++) for (let i = 0; i < nx; i++) {
      const c = k * nx + i; if (!nearB[c]) continue;
      tot++;
      if (felt[c]) { empty++; sx += X0 + (i + 0.5) * RES; sz += Z0 + (k + 0.5) * RES; }
    }
    // hint: the visible extent inside the box (its tight XZ bounds) and what would still be felt with the box cut to it
    let tx0 = Infinity, tx1 = -Infinity, tz0 = Infinity, tz1 = -Infinity, rest = 0;
    for (let k = 0; k < nz; k++) for (let i = 0; i < nx; i++) {
      if (!mark[k * nx + i]) continue;
      const x = X0 + (i + 0.5) * RES, z = Z0 + (k + 0.5) * RES;
      if (x < b.x0 || x > b.x1 || z < b.z0 || z > b.z1) continue;
      tx0 = Math.min(tx0, x - RES / 2); tx1 = Math.max(tx1, x + RES / 2); tz0 = Math.min(tz0, z - RES / 2); tz1 = Math.max(tz1, z + RES / 2);
    }
    for (let k = 0; k < nz; k++) for (let i = 0; i < nx; i++) {
      const c = k * nx + i; if (!felt[c]) continue;
      const x = X0 + (i + 0.5) * RES, z = Z0 + (k + 0.5) * RES;
      const qx = Math.max(tx0, Math.min(x, tx1)), qz = Math.max(tz0, Math.min(z, tz1));
      if ((qx - x) * (qx - x) + (qz - z) * (qz - z) < PR * PR) rest++;
    }
    if (b.id === dump) {   // 0.1 m cells: # visual, - / = (in the box) the capsule can't be there, . FELT (the box stops
      const rows = [];     // the player in the open), ' ' / _ (in the box) reachable, o unreachable
      for (let k = 0; k < nz; k += 2) { let r = ''; for (let i = 0; i < nx; i += 2) {
        const c = k * nx + i, x = X0 + (i + 0.5) * RES, z = Z0 + (k + 0.5) * RES, ins = x >= b.x0 && x <= b.x1 && z >= b.z0 && z <= b.z1;
        r += mark[c] ? '#' : felt[c] ? '.' : !free(c) ? (ins ? '=' : '-') : reach[c] ? (ins ? '_' : ' ') : 'o'; } rows.push(r); }
      return { dump: rows.join('\n'), box: b, felt: +(empty * RES * RES).toFixed(2) };
    }
    const area = empty * RES * RES;
    if (area > report) out.push({ id: b.id, piece: b.piece || '(' + b.kind + ')', kind: b.kind, walk: !!b.walk, emptyArea: +area.toFixed(2), frac: +(empty / Math.max(1, tot)).toFixed(2),
      at: [+(sx / empty).toFixed(1), +(sz / empty).toFixed(1)], cell: [Math.floor(sx / empty - Z.ox), Math.floor(sz / empty - Z.oz)],
      box: [b.x0, b.y0, b.z0, b.x1, b.y1, b.z1].map(q => +q.toFixed(2)),
      cut: tx0 < Infinity ? { w: +(tx0 - b.x0).toFixed(2), e: +(b.x1 - tx1).toFixed(2), n: +(tz0 - b.z0).toFixed(2), s: +(b.z1 - tz1).toFixed(2), rest: +(rest * RES * RES).toFixed(2) } : null });
  }
  if (dump !== undefined) return { dump: 'box not audited' };
  return { zone: Z.name || Z.id || '', audited, tris: tris.length, flagged: out.sort((a, b) => b.emptyArea - a.emptyArea) };
}
module.exports = { auditZone };
if (require.main === module) (async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  let plans = process.env.PLANS ? process.env.PLANS.split(',') : null;
  if (!plans) {
    const pg0 = await browser.newPage();
    await pg0.goto(base + '?autotest=1');
    await pg0.waitForFunction(() => window.IB && IB.CAMPAIGN && IB.CAMPAIGN.length, null, { timeout: 90000 });
    plans = await pg0.evaluate(() => IB.CAMPAIGN.slice());
    await pg0.close();
  }
  check('campaign has plans to audit', plans.length > 0, plans.join(','));
  const all = [];
  for (const plan of plans) {
    const t0 = Date.now();
    const pg = await browser.newPage({ viewport: { width: 320, height: 180 } });
    const logs = [];
    pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
    await pg.goto(base + '?autotest=1&plan=' + plan);
    await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
    await pg.evaluate(() => { window.requestAnimationFrame = () => 1; });
    const nz = await pg.evaluate(() => IB.Game.level.zones.length);
    let audited = 0; const bad = [], flagged = [];
    for (let zi = 0; zi < nz; zi++) {
      const res = await pg.evaluate(auditZone, [zi, REPORT]).catch(e => ({ error: String(e) }));
      if (res.error) { check(plan + ' zone ' + zi + ': audit', false, res.error); continue; }
      audited += res.audited;
      res.flagged.forEach(f => { f.plan = plan; f.zone = zi; flagged.push(f); all.push(f); if (f.emptyArea > LIMIT) bad.push(f); });
    }
    flagged.sort((a, b) => b.emptyArea - a.emptyArea);
    const fmt = f => 'z' + f.zone + ' ' + f.piece + ' ' + f.emptyArea + 'm2 (' + Math.round(f.frac * 100) + '%) cell ' + f.cell.join(',') + ' at ' + f.at.join(',');
    check(plan + ': no collision box with more than ' + LIMIT + ' m^2 of invisible wall (' + audited + ' boxes, ' + flagged.length + ' over ' + REPORT + ')', !bad.length,
      bad.slice(0, TOP).map(fmt).join(' | ') + (bad.length > TOP ? ' ... (' + bad.length + ')' : ''));
    if (process.env.VERBOSE) flagged.slice(0, TOP).forEach(f => console.log('    ' + fmt(f)));
    check(plan + ': no page errors', logs.length === 0, logs.slice(0, 3).join(' | '));
    console.log('  ' + plan + ' audited in ' + ((Date.now() - t0) / 1000).toFixed(0) + ' s');
    await pg.close();
  }
  if (process.env.OUT) fs.writeFileSync(process.env.OUT, JSON.stringify(all, null, 1));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
