// INKBOLT level bounds: for every zone of every campaign plan (IB.CAMPAIGN, so new maps are covered automatically) the
// real player movement code (IB.Player.step, its capsule-vs-box collision, step-up and jumps) is driven from every
// walkable spot next to an edge -- walls, closed gates, door modules, deck edges, rails, windows, prefabs -- outward,
// sprinting: plain, with jump spam, and with maxed Spring Boots (higher jump + double jump), on the ground and on every
// upper deck / walkable surface. With every gate shut it asserts that the player
//   (a) never leaves the zone's walled rectangle and never passes through a collision box (a solid-looking piece),
//   (b) never lands somewhere the zone's walkable area (the entry) cannot be reached from again (a soft-lock pit; the
//       plain player, since a pit only Spring Boots get out of still traps everyone else),
// (c) that every wall cell drawn on an upper layer ('#' in an "@layer <y>" grid) that someone stands next to is solid
// from that layer up to head height (a wall drawn on a mezzanine needs collision there, not just on the ground floor),
// and (d) that nobody jumps out of the trails between zones or the hatch room.
// Reachability is a graph of standable spots (1 m cells x surfaces: ground, box tops, decks, steps, elevator cabs)
// linked where the player can walk, step, jump (<= 1 m) or drop; a suspected pit is confirmed by trying to climb out
// of it with the real movement code before it fails. The render loop is paused; nothing renders while it runs.
// Run (after tools/build.py): node tests/e2e/bounds.spec.js      (PLANS=spire,classroom to pick plans; MAXF=n details)
// ~4 min for all 19 plans. On a failure: from = [col, row, feet y] of the start spot (zone cells), dir = yaw in
// degrees (0 = north, 90 = west), jump = 0 run / 1 jump spam / 2 Spring Boots, end = where the player got to.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const MAXF = +(process.env.MAXF || 6);
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

