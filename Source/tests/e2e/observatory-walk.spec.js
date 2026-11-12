// INKBOLT Vesper Peak Observatory (plan 'observatory'): the walk through both zones and the climbs. The player walks
// the summit compound from the station court up the road under the gantry to the annex porch, along the link
// corridor, through the Great Dome's lobby, round the telescope floor, the service hall and the exit corridor to the
// hatch (no invisible walls, nothing blocks the way); climbs the ground station's stair onto its roof deck (3 m) and
// crosses the gantry onto the east terrace, both terrace stairs, the steps onto the mast pad (1.5 m); in the dome both
// stairs onto the catwalk ring (4.8 m) and round it, over the bridge onto the gallery, the gallery's own stair, the
// star deck's stair (4.8 m); the rails keep the player up there. Ground robots follow onto the roof deck, the terrace,
// the mast pad, the ring, the gallery and the star deck. Run, rail, span and wall pieces are checked numerically to lie
// along their line of cells. The render loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/observatory-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=observatory');
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
    IB.Game.level.zones.forEach(z => { IB.Zones.setGate(z.exitGate, true, true); if (z.entryGate) IB.Zones.setGate(z.entryGate, true, true); });
  });
  // nav: open cells on the pad (1.5) and at 3 m (terrace, gantry, roof deck) in zone 1, at 4.8 m in zone 2
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, h15: 0, h3: 0, h48: 0 };
    for (let k = 0; k < NC * (N.layers || 1); k++) if (!N.blocked[k] && N.h) {
      const h = N.h[k];
      if (Math.abs(h - 1.5) < 0.01) o.h15++; if (Math.abs(h - 3.0) < 0.01) o.h3++; if (Math.abs(h - 4.8) < 0.01) o.h48++;
    }
    return o;
  }));
  check('nav: zone 1 has open cells on the mast pad and at 3 m, zone 2 at 4.8 m (ring, gallery, star deck)', nav[0].h15 > 400 && nav[0].h3 > 2000 && nav[1].h48 > 1000, JSON.stringify(nav));

  // ---- the walk: station court -> the road -> under the gantry -> the porch -> link corridor -> lobby -> hall -> service hall -> hatch
  let r = await pg.evaluate(() => { __place(0, 35.5, 68.0, 0); return __route(0, [[35.5, 60.0], [37.5, 56.5], [36.0, 52.0], [35.5, 45.0], [35.5, 30.0], [35.5, 3.0], [35.5, 1.0], [35.5, -6.0], [35.5, -11.5]], 160); });
  check('walk zone 1: from the station court up the road under the gantry to the annex porch and into the link corridor', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[35.5, 72.5], [35.5, 64.0], [21.0, 62.0], [21.0, 58.5], [21.0, 56.0], [20.5, 40.0], [20.5, 15.0], [23.5, 12.0], [23.5, 9.5], [23.5, 6.0], [34.0, 4.0], [35.5, 2.0], [35.5, -4.0], [35.5, -20.0]], 220));
  check('walk zone 2: the lobby, the dome hall round the telescope, the service hall, the exit corridor', r.reached === r.of && r.stuck === 0 && r.hi < 0.6, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit corridor leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));

  // ---- zone 1 climbs
  r = await pg.evaluate(() => { __place(0, 23.0, 50.5, 0); return __route(0, [[23.0, 45.0], [23.0, 43.0], [27.0, 41.0], [40.0, 41.0], [50.0, 41.0], [58.0, 34.0]], 60); });
  check('zone 1: up the ground station stair onto its roof deck, over the gantry onto the terrace (3 m)', r.reached === r.of && Math.abs(r.y - 3.0) < 0.05 && r.lo > -0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 54.0, 50.5, 0); return __route(0, [[54.0, 44.0], [54.0, 41.0]], 30); });
  check('zone 1: up the south terrace stair (3 m)', r.reached === r.of && Math.abs(r.y - 3.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 40.0, 12.0, 0); return __route(0, [[46.5, 12.0], [50.0, 12.0]], 30); });
  check('zone 1: up the west terrace stair (3 m)', r.reached === r.of && Math.abs(r.y - 3.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 10.5, 22.5, 0); return __route(0, [[10.5, 18.5], [10.5, 16.0], [14.0, 12.0]], 30); });
  check('zone 1: up the steps onto the mast pad (1.5 m)', r.reached === r.of && Math.abs(r.y - 1.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 60.0, 8.0, 3.0); return __route(0, [[60.0, 3.0]], 3); });
  check('zone 1: the terrace rail keeps the player up', r.lo > 2.95, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 40.0, 40.5, 3.0); return __route(0, [[40.0, 36.0]], 3); });
  check('zone 1: the gantry rail keeps the player up', r.lo > 2.95, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 15.0, 15.0, 1.5); return __route(0, [[15.0, 20.0]], 3); });
  check('zone 1: the pad rail keeps the player up', r.lo > 1.45, JSON.stringify(r));

  // ---- zone 2 climbs: both stairs onto the ring and round it, the bridge, the gallery stair, the star deck
  r = await pg.evaluate(() => {
    __place(1, 36.0, 57.5, 0);
    const pts = [[36.0, 47.5], [36.0, 46.0]];
    for (let a = 100; a <= 450; a += 25) pts.push([36 + 12 * Math.cos(a * Math.PI / 180), 34 + 12 * Math.sin(a * Math.PI / 180)]);
    pts.push([48.5, 34.0], [52.0, 34.0], [56.5, 34.0], [56.5, 20.0]);
    return __route(1, pts, 120);
  });
  check('zone 2: up the south stair onto the catwalk ring (4.8 m), all the way round, over the bridge onto the gallery', r.reached === r.of && Math.abs(r.y - 4.8) < 0.05 && r.lo > 4.75 - 4.8 + 0 && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 36.0, 10.5, 0); return __route(1, [[36.0, 20.5], [36.0, 22.5]], 30); });
  check('zone 2: up the north stair onto the ring', r.reached === r.of && Math.abs(r.y - 4.8) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 42.0, 51.0, 0); return __route(1, [[53.5, 51.0], [56.5, 51.0], [56.5, 45.0]], 30); });
  check('zone 2: up the gallery stair onto the gallery', r.reached === r.of && Math.abs(r.y - 4.8) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 64.0, 20.0, 0); return __route(1, [[64.0, 8.5], [66.0, 6.0], [68.0, 15.0]], 30); });
  check('zone 2: up the star deck stair onto the viewing deck along the glass', r.reached === r.of && Math.abs(r.y - 4.8) < 0.05, JSON.stringify(r));
  for (const [tag, at, to] of [['ring inner rail', [36.0, 22.5], [36.0, 28.0]], ['ring outer rail', [44.5, 25.5], [48.0, 22.0]], ['gallery rail', [56.5, 25.0], [50.0, 25.0]], ['star deck rail', [66.5, 15.0], [62.0, 15.0]]]) {
    r = await pg.evaluate(([at, to]) => { __place(1, at[0], at[1], 4.8); return __route(1, [to], 3); }, [at, to]);
    check('zone 2: the ' + tag + ' keeps the player up', r.lo > 4.75, JSON.stringify(r));
  }

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
  for (const [tag, zi, at, bot, goal] of [
    ['zone 1: a Crawler climbs to the player on the ground station roof', 0, [27.0, 40.0, 3.0], ['crawler', 30, 52], 2.9],
    ['zone 1: a Crawler climbs to the player on the terrace by the Halden Dome', 0, [60.0, 30.0, 3.0], ['crawler', 40, 54], 2.9],
    ['zone 1: a Crawler climbs to the player on the mast pad', 0, [12.0, 9.0, 1.5], ['crawler', 26, 24], 1.4],
    ['zone 2: a Crawler from the lobby climbs to the player on the ring', 1, [24.5, 34.0, 4.8], ['crawler', 30, 62], 4.7],
    ['zone 2: a Blade Bot climbs to the player on the gallery', 1, [57.0, 20.0, 4.8], ['blader', 45, 44], 4.7],
    ['zone 2: a Crawler from the lounge climbs to the player on the star deck', 1, [68.0, 15.0, 4.8], ['crawler', 63, 40], 4.7]]) {
    const w = await chase(zi, at, [bot], 80, goal);
    check(tag + ' (< 4 m) within 80 s', w.best > goal, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  }

  // ---- run / rail / span / wall pieces lie along their line of cells: the drawn vertices (outline shell left out)
  // inside each cell or block, in a height band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [], kinds: {} };
    function ext(zi, c0, r0, w, h, y0, y1, alongX) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], x0 = Z.ox + c0, x1 = Z.ox + c0 + w, z0 = Z.oz + r0, z1 = Z.oz + r0 + h;
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let i = 0; i < P.length; i += 3) {
          if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
          const x = P[i], y = P[i + 1], z = P[i + 2];
          if (y < y0 || y > y1 || x < x0 || x > x1 || z < z0 || z > z1) continue;
          const a = alongX ? x : z, end = Math.min(Math.abs(a - (alongX ? x0 : z0)), Math.abs(a - (alongX ? x1 : z1))) < 0.005;
          if (alongX) { e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); if (!end) { e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z); } }
          else { e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z); if (!end) { e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); } }
        }
      });
      return [Math.max(0, e[1] - e[0]), Math.max(0, e[3] - e[2])];
    }
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1, alongX), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++; out.kinds[tag] = (out.kinds[tag] || 0) + 1;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + zi + ':' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    const blocks = (G, ch) => { const seen = {}, res = []; for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) { if (G.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (G.at(c + w, r) === ch) w++; while (G.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, W = g.w - 1, H = g.h - 1;
      // the zone's west / east edges: parapets (zone 1) or wall faces / the glazing (zone 2), along Z
      for (let r = 4; r < H - 6; r++) {
        if (zi === 0) { expect('parapet-W', 0, 0, r, 1, 1, 0.05, 1.15, false, 0.95, 0.5); expect('parapet-E', 0, W, r, 1, 1, 0.05, 1.15, false, 0.95, 0.5); }
        else { expect('wall-W', 1, 0, r, 1, 1, 0.05, 0.2, false, 0.95, 0.12); if (r !== 29 && r !== 28 && r !== 30) expect('glazing-E', 1, W, r, 1, 1, 0.1, 0.2, false, 0.95, 0.35); }
      }
      // the station's and the annex's fronts along X (zone 1), the lobby and service hall walls (zone 2)
      for (let c = 2; c < W - 1; c++) {
        if (Math.abs(c - 35) <= 2) continue;
        if (zi === 0 && (c < 27 || c > 44)) { expect('station-N', 0, c, 64, 1, 1, 0.85, 0.95, true, 0.95, 0.12); expect('annex-S', 0, c, 2, 1, 1, 0.55, 0.65, true, 0.95, 0.12); }
        if (zi === 1) { expect('lobby-S', 1, c, H, 1, 1, 0.05, 0.2, true, 0.95, 0.12); if (c !== 11 && c !== 60) expect('north-N', 1, c, 0, 1, 1, c > 11 && c < 60 ? 0.85 : 0.05, c > 11 && c < 60 ? 0.95 : 0.2, true, 0.95, 0.12); }
      }
      [g].concat(g.layers || []).forEach(G => {
        if (IB.Zones.isDataLayer(L.theme, G)) return;
        const y = G === g ? 0 : G.y, ga = (c, r) => G.at(c, r);
        for (let r = 1; r < H; r++) for (let c = 1; c < W; c++) {
          const ch = ga(c, r); if (!"fr'x".includes(ch)) continue;
          const same = (cc, rr) => (ch === 'x' ? ga(cc, rr) === 'x' : "fr'".includes(ga(cc, rr)) && (ch === 'f') === (ga(cc, rr) === 'f'));
          const ew = same(c - 1, r) && same(c + 1, r) && !same(c, r - 1) && !same(c, r + 1);
          const ns = same(c, r - 1) && same(c, r + 1) && !same(c - 1, r) && !same(c + 1, r);
          if (!ew && !ns) continue;
          if (ch === 'x') expect('cable-bridge', zi, c, r, 1, 1, 2.6, 2.79, ew, 0.95, 0.5);
          else if (ch === 'f') expect('fence', zi, c, r, 1, 1, 1.85, 2.01, ew, 0.95, 0.12);
          else expect('rail', zi, c, r, 1, 1, y + 0.2, y + 1.08, ew, 0.95, 0.12);
        }
      });
      // spans: [n, 1] pieces along their long side, the doorways along their wall line, the stairs along their run
      const span = (ch, tag, y0, y1, minA, maxX, G) => blocks(G || g, ch).forEach(([c, r, w, h]) => expect(tag, zi, c, r, w, h, (G ? G.y : 0) + y0, (G ? G.y : 0) + y1, w > h, minA * Math.max(w, h), maxX));
      if (zi === 0) {
        span('=', 'bench', 0.4, 0.5, 0.9, 0.5); span('i', 'panorama', 1.0, 1.5, 0.85, 0.25); span('j', 'panorama', 1.0, 1.5, 0.85, 0.25);
        const S = g.layers.find(Lr => Math.abs(Lr.y - 0.01) < 1e-4);
        span('1', 'sign', 7.9, 9.2, 0.95, 0.2, S); span('2', 'sign', 6.9, 8.3, 0.95, 0.2, S);
      } else {
        // doorways: the threshold plate (4 mm up, inside the cell; the frame stands 6 cm proud of it either side)
        span('D', 'door', 0.002, 0.006, 0.85, 1.05); span('W', 'door4', 0.002, 0.006, 0.9, 1.05);
        span('l', 'lockers', 0.5, 1.5, 0.9, 0.8); span('[', 'sofa', 0.05, 0.45, 0.9, 0.95); span('&', 'cafe', 1.0, 1.12, 0.95, 0.95);
        span('b', 'labbench', 0.85, 0.95, 0.95, 0.95); span('p', 'platecab', 0.5, 1.5, 0.9, 0.9); span('V', 'videowall', 1.2, 3.0, 0.95, 0.3);
        span(';', 'bench', 0.4, 0.5, 0.9, 0.5);
      }
    });
    return out;
  });
  check('run, rail, span and wall pieces lie along their line of cells (none a quarter turn off)', runs.checked > 600 && runs.bad.length === 0, runs.checked + ' checked ' + JSON.stringify(runs.kinds) + ' ' + runs.bad.slice(0, 16).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
