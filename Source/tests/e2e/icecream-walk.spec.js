// INKBOLT Scoops & Cream (plan 'icecream'): the walk through both zones and the climbs. The player walks from the
// entrance vestibule through the automatic doors, past the giant cone and through a counter gap behind the counters
// to the STAFF ONLY gate and the trail; then through the creamery from the staff entrance past the novelty line and
// the churns to the exit gate and the hatch (no invisible walls, nothing blocks the way). Climbs: the terrace steps
// onto the terrace (1.2 m; its rail keeps the player on it), the steel stair onto the mezzanine (3.5 m) and into the
// PARTY ROOM through its doorway. Ground robots follow onto the terrace, up to the mezzanine and into the party room.
// Every link run (belts, vestibule glass, terrace rails, freezer panels, mezzanine rails) lies along its line of
// cells; counters, doors and wall-backed pieces face the right way (collision boxes and drawn vertices).
// The render loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/icecream-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=icecream');
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && IB.Game.run && IB.Game.run.started && !document.getElementById('boot'), null, { timeout: 120000 });
  await pg.evaluate(() => {
    window.requestAnimationFrame = () => 1;
    IB.Game.level.world.boxes.forEach(b => { if (b.kind === 'canister') b.on = false; });
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
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });

  // nav: open cells on the terrace (1.2 m) in zone 1, on the mezzanine and in the party room (3.5 m) in zone 2
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, terrace: 0, deck: 0 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k]) { const h = N.h[k]; if (Math.abs(h - 1.2) < 0.02) o.terrace++; if (Math.abs(h - 3.5) < 0.02) o.deck++; }
    return o;
  }));
  check('nav: zone 1 has open cells on the terrace, zone 2 on the mezzanine', nav[0].terrace > 300 && nav[1].deck > 400, JSON.stringify(nav));

  // ---- the walk: vestibule -> doors -> past the cone -> counter gap -> behind the counters -> gate -> trail
  let r = await pg.evaluate(() => { __place(0, 35.5, 57.5, 0); return __route(0, [[36.0, 53.0], [36.5, 49.0], [36.5, 28.0], [42.5, 27.5], [42.5, 16.0], [46.5, 13.0], [46.5, 4.6], [35.5, 4.6], [35.5, -2.0], [35.5, -8.0]], 150); });
  check('walk zone 1: from the vestibule through the doors, past the cone and a counter gap to the STAFF ONLY gate and the trail', r.reached === r.of && r.stuck === 0 && r.hi < 0.4, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 35.5, 57.5, 0); return __route(1, [[35.5, 41.0], [36.5, 39.5], [36.5, 4.0], [35.5, 2.5], [35.5, -2.0], [35.5, -20.0]], 150); });
  check('walk zone 2: from the staff entrance past the novelty line and the churns to the exit gate and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.4, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1: up the terrace steps; the rail keeps the player on the terrace
  r = await pg.evaluate(() => { __place(0, 5.5, 58.5, 0); return __route(0, [[5.5, 54.0], [8.0, 48.5]], 30); });
  check('zone 1: up the west steps onto the terrace (1.2 m)', r.reached === r.of && Math.abs(r.y - 1.2) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 12.5, 58.5, 0); return __route(0, [[12.5, 53.5]], 20); });
  check('zone 1: up the east steps onto the terrace', r.reached === r.of && Math.abs(r.y - 1.2) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 10.5, 45.6, 1.2); return __route(0, [[10.5, 42.0]], 4); });
  check('zone 1: the terrace rail keeps the player on the terrace (north edge)', r.lo > 1.15, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 15.5, 49.5, 1.2); return __route(0, [[19.0, 49.5]], 4); });
  check('zone 1: the terrace rail keeps the player on the terrace (east edge)', r.lo > 1.15, JSON.stringify(r));

  // ---- zone 2: up the stair onto the mezzanine and into the party room; the rail keeps the player up
  r = await pg.evaluate(() => { __place(1, 19.0, 25.5, 0); return __route(1, [[19.0, 15.0], [19.0, 8.0], [10.0, 8.0], [10.0, 4.5]], 40); });
  check('zone 2: up the steel stair onto the mezzanine (3.5 m) and into the PARTY ROOM', r.reached === r.of && Math.abs(r.y - 3.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 12.5, 15.4, 3.5); return __route(1, [[12.5, 19.0]], 4); });
  check('zone 2: the mezzanine rail keeps the player on the deck', r.lo > 3.45, JSON.stringify(r));
  // the walk-in freezer: in through its door and out again
  r = await pg.evaluate(() => { __place(1, 7.5, 15.0, 0); return __route(1, [[7.5, 10.5], [7.5, 9.6], [7.5, 15.0]], 20); });
  check('zone 2: into the walk-in freezer through its door and out again', r.reached === r.of && r.stuck === 0, JSON.stringify(r));

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
  let w = await chase(0, [8.5, 49.5, 1.2], [['crawler', 30, 40]], 60, 1.15);
  check('zone 1: a Crawler from the tables climbs the terrace steps to the player (< 4 m) within 60 s', w.best > 1.15, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [10.0, 4.5, 3.5], [['crawler', 40, 40]], 80, 3.45);
  check('zone 2: a Crawler from the prep tables climbs the stair into the party room to the player (< 4 m) within 80 s', w.best > 3.45, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [2.5, 11.5, 3.5], [['blader', 50, 30]], 80, 3.45);
  check('zone 2: a Blade Bot climbs to the player at the far end of the mezzanine within 80 s', w.best > 3.45, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- runs along their line of cells (each Full module's box long along the run) and facings (boxes, vertices)
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, bad = [], n = {};
    const FULL = { KIT_ICECREAM_BeltFull: 'q', KIT_ICECREAM_VGlassFull: 'e', KIT_ICECREAM_TRailFull: 'l', KIT_ICECREAM_PanFull: 'i', KIT_ICECREAM_RailFull: 'r' };
    L.world.boxes.forEach(b => {
      const z = L.zones[b.zone]; if (!z) return;
      const ch = FULL[b.piece]; if (!ch) return;
      const c = Math.floor((b.x0 + b.x1) / 2 - z.ox), r = Math.floor((b.z0 + b.z1) / 2 - z.oz), ex = b.x1 - b.x0, ez = b.z1 - b.z0;
      const grids = [z.grid].concat(z.grid.layers.filter(l => Math.abs(l.y - b.y0) < 0.3));
      const G = grids.find(g => g.at(c, r) === ch); if (!G) { bad.push('no ' + ch + ' cell under ' + b.piece + ' at ' + c + ',' + r); return; }
      n[ch] = (n[ch] || 0) + 1;
      const ew = G.at(c - 1, r) === ch && G.at(c + 1, r) === ch, ns = G.at(c, r - 1) === ch && G.at(c, r + 1) === ch;
      if (ew && !(ex > 4 * ez)) bad.push(ch + ' east-west run, box ' + ex.toFixed(2) + ' x ' + ez.toFixed(2) + ' at ' + c + ',' + r);
      if (ns && !(ez > 4 * ex)) bad.push(ch + ' north-south run, box ' + ex.toFixed(2) + ' x ' + ez.toFixed(2) + ' at ' + c + ',' + r);
    });
    // drawn vertices of a block (outline shell left out) in a height band: [extent x, extent z, centre z]
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
      return [e[1] - e[0], e[3] - e[2], (e[2] + e[3]) / 2 - Z.oz];
    }
    let checked = 0;
    // the counters (front south): the glass hood / sneeze guard / cone tree stands on the customer (south) half
    const g1 = L.zones[0].grid;
    // block starts along a row: runs of ch cut into [w]-wide blocks
    function blocksOf(g, row, ch, w) { const out = []; for (let c = 0; c < g.w; c++) if (g.at(c, row) === ch && g.at(c - 1, row) !== ch) { let n = 0; while (g.at(c + n, row) === ch) n++; for (let k = 0; k + w <= n; k += w) out.push(c + k); } return out; }
    for (const [ch, w, y0, y1] of [['D', 2, 1.1, 1.36], ['U', 3, 1.3, 1.5]]) {
      blocksOf(g1, 6, ch, w).forEach(c => {
        const [ex, ez, zc] = ext(0, c, 6, w, 2, y0, y1); checked++;
        if (!(ex > w - 0.4 && zc > 7.0)) bad.push(ch + ' counter at ' + c + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2) + ' zc ' + zc.toFixed(2));
      });
    }
    // the window bars: the ledge (1.0 - 1.05 m) against the shop window (south), long along the wall
    blocksOf(g1, 58, 'n', 2).forEach(c => {
      const [ex, ez, zc] = ext(0, c, 58, 2, 1, 1.0, 1.06); checked++;
      if (!(ex > 1.8 && ez < 0.5 && zc > 58.5)) bad.push('window bar at ' + c + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2) + ' zc ' + zc.toFixed(2));
    });
    // the vestibule doors (along their glass line, east - west): the header 2.7 - 3.1 m is long along x
    { const [ex, ez] = ext(0, 34, 54, 4, 1, 2.7, 3.1); checked++; if (!(ex > 3.5 && ez < 0.5)) bad.push('vestibule doors ' + ex.toFixed(2) + 'x' + ez.toFixed(2)); }
    // the freezer door: its leaf stands open inside the freezer (north of the panel line)
    L.world.boxes.filter(b => b.piece === 'KIT_ICECREAM_FreezerDoor').forEach(b => {
      const Z = L.zones[b.zone], zc = (b.z0 + b.z1) / 2 - Z.oz, ex = b.x1 - b.x0, ez = b.z1 - b.z0;
      if (ez > 0.6) { checked++; if (!(zc < 12.0 && ex < 0.3)) bad.push('freezer door leaf zc ' + zc.toFixed(2) + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2)); }
    });
    // blast freezers (east wall): the compressor box 2.4 - 2.7 m sits on the cabinet, which is long along the wall (z)
    const g2 = L.zones[1].grid;
    for (let r = 1; r < g2.h - 3; r++) if (g2.at(67, r) === 'X' && g2.at(67, r - 1) !== 'X') {
      const [ex, ez] = ext(1, 67, r, 2, 3, 1.0, 2.0); checked++;
      if (!(ez > 2.6 && ex < 2.0)) bad.push('blast freezer at ' + r + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    return { n, bad, checked };
  });
  check('run pieces lie along their line of cells (belts, glass, rails, panels); counters, bars, doors and freezers face the right way',
    runs.bad.length === 0 && runs.n.q > 15 && runs.n.e > 4 && runs.n.l > 15 && runs.n.i > 10 && runs.n.r > 20 && runs.checked > 20,
    JSON.stringify(runs.n) + ' checked ' + runs.checked + ' ' + runs.bad.slice(0, 5).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
