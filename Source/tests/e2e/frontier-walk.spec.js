// INKBOLT Cinder Ridge Outpost (plan 'frontier'): the walk through both zones and the climbs. The player walks the
// main street from the main gate to the back gate, the trail, the logging road and the ravine floor to the exit gate
// and the hatch (no invisible walls, nothing blocks the way); climbs a watchtower stair to its platform, walks into
// the general store and up its stair to the upper floor by the open front windows, walks up the west plateau's trail
// and the lookout stair onto the deck (5.54 m), and crosses the rope bridge over the ravine at 3.2 m (its ropes keep
// the player on it). Ground robots follow: up the store stair, up to the lookout deck, across the ravine. The water
// wheel's rotor turns. The render loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/frontier-walk.spec.js
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
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

(async () => {
  const srv = await serve(), base = 'http://localhost:' + srv.address().port + '/Play%20Inkbolt.html';
  const browser = await chromium.launch({ args: ARGS });
  const ctx = await browser.newContext({ viewport: { width: 640, height: 360 } });
  const pg = await ctx.newPage();
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto(base + '?autotest=1&plan=frontier');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    const idle = { mx: 0, mz: 0, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
    window.__sim = (secs, zi) => {
      const G = IB.Game, p = G.player, dt = 1 / 60;
      const ctx = { player: p, world: G.level.world, level: G.level, activeZone: zi, hurt: G.hurt, shake: function () { }, onKill: function () { } };
      for (let i = 0; i < Math.round(secs * 60); i++) { IB.Player.step(p, idle, G.level.world, dt, null); IB.AI.update(dt, ctx); if (IB.Projectiles) IB.Projectiles.update(dt, ctx); IB.AI.updateCorpses(dt); }
    };
    // walk toward each way point in turn (zone-local metres of zone zi; a point may lie outside it, on the trail)
    window.__route = (zi, pts, secs) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi], dt = 1 / 60, inp = { mx: 0, mz: -1, sprint: false, jumpPressed: false, slidePressed: false, crouch: false };
      let k = 0, lo = 1e9, hi = -1e9, n = 0, stuck = 0, last = [p.x, p.z];
      while (k < pts.length && n++ < secs * 60) {
        const tx = Z.ox + pts[k][0], tz = Z.oz + pts[k][1], dx = tx - p.x, dz = tz - p.z;
        if (Math.hypot(dx, dz) < 0.3) { k++; continue; }
        p.yaw = Math.atan2(-dx, -dz);
        IB.Player.step(p, inp, G.level.world, dt, null);
        lo = Math.min(lo, p.y); hi = Math.max(hi, p.y);
        if (n % 60 === 0) { if (Math.hypot(p.x - last[0], p.z - last[1]) < 0.2) stuck++; last = [p.x, p.z]; }
      }
      return { reached: k, of: pts.length, lo: +lo.toFixed(2), hi: +hi.toFixed(2), x: +(p.x - Z.ox).toFixed(2), y: +p.y.toFixed(2), z: +(p.z - Z.oz).toFixed(2), stuck };
    };
    window.__place = (zi, x, z, y) => {
      const G = IB.Game, p = G.player, Z = G.level.zones[zi];
      IB.AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
      G.level.zones.forEach(q => { q.queue.length = 0; q.plan = Object.assign({}, q.plan, { waves: [[]] }); q.wave = 0; });
      p.protect = 0; p.health = p.maxHp; p.x = Z.ox + x; p.z = Z.oz + z; p.y = y; p.vx = p.vz = p.vy = 0;
    };
    // every gate open (the zones count as cleared for the walk)
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });
  // nav: open cells on the tower platforms and the store's upper floor (zone 1), the plateaus, the bridge and the
  // lookout deck (zone 2)
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, h36: 0, h355: 0, plat: 0, deck: 0 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k]) {
      const h = N.h[k];
      if (Math.abs(h - 3.6) < 0.005) o.h36++; if (Math.abs(h - 3.59) < 0.005) o.h355++; if (Math.abs(h - 3.2) < 0.02) o.plat++; if (Math.abs(h - 5.54) < 0.02) o.deck++;
    }
    return o;
  }));
  check('nav: zone 1 has open cells on the tower platforms and the store upstairs, zone 2 on the plateaus and the lookout deck',
    nav[0].h36 > 60 && nav[0].h355 > 60 && nav[1].plat > 2000 && nav[1].deck > 40, JSON.stringify(nav));

  // ---- the walk: main gate -> street -> back gate -> trail -> logging road -> ravine floor -> exit gate -> hatch
  let r = await pg.evaluate(() => { __place(0, 35.5, 67.0, 0); return __route(0, [[34.0, 60.0], [33.5, 50.0], [32.0, 40.0], [32.0, 30.0], [35.5, 22.0], [35.5, 2.0], [35.5, -6.0], [35.5, -13.0]], 120); });
  check('walk zone 1: the main street from the main gate through the back gate onto the trail', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[37.5, 69.0], [37.5, 46.0], [34.0, 38.0], [32.5, 29.0], [32.5, 12.0], [32.5, 2.0], [32.5, -4.0], [32.5, -20.0]], 140));
  check('walk zone 2: the logging road and the ravine floor to the exit gate and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1: a watchtower stair, the general store and its stair to the upper floor
  r = await pg.evaluate(() => { __place(0, 2.5, 10.2, 0); return __route(0, [[2.5, 9.2], [2.5, 3.0]], 30); });
  check('zone 1: up the north-west watchtower stair onto its platform (3.6 m)', r.reached === 2 && Math.abs(r.y - 3.6) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 2.5, 2.5, 3.6); return __route(0, [[2.5, -0.5]], 3); });
  check('zone 1: the tower railing keeps the player on the platform', r.lo > 3.55, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 32.5, 59.0, 0); return __route(0, [[29.0, 59.0], [25.0, 57.6], [21.0, 57.6], [20.85, 58.0], [20.85, 63.2], [23.5, 63.2], [23.5, 61.5], [27.0, 61.5]], 40); });
  check('zone 1: into the general store, up its stair to the upper floor by the open windows (3.59 m)', r.reached === r.of && Math.abs(r.y - 3.59) < 0.05, JSON.stringify(r));
  const sight = await pg.evaluate(() => { const W = IB.Game.level.world, Z = IB.Game.level.zones[0]; return W.los(Z.ox + 27.3, 3.59 + 1.5, Z.oz + 61.5, Z.ox + 36, 1.5, Z.oz + 61.5); });
  check('zone 1: the open upper window looks down onto the street (clear sight line)', sight, String(sight));

  // ---- zone 2: up the west plateau's trail and the lookout stair; across the rope bridge
  r = await pg.evaluate(() => { __place(1, 17.0, 40.0, 0); return __route(1, [[16.5, 28.0], [16.0, 21.0], [12.0, 19.5], [11.0, 15.0], [10.8, 10.0], [5.0, 10.0]], 60); });
  check('zone 2: up the trail onto the west plateau (3.2 m) and the lookout stair onto the deck (5.54 m)', r.reached === r.of && Math.abs(r.y - 5.54) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 4.0, 10.0, 5.54); return __route(1, [[0.5, 10.0]], 3); });
  check('zone 2: the lookout railing keeps the player on the deck over the cliff edge', r.lo > 5.49, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 25.5, 11.0, 3.2); return __route(1, [[28.0, 11.0], [36.5, 11.0], [38.5, 11.0]], 20); });
  check('zone 2: across the rope bridge over the ravine at 3.2 m', r.reached === 3 && r.lo > 3.15 && Math.abs(r.y - 3.2) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 32.5, 11.0, 3.2); return __route(1, [[32.5, 14.0]], 3); });
  check('zone 2: the bridge ropes keep the player on the bridge', r.lo > 3.15, JSON.stringify(r));

  // ---- robots follow
  async function chase(zi, at, robots, secs, goal) {
    const list = await pg.evaluate(([zi, at, robots]) => {
      __place(zi, at[0], at[1], at[2]);
      IB.Game.player.protect = 1e9;
      const Z = IB.Game.level.zones[zi];
      return robots.map(([type, c, r]) => {
        const slot = __TEST__.spawnRobot(type, Z.ox + c + 0.5, Z.oz + r + 0.5);
        const rb = IB.AI.types[type].slots[slot]; rb.state = IB.AI.VIS[type].home; rb.st = 0; rb.thinkT = 0; rb.zone = zi;
        return [type, slot];
      });
    }, [zi, at, robots]);
    let best = 0, last = null, t = 0;
    while (t < secs) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2) }; }, [list, zi]);
      t += 0.5; if (last.on && last.d < 4) best = Math.max(best, last.y);
      if (best > goal) break;
    }
    return { best, last, t };
  }
  let w = await chase(0, [26.0, 61.5, 3.59], [['crawler', 36, 50]], 60, 3.5);
  check('zone 1: a Crawler from the street climbs the store stair to the player upstairs (< 4 m) within 60 s', w.best > 3.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [4.0, 10.0, 5.54], [['crawler', 22, 40]], 80, 5.45);
  check('zone 2: a Crawler from the camp climbs the plateau and the lookout stair to the player (< 4 m) within 80 s', w.best > 5.5, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [44.0, 9.0, 3.2], [['blader', 16, 8]], 80, 3.1);
  check('zone 2: a Blade Bot on the west plateau crosses the ravine to the player (< 4 m) on the east plateau within 80 s', w.best > 3.1, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- run / rail / span / wall pieces lie along their line of cells: the drawn vertices (outline shell left out)
  // inside each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    function ext(zi, c0, r0, w, h, y0, y1) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], x0 = Z.ox + c0, x1 = Z.ox + c0 + w, z0 = Z.oz + r0, z1 = Z.oz + r0 + h;
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let i = 0; i < P.length; i += 3) {
          if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
          const x = P[i], y = P[i + 1], z = P[i + 2];
          if (y < y0 || y > y1 || x < x0 || x > x1 || z < z0 || z > z1) continue;
          e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z);
        }
      });
      return [e[1] - e[0], e[3] - e[2]];
    }
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r);
      for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
        const ch = at(c, r);
        if (ch === 'f') {   // corral fence: a straight run cell carries the full module along its run
          const ew = at(c - 1, r) === 'f' && at(c + 1, r) === 'f' && at(c, r - 1) !== 'f' && at(c, r + 1) !== 'f';
          const ns = at(c, r - 1) === 'f' && at(c, r + 1) === 'f' && at(c - 1, r) !== 'f' && at(c + 1, r) !== 'f';
          if (ew || ns) expect('fence', zi, c, r, 1, 1, 0.4, 0.6, ew, 0.9, 0.3);
        }
      }
      // palisade modules along the stockade walls (zone 1): long along the wall, thin across it
      if (zi === 0) {
        for (let c = 4; c < g.w - 4; c++) { if (Math.abs(c - 35) > 3) { expect('palisade', 0, c, 0, 1, 1, 0.0, 3.0, true, 0.85, 0.7); expect('palisade', 0, c, g.h - 1, 1, 1, 0.0, 3.0, true, 0.85, 0.7); } }
        for (let r = 10; r < g.h - 10; r++) { expect('palisade', 0, 0, r, 1, 1, 0.0, 3.0, false, 0.85, 0.7); expect('palisade', 0, g.w - 1, r, 1, 1, 0.0, 3.0, false, 0.85, 0.7); }
      }
      // [n, 1] prefabs and spans: the hitching rails, troughs, firewood stacks, felled logs, log piles, the flume, the bridge
      const blocks = (ch) => { const seen = {}, res = []; for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) { if (at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (at(c + w, r) === ch) w++; while (at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
      [['r', 0.85, 1.1, 2.6, 0.4], ['t', 0.1, 0.75, 1.6, 0.9], ['e', 0.3, 1.2, 1.6, 0.9], ['9', 0.1, 0.6, 4.2, 0.95], ['7', 0.1, 0.9, 3.5, 1.9], ['|', 5.5, 6.0, 3.8, 0.8], ['=', 3.0, 3.2, 6.6, 1.5]].forEach(([ch, y0, y1, minA, maxC]) => {
        blocks(ch).forEach(([c, r, w, h]) => {
          const n = ch === '|' ? 1 : (ch === '=' ? 1 : Math.max(1, Math.round(Math.max(w, h) / ({ r: 3, t: 2, e: 2, '9': 5, '7': 4 })[ch])));
          for (let k = 0; k < n; k++) {
            const L0 = ({ r: 3, t: 2, e: 2, '9': 5, '7': 4 })[ch] || Math.max(w, h);
            if (w >= h) expect(ch, zi, c + k * L0, r, L0, h, Z.ox !== undefined ? y0 : y0, y1, true, minA, maxC);
            else expect(ch, zi, c, r + k * L0, w, L0, y0, y1, false, minA, maxC);
          }
        });
      });
    });
    return out;
  });
  check('run, rail, span and wall pieces lie along their line of cells (none a quarter turn off)', runs.checked > 250 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 6).join(' | '));

  // ---- the water wheel turns
  const wheel = await pg.evaluate(() => {
    const L = IB.Game.level; let m = null;
    L.zones[1].group.traverse(o => { if (o.isMesh && o.geometry === IB.Assets.get('KIT_FRONTIER_Wheel_Rotor')) m = o; });
    if (!m) return null;
    const a0 = m.rotation.x; IB.Zones.updateClouds(L, 0.5); return { found: true, turned: Math.abs(m.rotation.x - a0) > 0.1, y: +m.position.y.toFixed(2) };
  });
  check('zone 2: the water wheel rotor stands on its frame and turns', wheel && wheel.turned && Math.abs(wheel.y - 2.95) < 0.05, JSON.stringify(wheel));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
