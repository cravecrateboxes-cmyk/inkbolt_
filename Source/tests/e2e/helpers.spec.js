// INKBOLT Handy Helpers sight + red Undercover (owner requests; game/helpersight.js, game.js, render.js):
//   - a helper (rogue robot) hidden behind a wall or crate draws a blue ghost through it; one in plain sight does not;
//   - a helper out of view (behind the player) lights a soft blue glow on the screen edge toward it;
//   - with no helpers nothing is drawn and no glow shows;
//   - Undercover: the robots' cloak outline glows red (it was blue).
// Run (after tools/build.py): DEV=1 node tests/e2e/helpers.spec.js   (SHOTS=1 also writes tests/e2e/review/helpers-*.png)
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const OUT = path.join(__dirname, 'review');
let fails = 0;
function check(name, ok, info) { console.log((ok ? 'PASS ' : 'FAIL ') + name + (info ? '  ' + info : '')); if (!ok) fails++; }
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.webp') ? 'image/webp' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}
(async () => {
  const srv = await serve(), page = process.env.DEV ? 'Source/dev.html' : 'Play%20Inkbolt.html';
  const plan = process.env.PLAN || 'metro';
  const browser = await chromium.launch({ args: ARGS });
  const pg = await browser.newPage({ viewport: { width: 960, height: 540 } });
  const logs = [];
  pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
  pg.on('pageerror', e => logs.push('pageerror: ' + e.message));
  await pg.goto('http://localhost:' + srv.address().port + '/' + page + '?autotest=1&plan=' + plan);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play' && !document.getElementById('boot'), null, { timeout: 300000 });
  // freeze the robots' brains (the frame loop still poses and draws them); find a hidden spot and an open one
  const spot = await pg.evaluate(() => {
    const G = IB.Game, AI = IB.AI, Zn = G.level.zones[G.zone], world = G.level.world;
    G.level.zones.forEach(z => { z.queue.length = 0; z.plan = Object.assign({}, z.plan, { waves: [[]] }); z.wave = 0; }); AI.update = () => { }; if (G.guard) G.guard.on = false;
    AI.robots.forEach(r => { r.on = false; });
    const open = (x, z) => IB.Zones.isOpen(Zn, x, z);
    for (let r = 3; r < Zn.h - 3; r++) for (let c = 3; c < Zn.w - 3; c++) {
      const x = Zn.ox + c + 0.5, z = Zn.oz + r + 0.5; if (!open(x, z)) continue;
      for (let k = 0; k < 16; k++) {
        const a = k / 16 * Math.PI * 2, px = x + Math.sin(a) * 7, pz = z + Math.cos(a) * 7;
        if (!open(px, pz)) continue;
        const hid = !world.los(px, 1.6, pz, x, 0.5, z) && !world.los(px, 1.6, pz, x, 1.6, z) && !world.los(px, 1.6, pz, x, 1.0, z);
        if (!hid) continue;
        // a second spot in plain sight of the same camera, 6 m off to the side
        for (let j = 0; j < 16; j++) {
          const b = j / 16 * Math.PI * 2, qx = px + Math.sin(b) * 6, qz = pz + Math.cos(b) * 6;
          if (open(qx, qz) && world.los(px, 1.6, pz, qx, 0.5, qz) && world.los(px, 1.6, pz, qx, 1.4, qz)) return { cam: { x: px, z: pz }, hid: { x, z }, vis: { x: qx, z: qz } };
        }
      }
    }
    return null;
  });
  check('found a hidden spot and an open spot for the test', !!spot, JSON.stringify(spot));
  if (!spot) { await browser.close(); srv.close(); process.exit(1); }
  // spawn helper robots (the test hook, then turned rogue), looking from the camera spot at the hidden spot
  const stage = (robots, lookAt) => pg.evaluate(({ robots, cam, lookAt }) => {
    const AI = IB.AI, G = IB.Game;
    AI.robots.forEach(r => { r.on = false; });
    const made = robots.map(o => {
      const slot = __TEST__.spawnRobot(o.type, o.x, o.z), r = AI.types[o.type].slots[slot];
      r.x = o.x; r.z = o.z; r.vx = r.vz = 0; r.zone = G.zone; r.yaw = Math.atan2(cam.x - o.x, cam.z - o.z);
      if (o.rogue) { r.state = 'alert'; r.rogue = 99; } else { r.state = 'idle'; r.rogue = 0; }
      return r.type;
    });
    __TEST__.teleportTo(cam.x, cam.z);
    const dx = lookAt.x - cam.x, dz = lookAt.z - cam.z;
    __TEST__.look(Math.atan2(-dx, -dz), -Math.atan2(0.6, Math.hypot(dx, dz)));
    if (IB.Render.vmScene) IB.Render.vmScene.visible = false;
    return made;
  }, { robots, cam: spot.cam, lookAt });
  const state = () => pg.evaluate(() => {
    const ghosts = []; IB.Render.scene.traverse(o => { if (o.name === 'helperGhost' && o.visible) ghosts.push(o.isSkinnedMesh ? 'skin' : 'inst'); });
    const edges = Array.from(document.querySelectorAll('#helperEdges > div')).filter(e => +e.style.opacity > 0.05).length;
    return { ghosts: ghosts.length, kinds: ghosts, hs: { g: IB.HelperSight.ghosts, e: IB.HelperSight.edges }, edges };
  });
  const shot = async (n) => { if (process.env.SHOTS) { fs.mkdirSync(OUT, { recursive: true }); await pg.screenshot({ path: path.join(OUT, 'helpers-' + n + '.png'), timeout: 600000 }); console.log('wrote helpers-' + n + '.png'); } };

  // 1. helpers hidden behind cover: a Crawler and a Soldier (trooper rig) -> ghosts
  await stage([{ type: 'crawler', x: spot.hid.x - 0.6, z: spot.hid.z, rogue: true }, { type: 'soldier', x: spot.hid.x + 0.6, z: spot.hid.z, rogue: true }], spot.hid);
  await pg.waitForTimeout(2500);
  let s = await state();
  check('helpers hidden behind cover are drawn as blue ghosts (crawler parts and the soldier rig)', s.hs.g === 2 && s.kinds.includes('skin') && s.kinds.includes('inst'), JSON.stringify(s));
  await shot('hidden');
  // 2. the same robots NOT helpers: no ghosts
  await stage([{ type: 'crawler', x: spot.hid.x - 0.6, z: spot.hid.z }, { type: 'soldier', x: spot.hid.x + 0.6, z: spot.hid.z }], spot.hid);
  await pg.waitForTimeout(1500);
  s = await state();
  check('enemies (not helpers) behind cover get no ghost', s.ghosts === 0 && s.hs.g === 0, JSON.stringify(s));
  // 3. a helper in plain sight: no ghost
  await stage([{ type: 'crawler', x: spot.vis.x, z: spot.vis.z, rogue: true }], spot.vis);
  await pg.waitForTimeout(1500);
  s = await state();
  check('a helper in plain sight has no ghost and no edge glow', s.ghosts === 0 && s.edges === 0, JSON.stringify(s));
  await shot('visible');
  // 4. a helper behind the player: an edge glow, no ghost
  await stage([{ type: 'crawler', x: spot.vis.x, z: spot.vis.z, rogue: true }], { x: spot.cam.x * 2 - spot.vis.x, z: spot.cam.z * 2 - spot.vis.z });
  await pg.waitForTimeout(1500);
  s = await state();
  check('a helper behind the player lights an edge glow toward it', s.edges === 1 && s.ghosts === 0, JSON.stringify(s));
  await shot('edge');
  // 5. Undercover: the robots' outline glows red
  await stage([{ type: 'crawler', x: spot.vis.x, z: spot.vis.z }], spot.vis);
  const ink = await pg.evaluate(async () => {
    const SF = IB.SkillFX; SF.fx = Object.assign({}, SF.fx || {}, { cloak: true, cloakTime: 30, cloakCooldown: 1 }); SF.cloakT = 0; SF.cloakCd = 0;
    SF.tryCloak(IB.Game.player);
    await new Promise(r => setTimeout(r, 2500));
    const c = IB.Render.robotOutline.uInk.value; return { r: +c.r.toFixed(2), g: +c.g.toFixed(2), b: +c.b.toFixed(2), cloak: IB.Render.cloak.value };
  });
  check('Undercover: the robots\' outline glows red (not blue)', ink.cloak > 0.4 && ink.r > 0.9 && ink.b < 0.3 && ink.g < 0.35, JSON.stringify(ink));
  await shot('undercover');
  check('no page errors', logs.length === 0, logs.slice(0, 3).join(' | '));
  await browser.close(); srv.close();
  console.log(fails ? fails + ' FAILED' : 'ALL PASS');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
