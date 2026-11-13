// INKBOLT look review shots (tactical look plan, Stage 0.2).
//   node Source/tests/e2e/look-shots.js <outDir> <plan> [plan ...]
// Env: LOOK=classic|on (classic adds &look=classic), TIER=high|medium|low|potato, ZONES=0,1 (overrides the automatic
// 8-spot recipe with long/mid/back/q per listed zone), VM=0 hides the viewmodel, HTML=<file> (default "Play Inkbolt.html"),
// EXTRA=<query string appended to the URL>, ONLY=<spot names, comma separated>.
// Spots come from look-spots.json (x/z in zone cells, like map-shots.js), else four automatic spots per zone.
// Robots off, waves cleared, player protected, no shake. One browser, one page per plan. Writes
// <outDir>/<plan>-<spot>.png at 1280 x 720 (env W, H to change) and prints one line per plan.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const [outDir, ...plans] = process.argv.slice(2);
if (!outDir || !plans.length) { console.log('usage: node look-shots.js <outDir> <plan> [plan ...]'); process.exit(2); }
const LOOK = process.env.LOOK || 'on';
const TIER = process.env.TIER || 'high';   // fixed: the auto tier guard would step down on the CPU renderer
const ZONES = (process.env.ZONES || '0,1').split(',').map(Number);
const VM = process.env.VM !== '0';
const HTML = process.env.HTML || 'Play Inkbolt.html';
const EXTRA = process.env.EXTRA || '';
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const SPOTS = JSON.parse(fs.readFileSync(path.join(__dirname, 'look-spots.json'), 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => {
        if (e) { r.writeHead(404); return r.end(); }
        r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' });
        r.end(d);
      });
    }).listen(0, () => res(s));
  });
}

// Automatic spots: a recipe of kinds per zone, so any map (including future ones) gets the same 8 review views
// with no hand work. Kinds: long (entry looking at the zone centre), mid, back, wall (a wall at about 2.5 m),
// floor (grazing floor), up (lamps and ceiling), aim (gun aimed), q (a quarter point).
const RECIPE = [['z0', 0, 'long'], ['z0', 0, 'wall'], ['z0', 0, 'floor'], ['z0', 0, 'up'], ['z0', 0, 'aim'],
  ['z1', 1, 'long'], ['z1', 1, 'back'], ['z1', 1, 'wall']];
async function autoSpots(pg, recipe) {
  return pg.evaluate((recipe) => {
    const G = IB.Game, Z = IB.Zones, out = [];
    const yawTo = (dx, dz) => Math.atan2(-dx, -dz);
    for (const [tag, zi0, kind] of recipe) {
      const zi = Math.min(zi0, G.level.zones.length - 1), z = G.level.zones[zi];
      const open = (x, zz) => Z.isOpen(z, x, zz);
      const roomy = (x, zz) => open(x, zz) && open(x + 0.6, zz) && open(x - 0.6, zz) && open(x, zz + 0.6) && open(x, zz - 0.6);
      const near = (tx, tz) => {
        for (let r = 0; r < 18; r++) for (let a = 0; a < 16; a++) {
          const x = tx + Math.cos(a / 16 * 6.283) * r, zz = tz + Math.sin(a / 16 * 6.283) * r;
          if (roomy(x, zz)) return [x, zz];
        }
        return [tx, tz];
      };
      const cx = z.ox + z.w / 2, cz = z.oz + z.h / 2, m = near(cx, cz), e = z.entry;
      const s = { name: tag + '-' + kind, zone: zi, pitch: -0.04 };
      if (kind === 'long') { const p = near(e.x, e.z); s.wx = p[0]; s.wz = p[1]; s.yaw = yawTo(m[0] - p[0], m[1] - p[1]); }
      else if (kind === 'mid') { s.wx = m[0]; s.wz = m[1]; s.yaw = 0.7; }
      else if (kind === 'back') { s.wx = m[0]; s.wz = m[1]; s.yaw = yawTo(e.x - m[0], e.z - m[1]); }
      else if (kind === 'q') { const q = near(z.ox + z.w * 0.25, z.oz + z.h * 0.3); s.wx = q[0]; s.wz = q[1]; s.yaw = -1.2; }
      else if (kind === 'floor') { s.wx = m[0]; s.wz = m[1]; s.yaw = 2.0; s.pitch = -0.38; }
      else if (kind === 'up') { s.wx = m[0]; s.wz = m[1]; s.yaw = -2.2; s.pitch = 0.32; }
      else if (kind === 'aim') { s.wx = m[0]; s.wz = m[1]; s.yaw = 0.7; s.aim = 1; }
      else if (kind === 'wall') {
        // march 16 rays from points around the zone; take the first wall hit between 3 and 7 m; stand 2.5 m off it
        let best = null;
        const starts = [m, near(z.ox + z.w * 0.3, z.oz + z.h * 0.7), near(z.ox + z.w * 0.7, z.oz + z.h * 0.3)];
        for (const st of starts) {
          for (let a = 0; a < 16 && !best; a++) {
            const dx = Math.cos(a / 16 * 6.283 + 0.2), dz = Math.sin(a / 16 * 6.283 + 0.2);
            for (let d = 0.5; d < 9; d += 0.25) {
              if (!open(st[0] + dx * d, st[1] + dz * d)) { if (d >= 3 && d <= 7) best = { x: st[0] + dx * (d - 2.5), z: st[1] + dz * (d - 2.5), dx, dz }; break; }
            }
          }
          if (best) break;
        }
        if (best && roomy(best.x, best.z)) { s.wx = best.x; s.wz = best.z; s.yaw = yawTo(best.dx, best.dz); s.pitch = -0.08; }
        else { s.wx = m[0]; s.wz = m[1]; s.yaw = -0.9; }
      }
      out.push(s);
    }
    return out;
  }, recipe);
}

