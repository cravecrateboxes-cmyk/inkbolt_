// INKBOLT headless smoke test (section 9). Run: node tests/e2e/smoke.spec.js [path-to-html]
// Serves the repo over http://localhost, drives the level through window.__TEST__ and real input.
const { chromium } = require('playwright');
const path = require('path');
const http = require('http');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
let failures = 0;
function check(name, ok, info) { console.log((ok ? 'PASS ' : 'FAIL ') + name + (info ? '  ' + info : '')); if (!ok) failures++; }

function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'application/octet-stream' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}
async function until(pg, fn, arg, ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { if (await pg.evaluate(fn, arg)) return true; await pg.waitForTimeout(100); }
  return false;
}
const st = pg => pg.evaluate(() => __TEST__.state());

async function newPage(browser, url, opts) {
  const ctx = await browser.newContext(Object.assign({ viewport: { width: 1280, height: 720 } }, opts || {}));
  const pg = await ctx.newPage();
  pg.logs = [];
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') pg.logs.push(m.type() + ': ' + m.text()); });
  pg.on('pageerror', e => pg.logs.push('pageerror: ' + e.message));
  await pg.goto(url);
  await pg.waitForFunction(() => window.__TEST__ && __TEST__.state().mode === 'play', null, { timeout: 30000 });
  return pg;
}

