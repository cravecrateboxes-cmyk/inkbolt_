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
    const open = await until(pg, i => __TEST__.state().exitGates[i] >= 0.99, z, 20000);
    check('zone ' + (z + 1) + ' gate rolls up', open, JSON.stringify((await st(pg)).exitGates));
    const lit = await until(pg, i => { const t = __TEST__.state().trailLit[i].split('/'); return +t[0] === +t[1]; }, z, 20000);
    check('zone ' + (z + 1) + ' trail arrows light', lit, (await st(pg)).trailLit[z]);
  }
  const g = await st(pg);
  check('gems vacuumed to player', g.runGems > 0, 'runGems=' + g.runGems);
  await pg.evaluate(() => __TEST__.teleport('hatch'));
  const done = await until(pg, () => __TEST__.state().complete, null, 6000);
  check('exit hatch ends the level', done);
  const resultsShown = await pg.evaluate(() => /Level cleared/i.test(document.getElementById('overlay').textContent));
  check('results screen shows', resultsShown);
  const lvText = await pg.evaluate(() => document.getElementById('overlay').textContent);
  check('results show the level-up (LV 2, +2 skill points)', /LV 2/.test(lvText) && /\+2 skill pts/.test(lvText), lvText.slice(-60));
  const saved =await pg.evaluate(() => { const v = localStorage.getItem('inkbolt.slot1'); return v && JSON.parse(v).highest >= 1; });
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
  const back = await until(pg, () => __TEST__.state().alivePlayer, null, 45000);   // 3 s of game time: slow under software GL on a busy machine
  const s = await st(pg);
  check('respawn after countdown with full health', back && s.health === 100, 'health=' + s.health);
  for (let i = 0; i < 3; i++) { await pg.evaluate(() => __TEST__.damagePlayer(500)); await until(pg, () => __TEST__.state().alivePlayer || __TEST__.state().mode === 'fail', null, 45000); }
  const fail = await until(pg, () => /Out of retries/i.test(document.getElementById('overlay').textContent), null, 15000);
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
  while (Date.now() - t0 < 200000) {
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
  // field kit on touch: the grid button next to pause opens it, the close button resumes
  const mb = await pg.evaluate(() => { const r = document.getElementById('menuBtn').getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height }; });
  check('touch menu button is a 48 px target', mb.w >= 48 && mb.h >= 48, mb.w + 'x' + mb.h);
  await touch('touchStart', [{ x: mb.x, y: mb.y, id: 4 }]); await touch('touchEnd', []);
  check('menu button opens the field kit', await until(pg, () => IB.Game.mode === 'menu' && !document.getElementById('tabmenu').hidden, null, 3000));
  check('touch controls hide while it is open', await pg.evaluate(() => document.getElementById('touch').hidden));
  await pg.tap('.tm-close');
  check('close button resumes play', await until(pg, () => IB.Game.mode === 'play' && document.getElementById('tabmenu').hidden && !document.getElementById('touch').hidden, null, 3000));
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function tabMenuRun(browser, base) {
  console.log('\n# field kit (Tab): pause, spend a skill point, change the loadout, respec, resume');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  await until(pg, () => IB.Game.run.started, null, 5000);
  // progress as if levels 1-3 were cleared (4 skill points) and a rifle was picked up earlier
  await pg.evaluate(() => { const G = IB.Game; G.slot.highest = 3; G.slot.gems = 100; G.slot.arsenal.push('rivet'); G.slot.owned = G.slot.arsenal.slice(); G.applyProgress(); });
  const p0 = await pg.evaluate(() => __TEST__.progress());
  check('progress derived from the save', p0.level === 4 && p0.points === 4 && p0.loadoutMax === 2, JSON.stringify(p0));
  check('HUD shows the level tag', await pg.evaluate(() => /LV\s*4/.test(document.getElementById('lvTag').textContent) && !document.getElementById('lvPts').hidden));
  await pg.mouse.move(640, 360);
  await pg.keyboard.press('Tab');
  check('Tab opens the field kit and pauses', await until(pg, () => IB.Game.mode === 'menu' && !document.getElementById('tabmenu').hidden, null, 3000));
  check('focus stays inside the menu (Tab did not move browser focus)', await pg.evaluate(() => document.getElementById('tabmenu').contains(document.activeElement)));
  const t0 = await pg.evaluate(() => IB.Game.run.time); await pg.waitForTimeout(500);
  check('game time is frozen while open', (await pg.evaluate(() => IB.Game.run.time)) === t0);
  check('HUD hidden behind the menu', await pg.evaluate(() => document.getElementById('hud').hidden));
  // skills: E twice from Loadout -> Gear -> Skills (keyboard), then mouse
  await pg.keyboard.press('KeyE');
  check('E switches to the Gear tab (empty state without the loot system)', await pg.evaluate(() => IB.TabMenu.tab === 'gear' && !!document.querySelector('#tmGear')));
  await pg.keyboard.press('KeyE');
  check('E again switches to Skills', await pg.evaluate(() => IB.TabMenu.tab === 'skills' && !!document.querySelector('.sk-tree')));
  await pg.click('[data-skill="overboard"]');
  await pg.click('[data-act="buy"]');
  let pr = await pg.evaluate(() => __TEST__.progress());
  check('Spend buys Overboard rank 1', pr.skills.overboard === 1 && pr.points === 3, JSON.stringify(pr.skills) + ' points=' + pr.points);
  await pg.focus('[data-skill="overboard"]'); await pg.keyboard.press('Enter');
  pr = await pg.evaluate(() => __TEST__.progress());
  check('Enter on the selected skill spends again', pr.skills.overboard === 2 && pr.points === 2, JSON.stringify(pr.skills));
  check('locked tier refuses (Heavy Ink needs 6 points above)', await pg.evaluate(() => { document.querySelector('[data-skill="heavyink"]').click(); return document.querySelector('[data-act="buy"]').disabled; }));
  const saved1 = await pg.evaluate(() => JSON.parse(localStorage.getItem('inkbolt.slot1')).skills);
  check('skills saved at once', saved1 && saved1.overboard === 2, JSON.stringify(saved1));
  // loadout: slot 2, then the rifle
  await pg.keyboard.press('KeyQ'); await pg.keyboard.press('KeyQ');
  check('Q goes back to Loadout', await pg.evaluate(() => IB.TabMenu.tab === 'loadout'));
  check('arsenal lists every owned gun, 2 slots + a locked third', await pg.evaluate(() => document.querySelectorAll('.lo-card').length === 3 && document.querySelectorAll('.lo-slot').length === 3 && !!document.querySelector('.lo-slot.locked')));
  await pg.click('[data-slot="1"]'); await pg.click('[data-gun="rivet"]');
  pr = await pg.evaluate(() => __TEST__.progress());
  check('rifle goes into slot 2', JSON.stringify(pr.loadout) === '["pip","rivet"]', JSON.stringify(pr.loadout));
  await pg.keyboard.press('Tab');
  check('Tab closes and resumes', await until(pg, () => IB.Game.mode === 'play' && document.getElementById('tabmenu').hidden && !document.getElementById('hud').hidden, null, 3000));
  pr = await pg.evaluate(() => __TEST__.progress());
  check('carried guns follow the loadout', JSON.stringify(pr.carried) === '["pip","rivet"]', JSON.stringify(pr.carried));
  check('Overboard applies (+20% magazine: Warden 12 -> 15)', await pg.evaluate(() => IB.Weapons.magSize(IB.Game.ws, IB.WEAPONS.pip) === 15));
  await pg.keyboard.press('Digit2'); await pg.waitForTimeout(700);
  check('key 2 draws the rifle from slot 2', (await st(pg)).weapon === 'rivet', (await st(pg)).weapon);
  await pg.keyboard.press('Digit3'); await pg.waitForTimeout(300);
  check('key 3 does nothing with 2 guns', (await st(pg)).weapon === 'rivet');
  // respec costs gems and refunds everything
  await pg.evaluate(() => __TEST__.tabMenu('skills'));
  await pg.click('[data-act="respec"]'); await pg.click('[data-act="respec"]');
  pr = await pg.evaluate(() => __TEST__.progress());
  const gems = await pg.evaluate(() => IB.Game.slot.gems);
  check('respec resets the tree for ' + 40 + ' gems', Object.keys(pr.skills).length === 0 && pr.points === 4 && gems === 60, JSON.stringify(pr.skills) + ' gems=' + gems);
  await pg.keyboard.press('Escape');
  check('Esc closes it too', await until(pg, () => IB.Game.mode === 'play', null, 3000));
  check('respec applied (magazine back to 12)', await pg.evaluate(() => IB.Weapons.magSize(IB.Game.ws, IB.WEAPONS.pip) === 12));
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function campaignRun(browser, base) {
  console.log('\n# campaign: big levels, no z-fighting, waypath -> loading -> next level');
  for (const plan of ['tt1', 'mountains', 'smallcity', 'classroom', 'office', 'bedroom', 'tt2', 'tt3']) {
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

async function lootRun(browser, base) {
  console.log('\n# loot: drops, pickup, attachments, shield, damage numbers, DoT');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  const gs = () => pg.evaluate(() => __TEST__.gearState());
  // robots cannot hurt the player in this run (G.hurt is parked); the test hurts through G.realHurt
  await pg.evaluate(() => { const G = IB.Game; G.realHurt = G.hurt; G.hurt = function () { }; G.slot.highest = 4; IB.Weapons.equip(G.ws, 'buzz', true); });
  const hurt = n => pg.evaluate(n => { const G = IB.Game, p = G.player; p.protect = 0; G.realHurt({ x: p.x, z: p.z - 1, type: 'crawler' }, n); }, n);
  await until(pg, () => __TEST__.state().alive > 0, null, 10000);
  // a kill can drop loot (forced to 100 % here): the drop shows in the world and on the radar
  await pg.evaluate(() => { IB.LOOT.dropChance = 1; __TEST__.forceWaves(); });
  await until(pg, () => IB.AI.robots.some(r => r.on && r.state !== 'spawn'), null, 10000);
  await pg.evaluate(() => { const r = IB.AI.robots.find(r => r.on && r.state !== 'spawn'); IB.AI.kill(r, IB.Game.onKill); IB.LOOT.dropChance = 0.05; });
  const d0 = await pg.evaluate(() => ({ n: __TEST__.drops().length, radar: IB.Drops.radar() }));
  check('a kill rolls a loot drop', d0.n >= 1, JSON.stringify(d0));
  check('the drop is on the radar with its rarity colour', d0.radar.length >= 1 && /^#[0-9A-F]{6}$/i.test(d0.radar[0].color), JSON.stringify(d0.radar[0]));
  await pg.evaluate(() => IB.Drops.clear());
  // forced drop -> walk over it -> bag + HUD card; a grip fits the SMG in hand automatically
  await pg.evaluate(() => __TEST__.forceDrop('grip', 'epic', 3));
  await pg.waitForTimeout(800);
  await pg.evaluate(() => { const d = __TEST__.drops()[0]; IB.Game.player.x = d.x; IB.Game.player.z = d.z; });
  check('walking over a drop collects it', await until(pg, () => __TEST__.gearState().inv.length === 1 && __TEST__.drops().length === 0, null, 5000));
  const card = await pg.evaluate(() => { const c = document.getElementById('lootCard'); return c && !c.hidden ? c.textContent : ''; });
  check('loot card shows name, rarity and stats', /ANCHOR GRIP/.test(card) && /Epic/i.test(card) && /Recoil/.test(card), card);
  let s = await gs();
  check('grip fitted: recoil and spread drop', s.attach.buzz && s.attach.buzz.grip && s.weapon.recoil < s.weapon.baseRecoil && s.weapon.spreadHip < 2.2, JSON.stringify(s.weapon));
  check('grip shows on the viewmodel', s.vm.includes('grip'), s.vm.join(','));
  // scope: zoom + aim through it
  await pg.evaluate(() => { const d = __TEST__.forceDrop('scope', 'rare', 0.5); });
  await until(pg, () => __TEST__.gearState().inv.length === 2, null, 5000);
  s = await gs();
  check('scope fitted: more zoom, tighter aim spread', s.weapon.aimZoom < s.weapon.baseAimZoom && s.vm.includes('scope'), JSON.stringify(s.weapon));
  await pg.evaluate(() => { IB.Input.aim = true; });
  const scoped = await until(pg, () => +document.getElementById('scopeView').style.opacity > 0.95 && IB.Game.ws.hidden, null, 5000);
  const eye = await pg.evaluate(() => { const m = IB.Weapons.models.buzz; return m.sightScoped && m.sight.y > m.mesh.getObjectByName('WPN_BUZZ_SIGHT').position.y; });
  check('ADS looks through the scope eye point (scope view on)', scoped && eye);
  await pg.evaluate(() => { IB.Input.aim = false; });
  check('scope view clears when not aiming', await until(pg, () => document.getElementById('scopeView').style.visibility === 'hidden' && !IB.Game.ws.hidden, null, 5000));
  // shield: absorbs before health, then recharges
  await pg.evaluate(() => __TEST__.forceDrop('shield', 'common', 0.5));
  await until(pg, () => __TEST__.gearState().playerShield !== null, null, 5000);
  await pg.evaluate(() => { IB.Game.player.health = IB.Game.player.maxHp; });
  s = await gs();
  const cap = s.playerShield.max;
  check('shield cell auto-equips and starts full; HUD bar shows', s.playerShield.cur === cap && cap >= 15 && await pg.evaluate(() => !document.getElementById('shieldBar').hidden), JSON.stringify(s.playerShield));
  await hurt(10);
  s = await gs();
  check('damage hits the shield first', s.health === 100 && Math.abs(s.playerShield.cur - (cap - 10)) < 0.01, JSON.stringify([s.health, s.playerShield]));
  await hurt(cap);
  s = await gs();
  check('overflow goes through to health', s.playerShield.cur === 0 && Math.abs(s.health - (100 - 10)) < 0.01, JSON.stringify([s.health, s.playerShield]));
  await pg.waitForTimeout(1500);
  check('no recharge inside the delay', (await gs()).playerShield.cur === 0);
  // fast-forward the delay (game time runs slow under software GL)
  await pg.evaluate(() => { const st = IB.Game.player.shield; st.since = st.delay - 0.05; });
  check('shield recharges after its delay', await until(pg, () => __TEST__.gearState().playerShield.cur > 0.5 && IB.Game.player.shield.charging, null, 15000));
  // acid muzzle + real shots: hit numbers, then green acid ticks
  await pg.evaluate(() => __TEST__.forceDrop('acid', 'epic', 0.5));
  await until(pg, () => __TEST__.gearState().weapon.acid > 0, null, 5000);
  check('acid muzzle fitted: acid stat and the silencer on the gun', (await gs()).vm.includes('muzzle'));
  await pg.evaluate(() => { IB.Game.player.protect = 999; });
  const seen = new Set(); const t0 = Date.now();
  while (Date.now() - t0 < 25000 && !(seen.has('acid') && (seen.has('hit') || seen.has('core')))) {
    await pg.evaluate(() => {
      const G = IB.Game, p = G.player; let best = null, bd = 1e9;
      IB.AI.robots.forEach(r => { if (!r.on || r.state === 'spawn' || r.state === 'pose') return; const d = Math.hypot(r.x - p.x, r.z - p.z); if (d < bd) { bd = d; best = r; } });
      if (!best) { __TEST__.forceWaves(); return; }
      best.hp = Math.max(best.hp, 500); best.maxHp = Math.max(best.maxHp, 500);   // keep it alive for the DoT
      best.x = p.x + 0.4; best.z = p.z - 5;
      const ey = p.y + 1.55, dx = best.x - p.x, dz = best.z - p.z, dy = (best.y + 0.45) - ey;
      p.yaw = Math.atan2(-dx, -dz); p.pitch = Math.atan2(dy, Math.hypot(dx, dz));
    });
    // hold the trigger across a few frames (the SMG is automatic)
    await pg.mouse.move(640, 360); await pg.mouse.down();
    for (let k = 0; k < 4; k++) { await pg.waitForTimeout(150); (await gs()).numbers.forEach(n => seen.add(n.kind)); }
    await pg.mouse.up();
  }
  check('bullet hits pop damage numbers', seen.has('hit') || seen.has('core'), [...seen].join(','));
  check('acid ticks pop green numbers', seen.has('acid'), [...seen].join(',') + ' ' + JSON.stringify(await pg.evaluate(() => [IB.Status.active(), IB.Status.list.filter(e => e.on).map(e => [e.kind, e.pool, e.left, e.total]), IB.Weapons.current(IB.Game.ws).def.acid])));
  const shock = await pg.evaluate(() => __TEST__.status('shock', 12, 1.5));
  const shocked = await until(pg, () => __TEST__.gearState().numbers.some(n => n.kind === 'shock'), null, 5000);
  check('IB.Status.apply shock ticks with blue numbers', shock && shocked);
  // gear panel: detach and scrap through the UI
  await pg.evaluate(() => __TEST__.gear());
  const panel = await pg.evaluate(() => [IB.Game.mode, /Gear/i.test(document.getElementById('overlay').textContent), document.querySelectorAll('#gearRoot .gu-item').length]);
  check('gear panel opens (paused, 4 items)', panel[0] === 'paused' && panel[1] && panel[2] === 4, JSON.stringify(panel));
  await pg.click('#gearRoot .gu-fit button[aria-pressed="true"][data-w="buzz"] >> nth=0');
  s = await gs();
  check('detaching in the panel restores the stat', Object.keys(s.attach.buzz || {}).length === 2, JSON.stringify(s.attach));
  const before = (await gs()).inv.length;
  await pg.click('#gearRoot .gu-discard >> nth=-1'); await pg.click('#gearRoot .gu-discard.sure');
  check('scrap needs a confirm tap, then removes the item', (await gs()).inv.length === before - 1);
  await pg.click('#overlay [data-act="resume"]');
  check('back to the fight', await until(pg, () => IB.Game.mode === 'play', null, 3000));
  const saved = await pg.evaluate(() => JSON.parse(localStorage.getItem('inkbolt.slot' + IB.Game.slot.id)).gear);
  check('gear is saved in the slot', saved && saved.inv.length === before - 1 && saved.shield, JSON.stringify(saved && { n: saved.inv.length, shield: saved.shield }));
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

(async () => {
  const server = await serve();
  const base = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET);
  console.log('target', base);
  const browser = await chromium.launch({ args: ARGS });
  try {
    // ONLY=lootRun,tabMenuRun runs a subset
    const runs = { hookRun, deathRun, inputRun, touchRun, tabMenuRun, slideRun, lootRun, campaignRun };
    for (const [name, fn] of Object.entries(runs)) if (!process.env.ONLY || process.env.ONLY.split(',').includes(name)) await fn(browser, base);
  } catch (e) { console.log('FAIL exception ' + e.stack); failures++; }
  await browser.close(); server.close();
  console.log('\n' + (failures ? failures + ' FAILED' : 'ALL PASSED'));
  process.exit(failures ? 1 : 0);
})();
