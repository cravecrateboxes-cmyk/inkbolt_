// INKBOLT gear review shots. Run: node tests/e2e/gear-shots.js [path-to-html]
// Writes tests/e2e/review/gear-*.png: the field kit Inventory with every rarity and the new gear (legendary Nova
// shield + vest worn, extended mags fitted, spares in the backpack) at desktop and phone sideways, an item card with
// compare, and the in-play HUD (legendary shield bar tint + perk pip, a legendary pickup card).
// ONLY=inv-desktop,inv-phone,card,hud narrows it down. Also checks the layout: no tile spills out of its column.
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const ROOT = path.resolve(__dirname, '../../..');
const TARGET = process.argv[2] || 'Play Inkbolt.html';
const OUT = path.join(__dirname, 'review');
const ONLY = process.env.ONLY ? process.env.ONLY.split(',') : null;
const ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
function serve() {
  return new Promise(res => {
    const s = http.createServer((req, r) => {
      const f = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.css') ? 'text/css' : f.endsWith('.woff2') ? 'font/woff2' : 'text/javascript' }); r.end(d); });
    }).listen(0, () => res(s));
  });
}

// a mid-campaign save (level 12 cleared) with gear of every rarity: worn legendary Nova cell + epic vest, the rifle
// fully kitted (legendary grip, rare scope, epic acid, legendary mag), a common mag on the SMG, spares in the bag
async function kit(pg) {
  await pg.evaluate(() => __TEST__.start());
  await pg.waitForFunction(() => IB.Game.run && IB.Game.run.started, null, { timeout: 60000 });
  await pg.evaluate(() => {
    const G = IB.Game, L = IB.Loot, g = IB.Gear.gear(G), T = __TEST__;
    G.slot.highest = 12; G.slot.gems = 4120;
    G.slot.arsenal = ['pip', 'buzz', 'rivet', 'handcannon', 'needle', 'whisk']; G.slot.loadout = ['rivet', 'buzz', 'pip'];
    G.applyProgress();
    g.starter = g.starterVest = true; g.inv.length = 0; g.shield = g.armor = null; g.attach = {};
    const give = (t, r, lv, perk) => T.giveItem(t, r, lv, perk);
    L.equipShield(g, give('shield', 'legendary', 12, 'nova'));
    L.equipWorn(g, 'armor', give('armor', 'epic', 11));
    [['grip', 'legendary'], ['scope', 'rare'], ['acid', 'epic'], ['mag', 'legendary']].forEach(([t, r]) => L.attach(g, 'rivet', IB.WEAPONS.rivet, give(t, r, 12)));
    L.attach(g, 'buzz', IB.WEAPONS.buzz, give('mag', 'common', 9));
    L.attach(g, 'pip', IB.WEAPONS.pip, give('acid', 'rare', 8));
    give('shield', 'epic', 11, 'overcharge'); give('shield', 'rare', 10); give('shield', 'common', 6);
    give('armor', 'legendary', 12); give('armor', 'rare', 7);
    give('mag', 'epic', 10); give('grip', 'rare', 9); give('scope', 'legendary', 12);
    IB.Gear.refresh(G, true); IB.Gear.save(G);
    T.tabMenu('inventory');
  });
  // the item pictures render in the background
  await pg.waitForFunction(() => { const s = [...document.querySelectorAll('#tmGear [data-thumb]')]; return s.length > 10 && s.every(e => e.querySelector('img')); }, null, { timeout: 60000 }).catch(() => {});
  await pg.waitForTimeout(400);
}
// layout check: every tile and card stays inside its panel, nothing scrolls sideways
async function layout(pg) {
  return pg.evaluate(() => {
    const out = [], W = innerWidth;
    if (document.documentElement.scrollWidth > W + 1) out.push('page scrolls sideways');
    document.querySelectorAll('#tmGear .inv-chip, #tmGear .inv-worn, #tmGear .inv-item, #tmGear .inv-wslot').forEach(t => {
      const p = t.closest('.ep'); if (!p) return;
      const a = t.getBoundingClientRect(), b = p.getBoundingClientRect();
      if (a.width > 0 && (a.left < b.left - 2 || a.right > b.right + 2)) out.push((t.dataset.k || t.className) + ' spills out of ' + p.className);
      const l = t.querySelector('.chip-l, .ws-name, .it-name');
      if (l && l.scrollWidth > l.clientWidth + 40) out.push((t.dataset.k || '') + ' label cut hard: ' + l.textContent);
    });
    return out;
  });
}

