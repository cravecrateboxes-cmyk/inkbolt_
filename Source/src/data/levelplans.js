/* INKBOLT campaign. Each theme file (src/data/themes/<id>.js) registers its level plans; this file orders them,
   numbers them, links each to the next and decides which new weapons wait at the start of each level.
   Waves are lists of [robotId, count]; the next wave drops in when 4 or fewer robots are left (or after 25 s).
   A robot type without a model falls back to the Crawler. */
(function (IB) {
  'use strict';
  IB.LEVEL_PLANS = IB.LEVEL_PLANS || {};
  // Toy Town district (the original big generated zones) — after the five hand-built themes
  var P = IB.LEVEL_PLANS;
  P.tt1 = { id: 'tt1', name: 'Main Street', themeId: 'toytown', intro: 'Clear each block. Gates open when the last robot drops.',
    zones: [
      { map: 'tt_main_street', waves: [[['crawler', 10], ['gunner', 2]], [['crawler', 10], ['gunner', 3]], [['crawler', 12], ['bomber', 3]]] },
      { map: 'tt_market', waves: [[['crawler', 10], ['drone', 2]], [['crawler', 8], ['gunner', 4]], [['crawler', 12], ['gunner', 3]], [['crawler', 10], ['bomber', 4]]] }
    ] };
  P.tt2 = { id: 'tt2', name: 'The Depot', themeId: 'toytown', intro: 'Gunners hold the yard. Use the containers for cover.',
    zones: [
      { map: 'tt_depot', waves: [[['crawler', 10], ['gunner', 3]], [['crawler', 10], ['gunner', 4]], [['crawler', 8], ['bomber', 4], ['gunner', 3]]] },
      { map: 'tt_rail_yard', waves: [[['crawler', 12], ['gunner', 4]], [['bomber', 5], ['crawler', 8]], [['gunner', 6], ['crawler', 10]], [['drone', 4], ['crawler', 8]]] }
    ] };
  P.tt3 = { id: 'tt3', name: 'Billboard Row', themeId: 'toytown', intro: 'Drones overhead. Keep moving.',
    zones: [
      { map: 'tt_billboard_row', waves: [[['crawler', 12], ['gunner', 4]], [['drone', 5], ['crawler', 8]], [['bomber', 5], ['gunner', 5], ['crawler', 6]]] },
      { map: 'tt_water_works', waves: [[['crawler', 14], ['gunner', 5]], [['drone', 6], ['bomber', 4]], [['gunner', 8], ['crawler', 12]], [['drone', 6], ['crawler', 14], ['bomber', 4]]] }
    ] };
  // small two-zone level kept for the fast smoke tests (?plan=greybox)
  P.greybox = { id: 'greybox', level: 1, name: 'Toy Town', themeId: 'toytown', intro: 'Clear each zone to open its gate.',
    start: ['pip', 'buzz'], weapons: [], next: null,
    zones: [
      { map: 'toytown_lot', waves: [[['crawler', 4]], [['crawler', 5]]] },
      { map: 'toytown_yard', waves: [[['crawler', 5]], [['crawler', 6]]] }
    ] };

  // campaign order (user's beta plan: mountains, small city, classroom, office tower, big bedroom, ... up to 20)
  // the Toy Town district levels (tt1-tt3) are retired from the campaign (kept registered for tests / ?plan=);
  // levels whose theme is not built yet are skipped by the filter below
  var ORDER = ['mountains', 'smallcity', 'classroom', 'office', 'bedroom', 'coalmine', 'castle', 'city2', 'factory', 'livingroom', 'garden', 'factory2', 'island', 'mall', 'police', 'grove', 'spire', 'foundry', 'parking'];   // 14-19: Galleria Mall, Strike Team HQ (armory racks), Redwood Hollow (climbable redwoods), The Spire (sky-bridged supertalls), Titan Foundry, Deep Park (multi-level car park)
  // new weapons waiting at the start of each campaign level (index = level - 1)
  // (melee weapons and the frag cans stand there too: every melee weapon and grenades are in hand by level 5)
  var WEAPONS = [];
  Object.keys(IB.UNLOCKS || {}).forEach(function (lv) { WEAPONS[lv - 1] = IB.UNLOCKS[lv].filter(function (id) { return lv > 1 || id !== 'pip'; }); });
  /* Wave tuning for an action shooter: more to shoot, a steady climb.
     - Soldiers from level 4, Blade Bots from level 7 (earlier ones become Crawlers / Gunners).
     - Every entry grows by WAVE_MUL(level): x1.15 on level 1 rising to x1.6 on level 13. The extra bodies are the
       light robots (crawler, drone, bomber, gunner); soldiers and blade bots keep their count, so the shooting
       grows faster than the danger.
     - The next wave drops in when 6 or fewer are left (game.js WAVE_NEXT), so there is little dead time. */
  IB.MIN_LEVEL = { soldier: 4, blader: 7 };
  var LIGHT = { crawler: 1, drone: 1, bomber: 1, gunner: 1 };
  var ELITE_MUL = 2.5;   // Soldiers and Blade Bots: 2.5x the theme files' counts, light robots make room
  IB.WAVE_MUL = function (L) { return 1.15 + 0.45 * Math.min(1, Math.max(0, (L - 1) / 12)); };
  function total(p) { var t = 0; p.zones.forEach(function (z) { z.waves.forEach(function (w) { w.forEach(function (e) { t += e[1]; }); }); }); return t; }
  // a steady climb: each level has at least 5% more robots than the one before (the extra are light robots)
  var prevTotal = 0;
  function smooth(p) {
    if (p.tour) return;
    var t = total(p), want = Math.round(prevTotal * 1.05);
    for (var pass = 0; pass < 4 && t < want; pass++, t = total(p)) {
      var light = 0; p.zones.forEach(function (z) { z.waves.forEach(function (w) { w.forEach(function (e) { if (LIGHT[e[0]]) light += e[1]; }); }); });
      var k = light ? 1 + (want - t) / light : 1;
      p.zones.forEach(function (z) { z.waves.forEach(function (w) { w.forEach(function (e) { if (LIGHT[e[0]]) e[1] = Math.round(e[1] * k); }); }); });
    }
    prevTotal = total(p);
  }
  function tuneWaves(p, L) {
    if (p.tuned) return; p.tuned = true;
    var m = IB.WAVE_MUL(L);
    (p.zones || []).forEach(function (z) {
      z.waves = z.waves.map(function (w) {
        var out = {};
        w.forEach(function (e) {
          var id = e[0], n = e[1];
          if (IB.MIN_LEVEL[id] && L < IB.MIN_LEVEL[id]) id = id === 'blader' ? 'crawler' : 'gunner';
          if (LIGHT[id]) n = Math.round(n * m);
          out[id] = (out[id] || 0) + n;
        });
        // elites x2.5 (Soldiers, Blade Bots), paid for by light robots from the same wave; elites stay at most half
        var tot = 0; Object.keys(out).forEach(function (k) { tot += out[k]; });
        ['soldier', 'blader'].forEach(function (k) {
          if (!out[k]) return;
          var add = Math.round(out[k] * ELITE_MUL) - out[k];
          for (var n = 0; n < add; n++) {
            var el = (out.soldier || 0) + (out.blader || 0);
            if (el + 1 > Math.floor(tot / 2)) break;
            var big = null; Object.keys(LIGHT).forEach(function (l) { if (out[l] > 1 && (!big || out[l] > out[big])) big = l; });
            if (!big) break;
            out[big]--; out[k]++;
          }
        });
        return Object.keys(out).map(function (k) { return [k, out[k]]; });
      });
    });    smooth(p);
  }
  /* Levels 20-30: the Second Tour. After Deep Park the campaign goes on through eleven of its best maps again, as new
     levels: robots at that level's strength (health / damage / tempo by level, core/damage.js) and the player level
     keeps rising to LV 30 (health, gear and gun levels with it; skill points stop at level 19). The robot count does
     not keep inflating: each tour level is the map's own waves scaled to TOUR_ROBOTS(L) (280 on level 20 rising to 360
     on level 30, below the 400-500 of levels 15-19), so the late game gets tougher through stronger robots, not ever
     bigger crowds. */
  var TOUR = ['city2', 'castle', 'factory2', 'mall', 'island', 'police', 'office', 'grove', 'spire', 'foundry', 'parking'];
  IB.TOUR_ROBOTS = function (L) { return 280 + 8 * Math.max(0, L - 20); };
  function cloneWaves(p) { return p.zones.map(function (z) { var o = {}; for (var k in z) o[k] = z[k]; o.waves = z.waves.map(function (w) { return w.map(function (e) { return e.slice(); }); }); return o; }); }
  var tourIds = [];
  TOUR.forEach(function (id) {
    var b = P[id]; if (!b) return;
    var t = {}; for (var k in b) t[k] = b[k];
    t.id = 'tour_' + id; t.tour = id; t.zones = cloneWaves(b); t.weapons = []; t.tuned = false; delete t.start;
    t.name = b.name + ' II'; t.intro = 'Second Tour: the robots are stronger here now. ' + (b.intro || '');
    P[t.id] = t; tourIds.push(t.id);
  });
  IB.CAMPAIGN = ORDER.filter(function (id) { return P[id]; });
  IB.MAIN_CAMPAIGN = IB.CAMPAIGN.length;   // levels 1..19; the tour follows
  IB.CAMPAIGN = IB.CAMPAIGN.concat(tourIds);
  IB.CAMPAIGN.forEach(function (id, i) {
    var p = P[id];
    p.level = i + 1;
    p.next = IB.CAMPAIGN[i + 1] || null;
    p.weapons = p.weapons || WEAPONS[i] || [];
    if (i === 0) p.start = p.start || ['pip'];
    if (p.tour) tuneTour(p, i + 1); else tuneWaves(p, i + 1);
  });
  // tour waves: the normal tuning (elites, no +5% climb), then every entry scaled so the level holds TOUR_ROBOTS(L)
  function tuneTour(p, L) {
    var keep = prevTotal; tuneWaves(p, L); prevTotal = keep;
    var k = IB.TOUR_ROBOTS(L) / total(p);
    p.zones.forEach(function (z) { z.waves.forEach(function (w) { w.forEach(function (e) { e[1] = Math.max(1, Math.round(e[1] * k)); }); }); });
  }

})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