async function hookRun(browser, base) {
  console.log('\n# level 1 via test hooks');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  const zones = (await st(pg)).zones.length;
  for (let z = 0; z < zones; z++) {
    if (z > 0) {
      await pg.evaluate(i => __TEST__.teleport(i), z);
      const started = await until(pg, i => __TEST__.state().zones[i] === 'active', z, 8000);
      check('zone ' + (z + 1) + ' starts on entry', started);
      const shut = await until(pg, i => __TEST__.state().entryGates[i] === 0, z, 8000);
      check('zone ' + (z + 1) + ' entry gate shuts behind the player', shut);
    }
    const spawned = await until(pg, () => __TEST__.state().alive > 0, null, 10000);
    check('zone ' + (z + 1) + ' robots drop in', spawned);
    // kill until cleared (waves keep coming until the zone is done)
    const t0 = Date.now();
    while (Date.now() - t0 < 20000) {
      const s = await st(pg); if (s.zones[z] === 'cleared') break;
      await pg.evaluate(() => __TEST__.killZone()); await pg.waitForTimeout(250);
    }
    const s1 = await st(pg);
    check('zone ' + (z + 1) + ' cleared', s1.zones[z] === 'cleared', JSON.stringify(s1.zones));
    const open = await until(pg, i => __TEST__.state().exitGates[i] >= 0.99, z, 6000);
    check('zone ' + (z + 1) + ' gate rolls up', open, JSON.stringify((await st(pg)).exitGates));
    const lit = await until(pg, i => { const t = __TEST__.state().trailLit[i].split('/'); return +t[0] === +t[1]; }, z, 6000);
    check('zone ' + (z + 1) + ' trail arrows light', lit, (await st(pg)).trailLit[z]);
  }
  const g = await st(pg);
  check('gems vacuumed to player', g.runGems > 0, 'runGems=' + g.runGems);
  await pg.evaluate(() => __TEST__.teleport('hatch'));
  const done = await until(pg, () => __TEST__.state().complete, null, 6000);
  check('exit hatch ends the level', done);
  const resultsShown = await pg.evaluate(() => /Level cleared/i.test(document.getElementById('overlay').textContent));
  check('results screen shows', resultsShown);
  const saved = await pg.evaluate(() => { const v = localStorage.getItem('inkbolt.slot1'); return v && JSON.parse(v).highest >= 1; });
  check('save written', !!saved);
  const plat = (await st(pg)).plat;
  check('Plat hooks in order', plat[0] === 'init' && plat.includes('loaded') && plat.includes('start') && plat[plat.length - 1] === 'stop', plat.join(','));
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function deathRun(browser, base) {
  console.log('\n# death, respawn and retries');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  await until(pg, () => __TEST__.state().alive > 0, null, 10000);
  await pg.evaluate(() => __TEST__.damagePlayer(500));
  const elim = await pg.evaluate(() => !document.getElementById('elim').hidden && document.getElementById('elimName').textContent);
  check('eliminated card shows', !!elim, elim);
  const back = await until(pg, () => __TEST__.state().alivePlayer, null, 15000);
  const s = await st(pg);
  check('respawn after countdown with full health', back && s.health === 100, 'health=' + s.health);
  for (let i = 0; i < 3; i++) { await pg.evaluate(() => __TEST__.damagePlayer(500)); await until(pg, () => __TEST__.state().alivePlayer || __TEST__.state().mode === 'fail', null, 15000); }
  const fail = await until(pg, () => /Out of retries/i.test(document.getElementById('overlay').textContent), null, 6000);
  check('fail screen after 3 retries are used', fail);
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function inputRun(browser, base) {
  console.log('\n# real input: keyboard, mouse look, clicks (zone 1)');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  const p0 = (await st(pg)).pos;
  await pg.mouse.move(640, 360);
  await pg.keyboard.down('KeyW'); await pg.waitForTimeout(900); await pg.keyboard.up('KeyW');
  const p1 = (await st(pg)).pos;
  check('W moves forward (-Z)', p1[2] < p0[2] - 0.5, p0[2].toFixed(2) + ' -> ' + p1[2].toFixed(2));
  await pg.keyboard.press('Space');
  check('Space jumps', await until(pg, () => __TEST__.state().pos[1] > 0.05, null, 6000));
  const yaw0 = await pg.evaluate(() => IB.Game.player.yaw);
  await pg.mouse.move(640, 360); await pg.mouse.down({ button: 'right' }); await pg.mouse.move(540, 360, { steps: 5 }); await pg.mouse.up({ button: 'right' });
  const yaw1 = await pg.evaluate(() => IB.Game.player.yaw);
  check('mouse drag turns the view', Math.abs(yaw1 - yaw0) > 0.05, yaw0.toFixed(3) + ' -> ' + yaw1.toFixed(3));
  await pg.keyboard.press('Digit2'); await pg.waitForTimeout(700);
  check('2 switches to Buzz', (await st(pg)).weapon === 'buzz');
  await pg.keyboard.press('Digit1'); await pg.waitForTimeout(700);
  // aim at robots and click until zone 1 clears
  await until(pg, () => __TEST__.state().alive > 0, null, 10000);
  const t0 = Date.now(); let clicks = 0;
  while (Date.now() - t0 < 90000) {
    const s = await st(pg); if (s.zones[0] === 'cleared') break;
    const aimed = await pg.evaluate(() => {
      const G = IB.Game, p = G.player; let best = null, bd = 1e9;
      IB.AI.robots.forEach(r => { if (!r.on || r.state === 'spawn' || r.state === 'pose') return; const d = Math.hypot(r.x - p.x, r.z - p.z); if (d < bd) { bd = d; best = r; } });
      if (!best) return false;
      const ey = p.y + 1.55, dx = best.x - p.x, dz = best.z - p.z, dy = (best.y + 0.55) - ey;
      p.yaw = Math.atan2(-dx, -dz); p.pitch = Math.atan2(dy, Math.hypot(dx, dz)); p.protect = 5; return true;
    });
    if (aimed) { await pg.mouse.click(640, 360); clicks++; }
    if ((await st(pg)).ammo === 0) await pg.keyboard.press('KeyR');
    await pg.waitForTimeout(aimed ? 260 : 300);
  }
  const s2 = await st(pg);
  check('zone 1 cleared with real clicks', s2.zones[0] === 'cleared', 'clicks=' + clicks + ' kills=' + s2.kills);
  check('bullet decals placed', s2.decals > 0, 'decals=' + s2.decals);
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(300);
  const paused = await pg.evaluate(() => IB.Game.mode === 'paused' && document.querySelector('#overlay .btn').textContent.trim().startsWith('Resume'));
  check('Esc pauses with Resume first', paused);
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function touchRun(browser, base) {
  console.log('\n# touch: stick, look drag, fire button');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox', { viewport: { width: 844, height: 390 }, hasTouch: true, isMobile: true, deviceScaleFactor: 1 });
  check('touch controls visible', await pg.evaluate(() => !document.getElementById('touch').hidden && !!document.getElementById('tFire')));
  const cdp = await pg.context().newCDPSession(pg);
  const touch = (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts });
  const p0 = (await st(pg)).pos;
  await touch('touchStart', [{ x: 120, y: 280, id: 1 }]);
  for (let i = 1; i <= 6; i++) { await touch('touchMove', [{ x: 120, y: 280 - i * 8, id: 1 }]); await pg.waitForTimeout(40); }
  await pg.waitForTimeout(800);
  await touch('touchEnd', []);
  const p1 = (await st(pg)).pos;
  check('left stick moves the player', Math.hypot(p1[0] - p0[0], p1[2] - p0[2]) > 0.5, JSON.stringify([p0, p1].map(p => p.map(v => +v.toFixed(2)))));
  const yaw0 = await pg.evaluate(() => IB.Game.player.yaw);
  await touch('touchStart', [{ x: 560, y: 160, id: 2 }]);
  for (let i = 1; i <= 6; i++) { await touch('touchMove', [{ x: 560 - i * 12, y: 160, id: 2 }]); await pg.waitForTimeout(30); }
  await touch('touchEnd', []);
  const yaw1 = await pg.evaluate(() => IB.Game.player.yaw);
  check('right drag turns the view', Math.abs(yaw1 - yaw0) > 0.05, yaw0.toFixed(3) + ' -> ' + yaw1.toFixed(3));
  const a0 = (await st(pg)).ammo;
  const fb = await pg.evaluate(() => { const r = document.getElementById('tFire').getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; });
  await touch('touchStart', [{ x: fb.x, y: fb.y, id: 3 }]); await pg.waitForTimeout(120); await touch('touchEnd', []);
  await pg.waitForTimeout(300);
  check('fire button shoots', (await st(pg)).ammo < a0, a0 + ' -> ' + (await st(pg)).ammo);
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function campaignRun(browser, base) {
  console.log('\n# campaign: big levels, no z-fighting, waypath -> loading -> next level');
  for (const plan of ['tt1', 'tt2', 'tt3']) {
    const pg = await newPage(browser, base + '?autotest=1&zcheck=1&plan=' + plan);
    const z = await pg.evaluate(() => IB.Game.level.zfight);
    check(plan + ' has no coplanar overlapping pieces', z.length === 0, z.slice(0, 3).join(' | '));
    const big = await pg.evaluate(() => IB.Game.level.zones.map(z => z.w * z.h));
    check(plan + ' zones are big (>= 2,000 m2 each)', big.every(a => a >= 2000), big.join(','));
    if (plan !== 'tt1') { await pg.context().close(); continue; }
    const stands = await pg.evaluate(() => (IB.Game.weaponStands || []).map(w => w.id));
    check('new weapon waits at the start of level 1', stands.length >= 1, stands.join(','));
    await pg.evaluate(() => { const w = IB.Game.weaponStands[0]; IB.Game.player.x = w.x; IB.Game.player.z = w.z; });
    check('walking up to it picks it up', await until(pg, () => IB.Game.weaponStands[0].taken, null, 5000), (await st(pg)).weapon);
    for (let zi = 0; zi < 2; zi++) {
      if (zi > 0) { await pg.evaluate(i => __TEST__.teleport(i), zi); await until(pg, i => __TEST__.state().zones[i] === 'active', zi, 8000); }
      const t0 = Date.now();
      while (Date.now() - t0 < 30000) { if ((await st(pg)).zones[zi] === 'cleared') break; await pg.evaluate(() => { __TEST__.forceWaves(); __TEST__.killZone(); }); await pg.waitForTimeout(250); }
      check('tt1 zone ' + (zi + 1) + ' cleared', (await st(pg)).zones[zi] === 'cleared');
    }
    // walk the exit waypath: it dims, then the next level loads and lights up
    await pg.evaluate(() => { const h = IB.Game.level.hatch; IB.Game.player.x = h.x; IB.Game.player.z = h.z0 - (h.z0 - h.z) * 0.5; });
    const dimmed = await until(pg, () => IB.Game.dimV > 0.25 && IB.Game.dimV < 1, null, 4000);
    check('screen dims along the waypath', dimmed, 'dim=' + (await pg.evaluate(() => IB.Game.dimV)));
    await pg.evaluate(() => __TEST__.teleport('hatch'));
    const loaded = await until(pg, () => IB.Game.plan.id === 'tt2' && IB.Game.mode === 'play', null, 30000);
    check('next level loads after the waypath', loaded, (await pg.evaluate(() => IB.Game.plan.id + ' ' + IB.Game.mode)));
    const lit = await until(pg, () => IB.Game.dimV === 0 || IB.Game.dimV < 0.02, null, 15000);
    check('screen lights up again', lit, 'dim=' + (await pg.evaluate(() => IB.Game.dimV)));
    const saved = await pg.evaluate(() => JSON.parse(localStorage.getItem('inkbolt.slot1') || '{}'));
    check('save moved on to level 2 with the new weapon', saved.plan === 'tt2' && (saved.owned || []).length >= 2, JSON.stringify({ plan: saved.plan, owned: saved.owned }));
    check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
    await pg.context().close();
  }
}

async function slideRun(browser, base) {
  console.log('\n# movement: sprint, slide, crouch');
  const pg = await newPage(browser, base + '?autotest=1');
  await pg.evaluate(() => { IB.Game.player.protect = 999; IB.Game.player.yaw = 0.75; });
  await pg.keyboard.down('KeyW'); await pg.keyboard.down('ShiftLeft');
  check('sprint reaches > 7.5 m/s', await until(pg, () => Math.hypot(IB.Game.player.vx, IB.Game.player.vz) > 7.5, null, 6000));
  await pg.keyboard.press('KeyC');
  check('C slides out of a sprint', await until(pg, () => IB.Game.player.sliding, null, 2000));
  const s1 = await pg.evaluate(() => ({ v: Math.hypot(IB.Game.player.vx, IB.Game.player.vz) }));
  check('slide is faster than a sprint at the start', s1.v > 8, s1.v.toFixed(2));
  check('slide ends on its own', await until(pg, () => !IB.Game.player.sliding, null, 25000));
  await pg.keyboard.up('ShiftLeft'); await pg.keyboard.up('KeyW');
  await pg.keyboard.down('KeyC');
  check('holding C crouches', await until(pg, () => IB.Game.player.crouching && IB.Game.player.low > 0.4, null, 3000));
  await pg.keyboard.up('KeyC');
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

(async () => {
  const server = await serve();
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET);
  console.log('target', base);
  const browser = await chromium.launch({ args: ARGS });
  try {
    await hookRun(browser, base);
    await deathRun(browser, base);
    await inputRun(browser, base);
    await touchRun(browser, base);
    await slideRun(browser, base);
    await campaignRun(browser, base);
  } catch (e) { console.log('FAIL exception ' + e.stack); failures++; }
  await browser.close(); server.close();
  console.log('\n' + (failures ? failures + ' FAILED' : 'ALL PASSED'));
  process.exit(failures ? 1 : 0);
})();
