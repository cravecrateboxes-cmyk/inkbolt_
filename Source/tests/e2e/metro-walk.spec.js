// INKBOLT Metro Central (plan 'metro'): the walk through both zones and the climbs. The player walks from the street
// entrance through the ticket hall, a fare gate aisle, along the west balcony round the escalator well and down the
// platform passage to the exit, the trail, the entry hall, the cross passage, onto platform A, through a stopped
// train to the island, through the other train to platform B and the north passage to the exit and the hatch (no
// invisible walls, nothing blocks the way); goes over a footbridge (4.5 m) from platform A to platform B, down the
// platform-end steps into a trackbed (0.9 m down) and back, down the well stair to the lower landing (4.5 m down)
// and up an escalator. Ground robots follow onto the footbridge, into the trackbed, down into the well and into a
// train. Wall faces, sunk side faces, rails, benches, fare gates, trains, track, stairs, the escalator bank and the
// doors are checked numerically along their line of cells. The render loop is paused and the real Player / AI code
// is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/metro-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=metro');
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
  // nav: open cells on the footbridges (4.5 m), in the trackbeds (-0.9 m), on the well floor (-4.5 m), in the trains
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, deck: 0, track: 0, well: 0, train: 0 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k]) {
      const h = N.h[k];
      if (Math.abs(h - 4.5) < 0.005) o.deck++; if (Math.abs(h + 0.9) < 0.005) o.track++; if (Math.abs(h + 4.5) < 0.005) o.well++; if (Math.abs(h - 0.02) < 0.005) o.train++;
    }
    return o;
  }));
  check('nav: the lower landing (zone 1); the footbridges, the trackbeds and the train floors (zone 2) hold open cells',
    nav[0].well > 400 && nav[1].deck > 300 && nav[1].track > 300 && nav[1].train > 400, JSON.stringify(nav));

  // ---- the walk: street entrance -> ticket hall -> fare gates -> west balcony -> platform passage -> exit -> trail
  let r = await pg.evaluate(() => { __place(0, 35.5, 66.5, 0); return __route(0, [[35.5, 60.0], [28.0, 56.0], [28.0, 40.0], [34.0, 37.0], [34.0, 33.5], [23.5, 31.0], [23.5, 10.0], [17.5, 7.6], [17.5, 4.0], [30.0, 2.5], [35.5, 2.0], [35.5, -6.0], [35.5, -13.0]], 160); });
  check('walk zone 1: the ticket hall, a fare gate aisle, the west balcony, the platform passage, the exit and onto the trail', r.reached === r.of && r.stuck === 0 && r.hi < 0.3 && r.lo > -0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[35.5, 66.0], [35.5, 55.0], [35.5, 47.5], [35.5, 44.0], [36.0, 41.5], [36.0, 37.0], [36.0, 33.5], [36.0, 32.0], [36.0, 30.3], [44.5, 29.0], [44.5, 21.5], [42.0, 20.5], [42.0, 18.5], [42.0, 17.0], [42.0, 15.3], [42.0, 12.0], [36.5, 10.5], [36.0, 8.0], [35.5, 5.0], [35.5, 2.0], [35.5, -4.0], [35.5, -20.0]], 180));
  check('walk zone 2: the entry hall, the cross passage, platform A, through train 1, the island, through train 2, platform B, the north passage, the exit and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.3 && r.lo > -0.05, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));
  // the east balcony is open end to end too (the other flank round the well)
  r = await pg.evaluate(() => { __place(0, 40.0, 33.5, 0); return __route(0, [[48.5, 31.0], [48.5, 10.0], [53.5, 7.6], [53.5, 4.0], [40.0, 2.5]], 80); });
  check('zone 1: the east balcony round the well to the platform passage', r.reached === r.of && r.stuck === 0, JSON.stringify(r));

  // ---- climbs
  r = await pg.evaluate(() => { __place(1, 27.5, 39.6, 0); return __route(1, [[23.0, 39.6], [19.3, 39.6], [17.0, 39.5], [16.5, 30.0], [16.5, 11.0], [17.0, 9.6]], 60); });
  check('zone 2: up the west footbridge stair from platform A and across the tracks on the deck (4.5 m)', r.reached === r.of && Math.abs(r.y - 4.5) < 0.05 && r.lo > -0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[20.5, 9.5], [27.6, 9.6], [28.5, 11.5]], 30));
  check('zone 2: down the footbridge stair onto platform B', r.reached === r.of && Math.abs(r.y) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 16.5, 25.0, 4.5); return __route(1, [[13.5, 25.0]], 3); });
  check('zone 2: the footbridge rail keeps the player on the deck', r.lo > 4.45, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 2.5, 37.5, 0); return __route(1, [[2.5, 36.0], [2.5, 34.3], [2.5, 32.5], [7.5, 32.5]], 30); });
  check('zone 2: down the platform-end steps into the trackbed (0.9 m down) and along the track', r.reached === r.of && Math.abs(r.y + 0.9) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[2.5, 32.6], [2.5, 34.5], [2.5, 37.0]], 30));
  check('zone 2: back up the steps onto platform A', r.reached === r.of && Math.abs(r.y) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 27.3, 29.5, 0); return __route(0, [[27.3, 27.6], [27.3, 19.2], [27.3, 16.0]], 40); });
  check('zone 1: down the well stair to the lower landing (4.5 m down)', r.reached === r.of && Math.abs(r.y + 4.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => __route(0, [[34.75, 16.0], [34.75, 18.5], [34.75, 29.5]], 40));
  check('zone 1: up an escalator to the paid concourse', r.reached === r.of && Math.abs(r.y) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 24.0, 15.0, 0); return __route(0, [[27.5, 15.0]], 3); });
  check('zone 1: the well balustrade keeps the player on the balcony', r.lo > -0.05, JSON.stringify(r));

  // ---- robots follow
  async function chase(zi, at, robots, secs, test) {
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
    let last = null, t = 0, ok = false;
    while (t < secs && !ok) {
      last = await pg.evaluate(([list, zi]) => { __sim(0.5, zi); const [type, slot] = list[0]; const r = IB.AI.types[type].slots[slot], p = IB.Game.player; return { on: r.on, x: +r.x.toFixed(2), y: +r.y.toFixed(2), z: +r.z.toFixed(2), d: +Math.hypot(r.x - p.x, r.z - p.z).toFixed(2), dy: +Math.abs(r.y - p.y).toFixed(2) }; }, [list, zi]);
      t += 0.5; ok = last.on && test(last);
    }
    return { ok, last, t };
  }
  let w = await chase(1, [16.5, 25.0, 4.5], [['crawler', 30, 37]], 70, (s) => s.d < 4 && s.y > 4.4);
  check('zone 2: a Crawler from platform A climbs onto the footbridge to the player within 70 s', w.ok, JSON.stringify(w));
  w = await chase(1, [5.5, 32.5, -0.9], [['blader', 50, 27]], 70, (s) => s.d < 4 && s.y < -0.8);
  check('zone 2: a Blade Bot from the island gets down into the trackbed to the player within 70 s', w.ok, JSON.stringify(w));
  w = await chase(1, [12.5, 12.0, 0], [['crawler', 6, 17]], 60, (s) => s.d < 4 && s.y > -0.05);
  check('zone 2: a Crawler in the trackbed climbs out onto platform B to the player within 60 s', w.ok, JSON.stringify(w));
  w = await chase(1, [36.0, 32.0, 0.02], [['crawler', 50, 12]], 60, (s) => s.d < 3 && s.y > -0.05);
  check('zone 2: a Crawler from platform B gets into the train on track 1 to the player within 60 s', w.ok, JSON.stringify(w));
  w = await chase(0, [35.0, 13.0, -4.5], [['crawler', 40, 31]], 70, (s) => s.d < 4 && s.y < -4.4);
  check('zone 1: a Crawler from the paid concourse goes down into the well to the player within 70 s', w.ok, JSON.stringify(w));

  // ---- pieces along their line of cells: drawn vertices (outline shell left out) in a cell or block, in a height
  // band, are long along the line and short across it
  const runs = await pg.evaluate(() => {
    const L = IB.Game.level, out = { checked: 0, bad: [] };
    function verts(zi, c0, r0, w, h, y0, y1, pad, fn) {
      const Z = L.zones[zi], p = pad || 0, x0 = Z.ox + c0 - p, x1 = Z.ox + c0 + w + p, z0 = Z.oz + r0 - p, z1 = Z.oz + r0 + h + p;
      Z.meshes.forEach(m => {
        const P = m.geometry.attributes.position.array, H = m.geometry.attributes.aHull ? m.geometry.attributes.aHull.array : null;
        for (let i = 0; i < P.length; i += 3) {
          if (H && (H[i] || H[i + 1] || H[i + 2])) continue;
          const x = P[i], y = P[i + 1], z = P[i + 2];
          if (y < y0 || y > y1 || x < x0 || x > x1 || z < z0 || z > z1) continue;
          fn(x - Z.ox, y, z - Z.oz);
        }
      });
    }
    function ext(zi, c0, r0, w, h, y0, y1, pad) {
      const e = [1e9, -1e9, 1e9, -1e9];
      verts(zi, c0, r0, w, h, y0, y1, pad, (x, y, z) => { e[0] = Math.min(e[0], x); e[1] = Math.max(e[1], x); e[2] = Math.min(e[2], z); e[3] = Math.max(e[3], z); });
      return [e[1] - e[0], e[3] - e[2]];
    }
    function expect(tag, zi, c0, r0, w, h, y0, y1, alongX, minAlong, maxAcross, pad) {
      const [ex, ez] = ext(zi, c0, r0, w, h, y0, y1, pad), along = alongX ? ex : ez, across = alongX ? ez : ex;
      out.checked++;
      if (!(along >= minAlong && across <= maxAcross)) out.bad.push(tag + '@' + zi + ':' + c0 + ',' + r0 + ' ' + ex.toFixed(2) + 'x' + ez.toFixed(2));
    }
    const blocks = (G, ch) => { const seen = {}, res = []; for (let r = 0; r < G.h; r++) for (let c = 0; c < G.w; c++) { if (G.at(c, r) !== ch || seen[c + ',' + r]) continue; let w = 0, h = 0; while (G.at(c + w, r) === ch) w++; while (G.at(c, r + h) === ch) h++; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) seen[(c + x) + ',' + (r + y)] = 1; res.push([c, r, w, h]); } return res; };
    const WALLISH = '#GEDOd', DOORS = 'DOd';
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r), sunk = Z.sunk;
      const sk = (c, r) => sunk && c >= 0 && r >= 0 && c < g.w && r < g.h ? sunk.d[r * g.w + c] : 0;
      // drawn area per cell side (triangles in the plane of a cell edge, facing out of the cell), per height band
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
          const band = cy < -0.05 ? 'sub' : cy < 2.6 ? 'lo' : cy < 4.0 ? 'mid' : 'hi';
          area[key + band] = (area[key + band] || 0) + A2 / 2;
        }
      });
      const W = (x, y) => WALLISH.indexOf(at(x, y)) >= 0, SD = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
      for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
        const ch = at(c, r);
        Object.keys(SD).forEach(sd => {
          const [dc, dr] = SD[sd];
          // a sunk side face: every edge from a cell that is not sunk down into a sunk one carries a face below 0
          if (!sk(c, r) && sk(c + dc, r + dr)) {
            const A = area[c + ',' + r + ',' + sd + 'sub'] || 0;
            out.checked++;
            if (A < 0.4 * Math.min(1, sk(c + dc, r + dr))) out.bad.push('sunk face missing ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
          }
          if (ch !== '#') return;
          if (DOORS.indexOf(at(c + dc, r + dr)) >= 0) return;   // a door's jamb reveal against this cell
          if ((r === 0 || r === g.h - 1) && [-1, 0, 1].some(k => 'GE'.indexOf(at(c + k, r)) >= 0)) return;   // the gate frame's
          const open = !W(c + dc, r + dr), A = area[c + ',' + r + ',' + sd + 'lo'] || 0;
          out.checked++;
          if (open && A < 0.2) out.bad.push('wall face missing ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
          if (!open && A > 0.05) out.bad.push('wall face on a closed side ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
        });
      }
      // doorways in their wall line: the header band (2.6 - 4 m) runs along the wall, one cell deep, on both faces
      ['D', 'd', 'O'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => {
        expect('door ' + ch, zi, c, r, w, h, 2.65, 3.95, w > h, Math.max(w, h) - 0.05, 1.12, 0.02);
        (w > h ? ['N', 'S'] : ['E', 'W']).forEach(sd => {
          let A = 0; for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) A += area[(c + x) + ',' + (r + y) + ',' + sd + 'mid'] || 0;
          out.checked++; if (A < 0.9 * Math.max(w, h)) out.bad.push('door header ' + ch + ' ' + zi + ':' + c + ',' + r + sd + ' ' + A.toFixed(2));
        });
      }));
      // [n, 1] / [n, m] prefabs along their block: [symbol, band, piece length along the line, pad, max across, long axis]
      // benches (seat), trains (roof line), track (rail heads), footbridge stairs, trackbed steps, ticket machines
      [['B', 0.43, 0.47, 3, 0.02, 0.6], ['e', 3.29, 3.35, 18, 0.05, 3.0], ['x', 3.29, 3.35, 18, 0.05, 3.0], ['~', 0.24, 0.26, 2, 0.02, 1.6],
        ['<', 1.0, 3.0, 8, 0.05, 2.1, 0.5], ['>', 1.0, 3.0, 8, 0.05, 2.1, 0.5], ['V', 1.86, 2.19, 3, 0.02, 0.6], ['Q', 0.8, 0.95, 3, 0.02, 0.3]].forEach(([ch, y0, y1, L0, pad, across, fr]) => {
        blocks(g, ch).forEach(([c, r, w, h]) => {
          const n = Math.max(1, Math.round(Math.max(w, h) / L0)), dy = -sk(c, r);   // a block in a sunk area stands on its floor
          for (let k = 0; k < n; k++) {
            if (w >= h) expect(ch, zi, c + k * L0, r, L0, h, y0 + dy, y1 + dy, true, L0 * (fr || 0.8), across, pad);
            else expect(ch, zi, c, r + k * L0, w, L0, y0 + dy, y1 + dy, false, L0 * (fr || 0.8), across, pad);
          }
        });
      });
      // shop fascias (layer 2.9) along the shopfront line (the west wall of the hall: the box stands proud of its east face)
      (g.layers || []).filter(l => Math.abs(l.y - 2.9) < 0.01).forEach(D => ['3', '4', '5', '6'].forEach(ch => blocks(D, ch).forEach(([c, r, w, h]) => expect('fascia ' + ch, zi, c + 1.01, r, 0.3, h, 2.95, 3.4, false, 6.5, 0.25))));
      // fare gates: each cabinet stands across the gate line (its 1.1 m along the aisles, north-south)
      ['F', 'W'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => { for (let k = 0; k < w / 2; k++) expect('gate ' + ch, zi, c + 2 * k + 0.6, r - 0.2, 0.8, 1.4, 1.02, 1.08, false, 1.05, 0.4); }));
      // the escalator bank and the well stairs climb toward the south (their top at the rim)
      ['X', 'N'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => {
        let n0 = -1e9, s0 = -1e9;
        verts(zi, c + 0.6, r + 0.2, w - 1.2, 2.5, -5, 1.5, 0, (x, y) => { n0 = Math.max(n0, y); });
        verts(zi, c + 0.6, r + h - 2.7, w - 1.2, 2.5, -5, 1.5, 0, (x, y) => { s0 = Math.max(s0, y); });
        out.checked++; if (!(s0 > n0 + 2.5)) out.bad.push('flight ' + ch + ' not rising south ' + zi + ':' + c + ',' + r + ' ' + n0.toFixed(2) + '/' + s0.toFixed(2));
      }));
      // rails: straight cells carry the full module along the run (the glass screens / balustrades on the floor plan,
      // the footbridge rails on the 4.5 m deck)
      [[g, '|', 1.02, 1.08], ...((g.layers || []).filter(l => Math.abs(l.y - 4.5) < 0.01).map(l => [l, ']', 5.52, 5.58]))].forEach(([D, ch, y0, y1]) => {
        for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
          if (D.at(c, r) !== ch) continue;
          const ew = D.at(c - 1, r) === ch && D.at(c + 1, r) === ch && D.at(c, r - 1) !== ch && D.at(c, r + 1) !== ch;
          const ns = D.at(c, r - 1) === ch && D.at(c, r + 1) === ch && D.at(c - 1, r) !== ch && D.at(c + 1, r) !== ch;
          if (ew || ns) expect('rail ' + ch, zi, c, r, 1, 1, y0, y1, ew, 0.9, 0.3);
        }
      });
    });
    return out;
  });
  check('wall faces, sunk side faces, rails, benches, gates, trains, track, stairs and doors lie along their line of cells (none a quarter turn off)', runs.checked > 1500 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 8).join(' | '));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