const SHOTS = {
  // desktop: the worn legendary Nova cell's card (perk row), the rifle's four attachment slots, the full backpack
  'inv-desktop': { view: { w: 1920, h: 1080 }, run: async pg => { await kit(pg); await pg.hover('#tmGear .inv-worn.filled[data-item] >> nth=0'); } },
  // desktop: a backpack mag picked: its card compared with the mag on the rifle
  card: { view: { w: 1920, h: 1080 }, run: async pg => {
    await kit(pg);
    await pg.evaluate(() => { const G = IB.Game, g = IB.Gear.gear(G), m = g.inv.find(i => i.type === 'mag' && i.rarity === 'epic'); IB.GearUI.state.slot = 0; IB.GearUI.state.sel = { k: 'item', id: m.id }; IB.GearUI.render(document.getElementById('tmGear'), G); });
    await pg.mouse.move(5, 5);
  } },
  // phone sideways: the same inventory, a legendary vest selected
  'inv-phone': { view: { w: 844, h: 390, touch: true }, run: async pg => {
    await kit(pg);
    await pg.evaluate(() => { const G = IB.Game, g = IB.Gear.gear(G), v = g.inv.find(i => i.type === 'armor' && i.rarity === 'legendary'); IB.GearUI.state.sel = { k: 'item', id: v.id }; IB.GearUI.render(document.getElementById('tmGear'), G); });
  } },
  // in play: the legendary cell's orange shield bar with the Nova pip lit, a legendary pickup card
  hud: { view: { w: 1920, h: 1080 }, run: async pg => {
    await kit(pg);
    await pg.evaluate(() => { __TEST__.closeTabMenu(); });
    await pg.waitForTimeout(300);
    await pg.evaluate(() => { const G = IB.Game; G.player.protect = 99; IB.AI.update = () => {}; __TEST__.forceDrop('mag', 'legendary', 0.4, 12); });
    await pg.waitForFunction(() => { const c = document.getElementById('lootCard'); return c && !c.hidden; }, null, { timeout: 30000 });
    await pg.evaluate(() => { IB.LootHUD.tick = () => {}; });
  } }
};

(async () => {
  const server = await serve();
  const url = 'http://localhost:' + server.address().port + '/' + encodeURI(TARGET) + '?autotest=1&plan=mountains';
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args: ARGS });
  let errors = 0;
  for (const name of Object.keys(SHOTS).filter(n => !ONLY || ONLY.includes(n))) {
    const v = SHOTS[name].view;
    const ctx = await browser.newContext({ viewport: { width: v.w, height: v.h }, hasTouch: !!v.touch, isMobile: !!v.touch, deviceScaleFactor: 1 });
    const pg = await ctx.newPage(); const logs = [];
    pg.on('pageerror', e => logs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') logs.push(m.text()); });
    await pg.goto(url);
    await pg.waitForFunction(() => window.__TEST__ && IB.Game.mode === 'play', null, { timeout: 90000 });
    await SHOTS[name].run(pg);
    await pg.waitForTimeout(700);
    const file = path.join(OUT, 'gear-' + name + '.png');
    await pg.screenshot({ path: file, timeout: 120000 });
    const bad = name === 'hud' ? [] : await layout(pg);
    const errs = await pg.evaluate(() => (IB.Game.errors || []).slice());
    const all = logs.concat(errs, bad);
    console.log((all.length ? 'ERR  ' : 'ok   ') + path.relative(ROOT, file) + (all.length ? '  ' + all.join(' | ') : ''));
    if (all.length) errors++;
    await ctx.close();
  }
  await browser.close(); server.close();
  process.exit(errors ? 1 : 0);
})();