(async () => {
  const server = await serve();
  const q = '?autotest=1' + (LOOK === 'classic' ? '&look=classic' : '') + (EXTRA ? '&' + EXTRA.replace(/^[?&]/, '') : '');
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(HTML) + q;
  const browser = await chromium.launch({ args: ARGS });
  let fails = 0;
  for (const plan of plans) {
    const t0 = Date.now();
    const ctx = await browser.newContext({ viewport: { width: +(process.env.W || 1280), height: +(process.env.H || 720) }, deviceScaleFactor: 1 });
    const pg = await ctx.newPage();
    const logs = [];
    pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
    pg.on('console', m => { if (m.type() === 'error') logs.push('console: ' + m.text()); });
    let n = 0;
    try {
      await pg.goto(base + '&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 150000 });
      await pg.evaluate((t) => {
        IB.AI.spawn = function () { return null; }; IB.AI.robots.forEach(r => { r.on = false; });
        if (IB.Game.guard) IB.Game.guard.on = false;
        if (t) __TEST__.setTier(t);
      }, TIER);
      const nz = await pg.evaluate(() => IB.Game.level.zones.length);
      let spots = SPOTS[plan] && SPOTS[plan].spots;
      if (!spots) {
        const recipe = process.env.ZONES ? ZONES.flatMap(zi => [['z' + zi, zi, 'long'], ['z' + zi, zi, 'mid'], ['z' + zi, zi, 'back'], ['z' + zi, zi, 'q']]) : RECIPE;
        spots = await autoSpots(pg, recipe.filter(r => r[1] < nz || r[1] === 1));
        const seen = new Set(); spots = spots.filter(s => !seen.has(s.name) && seen.add(s.name));
      }
      if (ONLY) spots = spots.filter(s => ONLY.includes(s.name));
      let curZone = -1;
      for (const s of spots) {
        if (s.zone !== curZone) {
          await pg.evaluate(i => __TEST__.teleport(i), s.zone);
          await pg.waitForTimeout(600);
          // the look's light volume bakes zones in the background: wait until this zone is done
          await pg.evaluate(i => { if (IB.LightGrid && IB.LightGrid.ready) IB.LightGrid.bakeZoneNow(i); }, s.zone);
          curZone = s.zone;
        }
        await pg.evaluate((a) => {
          const G = IB.Game, p = G.player, z = G.level.zones[a.zone];
          p.protect = 1e9; G.settings.shake = false; G.trauma = 0;
          IB.AI.robots.forEach(r => { r.on = false; });
          G.level.zones.forEach(zz => { if (zz.queue) zz.queue.length = 0; zz.wave = zz.plan.waves.length - 1; });
          IB.Zones.setVisible(G.level, a.zone);
          const x = a.wx !== undefined ? a.wx : z.ox + a.x, zw = a.wz !== undefined ? a.wz : z.oz + a.z;
          p.x = x; p.z = zw; p.vx = p.vz = p.vy = 0; p.yaw = a.yaw || 0; p.pitch = a.pitch || 0;
          p.y = a.y !== undefined ? a.y : (IB.Zones.floorY(x, zw, 1.2) || 0);
        }, s);
        await pg.waitForTimeout(900);
        await pg.evaluate((a) => {
          const G = IB.Game, p = G.player, z = G.level.zones[a.zone];
          p.x = a.wx !== undefined ? a.wx : z.ox + a.x; p.z = a.wz !== undefined ? a.wz : z.oz + a.z;
          p.yaw = a.yaw || 0; p.pitch = a.pitch || 0;
          if (a.y !== undefined) p.y = a.y;
        }, s);
        if (!VM) await pg.evaluate(() => { if (IB.Render.vmScene) IB.Render.vmScene.visible = false; });
        if (s.aim) { await pg.mouse.move(640, 360); await pg.mouse.down({ button: 'right' }); }
        await pg.waitForTimeout(s.aim ? 900 : 250);
        await pg.screenshot({ path: path.join(outDir, plan + '-' + s.name + '.png'), timeout: 240000 });
        if (s.aim) await pg.mouse.up({ button: 'right' });
        n++;
      }
      const info = await pg.evaluate(() => { const st = __TEST__.state(), L = IB.Look && IB.Look.cur, D = IB.Dress;
        return { calls: st.calls, tris: st.triangles, family: L && L.family, guessed: L && L.guessed, gameErrors: IB.Game.errors.length,
          dress: D && D.stats ? D.stats.map(z => z.floor + '/' + z.wall + '/' + z.clutter).join(' ') : '' }; }).catch(() => ({}));
      console.log(plan, 'ok', n, 'shots', Math.round((Date.now() - t0) / 1000) + 's', JSON.stringify(info), logs.slice(0, 3).join(' | '));
      if (logs.length) fails++;
    } catch (e) {
      fails++;
      console.log(plan, 'FAIL after', n, 'shots:', e.message.slice(0, 200), logs.slice(0, 3).join(' | '));
    }
    await ctx.close();
  }
  await browser.close(); server.close();
  process.exit(fails ? 1 : 0);
})();