// ---- in-page analysis of one zone (runs inside the game page) ----
function analyzeZone(zi) {
  const G = IB.Game, L = G.level, W = L.world, Z = L.zones[zi], M = IB.MOVE, R = M.radius, H = M.height, CLIMB = 1.0;
  const theme = IB.Zones.themeOf(L.plan), wallH = (theme.wall && theme.wall.height) || 3;
  // every gate shut (a closed gate must hold), robots off
  L.zones.forEach(z => [z.exitGate, z.entryGate].forEach(g => { if (g) { g.was = 0; g.open = 0; g.target = 0; g.box.on = true; } }));
  if (IB.AI.robots) IB.AI.robots.forEach(r => { r.on = false; });
  // elevator boxes move / toggle at run time: the graph links each cab's stops instead
  const elev = new Set(), elevCells = [];
  (Z.elevators || []).forEach(E => {
    E.moving.forEach(m => elev.add(m.b)); E.stop.forEach(s => elev.add(s.b)); elev.add(E.door);
    const A = E.rot(-E.iw, -E.id), B = E.rot(E.iw, E.id);
    elevCells.push({ x0: Math.min(A[0], B[0]), x1: Math.max(A[0], B[0]), z0: Math.min(A[1], B[1]), z1: Math.max(A[1], B[1]), ys: [E.y0 + E.fy, E.y0 + E.top + E.fy] });
  });
  const tmp = [];
  function blocker(x, z, rad, ya, yb, skipElev, step) {   // an on box overlapping the circle whose y-range overlaps (ya, yb); step: not one the player steps up onto from ya
    W.query(x - rad, z - rad, x + rad, z + rad, tmp);
    for (let i = 0; i < tmp.length; i++) {
      const b = tmp[i]; if (b.y0 >= yb || b.y1 <= ya || (skipElev && elev.has(b)) || (step && b.y1 <= ya - 0.01 + (b.walk ? M.stepUpStair : M.stepUp))) continue;
      const cx = Math.max(b.x0, Math.min(x, b.x1)), cz = Math.max(b.z0, Math.min(z, b.z1));
      if ((x - cx) * (x - cx) + (z - cz) * (z - cz) < rad * rad) return b;
    }
    return null;
  }
  // ---- standable spots: per 1 m cell, the ground and every box top with head room ----
  const w = Z.w, h = Z.h, nodes = [], cellN = [];
  const cx = c => Z.ox + c + 0.5, cz = r => Z.oz + r + 0.5;
  for (let r = 0; r < h; r++) for (let c = 0; c < w; c++) {
    const x = cx(c), z = cz(r), ys = [W.groundAt(x, z)];
    W.query(x - 0.01, z - 0.01, x + 0.01, z + 0.01, tmp);
    const under = tmp.filter(b => !elev.has(b) && x >= b.x0 && x <= b.x1 && z >= b.z0 && z <= b.z1);
    under.forEach(b => ys.push(b.y1));
    elevCells.forEach(E => { if (x > E.x0 && x < E.x1 && z > E.z0 && z < E.z1) E.ys.forEach(y => ys.push(y)); });
    ys.sort((a, b) => a - b);
    const list = [];
    ys.forEach(y => {
      if (list.length && Math.abs(nodes[list[list.length - 1]].y - y) < 0.02) return;
      if (under.some(b => b.y0 < y + 0.01 && b.y1 > y + 0.01)) return;   // inside a box (under a ramp's top), not on it
      if (blocker(x, z, R * 0.9, y + 0.01, y + H, true, true)) return;
      list.push(nodes.length); nodes.push({ c, r, y, i: nodes.length });
    });
    cellN[r * w + c] = list;
  }
  const at = (c, r) => (c < 0 || r < 0 || c >= w || r >= h) ? [] : cellN[r * w + c];
  // ---- moves between neighbouring spots (walk, step, jump up to 1 m, drop) ----
  const fwd = nodes.map(() => []), rev = nodes.map(() => []), flat = new Uint8Array(nodes.length * 4);
  const D4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  function link(a, b) { fwd[a.i].push(b.i); rev[b.i].push(a.i); }
  nodes.forEach(a => {
    const xa = cx(a.c), za = cz(a.r);
    D4.forEach((d, di) => {
      const list = at(a.c + d[0], a.r + d[1]); if (!list.length) return;
      const xb = cx(a.c + d[0]), zb = cz(a.r + d[1]);
      let drop = null;
      list.forEach(k => { const b = nodes[k]; if (b.y <= a.y + 0.01) drop = b; });   // the highest spot at or below a
      list.forEach(k => {
        const b = nodes[k];
        if (b.y > a.y + CLIMB) return;
        if (b.y <= a.y + 0.01 && b !== drop) return;
        const base = Math.max(a.y, b.y);
        if (b.y > a.y + 0.01 && blocker(xa, za, R * 0.9, a.y + 0.01, b.y + H, true, true)) return;   // head room for the jump
        if (b.y < a.y - 0.01 && blocker(xb, zb, R * 0.9, b.y + 0.01, a.y + H, true, true)) return;   // nothing to land on between
        for (let s = 0.25; s < 0.8; s += 0.25) if (blocker(xa + (xb - xa) * s, za + (zb - za) * s, R * 0.9, base + 0.01, base + H, true, true)) return;
        link(a, b);
        if (Math.abs(b.y - a.y) < 0.05) flat[a.i * 4 + di] = 1;
      });
    });
  });
  elevCells.forEach(E => nodes.forEach(a => {   // an elevator cab carries the player between its stops
    const x = cx(a.c), z = cz(a.r); if (!(x > E.x0 && x < E.x1 && z > E.z0 && z < E.z1)) return;
    at(a.c, a.r).forEach(k => { const b = nodes[k]; if (b !== a && E.ys.some(y => Math.abs(y - a.y) < 0.02) && E.ys.some(y => Math.abs(y - b.y) < 0.02)) link(a, b); });
  }));
  function bfs(start, adj) {
    const seen = new Uint8Array(nodes.length), q = [start]; seen[start] = 1;
    for (let k = 0; k < q.length; k++) adj[q[k]].forEach(n => { if (!seen[n]) { seen[n] = 1; q.push(n); } });
    return seen;
  }
  const ec = Math.floor(Z.entry.x - Z.ox), er = Math.floor(Z.entry.z - Z.oz), e0 = at(ec, er)[0];
  if (e0 === undefined) return { error: 'no standable spot at the entry ' + ec + ',' + er };
  const reach = bfs(e0, fwd), back = bfs(e0, rev);
  // ---- the real player, driven out of every reachable edge spot ----
  const p = G.player, dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: true, jumpPressed: false, slidePressed: false, crouch: false };
  const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
  p.protect = 1e9; p.health = p.maxHp; p.doubleJump = false; p.jumpMul = 1; p.speedMul = 1;
  function outside(x, z) { return x < Z.ox + 1 || x > Z.ox + w - 1 || z < Z.oz + 1 || z > Z.oz + h - 1; }
  function inside() {   // the capsule centre inside a solid box (a piece that looks solid let the player through)
    W.query(p.x - 0.01, p.z - 0.01, p.x + 0.01, p.z + 0.01, tmp);
    for (let i = 0; i < tmp.length; i++) {
      const b = tmp[i]; if (elev.has(b)) continue;
      if (p.x > b.x0 + 0.05 && p.x < b.x1 - 0.05 && p.z > b.z0 + 0.05 && p.z < b.z1 - 0.05 && b.y0 < p.y + H - 0.2 && b.y1 > p.y + 0.2) return b;
    }
    return null;
  }
  function place(x, y, z, yaw) {
    p.x = x; p.y = y; p.z = z; p.vx = p.vy = p.vz = 0; p.onGround = true; p.coyote = 0; p.jumpBuf = 0; p.sliding = false; p.slideCd = 0;
    p.crouching = false; p.stamina = M.stamina; p.staminaRest = 0; p.knockX = p.knockZ = 0; p.yaw = yaw; p.usedDouble = false;
  }
  // the best jumper the game makes: Spring Boots at max level (jump height x1.45 and a double jump)
  const U = IB.UPGRADES && IB.UPGRADES.find(u => u.id === 'jump'), FX = U && IB.Upgrades ? IB.Upgrades.effects({ jump: U.max }) : { jumpMul: 1.45, doubleJump: true };
  // jump: 0 run, 1 run + jump spam, 2 run + Spring Boots jumps (a double jump at the apex)
  function drive(yaw, jump, frames) {   // returns null, or {kind, box?}
    p.yaw = yaw; p.jumpMul = jump === 2 ? FX.jumpMul : 1; p.doubleJump = jump === 2 && !!FX.doubleJump;
    for (let i = 0; i < frames; i++) {
      inp.jumpPressed = jump === 1 ? i % 9 === 4 : jump === 2 ? (i % 30 === 4 || i % 30 === 24) : false;
      IB.Player.step(p, inp, W, dt, null);
      if (outside(p.x, p.z)) return { kind: 'escaped' };
      const b = inside(); if (b) return { kind: 'through', box: b };
    }
    for (let i = 0; i < 240 && !p.onGround; i++) { IB.Player.step(p, idle, W, dt, null); if (outside(p.x, p.z)) return { kind: 'escaped' }; }
    return null;
  }
  function clear(x0, z0, x1, z1, y) {   // the capsule fits all along a straight walk (no thin wall in between)
    for (let s = 0; s <= 1.001; s += 0.2) if (blocker(x0 + (x1 - x0) * s, z0 + (z1 - z0) * s, R * 0.9, y + 0.01, y + H, true, true)) return false;
    return true;
  }
  function spotOK() {   // standing where the entry can be reached from again
    const c = Math.floor(p.x - Z.ox), r = Math.floor(p.z - Z.oz);
    for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
      if (at(c + dc, r + dr).some(k => back[k] && Math.abs(nodes[k].y - p.y) < 0.4 && clear(p.x, p.z, cx(c + dc), cz(r + dr), Math.max(p.y, nodes[k].y)))) return true;
    }
    return false;
  }
  function climbOut() {   // a suspected pit: try to get back out with the real movement code
    const x0 = p.x, y0 = p.y, z0 = p.z;
    for (let k = 0; k < 16; k++) for (const j of [1, 0]) {
      place(x0, y0, z0, k * Math.PI / 8);
      if (drive(k * Math.PI / 8, j, 120)) continue;
      if (p.onGround && spotOK()) return true;
      for (let k2 = 0; k2 < 8; k2++) {   // one more leg (out of an L-shaped nook)
        const x1 = p.x, y1 = p.y, z1 = p.z;
        place(x1, y1, z1, k2 * Math.PI / 4);
        if (!drive(k2 * Math.PI / 4, 1, 90) && p.onGround && spotOK()) return true;
        place(x1, y1, z1, 0);
      }
    }
    return false;
  }
  const fails = [], seenF = {};
  let sims = 0, starts = 0;
  function fail(kind, a, yaw, jump, extra) {
    const key = kind + ':' + (kind === 'pit' ? Math.round(p.x) + ',' + Math.round(p.z) + ',' + Math.round(p.y) : a.i);
    if (seenF[key]) return; seenF[key] = 1;
    fails.push(Object.assign({ kind, from: [a.c, a.r, +a.y.toFixed(2)], dir: Math.round(yaw * 180 / Math.PI), jump,
      end: [+(p.x - Z.ox).toFixed(2), +p.y.toFixed(2), +(p.z - Z.oz).toFixed(2)] }, extra || {}));
  }
  nodes.forEach(a => {
    if (!reach[a.i]) return;
    if (outside(cx(a.c), cz(a.r))) { p.x = cx(a.c); p.y = a.y; p.z = cz(a.r); return fail('escaped', a, 0, false, { graph: 1 }); }   // the graph walks out
    const miss = [];
    for (let di = 0; di < 4; di++) if (!flat[a.i * 4 + di]) miss.push(D4[di]);
    if (!miss.length) return;
    starts++;
    miss.forEach(d => {
      const base = Math.atan2(-d[0], -d[1]);   // yaw that faces +d (camera forward is -Z at yaw 0)
      [-Math.PI / 4, 0, Math.PI / 4].forEach(off => [1, 0, 2].forEach(jump => {
        const yaw = base + off; sims++;
        place(cx(a.c), a.y, cz(a.r), yaw);
        const res = drive(yaw, jump, jump === 2 ? 60 : 50);
        if (res) return fail(res.kind, a, yaw, jump, res.box ? { box: res.box.kind + ' ' + [res.box.x0 - Z.ox, res.box.y0, res.box.z0 - Z.oz, res.box.x1 - Z.ox, res.box.y1, res.box.z1 - Z.oz].map(v => +v.toFixed(2)).join(',') } : null);
        if (jump === 2 || spotOK()) return;   // pits: the plain player (a pit only Spring Boots get out of still traps)
        const ex = p.x, ey = p.y, ez = p.z;
        if (climbOut()) return;
        p.x = ex; p.y = ey; p.z = ez;
        fail('pit', a, yaw, jump);
      }));
    });
  });
  // ---- (c) walls drawn on upper layers are solid there ----
  const layerWalls = [];
  Z.grid.layers.forEach(lg => {
    if (!(lg.y > 0) || !nodes.some(n => reach[n.i] && Math.abs(n.y - lg.y) < 0.6)) return;   // a layer nobody stands on (a roof)
    for (let r = 0; r < lg.h; r++) for (let c = 0; c < lg.w; c++) {
      if (lg.rows[r][c] !== '#') continue;
      const x = cx(c), z = cz(r);
      for (const y of [lg.y + 0.3, lg.y + 1.0, lg.y + 1.6]) if (!blocker(x, z, 0.05, y - 0.01, y + 0.01, false)) { layerWalls.push([c, r, lg.y, +y.toFixed(2)]); break; }
    }
  });
  if (window.__BOUNDS_DEBUG) window.__BOUNDS_DEBUG({ nodes, cellN, reach, back, fwd, flat });
  return { zone: Z.plan.map, nodes: nodes.length, reach: reach.reduce((s, v) => s + v, 0), starts, sims, fails, layerWalls, wallH };
}

