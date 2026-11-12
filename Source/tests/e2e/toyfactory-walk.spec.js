// INKBOLT Topsy Toyworks (plan 'toyfactory'): the walk through both zones and the climbs. The player walks from the
// production floor's entry up the main aisle between the assembly lines to the north gate, the trail, the warehouse's
// entry walkway and its main aisle to the exit and the hatch (no invisible walls, nothing blocks the way); the west and
// east flanking aisles of the production floor are open end to end; both stairs of the pellet loft and of the dispatch
// mezzanine climb to their 3.5 m decks (the loft rail keeps the player on it). Ground robots follow onto both decks.
// Belts, rollers, pipes, racks, machines, benches, stairs and rails are checked numerically along their line of cells,
// wall faces in their wall plane. The render loop is paused and the real Player / AI code is stepped at a fixed 1/60 s.
// Run (after tools/build.py): node tests/e2e/toyfactory-walk.spec.js
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
  await pg.goto(base + '?autotest=1&plan=toyfactory');
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
  // nav: open cells on the pellet loft (zone 1) and the dispatch mezzanine (zone 2), both 3.5 m
  const nav = await pg.evaluate(() => IB.Game.level.zones.map(z => {
    const N = z.nav, NC = N.nx * N.nz, o = { layers: N.layers, deck: 0 };
    for (let k = 0; k < NC * N.layers; k++) if (!N.blocked[k] && Math.abs(N.h[k] - 3.5) < 0.01) o.deck++;
    return o;
  }));
  check('nav: the pellet loft (zone 1) and the dispatch mezzanine (zone 2) hold open cells at 3.5 m', nav[0].deck > 60 && nav[1].deck > 100, JSON.stringify(nav));

  // ---- the walk: production floor entry -> main aisle between the lines -> north gate -> trail -> warehouse -> exit
  let r = await pg.evaluate(() => { __place(0, 37.5, 63.5, 0); return __route(0, [[37.5, 60.0], [38.7, 50.0], [38.7, 26.0], [37.5, 12.0], [37.5, 2.0], [37.5, -6.0], [37.5, -13.0]], 140); });
  check('walk zone 1: from the entry up the main aisle between the lines to the north gate and onto the trail', r.reached === r.of && r.stuck === 0 && r.hi < 0.3, JSON.stringify(r));
  r = await pg.evaluate(() => __route(1, [[37.5, 66.0], [37.5, 58.0], [37.5, 40.0], [39.0, 22.0], [39.0, 9.0], [37.5, 2.0], [37.5, -4.0], [37.5, -20.0]], 160));
  check('walk zone 2: the warehouse walkway, the main aisle, the exit and the exit path', r.reached === r.of && r.stuck === 0 && r.hi < 0.3, JSON.stringify(r));
  const hatch = await pg.evaluate(() => { const L = IB.Game.level, p = IB.Game.player; return { d: +Math.hypot(p.x - L.hatch.x, p.z - L.hatch.z).toFixed(2) }; });
  check('the exit path leads on toward the hatch', hatch.d < 8, JSON.stringify(hatch));
  // flanking routes: the west aisle (between the moulding machines and the line heads) and the east aisle (between
  // the packaging machines and the pack benches) run from the south half to the north wall
  r = await pg.evaluate(() => { __place(0, 16.0, 44.0, 0); return __route(0, [[16.0, 30.0], [16.0, 11.0], [20.0, 9.0], [33.0, 9.0]], 90); });
  check('zone 1: the west aisle from the paint shop north past the line heads to the loft stairs', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 66.5, 42.0, 0); return __route(0, [[66.5, 30.0], [66.5, 2.0], [60.0, 6.0], [45.0, 6.0]], 90); });
  check('zone 1: the east aisle along the packing strip to the north wall', r.reached === r.of && r.stuck === 0, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 7.0, 56.0, 0); return __route(1, [[7.5, 44.0], [7.5, 31.0], [7.0, 26.0], [7.0, 9.0], [26.0, 9.0], [27.5, 31.0], [14.0, 31.0], [14.0, 47.0]], 120); });
  check('zone 2: down rack aisle 1, along the north end, back by the cross aisle and down aisle 5', r.reached === r.of && r.stuck === 0, JSON.stringify(r));

  // ---- climbs
  r = await pg.evaluate(() => { __place(0, 12.9, 18.5, 0); return __route(0, [[12.9, 16.8], [12.9, 10.3], [12.9, 8.3], [9.0, 8.3]], 30); });
  check('zone 1: up the loft stair from the moulding aisle onto the pellet loft (3.5 m)', r.reached === r.of && Math.abs(r.y - 3.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 26.0, 5.0, 0); return __route(0, [[24.2, 5.0], [17.3, 5.0], [15.2, 5.0], [13.5, 4.0]], 30); });
  check('zone 1: up the second loft stair from the line A aisle (rises west)', r.reached === r.of && Math.abs(r.y - 3.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(0, 6.0, 8.0, 3.5); return __route(0, [[6.0, 11.5]], 3); });
  check('zone 1: the loft rail keeps the player on the deck', r.lo > 3.45, JSON.stringify(r));
  const sight = await pg.evaluate(() => { const W = IB.Game.level.world, Z = IB.Game.level.zones[0]; return W.los(Z.ox + 15.0, 3.5 + 1.6, Z.oz + 8.0, Z.ox + 36.5, 1.5, Z.oz + 22); });
  check('zone 1: the loft looks out over the lines (clear sight line)', sight, String(sight));
  r = await pg.evaluate(() => { __place(1, 52.9, 20.5, 0); return __route(1, [[52.9, 18.8], [52.9, 12.3], [52.9, 10.3], [49.0, 9.5]], 30); });
  check('zone 2: up the main stair onto the dispatch mezzanine (3.5 m)', r.reached === r.of && Math.abs(r.y - 3.5) < 0.05, JSON.stringify(r));
  r = await pg.evaluate(() => { __place(1, 72.5, 6.0, 0); return __route(1, [[70.8, 6.0], [64.3, 6.0], [62.5, 6.0], [60.0, 9.0]], 30); });
  check('zone 2: up the east stair from the docks onto the mezzanine (rises west)', r.reached === r.of && Math.abs(r.y - 3.5) < 0.05, JSON.stringify(r));

  // ---- robots follow onto the decks
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
  let w = await chase(0, [6.0, 7.5, 3.5], [['crawler', 30, 20]], 70, 3.4);
  check('zone 1: a Crawler from the line A aisle climbs onto the pellet loft to the player (< 4 m) within 70 s', w.best > 3.4, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));
  w = await chase(1, [47.5, 9.5, 3.5], [['blader', 30, 40]], 70, 3.4);
  check('zone 2: a Blade Bot from the main aisle climbs onto the mezzanine to the player (< 4 m) within 70 s', w.best > 3.4, 'max y ' + w.best.toFixed(2) + ' in ' + w.t + ' s ' + JSON.stringify(w.last));

  // ---- pieces along their line of cells: drawn vertices (outline shell left out) in a block, in a height band, are
  // long along the block's line and short across it
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
    L.zones.forEach((Z, zi) => {
      const g = Z.grid, at = (c, r) => g.at(c, r);
      // wall faces: each module is drawn in the plane of its cell's open side, facing it (0 - 2.6 m band); a face
      // turned a quarter (onto a closed side) or missing fails
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
          if (cy > 2.6) continue;
          const kx = Math.abs(nx) / A2, kz = Math.abs(nz) / A2;
          let key = null;
          if (kx > 0.95 && Math.abs(cx - Math.round(cx)) < 0.012) key = (nx > 0 ? (Math.round(cx) - 1) + ',' + Math.floor(cz) + ',E' : Math.round(cx) + ',' + Math.floor(cz) + ',W');
          else if (kz > 0.95 && Math.abs(cz - Math.round(cz)) < 0.012) key = (nz > 0 ? Math.floor(cx) + ',' + (Math.round(cz) - 1) + ',S' : Math.floor(cx) + ',' + Math.round(cz) + ',N');
          if (key) area[key] = (area[key] || 0) + A2 / 2;
        }
      });
      const W = (x, y) => '#GE'.indexOf(at(x, y)) >= 0, SD = { S: [0, 1], N: [0, -1], E: [1, 0], W: [-1, 0] };
      const A = (g.layers || []).find(l => Math.abs(l.y - 0.02) < 1e-6);
      for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
        if (at(c, r) !== '#') continue;
        const code = A ? A.at(c, r) : '.';
        if (']_['.indexOf(code) >= 0 || code === 'c') continue;   // dock bays and chutes: openings in the wall plane
        const opens = Object.keys(SD).filter(sd => { const [dc, dr] = SD[sd]; return c + dc >= 0 && r + dr >= 0 && c + dc < g.w && r + dr < g.h && !W(c + dc, r + dr); });
        if (opens.length !== 1) continue;   // corner posts (drawn all round) and cells shut in
        const byGate = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dc, dr]) => 'GE'.indexOf(at(c + dc, r + dr)) >= 0);
        Object.keys(SD).forEach(sd => {
          const [dc, dr] = SD[sd];
          if (c + dc < 0 || r + dr < 0 || c + dc >= g.w || r + dr >= g.h) return;
          const open = !W(c + dc, r + dr), Ar = area[c + ',' + r + ',' + sd] || 0;
          out.checked++;
          if (open && Ar < 0.2) out.bad.push('wall face missing ' + zi + ':' + c + ',' + r + sd + ' ' + Ar.toFixed(2));
          if (!open && !byGate && Ar > 0.05) out.bad.push('wall face on a closed side ' + zi + ':' + c + ',' + r + sd + ' ' + Ar.toFixed(2));
        });
      }
      // belts (rows) and roller lines (columns): side rails in the 0.7 - 0.95 m band run the whole block, 1 m across
      ['=', '~', '-'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => expect('belt ' + ch, zi, c, r, w, h, 0.7, 0.95, true, w - 0.05, 1.02, 0.02)));
      ['r', 'z'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => expect('rollers ' + ch, zi, c, r, w, h, 0.7, 0.95, false, h - 0.05, 0.9, 0.02)));
      // racks: north-south runs, 2.04 m across
      blocks(g, 'N').forEach(([c, r, w, h]) => expect('rack', zi, c, r, w, h, 1.0, 1.5, false, h - 0.4, 2.1, 0.02));
      // moulding machines [5, 2] (turned against the west wall): 5 m along the wall
      blocks(g, 'M').forEach(([c, r, w, h]) => expect('mould', zi, c, r, w, h, 0.85, 0.95, false, 4.6, 2.0, 0.02));
      // benches [2, 1] along their row, pack benches [1, 2] along their column, packaging machines [6, 3] along the line
      ['k', 'K'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => { for (let k = 0; k < w / 2; k++) expect('bench ' + ch, zi, c + 2 * k, r, 2, 1, 0.85, 0.93, true, 1.85, 1.0, 0.02); }));
      blocks(g, 'b').forEach(([c, r, w, h]) => { for (let k = 0; k < h / 2; k++) expect('pack bench', zi, c, r + 2 * k, 1, 2, 0.85, 0.93, false, 1.85, 1.0, 0.02); });
      ['U', 'V', 'L'].forEach(ch => blocks(g, ch).forEach(([c, r, w, h]) => expect('packer ' + ch, zi, c, r + 1, w, 1, 0.7, 0.95, true, 5.7, 1.1, 0.02)));
      // stairs: s rises north (7 m along Z), l rises west (7 m along X); the top step is at the north / west end
      blocks(g, 's').forEach(([c, r, w, h]) => expect('stair s', zi, c, r, w, h, 1.5, 2.2, false, 2.5, 2.0, 0.02));
      blocks(g, 'l').forEach(([c, r, w, h]) => expect('stair l', zi, c, r, w, h, 1.5, 2.2, true, 2.5, 2.0, 0.02));
      (g.layers || []).forEach(D => {
        // overhead pipes (layer 4.2): a north-south run
        if (Math.abs(D.y - 4.2) < 0.01) blocks(D, '|').forEach(([c, r, w, h]) => expect('pipes', zi, c, r, w, h, 4.1, 4.3, w > h, Math.max(w, h) - 0.05, 0.9, 0.02));
        // deck rails (layer 3.5): straight cells carry the full module along the run
        if (Math.abs(D.y - 3.5) < 0.01) for (let r = 1; r < g.h - 1; r++) for (let c = 1; c < g.w - 1; c++) {
          if (D.at(c, r) !== '+') continue;
          const ew = D.at(c - 1, r) === '+' && D.at(c + 1, r) === '+' && D.at(c, r - 1) !== '+' && D.at(c, r + 1) !== '+';
          const ns = D.at(c, r - 1) === '+' && D.at(c, r + 1) === '+' && D.at(c - 1, r) !== '+' && D.at(c + 1, r) !== '+';
          if (ew || ns) expect('rail', zi, c, r, 1, 1, 4.5, 4.6, ew, 0.9, 0.3);
        }
      });
    });
    return out;
  });
  check('belt, roller, pipe, rack, machine, bench, stair, rail and wall-face pieces lie along their line of cells (none a quarter turn off)', runs.checked > 600 && runs.bad.length === 0, runs.checked + ' checked ' + runs.bad.slice(0, 8).join(' | '));
  // the stairs climb the right way: the step tops rise toward the deck side
  const stairs = await pg.evaluate(() => {
    const L = IB.Game.level, out = [];
    L.zones.forEach((Z, zi) => {
      const g = Z.grid;
      ['s', 'l'].forEach(ch => {
        for (let r = 0; r < g.h; r++) for (let c = 0; c < g.w; c++) {
          if (g.at(c, r) !== ch || g.at(c - 1, r) === ch || g.at(c, r - 1) === ch) continue;
          const lo = ch === 's' ? [c + 1, r + 6.5] : [c + 6.5, r + 1], hi = ch === 's' ? [c + 1, r + 0.5] : [c + 0.5, r + 1];
          const f = (p) => L.world.floorAt(Z.ox + p[0], Z.oz + p[1], 5);
          out.push({ zi, ch, lo: +(+f(lo)).toFixed(2), hi: +(+f(hi)).toFixed(2) });
        }
      });
    });
    return out;
  });
  check('stairs rise toward their deck (s north, l west)', stairs.length === 4 && stairs.every(s => s.hi > 3.0 && s.lo < 1.0), JSON.stringify(stairs));
  check('no console errors or warnings', logs.length === 0, logs.slice(0, 4).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
