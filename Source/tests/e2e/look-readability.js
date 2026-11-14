// Tactical look gate (plan Stage 4): enemy readability in the dark.
//   node Source/tests/e2e/look-readability.js [outDir] [plan ...]      (default plans: metro coalmine)
// For each plan: the darkest open cell of zone 0 (lowest light-volume value, sky included), a Crawler and a Soldier
// posed there, the camera 12 m and 30 m away with a clear line of sight. Two shots per case (with and without the
// robot); the robot's pixels are where the two differ. Gate: mean luminance of the robot's pixels differs from a
// 16 px ring around them by at least 0.06. Prints one line per case and writes the PNGs to outDir.
// Env: HTML (default Play Inkbolt.html), TIER (default high), W/H (default 960x540).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs'), { execFileSync } = require('child_process');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const OUT = path.resolve(process.argv[2] || 'Source/dist/look/readability');
const PLANS = process.argv.length > 3 ? process.argv.slice(3) : ['metro', 'coalmine'];
const W = +(process.env.W || 960), H = +(process.env.H || 540), TIER = process.env.TIER || 'high';
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const server = await new Promise(res => { const s = http.createServer((req, r) => { const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.webp') ? 'image/webp' : 'text/javascript' }); r.end(d); }); }).listen(0, () => res(s)); });
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(process.env.HTML || 'Play Inkbolt.html') + '?autotest=1';
  const browser = await chromium.launch({ args: ARGS });
  const rows = [];
  for (const plan of PLANS) {
    const pg = await browser.newPage({ viewport: { width: W, height: H } });
    const errs = [];
    pg.on('pageerror', e => errs.push(e.message));
    try {
      await pg.goto(base + '&plan=' + plan);
      await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 180000 });
      const target = await pg.evaluate((t) => {
        IB.AI.spawn = (function (orig) { IB.AI._spawnOrig = orig; return function () { return null; }; })(IB.AI.spawn);
        IB.AI.robots.forEach(r => { r.on = false; });
        if (IB.Game.guard) IB.Game.guard.on = false;
        __TEST__.setTier(t);
        while (!IB.LightGrid.idle()) IB.LightGrid.work(50);
        const G = IB.Game, Zn = G.level.zones[0], LG = IB.LightGrid, world = G.level.world;
        const cands = [];
        for (let r = 2; r < Zn.h - 2; r++) for (let c = 2; c < Zn.w - 2; c++) {
          const x = Zn.ox + c + 0.5, z = Zn.oz + r + 0.5;
          if (!IB.Zones.isOpen(Zn, x, z)) continue;
          // need open cells round it (room for the robot)
          let ok = true; for (let d = -1; d <= 1 && ok; d++) for (let e = -1; e <= 1 && ok; e++) if (!IB.Zones.isOpen(Zn, x + d, z + e)) ok = false;
          if (!ok) continue;
          const s = LG.sampleAt(x, 1.0, z); if (!s) continue;
          const L = s.local, v = 0.2126 * L[0] + 0.7152 * L[1] + 0.0722 * L[2] + s.sky * 0.5;   // sampleAt -> { local: [r, g, b], sky }
          cands.push({ x, z, v });
        }
        if (!cands.length) return null;
        cands.sort((a, b) => a.v - b.v);
        // camera spots at 12 and 30 m with a clear line of sight (eye 1.6 m, target 0.8 m)
        // the darkest cells first; a cell must have a clear sight line at both 12 m and 30 m (room-and-pillar
        // layouts block 30 m from many cells, so walk down the darkest 5% until one has both)
        for (const best of cands.slice(0, Math.max(10, Math.ceil(cands.length * 0.05)))) {
          const cams = {};
          for (const D of [12, 30]) {
            for (let k = 0; k < 32 && !cams[D]; k++) {
              const a = k / 32 * Math.PI * 2, px = best.x + Math.sin(a) * D, pz = best.z + Math.cos(a) * D;
              if (!IB.Zones.isOpen(Zn, px, pz)) continue;
              if (!world.los(px, 1.6, pz, best.x, 0.8, best.z)) continue;
              cams[D] = { x: px, z: pz };
            }
          }
          if (cams[12] && cams[30]) return { x: best.x, z: best.z, v: best.v, cams, rank: cands.indexOf(best), of: cands.length };
        }
        return null;
      }, TIER);
      if (!target) { rows.push({ plan, err: 'no dark cell with a 12 m and a 30 m sight line' }); console.log(plan, 'no dark cell with both sight lines'); continue; }
      console.log(plan, 'darkest usable cell: rank', target.rank, 'of', target.of, 'light', target.v.toFixed(3));
      for (const D of [12, 30]) {
        const cam = target.cams[D];
        if (!cam) { rows.push({ plan, D, err: 'no clear line of sight at ' + D + ' m' }); continue; }
        for (const type of ['crawler', 'soldier']) {
          const files = {};
          for (const withBot of [false, true]) {
            await pg.evaluate(({ target, cam, type, withBot }) => {
              const G = IB.Game, AI = IB.AI;
              AI.robots.forEach(r => { r.on = false; });
              if (withBot) {
                const r = AI._spawnOrig(type, target.x, target.z, 0, cam.x, cam.z, { pose: true });
                if (r) { r.x = target.x; r.z = target.z; r.y = 0; r.vx = r.vz = 0; r.yaw = Math.atan2(cam.x - target.x, cam.z - target.z); }
              }
              __TEST__.teleportTo(cam.x, cam.z);
              const dx = target.x - cam.x, dz = target.z - cam.z;
              __TEST__.look(Math.atan2(-dx, -dz), -Math.atan2(0.8, Math.hypot(dx, dz)));
              // only the robot may differ between the two shots: no gun, no film grain, no dust motes
              if (IB.Render.vmScene) IB.Render.vmScene.visible = false;
              if (IB.Post && IB.Post.M) IB.Post.M.comp.uniforms.uGrain.value = 0;
              if (IB.Atmo && IB.Atmo.extras && IB.Atmo.extras.dust) IB.Atmo.extras.dust.visible = false;
              return withBot ? AI.robots.filter(r => r.on).map(r => r.type + '@' + r.x.toFixed(1) + ',' + r.z.toFixed(1)).join(' ') : '';
            }, { target, cam, type, withBot }).then(v => { if (withBot) console.log('  ', plan, type, D + 'm robots on:', v || 'NONE'); });
            await pg.waitForTimeout(2500);
            const f = path.join(OUT, `${plan}-${type}-${D}m-${withBot ? 'bot' : 'empty'}.png`);
            await pg.screenshot({ path: f, timeout: 600000 });
            files[withBot] = f;
          }
          const res = JSON.parse(execFileSync('python3', [path.join(__dirname, 'look-readability.py'), files[false], files[true]]).toString());
          rows.push(Object.assign({ plan, type, D, cell: +target.v.toFixed(3) }, res));
          console.log(JSON.stringify(rows[rows.length - 1]));
        }
      }
    } catch (e) { rows.push({ plan, err: e.message.slice(0, 200) }); console.log(plan, 'FAIL', e.message.slice(0, 200)); }
    if (errs.length) console.log(plan, 'page errors:', errs.slice(0, 3).join(' | '));
    await pg.close();
  }
  await browser.close(); server.close();
  const fails = rows.filter(r => r.err || !(r.diff >= 0.06));
  console.log(fails.length ? 'READABILITY FAIL ' + fails.length + ' of ' + rows.length : 'READABILITY PASS ' + rows.length + ' cases');
})();
