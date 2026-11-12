// INKBOLT Chalkstone Academy (plan 'academy'): the walk through both zones and the climbs. The player walks from the
// entrance hall through the main corridor, the spine hall and the cafeteria to the north doors, the trail, the gym
// lobby, the gym, out under the covered walkway and across the courtyard to the exit and the hatch (no invisible
// walls, nothing blocks the way); climbs both library stairs onto the 4 m mezzanine (its rail keeps the player on
// it), the bleachers, the stage steps and the outdoor classroom tiers. Ground robots follow onto the mezzanine, the
// bleachers and the stage. Run, rail, span, door and wall-face pieces are checked numerically along their line of
// cells. The render loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/academy-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=academy');
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
  // nav: open cells on the library mezzanine (4 m), the bleacher tops (2.4 m), the stage (1 m), the tiers (1.2 m)
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, deck: 0, bleach: 0, stage: 0, tiers: 0 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k]) {
      const h = N.h[k];
      if (Math.abs(h - 4.0) < 0.005) o.deck++; if (Math.abs(h - 2.4) < 0.005) o.bleach++; if (Math.abs(h - 1.0) < 0.005) o.stage++; if (Math.abs(h - 1.2) < 0.005) o.tiers++;
    }
    return o;
  }));
  check('nav: the mezzanine (zone 1), the bleacher tops, the stage and the tiers (zone 2) hold open cells',
    nav[0].deck > 300 && nav[1].bleach > 100 && nav[1].stage > 150 && nav[1].tiers >= 30, JSON.stringify(nav));

  // ---- the walk: entrance hall -> main corridor -> spine -> cafeteria -> north doors -> trail
  let r = await pg.evaluate(() => { __place(0, 35.5, 67.0, 0); return __route(0, [[35.5, 60.0], [33.8, 56.5], [33.8, 50.0], [33.8, 38.5], [37.5, 30.0], [37.5, 13.0], [37.5, 5.0], [35.5, 2.0], [35.5, -6.0], [35.5, -13.0]], 140); });
  check('walk zone 1: the entrance hall, the main corridor, the spine hall, the cafeteria, the north doors and onto the trail', r.reached === r.of && r.stuck === 0 && r.hi < 0.3, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[59.5, 69.0], [59.5, 63.0], [49.0, 59.5], [44.5, 59.5], [44.5, 48.0], [43.0, 42.0], [43.0, 38.0], [44.0, 30.0], [44.0, 6.0], [40.5, 3.0], [35.5, 2.0], [35.5, -4.0], [35.5, -20.0]], 160));
  check('walk zone 2: the gym lobby, the gym, the courtyard doors, the covered walkway, the exit and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.3, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));
  // the west corridor and the east corridor are open end to end (flanking routes round the cafeteria)
  r = await pg.evaluate(() => { __place(0, 16.0, 53.0, 0); return __route(0, [[16.0, 30.0], [16.0, 2.0], [16.0, 20.0], [15.5, 21.5], [20.0, 21.5], [20.0, 25.8], [29.5, 25.8], [37.5, 18.0], [52.0, 18.0], [52.0, 21.5], [55.5, 21.5], [55.5, 52.0]], 120); });
  check('zone 1: the west corridor, through the cafeteria side doors and down the east corridor', r.reached === r.of && r.stuck === 0, JSON.stringify(r));

  // ---- climbs
  r = await pg.evaluate(() => { __place(0, 21.5, 26.0, 0); return __route(0, [[21.5, 24.5], [21.5, 17.5], [21.5, 15.6], [26.0, 15.6]], 30); });
  check('zone 1: up stair A onto the library mezzanine (4 m)', r.reached === r.of && Math.abs(r.y - 4.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 36.5, 7.5, 0); return __route(0, [[35.8, 7.5], [29.2, 7.5], [27.0, 7.5]], 30); });
  check('zone 1: up stair B onto the mezzanine from the cafeteria floor', r.reached === r.of && Math.abs(r.y - 4.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 27.5, 12.5, 4.0); return __route(0, [[31.0, 12.5]], 3); });
  check('zone 1: the mezzanine rail keeps the player on the deck', r.lo > 3.95, JSON.stringify(r));
  const sight = await pg.evaluate(() => { const W = IB.Game.level.world, Z = IB.Game.level.zones[0]; return W.los(Z.ox + 27.5, 4.0 + 1.5, Z.oz + 12.5, Z.ox + 45, 1.2, Z.oz + 18); });
  check('zone 1: the mezzanine looks down over the cafeteria (clear sight line)', sight, String(sight));
  r = await pg.evaluate(() => { __place(1, 25.0, 47.0, 0); return __route(1, [[25.0, 46.2], [25.0, 41.6]], 20); });
  check('zone 2: up the north bleachers to the top row (2.4 m)', r.reached === r.of && Math.abs(r.y - 2.4) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 9.0, 50.85, 0); return __route(1, [[7.4, 50.85], [5.0, 50.85], [4.0, 55.0]], 20); });
  check('zone 2: up the stage steps onto the stage (1 m)', r.reached === r.of && Math.abs(r.y - 1.0) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 56.5, 11.0, 0); return __route(1, [[56.5, 9.8], [56.5, 6.4]], 20); });
  check('zone 2: up the outdoor classroom tiers (1.2 m)', r.reached === r.of && Math.abs(r.y - 1.2) < 0.05, JSON.stringify(r));

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
  let w = await chase(0, [24.5, 4.0, 4.0], [['crawler', 44, 20]], 70, 3.9);
  check('zone 1: a Crawler from the cafeteria floor climbs to the player on the library mezzanine (< 4 m) within 70 s', w.best > 3.9, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [30.0, 41.6, 2.4], [['blader', 30, 56]], 60, 2.3);
  check('zone 2: a Blade Bot from the court climbs the bleachers to the player (< 4 m) within 60 s', w.best > 2.3, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [3.0, 56.0, 1.0], [['crawler', 30, 56]], 60, 0.95);
  check('zone 2: a Crawler from the court climbs onto the stage to the player (< 4 m) within 60 s', w.best > 0.95, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- pieces along their line of cells: drawn vertices (outline shell left out) in a cell or block, in a height
  // band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    function ext(zi, c0, r0, w, h, y0, y1, pad) {
      const Z = L.zones[zi], e = [1e9, -1e9, 1e9, -1e9], p = pad || 0, x0 = Z.ox + c0 - p, x1 = Z.ox + c0 + w + p, z0 = Z.oz + r0 - p, z1 = Z.oz + r0 + h + p;
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
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross, pad) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1, pad), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + zi + ':' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    const blocks = (G, ch) => { const seen = {}, res = []; for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) { if (G.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (G.at(c + w, r) === ch) w++; while (G.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
    const WALLISH = '#GED7OQ';
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r);
      // wall faces: every face piece is drawn in the plane of its cell's open side, facing it; a face turned a quarter
      // (onto a side that is wall) or missing fails. Area of drawn triangles (outline shell left out) per cell side,
      // band 0 - 2.6 m (the door headers: 2.5 - 4 m), from the triangles' planes and normals.
      const area = {};
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, I = m.geometry.index.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let t = 0; t < I.length; t += 3) {
          const a = I[t] * 3, b = I[t + 1] * 3, d = I[t + 2] * 3;
          if (H && (H[a] || H[a + 1] || H[a + 2])) continue;
          const ux = P[b] - P[a], uy = P[b + 1] - P[a + 1], uz = P[b + 2] - P[a + 2], vx = P[d] - P[a], vy = P[d + 1] - P[a + 1], vz = P[d + 2] - P[a + 2];
          const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx, A2 = Math.hypot(nx, ny, nz);
          if (A2 < 1e-6) continue;
          const cx = (P[a] + P[b] + P[d]) / 3 - Z.ox, cy = (P[a + 1] + P[b + 1] + P[d + 1]) / 3, cz = (P[a + 2] + P[b + 2] + P[d + 2]) / 3 - Z.oz;
          const kx = Math.abs(nx) / A2, kz = Math.abs(nz) / A2;
          let key = null;
          if (kx > 0.95 && Math.abs(cx - Math.round(cx)) < 0.012) key = (nx > 0 ? (Math.round(cx) - 1) + ',' + Math.floor(cz) + ',E' : Math.round(cx) + ',' + Math.floor(cz) + ',W');
          else if (kz > 0.95 && Math.abs(cz - Math.round(cz)) < 0.012) key = (nz > 0 ? Math.floor(cx) + ',' + (Math.round(cz) - 1) + ',S' : Math.floor(cx) + ',' + Math.round(cz) + ',N');
          if (!key) continue;
          const band = cy < 2.6 ? 'lo' : cy < 4.0 ? 'mid' : 'hi';
          area[key + band] = (area[key + band] || 0) + A2 / 2;
        }
      });
      const W = (x, y) => WALLISH.indexOf(at(x, y)) >= 0, SD = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
      for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
        const ch = at(c, r), door = 'D7OQ'.indexOf(ch) >= 0;
        if (ch !== '#' && !door) continue;
        Object.keys(SD).forEach(sd => {
          const [dc, dr] = SD[sd], open = !W(c + dc, r + dr), A = area[c + ',' + r + ',' + sd + (door ? 'mid' : 'lo')] || 0;
          if (door) return;
          if ('D7OQ'.indexOf(at(c + dc, r + dr)) >= 0) return;   // a door's jamb reveal against this cell
          out.checked++;
          if (open && A < 0.2) out.bad.push('wall face missing ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
          if (!open && A > 0.05) out.bad.push('wall face on a closed side ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
        });
      }
      // door headers: drawn on both faces of the doorway, in the wall line (2.5 - 4 m)
      ['D', '7', 'O', 'Q'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => {
        const sides = w > h ? ['N', 'S'] : ['E', 'W'];
        sides.forEach(sd => {
          let A = 0; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) A += area[(c + x) + ',' + (r + y) + ',' + sd + 'mid'] || 0;
          out.checked++; if (A < 0.9 * Math.max(w, h)) out.bad.push('door header ' + ch + ' ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
        });
      }));
      // doors in their wall line: the header band (2.55 - 3.5 m) runs along the wall, one cell deep
      ['D', '7', 'O', 'Q'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => expect('door ' + ch, zi, c, r, w, h, 2.45, 4.1, w > h, Math.max(w, h) - 0.05, 1.12, 0.02)));
      // [n, 1] / [n, 2] prefabs along their block: benches, cafeteria tables, bookcases, book stacks, the bleachers
      // [symbol, band, piece length, pad (+ out / - in: a box piece's vertices are at its ends), max across]
      [['B', 0.43, 0.47, 2, 0.02, 0.6], ['l', 0.72, 0.76, 6, -0.03, 1.8], ['K', 0.5, 1.0, 2, -0.03, 0.9], ['{', 1.0, 2.5, 8, 0.05, 5.2],
        ['}', 1.0, 2.5, 8, 0.05, 5.2], ['%', 0.25, 0.55, 2, 0.02, 1.0], ['2', 0.74, 0.84, 4, 0.02, 1.0]].forEach(([ch, y0, y1, L0, pad, across]) => {
        blocks(g, ch).forEach(([c, r, w, h]) => {
          const n = Math.max(1, Math.round(Math.max(w, h) / L0));
          for (let k = 0; k < n; k++) {
            if (w >= h) expect(ch, zi, c + k * L0, r, L0, h, y0, y1, true, L0 * 0.8, across, pad);
            else expect(ch, zi, c, r + k * L0, w, L0, y0, y1, false, L0 * 0.8, across, pad);
          }
        });
      });
      // the covered walkway: each 2 m piece is 4 m wide across the run (east-west), its roof band at 3 m
      blocks(g, '3').forEach(([c, r, w, h]) => { for (let k = 1; k < h / 2 - 1; k++) expect('canopy', zi, c - 0.2, r + k * 2, w + 0.4, 2, 2.95, 3.1, true, 4.0, 2.05); });
      // mezzanine rails ('|' on the deck layer at 4 m): straight cells carry the full module along the run
      (g.layers || []).filter(l => Math.abs(l.y - 4) < 0.01).forEach(D => {
        for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
          if (D.at(c, r) !== '|') continue;
          const ew = D.at(c - 1, r) === '|' && D.at(c + 1, r) === '|' && D.at(c, r - 1) !== '|' && D.at(c, r + 1) !== '|';
          const ns = D.at(c, r - 1) === '|' && D.at(c, r + 1) === '|' && D.at(c - 1, r) !== '|' && D.at(c + 1, r) !== '|';
          if (ew || ns) expect('rail', zi, c, r, 1, 1, 4.95, 5.05, ew, 0.9, 0.3);
        }
      });
    });
    return out;
  });
  check('run, rail, span, door and wall-face pieces lie along their line of cells (none a quarter turn off)', runs.checked > 600 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 8).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
