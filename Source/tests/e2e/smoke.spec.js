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
  console.log('\n# field kit (Tab): pause, inventory, spend a skill point, character, change the loadout, respec, resume');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  await until(pg, () => IB.Game.run.started, null, 5000);
  // progress as if levels 1-3 were cleared (6 skill points) and a rifle was picked up earlier
  await pg.evaluate(() => { const G = IB.Game; G.slot.highest = 3; G.slot.gems = 100; G.slot.arsenal.push('rivet'); G.slot.owned = G.slot.arsenal.slice(); G.applyProgress(); });
  const p0 = await pg.evaluate(() => __TEST__.progress());
  check('progress derived from the save', p0.level === 4 && p0.points === 6 && p0.loadoutMax === 2, JSON.stringify(p0));
  check('HUD shows the level tag', await pg.evaluate(() => /LV\s*4/.test(document.getElementById('lvTag').textContent) && !document.getElementById('lvPts').hidden));
  await pg.mouse.move(640, 360);
  await pg.keyboard.press('Tab');
  check('Tab opens the field kit and pauses', await until(pg, () => IB.Game.mode === 'menu' && !document.getElementById('tabmenu').hidden, null, 8000));
  check('focus stays inside the menu (Tab did not move browser focus)', await pg.evaluate(() => document.getElementById('tabmenu').contains(document.activeElement)));
  const t0 = await pg.evaluate(() => IB.Game.run.time); await pg.waitForTimeout(500);
  check('game time is frozen while open', (await pg.evaluate(() => IB.Game.run.time)) === t0);
  check('HUD hidden behind the menu', await pg.evaluate(() => document.getElementById('hud').hidden));
  check('it opens on the Inventory tab (equipped column, backpack, item card)', await pg.evaluate(() => IB.TabMenu.tab === 'inventory' && !!document.querySelector('#tmGear .inv-eq') && !!document.querySelector('#tmGear .inv-bp') && !!document.querySelector('#tmGear .inv-card')));
  // skills: E from Inventory -> Skills (keyboard), then mouse
  await pg.keyboard.press('KeyE');
  check('E switches to Skills', await pg.evaluate(() => IB.TabMenu.tab === 'skills' && !!document.querySelector('.sk-tree')));
  await pg.click('[data-skill="overload"]');
  await pg.click('[data-act="buy"]');
  let pr = await pg.evaluate(() => __TEST__.progress());
  check('Spend buys Overload rank 1', pr.skills.overload === 1 && pr.points === 5, JSON.stringify(pr.skills) + ' points=' + pr.points);
  await pg.focus('[data-skill="overload"]'); await pg.keyboard.press('Enter');
  pr = await pg.evaluate(() => __TEST__.progress());
  check('Enter on the selected skill spends again', pr.skills.overload === 2 && pr.points === 4, JSON.stringify(pr.skills));
  check('locked tier refuses (Hazard needs 5 points below)', await pg.evaluate(() => { document.querySelector('[data-skill="hazard"]').click(); return document.querySelector('[data-act="buy"]').disabled; }));
  const saved1 = await pg.evaluate(() => JSON.parse(localStorage.getItem('inkbolt.slot1')).skills);
  check('skills saved at once', saved1 && saved1.overload === 2, JSON.stringify(saved1));
  await pg.keyboard.press('KeyE');
  check('E again switches to Character (level, stats, record)', await pg.evaluate(() => IB.TabMenu.tab === 'character' && /Max health/.test(document.getElementById('tmPanel').textContent)));
  // inventory: slot 2, then the rifle from the backpack
  await pg.keyboard.press('KeyQ'); await pg.keyboard.press('KeyQ');
  check('Q twice goes back to Inventory', await pg.evaluate(() => IB.TabMenu.tab === 'inventory'));
  check('backpack lists the gun not carried, 2 weapon slots + a locked third', await pg.evaluate(() => document.querySelectorAll('.lo-card').length === 1 && document.querySelectorAll('.lo-slot').length === 3 && !!document.querySelector('.lo-slot.locked')));
  await pg.hover('[data-gun="rivet"]');
  check('pointing at a backpack gun shows its card, compared with the selected slot', await pg.evaluate(() => /AR-22 Rivet/i.test(document.querySelector('.inv-card').textContent) && !!document.querySelector('.inv-card .ic-vs')));
  await pg.click('[data-slot="1"]'); await pg.click('[data-gun="rivet"]');
  pr = await pg.evaluate(() => __TEST__.progress());
  check('rifle goes into slot 2', JSON.stringify(pr.loadout) === '["pip","rivet"]', JSON.stringify(pr.loadout));
  await pg.keyboard.press('Tab');
  check('Tab closes and resumes', await until(pg, () => IB.Game.mode === 'play' && document.getElementById('tabmenu').hidden && !document.getElementById('hud').hidden, null, 3000));
  pr = await pg.evaluate(() => __TEST__.progress());
  check('carried guns follow the loadout', JSON.stringify(pr.carried) === '["pip","rivet"]', JSON.stringify(pr.carried));
  check('Overload applies (+20% magazine: Warden 12 -> 15)', await pg.evaluate(() => IB.Weapons.magSize(IB.Game.ws, IB.WEAPONS.pip) === 15));
  await pg.keyboard.press('Digit2');
  // holster + draw of a gun first drawn now (shader compile under software GL): wait for it rather than a fixed 0.7 s
  check('key 2 draws the rifle from slot 2', await until(pg, () => __TEST__.state().weapon === 'rivet' && IB.Game.ws.state === 'idle', null, 8000), (await st(pg)).weapon);
  await pg.keyboard.press('Digit3'); await pg.waitForTimeout(300);
  check('key 3 does nothing with 2 guns', (await st(pg)).weapon === 'rivet');
  // respec costs gems and refunds everything
  await pg.evaluate(() => __TEST__.tabMenu('skills'));
  // (select a short card first: at 1280x720 a long locked card, e.g. Hazard, pushes the respec panel under the footer;
  // the field kit layout is being redone separately)
  await pg.click('[data-skill="overload"]');
  await pg.click('[data-act="respec"]'); await pg.click('[data-act="respec"]');
  pr = await pg.evaluate(() => __TEST__.progress());
  const gems = await pg.evaluate(() => IB.Game.slot.gems);
  check('respec resets the tree for ' + 40 + ' gems', Object.keys(pr.skills).length === 0 && pr.points === 6 && gems === 60, JSON.stringify(pr.skills) + ' gems=' + gems);
  await pg.keyboard.press('Escape');
  check('Esc closes it too', await until(pg, () => IB.Game.mode === 'play', null, 3000));
  check('respec applied (magazine back to 12)', await pg.evaluate(() => IB.Weapons.magSize(IB.Game.ws, IB.WEAPONS.pip) === 12));
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function skillsRun(browser, base) {
  console.log('\n# skills: stat skills, Undercover (F) vs the AI, V shove, Stream, Ricochet, Hazard, Hydrate, Handy Helpers');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  await until(pg, () => IB.Game.run.started, null, 5000);
  // a made-up tree straight into the save (the test hook skips gates, the budget and pick-one)
  await pg.evaluate(() => __TEST__.setSkills({ undercover: 1, stream: 3, ricochet: 3, hazard: 3, hydrate: 3, healthy: 3, stamina: 1, fastfingers: 3, tank: 3, electrify: 1, handyhelpers: 1, chainreaction: 1 }));
  let ss = await pg.evaluate(() => __TEST__.skillState());
  check('stat skills apply (Healthy 124 max health, Stamina x1.3 sprint + x1.15 move / 10 s, Fast Fingers 1/1.3 reload + swap)',
    ss.maxHp === 124 && ss.sprintMul === 1.3 && Math.abs(ss.staminaMax - 10) < 1e-6 && Math.abs(ss.swapMul - 1 / 1.3) < 1e-6 && Math.abs(ss.reloadMul - 1 / 1.3) < 1e-6, JSON.stringify(ss));
  // Stamina: x1.5 sprint straight at the far wall for a while: fast, and never inside or through a wall
  await pg.evaluate(() => { IB.Game.player.protect = 999; __TEST__.look(0, 0); });
  await pg.mouse.move(640, 360);
  await pg.keyboard.down('ShiftLeft'); await pg.keyboard.down('KeyW');
  // (sampled over ~2 s of game time: on a loaded machine software GL can run far below real time)
  let vmax = 0, inside = 0;
  const gt0 = await pg.evaluate(() => IB.Game.run.time), rt0 = Date.now();
  while (Date.now() - rt0 < 60000 && (await pg.evaluate(() => IB.Game.run.time)) - gt0 < 2) {
    await pg.waitForTimeout(200);
    const m = await pg.evaluate(() => {
      const p = IB.Game.player, w = IB.Game.level.world, out = [];
      w.query(p.x - 0.3, p.z - 0.3, p.x + 0.3, p.z + 0.3, out);
      const hit = out.some((b) => b.y1 > p.y + 0.4 && b.y0 < p.y + 1.6 && p.x > b.x0 + 0.05 && p.x < b.x1 - 0.05 && p.z > b.z0 + 0.05 && p.z < b.z1 - 0.05);
      return [Math.hypot(p.vx, p.vz), hit];
    });
    vmax = Math.max(vmax, m[0]); if (m[1]) inside++;
  }
  await pg.keyboard.up('KeyW'); await pg.keyboard.up('ShiftLeft');
  check('Stamina: sprint reaches ~13 m/s, the player never ends up inside a wall', vmax > 11.5 && inside === 0, 'vmax=' + vmax.toFixed(1) + ' inside=' + inside);
  // Undercover: robots must have noticed the player first
  await pg.evaluate(() => { IB.Game.player.protect = 999; __TEST__.teleport(0); });
  await until(pg, () => __TEST__.state().alive > 0, null, 10000);
  check('robots see the player before the cloak', await until(pg, () => __TEST__.skillState().seeing > 0, null, 20000));
  await pg.mouse.move(640, 360);
  await pg.keyboard.press('KeyF');
  check('F turns Undercover on', await until(pg, () => __TEST__.skillState().cloak.active, null, 3000));
  ss = await pg.evaluate(() => __TEST__.skillState());
  check('cloak: 5 s, then a 30 s cooldown; the AI is told', ss.cloaked && ss.cloak.t <= 5 && ss.cloak.t > 3 && ss.cloak.cd === 30, JSON.stringify(ss.cloak));
  check('after a quick flicker the world sinks into the ink-black stealth look (robots glow a bright stealth blue)', await until(pg, () => document.body.classList.contains('cloak-on') &&
    IB.Render.cloak.value > 0.9 && IB.Render.robotHull.value > 2 && +getComputedStyle(document.getElementById('cloakFx')).opacity > 0.9 &&
    IB.Render.robotOutline.uInk.value.b > 0.5, null, 5000));
  check('HUD cooldown badge shows the cloak', await pg.evaluate(() => !document.getElementById('cloakHud').hidden && /HIDDEN/.test(document.getElementById('cloakHud').textContent)));
  let worst = 0;
  for (let i = 0; i < 8; i++) { await pg.waitForTimeout(150); const s = await pg.evaluate(() => __TEST__.skillState()); if (!s.cloak.active) break; worst = Math.max(worst, s.seeing + s.attacking); }
  check('robots lose the player: nobody sees him or winds up an attack', worst === 0, 'seeing+attacking=' + worst);
  await pg.evaluate(() => { IB.SkillFX.cloakT = Math.min(IB.SkillFX.cloakT, 0.3); });   // skip to the end of the 5 s (slow software GL)
  check('the cloak wears off', await until(pg, () => !__TEST__.skillState().cloak.active && !__TEST__.skillState().cloaked, null, 40000));
  check('screen back in colour, cooldown counting', await pg.evaluate(() => !document.body.classList.contains('cloak-on') && __TEST__.skillState().cloak.cd > 0 && /\d+s/.test(document.getElementById('cloakHud').textContent)));
  await pg.keyboard.press('KeyF'); await pg.waitForTimeout(300);
  check('F during the cooldown does nothing', !(await pg.evaluate(() => __TEST__.skillState().cloak.active)));
  await pg.keyboard.press('KeyV');
  check('V shoves (moved off F)', await until(pg, () => __TEST__.skillState().shoveT > 0, null, 5000));
  // Stream / Ricochet / Hazard / Hydrate: two Gunners lined up in front of the zone entry, one bullet
  const only = (k) => pg.evaluate((k) => { ['stream', 'ricochet', 'hazard', 'hydrate', 'chain', 'rogue'].forEach((id) => __TEST__.forceSkill(id, id === k ? 1 : 0)); }, k);
  const lineShot = (gap, side) => pg.evaluate(([gap, side]) => {
    const G = IB.Game, z = G.level.zones[G.zone], x = z.entry.x, zz = z.entry.z;
    __TEST__.killZone();
    const a = __TEST__.spawnRobot('gunner', x, zz - 4), b = __TEST__.spawnRobot('gunner', x + side, zz - 4 - gap);
    const ra = IB.AI.types.gunner.slots[a], rb = IB.AI.types.gunner.slots[b], ha = ra.hp, hb = rb.hp;
    __TEST__.fireRay(x, 0.55, zz - 1, 0, 0, -1);
    return { a, b, da: ha - ra.hp, db: hb - rb.hp, wet: ra.wet, pools: IB.SkillFX.activePools(), coats: IB.SkillFX.activeCoats() };
  }, [gap, side]);
  await only('stream');
  let r = await lineShot(2, 0);
  check('Stream: the bullet punches through into the robot behind for x2', r.da > 0 && Math.abs(r.db - 2 * r.da) < 0.01, JSON.stringify(r));
  await only('ricochet');
  r = await lineShot(0.5, 3);
  check('Ricochet: bounces into a robot 3 m away for 60%', r.da > 0 && Math.abs(r.db - 0.6 * r.da) < 0.01, JSON.stringify(r));
  await only('hazard');
  r = await lineShot(0.5, 6);
  check('Hazard: a hit leaves an acid pool', r.pools >= 1, JSON.stringify(r));
  check('a robot in the pool burns with acid', await until(pg, (slot) => IB.Status.has(IB.AI.types.gunner.slots[slot], 'acid'), r.a, 8000));
  await only('hydrate');
  r = await lineShot(1.5, 0.5);
  check('Hydrate: the robot is coated (wet)', r.coats >= 1 && r.wet > 5, JSON.stringify(r));
  check('the robot next to the coated one takes shock', await until(pg, (slot) => IB.Status.has(IB.AI.types.gunner.slots[slot], 'shock'), r.b, 8000));
  check('the coated robot shows the wet tint', await until(pg, (slot) => IB.AI.types.gunner.parts.Body.fx.getZ(slot) === 2, r.a, 5000));
  // Chain Reaction: a hit on a robot with two others within 4 m blows the group up for 40% of each one's max health
  await only('chain');
  const ch = await pg.evaluate(() => {
    const G = IB.Game, z = G.level.zones[G.zone], x = z.entry.x, zz = z.entry.z;
    __TEST__.killZone();
    const sl = [[x, zz - 4], [x + 1.6, zz - 4.6], [x - 1.6, zz - 4.6]].map((q) => __TEST__.spawnRobot('gunner', q[0], q[1]));
    const rs = sl.map((k) => IB.AI.types.gunner.slots[k]), hp0 = rs.map((r) => r.hp);
    __TEST__.fireRay(x, 0.55, zz - 1, 0, 0, -1);
    return { lost: rs.map((r, i) => +(hp0[i] - r.hp).toFixed(2)), max: rs[0].maxHp, on: rs.map((r) => r.on), chains: IB.SkillFX.stats.chains };
  });
  check('Chain Reaction: the group blows up for 40% of max health each, nobody wiped at once', ch.chains === 1 && ch.on.every(Boolean) &&
    Math.abs(ch.lost[1] - 0.4 * ch.max) < 0.01 && Math.abs(ch.lost[2] - 0.4 * ch.max) < 0.01 && ch.lost[0] > 0.4 * ch.max, JSON.stringify(ch));
  // Handy Helpers: a wreck turns rogue (forced chance), still counts as a kill, fights for the player
  await only('rogue');
  const h = await pg.evaluate(() => {
    const G = IB.Game, z = G.level.zones[G.zone], k0 = G.run.kills, alive0 = IB.AI.alive(G.zone);
    const slot = __TEST__.spawnRobot('gunner', z.entry.x + 4, z.entry.z - 6);
    const alive1 = IB.AI.alive(G.zone);
    const killed = __TEST__.wreck('gunner', slot);
    return { slot, killed, kills: G.run.kills - k0, alive0, alive1, alive2: IB.AI.alive(G.zone), r: __TEST__.robot('gunner', slot) };
  });
  check('Handy Helpers: the wreck turns rogue instead (counts as a kill, not as a robot left)', h.killed && h.kills === 1 && h.r.on && h.r.rogue > 14 && h.alive2 === h.alive1 - 1, JSON.stringify(h));
  check('rogue gets the teal tint', await until(pg, (slot) => IB.AI.types.gunner.parts.Body.fx.getZ(slot) === 1, h.slot, 3000));
  check('player bullets pass through the rogue', await pg.evaluate((slot) => { const r = IB.AI.types.gunner.slots[slot]; return !IB.AI.raycast(r.x, 0.55, r.z + 3, 0, 0, -1, 6); }, h.slot));
  const c = await pg.evaluate((slot) => { const r = IB.AI.types.gunner.slots[slot]; return __TEST__.spawnRobot('crawler', r.x + 1.5, r.z); }, h.slot);
  check('robots go for the rogue', await until(pg, (c) => __TEST__.robot('crawler', c).tgtRogue || !__TEST__.robot('crawler', c).on, c, 8000));
  // clear the zone, then let the rogue self-destruct next to the (unprotected) player: no damage to him
  await pg.evaluate(() => __TEST__.killZone());
  await until(pg, () => __TEST__.state().zones[0] === 'cleared', null, 8000);
  const hp0 = await pg.evaluate((slot) => { const p = IB.Game.player, r = IB.AI.types.gunner.slots[slot]; p.protect = 0; if (r.on) { r.x = p.x + 1.2; r.z = p.z; } __TEST__.setRogueTime(0.2); return p.health; }, h.slot);
  check('after 15 s (shortened) the rogue self-destructs', await until(pg, (slot) => !__TEST__.robot('gunner', slot).on, h.slot, 8000));
  await pg.waitForTimeout(400);
  const hp1 = await pg.evaluate(() => IB.Game.player.health);
  check('its blast is harmless to the player', hp1 >= hp0, hp0 + ' -> ' + hp1);
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

// melee (V), frag cans (G), the new guns: unlock stands, hits, combo, grenade blast, per-shell reload, piercing rounds
async function meleeRun(browser, base) {
  console.log('\n# melee (V), frag cans (G), shell reload, piercing rounds');
  let pg = await newPage(browser, base + '?autotest=1&plan=classroom');   // campaign level 3: the dagger waits on a stand
  await pg.evaluate(() => { const G = IB.Game; G.slot.highest = 2; G.slot.melee = []; G.slot.frag = false; G.startLevel(); });
  await until(pg, () => IB.Game.run.started, null, 10000);
  const stands = await pg.evaluate(() => IB.Game.weaponStands.map((w) => w.id));
  check('level 3 start: the dagger stands with the guns', stands.includes('dagger') && !stands.includes('katana'), stands.join(','));
  await pg.evaluate(() => { const G = IB.Game, w = G.weaponStands.find((x) => x.id === 'dagger'); G.player.x = w.x; G.player.z = w.z; });
  check('walking over it puts the dagger on V', await until(pg, () => IB.Game.meleeId() === 'dagger', null, 10000));
  check('no frag cans before level 4', await pg.evaluate(() => IB.Game.slot.frag !== true && IB.Game.grenades === 0));
  await pg.context().close();

  // level 5 for a save that cleared 1-5 (a small window: software GL renders the big bedroom slowly, game time crawls)
  pg = await newPage(browser, base + '?autotest=1&plan=bedroom', { viewport: { width: 640, height: 360 } });
  await pg.evaluate(() => __TEST__.setTier('potato'));
  await pg.evaluate(() => { const G = IB.Game; G.slot.highest = 5; G.startLevel(); G.player.protect = 1e9; });
  await until(pg, () => IB.Game.run.started, null, 10000);
  const kit = await pg.evaluate(() => ({ melee: IB.Game.slot.melee.slice().sort(), frag: IB.Game.slot.frag, cans: IB.Game.grenades,
    kitShown: !document.getElementById('kit').hidden }));
  check('by level 5: all four melee weapons, frag cans x3, equipment row shown',
    kit.melee.join() === 'dagger,eaxe,katana,nunchucks' && kit.frag === true && kit.cans === 3 && kit.kitShown, JSON.stringify(kit));
  // a robot right in front: each melee weapon lands a blow
  for (const id of ['katana', 'eaxe', 'dagger', 'nunchucks']) {
    const slot = await pg.evaluate(() => { const p = IB.Game.player; return __TEST__.spawnRobot('gunner', p.x, p.z - 1.7); });
    await until(pg, (s) => __TEST__.robot('gunner', s).state !== 'spawn', slot, 10000);
    const hp0 = await pg.evaluate((a) => { const r = IB.AI.types.gunner.slots[a[0]], p = IB.Game.player; r.x = p.x; r.z = p.z - 1.7; p.yaw = 0; p.pitch = 0; IB.Game.slot.meleeSel = a[1]; IB.Game.ws.comboT = 9; return r.hp; }, [slot, id]);
    await until(pg, () => !IB.Game.ws.melee && !IB.Game.ws.throwing, null, 10000);
    await pg.keyboard.press('KeyV');
    const hit = await until(pg, (a) => { const r = IB.AI.types.gunner.slots[a[0]]; const p = IB.Game.player; if (r.on) { r.x = p.x; r.z = p.z - 1.7; } return !r.on || r.hp < a[1]; }, [slot, hp0], 15000);
    check(id + ' strikes on V (the gun comes back after the swing)', hit && await until(pg, () => !IB.Game.ws.melee && IB.Game.ws.cur, null, 15000));
    await pg.evaluate((s) => { const r = IB.AI.types.gunner.slots[s]; if (r.on) IB.AI.kill(r); }, slot);
  }
  // katana combo: three quick swings play Strike, Strike2, Strike3
  await pg.evaluate(() => { IB.Game.slot.meleeSel = 'katana'; IB.Game.ws.comboT = 9; });
  const combo = [];
  for (let i = 0; i < 3; i++) {
    await until(pg, () => !IB.Game.ws.melee, null, 15000);
    await pg.evaluate(() => { IB.Game.ws.comboT = 0.1; });
    await pg.keyboard.press('KeyV');
    await until(pg, () => !!IB.Game.ws.melee, null, 10000);
    combo.push(await pg.evaluate(() => IB.Game.ws.melee.combo));
  }
  check('katana: three swings in a row run the 3-cut combo', combo.join() === '0,1,2' || combo.join() === '1,2,0', combo.join());
  await until(pg, () => !IB.Game.ws.melee, null, 15000);
  // frag can: thrown along the view, bounces, goes off, robots in reach take the blast
  const grp = await pg.evaluate(() => { const p = IB.Game.player; p.yaw = 0; p.pitch = 0.1; const o = []; for (let i = 0; i < 3; i++) o.push(__TEST__.spawnRobot('crawler', p.x - 1 + i, p.z - 11)); return o; });
  await until(pg, (ids) => ids.every((s) => __TEST__.robot('crawler', s).state !== 'spawn'), grp, 10000);
  await pg.evaluate((ids) => { const p = IB.Game.player; ids.forEach((s, i) => { const r = IB.AI.types.crawler.slots[s]; r.x = p.x - 1 + i; r.z = p.z - 11; r.frozenTest = true; }); IB.AI.update0 = IB.AI.update0 || IB.AI.update; IB.AI.update = function () {}; }, grp);
  await pg.keyboard.press('KeyG');
  check('G throws a frag can', await until(pg, () => IB.Throwables.live() === 1 && IB.Game.grenades === 2, null, 15000));
  const fused = await until(pg, () => IB.Throwables.live() === 0, null, 90000);
  const dbg = async () => pg.evaluate(() => JSON.stringify({ cans: IB.Throwables.list.filter((g) => g.on).map((g) => [g.t, g.rest]), time: IB.Game.run.time, hs: IB.Game.hitstop, errs: IB.Game.errors, dead: IB.Game.dead, cpl: IB.Game.complete }));
  const d1 = fused ? '' : await dbg(); if (!fused) await pg.waitForTimeout(2000);
  check('it goes off on its fuse', fused, fused ? '' : d1 + ' / ' + await dbg());
  await pg.waitForTimeout(400);
  const hurt = await pg.evaluate((ids) => ids.filter((s) => { const r = __TEST__.robot('crawler', s); return !r.on || r.hp < r.maxHp; }).length, grp);
  await pg.evaluate(() => { IB.AI.update = IB.AI.update0; });
  check('robots in its reach take the blast', hurt >= 2, hurt + ' of 3');
  // ammo box gives a can back (up to 3)
  await pg.evaluate(() => { const G = IB.Game, p = G.player; if (!G.spawnPickup('ammo', p.x, p.z)) { const k = G.pickups.find((q) => q.on && q.kind === 'ammo'); p.x = k.x; p.z = k.z; } });
  const back = await until(pg, () => IB.Game.grenades === 3, null, 20000);
  check('an ammo box gives a frag can back', back, back ? '' : await pg.evaluate(() => JSON.stringify({ g: IB.Game.grenades, p: [IB.Game.player.x, IB.Game.player.y, IB.Game.player.z], pk: IB.Game.pickups.filter((k) => k.on).map((k) => [k.kind, k.x, k.z]) })));
  // pump shotgun: one shell per reload cycle
  await pg.evaluate(() => { const G = IB.Game, W = IB.Weapons; W.give(G.ws, 'scrapper'); W.equip(G.ws, 'scrapper', true); G.ws.guns.scrapper.mag = 1; W.reload(G.ws); });
  check('Scrapper loads shell by shell up to 6', await until(pg, () => IB.Game.ws.guns.scrapper.mag === 6 && IB.Game.ws.state === 'idle', null, 30000));
  // Railspike: one round through two robots in a line
  const line = await pg.evaluate(() => { const p = IB.Game.player; return [__TEST__.spawnRobot('gunner', p.x, p.z - 6), __TEST__.spawnRobot('gunner', p.x, p.z - 9)]; });
  await until(pg, (ids) => ids.every((s) => __TEST__.robot('gunner', s).state !== 'spawn'), line, 10000);
  const pierced = await pg.evaluate((ids) => {
    const G = IB.Game, W = IB.Weapons, p = G.player; W.give(G.ws, 'railspike'); W.equip(G.ws, 'railspike', true);
    IB.AI.update = function () {};
    ids.forEach((s, i) => { const r = IB.AI.types.gunner.slots[s]; r.x = p.x; r.z = p.z - 6 - i * 3; });
    __TEST__.fireRay(p.x, 1.0, p.z, 0, 0, -1);
    IB.AI.update = IB.AI.update0;
    return ids.map((s) => { const r = __TEST__.robot('gunner', s); return !r.on || r.hp < r.maxHp; });
  }, line);
  check('Railspike pierces: both robots in the line are hit', pierced[0] && pierced[1], JSON.stringify(pierced));
  check('no console errors (melee run)', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

// tiered weapon drops, melee drops, melee stamina, Void can pull, Undercover blue robot outline
async function round4Run(browser, base) {
  console.log('\n# weapon drops, melee stamina, muzzle cans, Undercover look');
  const pg = await newPage(browser, base + '?autotest=1&plan=bedroom', { viewport: { width: 640, height: 360 } });
  await pg.evaluate(() => { __TEST__.setTier('potato'); const G = IB.Game; G.slot.highest = 5; G.slot.melee = ['dagger']; G.slot.meleeSel = 'dagger'; G.startLevel(); G.player.protect = 1e9; });
  await until(pg, () => IB.Game.run.started, null, 15000);
  // a purple Vanguard lands in front: walking over it adds it to the arsenal at that tier
  await pg.evaluate(() => { IB.WeaponDrops.testDrop('vanguard', 'purple'); const d = IB.WeaponDrops.live()[0], p = IB.Game.player; setTimeout(() => { p.x = d.x; p.z = d.z; }, 900); });
  check('a dropped gun joins the arsenal at its tier', await until(pg, () => IB.Game.slot.arsenal.includes('vanguard') && IB.Game.slot.gunTier.vanguard === 'purple', null, 30000));
  check('its tier raises its damage (purple x1.22)', await pg.evaluate(() => Math.abs(IB.WeaponDrops.dmgMul('vanguard') - 1.22) < 1e-9));
  await pg.evaluate(() => { IB.Game.slot.melee = ['dagger']; IB.Game.slot.meleeSel = 'dagger'; IB.WeaponDrops.testDrop('katana', null, true); const d = IB.WeaponDrops.live()[0], p = IB.Game.player; setTimeout(() => { p.x = d.x; p.z = d.z; }, 900); });
  const kat = await until(pg, () => IB.Game.slot.melee.includes('katana') && IB.Game.meleeId() === 'katana', null, 30000);
  check('a dropped katana goes on V', kat, kat ? '' : await pg.evaluate(() => JSON.stringify({ live: IB.WeaponDrops.live(), p: [IB.Game.player.x, IB.Game.player.y, IB.Game.player.z], m: IB.Game.slot.melee, sel: IB.Game.slot.meleeSel })));
  // melee costs stamina (katana: 20% of the pool), and ends a sprint
  const st = await pg.evaluate(() => { const p = IB.Game.player; p.stamina = p.staminaMax; const a = p.stamina; IB.Game.meleeSwing('katana'); return [a, p.stamina, p.staminaMax]; });
  check('a katana swing spends 20% of the stamina pool', Math.abs((st[0] - st[1]) - 0.2 * st[2]) < 1e-6, JSON.stringify(st));
  await until(pg, () => !IB.Game.ws.melee, null, 20000);
  const winded = await pg.evaluate(() => { const p = IB.Game.player; p.stamina = 0; IB.Game.meleeSwing('katana'); return [IB.Game.meleeWinded, IB.Game.ws.fx.meleeRate]; });
  check('out of stamina: winded swings are slower', winded[0] === true && winded[1] < 1, JSON.stringify(winded));
  await until(pg, () => !IB.Game.ws.melee, null, 20000);
  // Void can: a hit pulls the robots around the target in
  const ids = await pg.evaluate(() => { const p = IB.Game.player; return [__TEST__.spawnRobot('crawler', p.x, p.z - 8), __TEST__.spawnRobot('crawler', p.x + 4, p.z - 8)]; });
  await until(pg, (a) => a.every((s) => __TEST__.robot('crawler', s).state !== 'spawn'), ids, 20000);
  const pull = await pg.evaluate((a) => {
    IB.AI.update0 = IB.AI.update; IB.AI.update = function () {};
    const A = IB.AI.types.crawler.slots[a[0]], B = IB.AI.types.crawler.slots[a[1]], p = IB.Game.player;
    A.x = p.x; A.z = p.z - 8; B.x = p.x + 4; B.z = p.z - 8;
    const d0 = Math.hypot(B.x - A.x, B.z - A.z);
    IB.Gear.onHit(A, { damage: 5 }, 'body', { can: { type: 'void', stats: { chance: 1, radius: 8 } } }, false);
    return [d0, IB.Gear.voidCount()];
  }, ids);
  await pg.waitForTimeout(2500);
  const d1 = await pg.evaluate((a) => { const A = IB.AI.types.crawler.slots[a[0]], B = IB.AI.types.crawler.slots[a[1]]; IB.AI.update = IB.AI.update0; return Math.hypot(B.x - A.x, B.z - A.z); }, ids);
  check('a Void can hit opens a singularity that pulls robots in', pull[1] === 1 && d1 < pull[0] - 0.5, 'd ' + pull[0].toFixed(2) + ' -> ' + d1.toFixed(2));
  // Undercover: robots get a dark-blue outline while hidden (after the flicker in)
  await pg.evaluate(() => { __TEST__.setSkills({ undercover: 1 }); IB.SkillFX.tryCloak(IB.Game.player); });
  check('Undercover tints the robot outlines blue', await until(pg, () => { const c = IB.Render.robotOutline.uInk.value; return c.b > 0.5 && c.r < 0.3; }, null, 20000));
  check('no console errors (round 4)', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

/* armory mounts (themes with `mounts`, e.g. Strike Team HQ): every rack gun clear of the rack and level geometry, of
   the other guns and of the tier plates, its back on or in front of the mount plane and its front reachable by rays
   from the room (never behind a board); bench / shelf gear resting on the surface under it and clear of it. Bounding
   boxes use the visible surface (outline-shell vertices left out). Runs in the page. */
function armoryCheck() {
  const T = THREE, G = IB.Game, gun = [], item = [], m4 = new T.Matrix4(), v = new T.Vector3();
  function worldBox(im, idx) {
    im.getMatrixAt(idx, m4);
    const p = im.geometry.attributes.position, hl = im.geometry.attributes.aHull, b = new T.Box3();
    for (let i = 0; i < p.count; i++) {
      if (hl && (hl.getX(i) || hl.getY(i) || hl.getZ(i))) continue;
      b.expandByPoint(v.fromBufferAttribute(p, i).applyMatrix4(m4));
    }
    return b;
  }
  const cache = new Map();
  function tris(zi) {
    if (cache.has(zi)) return cache.get(zi);
    const z = G.level.zones[zi], out = [];
    [z.ground].concat(z.meshes).forEach(m => {
      const g = m.geometry, pos = g.attributes.position.array, hull = g.attributes.aHull ? g.attributes.aHull.array : null, idx = g.index.array;
      for (let t = 0; t < idx.length; t += 3) {
        const a = idx[t], b = idx[t + 1], c = idx[t + 2];
        if (hull && (hull[a * 3] || hull[a * 3 + 1] || hull[a * 3 + 2])) continue;
        out.push([a, b, c].map(i => new T.Vector3(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2])));
      }
    });
    cache.set(zi, out); return out;
  }
  function triBox(t, box) {   // separating-axis test
    const c = box.getCenter(new T.Vector3()), h = box.getSize(new T.Vector3()).multiplyScalar(0.5);
    const p = t.map(q => q.clone().sub(c)), e = [p[1].clone().sub(p[0]), p[2].clone().sub(p[1]), p[0].clone().sub(p[2])];
    const ax = [new T.Vector3(1, 0, 0), new T.Vector3(0, 1, 0), new T.Vector3(0, 0, 1)];
    const sep = a => { if (a.lengthSq() < 1e-12) return false; const d = p.map(q => q.dot(a)), r = h.x * Math.abs(a.x) + h.y * Math.abs(a.y) + h.z * Math.abs(a.z); return Math.min(...d) > r || Math.max(...d) < -r; };
    if (ax.some(sep) || sep(e[0].clone().cross(e[1]))) return false;
    for (const a of ax) for (const ed of e) if (sep(a.clone().cross(ed))) return false;
    return true;
  }
  function hits(zi, box) {
    for (const t of tris(zi)) {
      if (Math.max(t[0].x, t[1].x, t[2].x) < box.min.x || Math.min(t[0].x, t[1].x, t[2].x) > box.max.x) continue;
      if (Math.max(t[0].y, t[1].y, t[2].y) < box.min.y || Math.min(t[0].y, t[1].y, t[2].y) > box.max.y) continue;
      if (Math.max(t[0].z, t[1].z, t[2].z) < box.min.z || Math.min(t[0].z, t[1].z, t[2].z) > box.max.z) continue;
      if (triBox(t, box)) return true;
    }
    return false;
  }
  const rc = new T.Raycaster();
  function ray(zi, from, dir) { const z = G.level.zones[zi]; rc.set(from, dir); rc.far = 5; const h = rc.intersectObjects([z.ground].concat(z.meshes), false); return h.length ? h[0].distance : Infinity; }
  const guns = G.loot.filter(L => L.kind === 'gun'), boxes = guns.map(L => worldBox(L.im, L.idx));
  guns.forEach((L, i) => {
    const b = boxes[i], nm = L.id + '@' + [L.x, L.y, L.z].map(q => q.toFixed(2)).join(',');
    if (hits(L.zone, b.clone().expandByScalar(-0.002))) gun.push(nm + ' cuts into the rack / level');
    const n = new T.Vector3(Math.sin(L.yaw), 0, Math.cos(L.yaw)), side = new T.Vector3(n.z, 0, -n.x);
    const along = q => (q.x - L.x) * n.x + (q.z - L.z) * n.z, back = Math.min(along(b.min), along(b.max)), front = Math.max(along(b.min), along(b.max));
    if (back < -0.002) gun.push(nm + ' reaches ' + (-back).toFixed(3) + ' m behind its mount plane');
    const c = b.getCenter(new T.Vector3()), half = Math.abs(side.x) * (b.max.x - b.min.x) / 2 + Math.abs(side.z) * (b.max.z - b.min.z) / 2;
    [-0.3, 0, 0.3].forEach(k => {
      const from = c.clone().addScaledVector(side, k * half).addScaledVector(n, front - along(c) + 0.8);
      if (ray(L.zone, from, n.clone().negate()) < 0.79) gun.push(nm + ' hidden behind level geometry');
    });
    for (let j = i + 1; j < guns.length; j++) if (b.intersectsBox(boxes[j])) gun.push(nm + ' overlaps ' + guns[j].id);
  });
  G.loot.forEach(L => {
    if (!L.tag) return;
    const tb = worldBox(L.tag, L.tagIdx), nm = (L.id || L.kind) + '@' + [L.x, L.y, L.z].map(q => q.toFixed(2)).join(',');
    boxes.forEach((b, j) => { if (b.intersectsBox(tb)) gun.push('tier plate of ' + nm + ' overlaps ' + guns[j].id); });
    if (hits(L.zone, tb.clone().expandByScalar(-0.002))) (L.kind === 'gun' ? gun : item).push('tier plate of ' + nm + ' cuts into the level');
  });
  G.loot.filter(L => L.kind !== 'gun').forEach(L => {
    const b = worldBox(L.im, L.idx), nm = L.kind + '@' + [L.x, L.y, L.z].map(q => q.toFixed(2)).join(',');
    const sb = b.clone(); sb.min.y += 0.004; sb.expandByScalar(-0.002);
    if (hits(L.zone, sb)) item.push(nm + ' cuts into the level');
    const c = b.getCenter(new T.Vector3()); c.y = b.min.y + 0.02;
    const d = ray(L.zone, c, new T.Vector3(0, -1, 0));
    if (!(d < 0.03)) item.push(nm + ' floats ' + (d - 0.02).toFixed(3) + ' m');
  });
  return { guns: guns.length, items: G.loot.length - guns.length, gun, item };
}

async function campaignRun(browser, base) {
  console.log('\n# campaign: big levels, no z-fighting, waypath -> loading -> next level');
  // PLANS=castle,city2 checks a subset (the full level-1 flow runs only when mountains is in the list);
  // campaign levels whose theme isn't built are skipped
  const plans = process.env.PLANS ? process.env.PLANS.split(',') : ['mountains', 'smallcity', 'classroom', 'office', 'bedroom', 'coalmine', 'castle', 'city2', 'factory', 'livingroom', 'garden', 'factory2', 'island', 'mall', 'police', 'grove', 'foundry'];
  for (const plan of plans) {
    const pg = await newPage(browser, base + '?autotest=1&zcheck=1&plan=' + plan);
    if (!(await pg.evaluate(p => !!IB.LEVEL_PLANS[p], plan))) { console.log('SKIP ' + plan + ' (not built)'); await pg.context().close(); continue; }
    const z = await pg.evaluate(() => IB.Game.level.zfight);
    check(plan + ' has no coplanar overlapping pieces', z.length === 0, z.slice(0, 3).join(' | '));
    const big = await pg.evaluate(() => IB.Game.level.zones.map(z => z.w * z.h));
    check(plan + ' zones are big (>= 2,000 m2 each)', big.every(a => a >= 2000), big.join(','));
    if (await pg.evaluate(() => (IB.Game.loot || []).length)) {
      const ar = await pg.evaluate(armoryCheck);
      check(plan + ' armory: every rack gun clear of its rack, neighbours and tier plate, visible in front of the board', ar.guns > 0 && ar.gun.length === 0, ar.guns + ' guns ' + ar.gun.slice(0, 4).join(' | '));
      check(plan + ' armory: bench / shelf gear rests on its surface, clear of it', ar.items > 0 && ar.item.length === 0, ar.items + ' items ' + ar.item.slice(0, 4).join(' | '));
      // look at a rack gun from 1 m in front of it: the E prompt names it, E takes it into the arsenal
      const tk = await pg.evaluate(() => {
        const G = IB.Game, L = G.loot.find(l => l.kind === 'gun' && l.zone === 0 && !l.taken), p = G.player;
        p.protect = 1e9; p.x = L.x + Math.sin(L.yaw); p.z = L.z + Math.cos(L.yaw); p.vx = p.vz = 0;
        p.yaw = L.yaw; p.pitch = Math.atan2(L.y + 0.05 - (p.y + 1.5), 1);
        const before = (G.slot.arsenal || []).length, gems = G.slot.gems || 0;
        return { id: L.id, near: G.nearestLoot() === L, before, gems, i: G.loot.indexOf(L) };
      });
      check(plan + ' armory: looking at a rack gun within reach selects it', tk.near, tk.id);
      await pg.keyboard.press('KeyE');
      const got = await until(pg, i => IB.Game.loot[i].taken, tk.i, 3000);
      const after = await pg.evaluate(id => ({ has: (IB.Game.slot.arsenal || []).indexOf(id) >= 0, gems: IB.Game.slot.gems || 0, prompt: !document.getElementById('usePrompt').hidden }), tk.id);
      check(plan + ' armory: E takes it (into the arsenal, or as gems / an upgrade)', got && (after.has || after.gems > tk.gems), JSON.stringify(after));
    }
    // moving lines (theme conveyor symbols): the first zone's items travel; a player standing on a belt rides it
    const lineAt = () => pg.evaluate(() => {
      const z = IB.Game.level.zones[0]; if (!z.lines) return null;
      const l = z.lines[0], a = l.items.mesh.instanceMatrix.array, i = l.base * 16; return [a[i + 12], a[i + 14]];
    });
    const l0 = await lineAt();
    if (l0) {
      await pg.waitForTimeout(800);
      const l1 = await lineAt();
      check(plan + ' assembly lines move', Math.hypot(l1[0] - l0[0], l1[1] - l0[1]) > 0.05, JSON.stringify([l0, l1]));
      const ride = await pg.evaluate(() => {
        const z = IB.Game.level.zones[0], l = z.lines.find(l => l.C.carry && l.len >= 3); if (!l) return null;
        const p = IB.Game.player; p.protect = 1e9; p.x = l.cx; p.z = l.cz; p.y = l.C.carry.top; p.vx = p.vz = p.vy = 0; p.onGround = true;
        return { x: p.x, z: p.z, dir: [l.dir * l.c, -l.dir * l.s] };
      });
      if (ride) {
        await pg.waitForTimeout(1500);   // headless frames are slow and dt is clamped per frame
        const p1 = await pg.evaluate(() => ({ x: IB.Game.player.x, z: IB.Game.player.z, y: IB.Game.player.y }));
        const along = (p1.x - ride.x) * ride.dir[0] + (p1.z - ride.z) * ride.dir[1];
        check(plan + ' a belt carries the player standing on it (downstream)', along > 0.02, JSON.stringify({ along, p1 }));
      }
    }
    if (plan !== 'mountains') { await pg.context().close(); continue; }
    const stands = await pg.evaluate(() => (IB.Game.weaponStands || []).map(w => w.id));
    check('new weapon waits at the start of level 1', stands.length >= 1, stands.join(','));
    await pg.evaluate(() => { const w = IB.Game.weaponStands[0]; IB.Game.player.x = w.x; IB.Game.player.z = w.z; });
    check('walking up to it picks it up', await until(pg, () => IB.Game.weaponStands[0].taken, null, 5000), (await st(pg)).weapon);
    const nz = await pg.evaluate(() => IB.Game.level.zones.length);
    for (let zi = 0; zi < nz; zi++) {
      if (zi > 0) { await pg.evaluate(i => __TEST__.teleport(i), zi); await until(pg, i => __TEST__.state().zones[i] === 'active', zi, 8000); }
      const t0 = Date.now();
      while (Date.now() - t0 < 30000) { if ((await st(pg)).zones[zi] === 'cleared') break; await pg.evaluate(() => { __TEST__.forceWaves(); __TEST__.killZone(); }); await pg.waitForTimeout(250); }
      check('level 1 zone ' + (zi + 1) + ' cleared', (await st(pg)).zones[zi] === 'cleared');
    }
    // walk the exit waypath: it dims, then the next level loads and lights up
    await pg.evaluate(() => { const h = IB.Game.level.hatch; IB.Game.player.x = h.x; IB.Game.player.z = h.z0 - (h.z0 - h.z) * 0.5; });
    const dimmed = await until(pg, () => IB.Game.dimV > 0.25 && IB.Game.dimV < 1, null, 4000);
    check('screen dims along the waypath', dimmed, 'dim=' + (await pg.evaluate(() => IB.Game.dimV)));
    await pg.evaluate(() => __TEST__.teleport('hatch'));
    const loaded = await until(pg, () => IB.Game.plan.id === 'smallcity' && IB.Game.mode === 'play', null, 30000);
    check('next level loads after the waypath', loaded, (await pg.evaluate(() => IB.Game.plan.id + ' ' + IB.Game.mode)));
    const lit = await until(pg, () => IB.Game.dimV === 0 || IB.Game.dimV < 0.02, null, 15000);
    check('screen lights up again', lit, 'dim=' + (await pg.evaluate(() => IB.Game.dimV)));
    const saved = await pg.evaluate(() => JSON.parse(localStorage.getItem('inkbolt.slot1') || '{}'));
    check('save moved on to level 2 with the new weapon', saved.plan === 'smallcity' && (saved.owned || []).length >= 2, JSON.stringify({ plan: saved.plan, owned: saved.owned }));
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

async function hudRun(browser, base) {
  console.log('\n# HUD: enemy health bars, damage chip, loader');
  const pg = await newPage(browser, base + '?autotest=1&plan=greybox');
  // one robot 8 m ahead (AI parked so it holds still), at full health and not under the crosshair: no bar
  await pg.evaluate(() => {
    const G = IB.Game, p = G.player, AI = IB.AI; p.protect = 999; AI.update = () => {};
    AI.robots.forEach(r => { if (r.on) { r.on = false; r.state = 'off'; } });
    const r = AI.spawn('crawler', p.x + 3, p.z - 8, G.zone || 0, p.x, p.z); r.state = 'chase'; r.y = 0; window.__hbR = r;
    p.yaw = Math.PI;   // looking away
  });
  await pg.waitForTimeout(600);
  check('robots at full health show no bar', (await pg.evaluate(() => IB.HPBars.stats().shown)) === 0, JSON.stringify(await pg.evaluate(() => IB.HPBars.stats())));
  // hit it: its bar shows, drains, and keeps a chip of the damage for a moment
  await pg.evaluate(() => { const r = window.__hbR; IB.AI.damage(r, r.maxHp * 0.4, {}); });
  check('a hurt robot gets a health bar', await until(pg, () => IB.HPBars.stats().bars.some(b => b.hp < 0.9 && b.a > 0.5), null, 5000), JSON.stringify(await pg.evaluate(() => IB.HPBars.stats())));
  check('the bar drains to the robot\'s health', await until(pg, () => { const r = window.__hbR, b = IB.HPBars.stats().bars[0]; return b && Math.abs(b.hp - r.hp / r.maxHp) < 0.03; }, null, 5000));
  // one draw call for every bar, and it goes when the HUD hides (pause) and comes back
  await pg.evaluate(() => __TEST__.pause());
  check('bars hide while paused', await until(pg, () => IB.HPBars.stats().shown === 0 && !IB.Render.scene.getObjectByName('hpbars').visible, null, 5000));
  await pg.evaluate(() => __TEST__.resume());
  check('bars come back after resume', await until(pg, () => IB.HPBars.stats().shown > 0, null, 5000));
  // a kill: the bar empties and fades out
  await pg.evaluate(() => IB.AI.kill(window.__hbR, IB.Game.onKill));
  check('a killed robot\'s bar fades out', await until(pg, () => !IB.HPBars.stats().bars.length, null, 5000));
  // player health: the damage chip trails the fill, healing snaps it
  await pg.evaluate(() => { const H = IB.HUD; H.health(100, 100); H.health(70, 100); H.realHealth = H.health; H.health = () => {}; });   // the widget itself (game calls parked)
  await pg.waitForTimeout(120);
  const chip = await pg.evaluate(() => ({ fill: parseFloat(document.getElementById('hpFill').style.width), chip: document.getElementById('hpChip').getBoundingClientRect().width / document.querySelector('.hp-bar').getBoundingClientRect().width * 100 }));
  check('HUD health keeps a damage chip behind the fill for a moment', chip.chip > chip.fill + 5, JSON.stringify(chip));
  // loader: black screen with the 3D gear canvas; hides on cue
  const ld = await pg.evaluate(() => { IB.Menus.loading({ level: 2, name: 'Backyard' }); IB.Menus.loadingProgress(0.5); const el = document.getElementById('loading'); return { vis: IB.Menus.isLoading(), cv: !!el.querySelector('canvas.ldr-cv'), bg: getComputedStyle(el).backgroundColor, text: el.textContent }; });
  check('loader shows a black screen with the gear canvas and the level name', ld.vis && ld.cv && ld.bg === 'rgb(0, 0, 0)' && /Backyard/i.test(ld.text), JSON.stringify(ld));
  await pg.evaluate(() => new Promise(done => IB.Menus.loadingHide(done, 100)));
  check('loader hides', await pg.evaluate(() => !IB.Menus.isLoading() && document.getElementById('loading').hidden));
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
  await until(pg, () => IB.AI.robots.some(r => r.on && r.state !== 'spawn'), null, 30000);
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
  await until(pg, () => { const d = __TEST__.drops()[0]; if (d) { IB.Game.player.x = d.x; IB.Game.player.z = d.z; } return __TEST__.gearState().inv.length === 2; }, null, 15000);
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
  await until(pg, () => { const d = __TEST__.drops()[0]; if (d) { IB.Game.player.x = d.x; IB.Game.player.z = d.z; } return __TEST__.gearState().playerShield !== null; }, null, 15000);
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
  await until(pg, () => { const d = __TEST__.drops()[0]; if (d) { IB.Game.player.x = d.x; IB.Game.player.z = d.z; } return __TEST__.gearState().weapon.acid > 0; }, null, 15000);
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
  // burns tick on their own cadence (longer DoT since the skills update): watch a few more seconds for the green ticks
  for (let k = 0; k < 20 && !seen.has('acid'); k++) { await pg.waitForTimeout(200); (await gs()).numbers.forEach(n => seen.add(n.kind)); }
  check('acid ticks pop green numbers', seen.has('acid'), [...seen].join(',') + ' ' + JSON.stringify(await pg.evaluate(() => [IB.Status.active(), IB.Status.list.filter(e => e.on).map(e => [e.kind, e.pool, e.left, e.total]), IB.Weapons.current(IB.Game.ws).def.acid])));
  const shock = await pg.evaluate(() => __TEST__.status('shock', 12, 1.5));
  const shocked = await until(pg, () => __TEST__.gearState().numbers.some(n => n.kind === 'shock'), null, 5000);
  check('IB.Status.apply shock ticks with blue numbers', shock && shocked);
  // gear panel: detach and scrap through the UI
  await pg.evaluate(() => __TEST__.gear());
  const panel = await pg.evaluate(() => [IB.Game.mode, /Inventory/i.test(document.getElementById('overlay').textContent), new Set([...document.querySelectorAll('#gearRoot [data-item]')].map(e => e.dataset.item)).size]);
  check('inventory panel opens (paused, 4 items: shield + 3 fitted to the SMG)', panel[0] === 'paused' && panel[1] && panel[2] === 4, JSON.stringify(panel));
  await pg.click('#gearRoot .inv-chip.filled[data-w="buzz"] >> nth=0');
  check('picking a fitted attachment shows its card with the guns it fits', await pg.evaluate(() => !!document.querySelector('#gearRoot .inv-card .gu-fit button[aria-pressed="true"][data-w="buzz"]')));
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
  // starter vest: the first level start after level 5 is cleared puts a common vest in the bag and on the player
  const hp0 = (await gs()).maxHp;
  await pg.evaluate(() => { const G = IB.Game, g = IB.Gear.gear(G); G.slot.highest = 5; delete g.starterVest; G.grantStarterShield(); IB.Gear.refresh(G); });
  s = await gs();
  const vest = s.inv.find(i => i.id === s.armor);
  check('starter vest after level 5: common vest worn, max health up', vest && vest.type === 'armor' && vest.rarity === 'common' && s.maxHp === hp0 + s.vestHp && s.vestHp > 0, JSON.stringify([vest, hp0, s.maxHp, s.vestHp]));
  check('the starter vest is handed out once', await pg.evaluate(() => { const G = IB.Game, g = IB.Gear.gear(G), n = g.inv.length; G.grantStarterShield(); return g.inv.length === n && g.starterVest === true; }));
  // the vest cuts damage that gets past the shield
  await pg.evaluate(() => { const G = IB.Game, st = G.player.shield; st.cur = 0; st.since = 0; G.player.health = G.player.maxHp; });
  const vdr = await pg.evaluate(() => IB.Loot.armorOf(IB.Loot.worn(IB.Gear.gear(IB.Game), 'armor')).dr);
  const hpA = (await gs()).health; await hurt(20); const hpB = (await gs()).health;
  check('vest: 20 damage past the shield takes 20 x (1 - armour)', Math.abs((hpA - hpB) - 20 * (1 - vdr)) < 0.01, JSON.stringify([hpA, hpB, vdr]));
  // extended mag: fits the SMG in hand (empty mag slot): more rounds, faster reload, on the viewmodel under the magazine
  await pg.evaluate(() => __TEST__.forceDrop('mag', 'epic', 0.5));
  check('extended mag auto-fits the SMG', await until(pg, () => { const s = __TEST__.gearState(); return s.attach.buzz && s.attach.buzz.mag; }, null, 15000));
  s = await gs();
  check('extended mag: bigger magazine and faster reload', s.weapon.mag > s.weapon.baseMag && s.weapon.magSize >= s.weapon.mag && s.weapon.reload < s.weapon.baseReload, JSON.stringify(s.weapon));
  check('extended mag rides the magazine on the viewmodel', s.vm.includes('mag') && await pg.evaluate(() => { const m = IB.Weapons.models.buzz; return m.gearParts.mag.parent === m.mag; }), s.vm.join(','));
  // legendary drop: orange beam on the radar, its own name
  await pg.evaluate(() => { IB.Drops.clear(); __TEST__.forceDrop('grip', 'legendary', 6); });
  check('legendary drop shows orange on the radar', await pg.evaluate(() => IB.Drops.radar().some(r => r.color === '#FF9A2E')));
  await pg.waitForTimeout(800);
  check('legendary grip collected (Titan Grip)', await until(pg, () => { const d = __TEST__.drops()[0]; if (d) { IB.Game.player.x = d.x; IB.Game.player.z = d.z; } return __TEST__.gearState().inv.some(i => i.rarity === 'legendary' && /Titan Grip/.test(i.name)); }, null, 15000),
    JSON.stringify(await pg.evaluate(() => [__TEST__.drops(), __TEST__.gearState().inv.length])));
  // Overcharge: a kill starts the recharge at once and boosts it
  const oc = await pg.evaluate(() => __TEST__.giveItem('shield', 'epic', 8, 'overcharge'));
  await pg.evaluate(id => __TEST__.equipWorn('shield', id), oc);
  await hurt(12);
  s = await gs();
  check('overcharge cell worn, hit, recharge waiting', s.playerShield.perk === 'overcharge' && !s.playerShield.charging && s.playerShield.cur < s.playerShield.max, JSON.stringify(s.playerShield));
  const kick = await pg.evaluate(() => __TEST__.gearKill());
  check('Overcharge: a kill starts the recharge at once, boosted', kick && await until(pg, () => { const p = __TEST__.gearState().playerShield; return p.charging && p.boostT > 0; }, null, 3000));
  check('HUD shield bar takes the Epic tint with a perk pip', await pg.evaluate(() => { const b = document.getElementById('shieldBar'); return b.classList.contains('t-epic') && b.classList.contains('has-perk') && !b.querySelector('.sh-perk').hidden; }));
  // Nova: breaking the cell shocks nearby robots once per charge
  const nv = await pg.evaluate(() => __TEST__.giveItem('shield', 'legendary', 8, 'nova'));
  await pg.evaluate(id => __TEST__.equipWorn('shield', id), nv);
  // a tough robot right next to the player (spawn a wave if none is up)
  const near = () => pg.evaluate(() => {
    const G = IB.Game, p = G.player, r = IB.AI.robots.find(r => r.on && r.state !== 'spawn' && r.state !== 'pose');
    if (!r) { __TEST__.forceWaves(); return false; }
    r.x = p.x + 1.5; r.z = p.z - 1.5; r.hp = r.maxHp = 5000; p.health = p.maxHp; return true;
  });
  for (let k = 0; k < 40 && !(await near()); k++) await pg.waitForTimeout(200);
  s = await gs();
  check('legendary Nova cell worn and armed (orange bar)', s.playerShield.perk === 'nova' && s.playerShield.nova === true && await pg.evaluate(() => document.getElementById('shieldBar').classList.contains('t-legendary')), JSON.stringify(s.playerShield));
  const n0 = s.novas;
  await hurt(s.playerShield.cur + 5);
  check('Nova: breaking the cell fires a shock burst that hits the robot next to you', await until(pg, () => __TEST__.gearState().novas > 0 && __TEST__.gearState().novaHit >= 1, null, 15000), JSON.stringify(await gs().then(x => [x.novas, x.novaHit, n0])));
  await pg.evaluate(() => { const st = IB.Game.player.shield; st.since = 0; st.cur = 5; });
  await hurt(10);
  await pg.waitForTimeout(400);
  check('Nova fires once per charge (not again before the cell was full)', (await gs()).novas === n0 + 1);
  check('no console errors or warnings', pg.logs.length === 0, pg.logs.join(' | '));
  await pg.context().close();
}

async function vfxRun(browser, base) {
  console.log('\n# vfx: comic explosions, canisters, escalation, pools');
  // level 1: no canisters, intensity 1
  let pg = await newPage(browser, base + '?autotest=1&plan=mountains');
  let v = await pg.evaluate(() => ({ s: IB.Boom.stats(), cans: IB.Boom.canisters().length }));
  check('level 1 runs at intensity 1 with no canisters', v.s.intensity === 1 && v.cans === 0, JSON.stringify(v));
  await pg.context().close();
  // level 7: canisters placed safely, robots wreck into explosions, a shot canister chains, pools stay bounded
  pg = await newPage(browser, base + '?autotest=1&plan=castle');   // campaign level 7
  await pg.evaluate(() => { IB.Game.player.protect = 1e9; });
  v = await pg.evaluate(() => {
    const G = IB.Game, L = G.level, cans = IB.Boom.canisters(), bad = [];
    cans.forEach(c => {
      const z = L.zones[c.zone];
      if (Math.hypot(c.x - z.entry.x, c.z - z.entry.z) < IB.Boom.CAN.fromEntry) bad.push('near entry');
      z.spawns.forEach(s => { if (Math.hypot(c.x - s.x, c.z - s.z) < IB.Boom.CAN.fromSpawn) bad.push('near spawn'); });
    });
    // with every canister's cells blocked, the exit gate is still reachable from the entry in every zone
    const reach = L.zones.map(z => { IB.Zones.flowField(z, z.exitGate.x, z.exitGate.z + 1.2); const c = IB.Zones.navCell(z, z.entry.x, z.entry.z); return c >= 0 && z.nav.dist[c] < 32767; });
    IB.Zones.flowField(L.zones[G.zone], G.player.x, G.player.z);
    return { n: cans.length, zones: L.zones.length, per: IB.Boom.canistersPerZone(G.plan.level), bad, reach, I: IB.Boom.stats().intensity };
  });
  check('level 7 places canisters (' + v.n + ' in ' + v.zones + ' zones), intensity ' + v.I, v.n > 0 && v.n <= v.per * v.zones && v.I > 1.8, JSON.stringify(v));
  check('canisters keep clear of the entry and the spawn cans', v.bad.length === 0, v.bad.join(','));
  check('canisters never block the way to the exit gate', v.reach.every(Boolean), JSON.stringify(v.reach));
  await until(pg, () => IB.AI.robots.filter(r => r.on && r.state !== 'spawn' && r.state !== 'pose').length >= 3, null, 30000);
  const kill = await pg.evaluate(() => new Promise(done => {
    const G = IB.Game, rs = IB.AI.robots.filter(r => r.on && r.state !== 'spawn' && r.state !== 'pose');
    rs.slice(0, 4).forEach(r => IB.AI.damage(r, 1e6, {}, G.onKill));
    const s0 = IB.Boom.stats();
    setTimeout(() => done({ s0, s1: IB.Boom.stats(), kills: G.run.kills }), 400);
  }));
  check('robot wrecks throw fire, smoke, cards and debris', kill.s0.puffs > 0 && kill.s0.cards > 0 && kill.s0.debris > 0, JSON.stringify(kill.s0));
  const chain = await pg.evaluate(() => new Promise(done => {
    const G = IB.Game, cans = IB.Boom.canisters().filter(c => c.zone === G.zone && c.state === 'intact');
    if (!cans.length) return done({ skip: true });
    const c = cans[0], q = []; G.level.world.query(c.x - 0.1, c.z - 0.1, c.x + 0.1, c.z + 0.1, q);
    const box = q.find(b => b.kind === 'canister');
    IB.Boom.hitCan(box, 10); const after1 = IB.Boom.canisters().find(k => k.x === c.x && k.z === c.z).state;
    IB.Boom.hitCan(box, 99);
    const t0 = performance.now();
    (function wait() {
      const st = IB.Boom.canisters().find(k => k.x === c.x && k.z === c.z).state;
      if (st === 'gone' && performance.now() - t0 > 300) return done({ after1, st, box: box.on, nav: IB.Zones.isOpen(G.level.zones[c.zone], c.x, c.z) });
      if (performance.now() - t0 > 20000) return done({ after1, st, timeout: true });
      setTimeout(wait, 50);
    })();
  }));
  check('a canister survives one light hit, a heavy one lights it, it blows (box and nav cell freed)', chain.skip || (chain.after1 === 'intact' && chain.st === 'gone' && chain.box === false && chain.nav === true), JSON.stringify(chain));
  const pools = await pg.evaluate(() => new Promise(done => {
    const G = IB.Game, z = G.level.zones[G.zone]; let calls = 0;
    for (let k = 0; k < 30; k++) { IB.AI.spawn(k % 3 ? 'crawler' : 'gunner', z.entry.x - 6 + (k % 6) * 2.2, z.entry.z - 8 - Math.floor(k / 6) * 2, G.zone, z.entry.x, z.entry.z, { pose: true }); }
    IB.AI.robots.forEach(r => { if (r.on) IB.AI.kill(r, G.onKill); });
    for (let k = 0; k < 6; k++) IB.Projectiles.explode(z.entry.x - 4 + k * 1.6, 0.5, z.entry.z - 10, 3, 0, 40, { type: 'bomber' });
    G.player.yaw = 0; G.player.pitch = -0.1;
    let n = 0; (function tick() { calls = Math.max(calls, IB.Render.renderer.info.render.calls); if (++n < 25) requestAnimationFrame(tick); else done({ calls, s: IB.Boom.stats() }); })();
  }));
  check('30 wrecks + 6 blasts at once: pools capped, draw calls within 200', pools.s.cards <= 480 && pools.s.puffs <= 200 && pools.calls <= 200, JSON.stringify(pools));
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
    const runs = { hookRun, deathRun, inputRun, touchRun, tabMenuRun, skillsRun, slideRun, hudRun, lootRun, meleeRun, round4Run, campaignRun, vfxRun };
    for (const [name, fn] of Object.entries(runs)) if (!process.env.ONLY || process.env.ONLY.split(',').includes(name)) await fn(browser, base);
  } catch (e) { console.log('FAIL exception ' + e.stack); failures++; }
  await browser.close(); server.close();
  console.log('\n' + (failures ? failures + ' FAILED' : 'ALL PASSED'));
  process.exit(failures ? 1 : 0);
})();