// the corridors between zones and the exit waypath to the hatch: no way out over their walls either
function analyzeTrails() {
  const G = IB.Game, L = G.level, W = L.world, p = G.player, M = IB.MOVE, dt = 1 / 60, out = [];
  L.zones.forEach(z => [z.exitGate, z.entryGate].forEach(g => { if (g) { g.was = 0; g.open = 0; g.target = 0; g.box.on = true; } }));
  const U = IB.UPGRADES && IB.UPGRADES.find(u => u.id === 'jump'), FX = U && IB.Upgrades ? IB.Upgrades.effects({ jump: U.max }) : { jumpMul: 1.45, doubleJump: true };
  const inp = { mx: 0, mz: -1, sprint: true, jumpPressed: false, slidePressed: false, crouch: false };
  let runs = 0;
  L.trails.forEach((tr, ti) => {
    const hz = L.hatch && ti === L.trails.length - 1 ? L.hatch.z : null;
    for (let z = tr.z1 + 0.5; z < tr.z0 - 0.4; z += 1) for (const yaw of [Math.PI / 2, -Math.PI / 2, Math.PI / 4, -Math.PI / 4, 3 * Math.PI / 4, -3 * Math.PI / 4]) for (const jump of [1, 2]) {
      Object.assign(p, { x: tr.x, y: 0, z, vx: 0, vy: 0, vz: 0, onGround: true, coyote: 0, jumpBuf: 0, sliding: false, stamina: M.stamina, knockX: 0, knockZ: 0, yaw, usedDouble: false,
        jumpMul: jump === 2 ? FX.jumpMul : 1, doubleJump: jump === 2 && !!FX.doubleJump, protect: 1e9 });
      runs++;
      for (let i = 0; i < 70; i++) {
        inp.jumpPressed = jump === 1 ? i % 9 === 4 : (i % 30 === 4 || i % 30 === 24);
        IB.Player.step(p, inp, W, dt, null);
        const dx = Math.abs(p.x - tr.x), inHatch = hz !== null && p.z < tr.z1;
        if (inHatch ? (dx > 2.8 || p.z < hz - 2.75) : dx > 2.05) { out.push({ trail: ti, from: +(z - tr.z1).toFixed(1), yaw: Math.round(yaw * 180 / Math.PI), jump, end: [+(p.x - tr.x).toFixed(2), +p.y.toFixed(2), +(p.z - tr.z1).toFixed(2)] }); return; }
      }
    }
  });
  return { runs, fails: out };
}
module.exports = { analyzeZone, analyzeTrails };
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
  check('campaign has plans to check', plans.length > 0, plans.join(','));
  for (const plan of plans) {
    const t0 = Date.now();
    const pg = await browser.newPage({ viewport: { width: 480, height: 270 } });
    const logs = [];
    pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
    await pg.goto(base + '?autotest=1&plan=' + plan);
    await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
    await pg.evaluate(() => { window.requestAnimationFrame = () => 1; });
    await pg.waitForTimeout(100);
    const nz = await pg.evaluate(() => IB.Game.level.zones.length);
    for (let zi = 0; zi < nz; zi++) {
      const res = await pg.evaluate(analyzeZone, zi);
      const tag = plan + ' zone ' + zi + (res.zone ? ' (' + res.zone + ')' : '');
      if (res.error) { check(tag + ': analysis', false, res.error); continue; }
      const by = k => res.fails.filter(f => f.kind === k);
      const info = f => f.slice(0, MAXF).map(x => JSON.stringify(x)).join(' ') + (f.length > MAXF ? ' ...' : '');
      const stat = res.reach + '/' + res.nodes + ' spots reachable, ' + res.starts + ' edge spots, ' + res.sims + ' runs';
      check(tag + ': the player never leaves the zone (' + stat + ')', !by('escaped').length, info(by('escaped')));
      check(tag + ': the player never passes through a solid piece', !by('through').length, info(by('through')));
      check(tag + ': no soft-lock pits (every landing spot leads back to the entry)', !by('pit').length, info(by('pit')));
      check(tag + ': walls drawn on upper layers are solid there', !res.layerWalls.length, res.layerWalls.slice(0, MAXF).map(v => JSON.stringify(v)).join(' '));
    }
    const tr = await pg.evaluate(analyzeTrails);
    check(plan + ': the player never leaves a trail or the hatch room (' + tr.runs + ' runs)', !tr.fails.length, tr.fails.slice(0, MAXF).map(v => JSON.stringify(v)).join(' '));
    check(plan + ': no page errors', logs.length === 0, logs.slice(0, 3).join(' | '));
    console.log('  ' + plan + ' checked in ' + ((Date.now() - t0) / 1000).toFixed(0) + ' s');
    await pg.close();
  }
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
