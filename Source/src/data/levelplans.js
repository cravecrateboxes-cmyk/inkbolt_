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
  var ORDER = ['mountains', 'smallcity', 'classroom', 'office', 'bedroom', 'coalmine', 'castle', 'city2', 'factory', 'livingroom', 'garden', 'factory2', 'island', 'mall', 'police', 'grove', 'spire', 'foundry', 'parking', 'hotel', 'techhq', 'cargoship', 'datacenter', 'downtown', 'highrise'];   // 14-19: Galleria Mall, Strike Team HQ (armory racks), Redwood Hollow (climbable redwoods), The Spire (sky-bridged supertalls), Titan Foundry, Deep Park (multi-level car park)
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
  IB.MIN_LEVEL = { soldier: 4, blader: 7, bomber: 4, mech: 20, hawk: 20, grenadier: 20 };   // no exploding Bombers before level 4
  // what a robot named too early becomes (the levels 20+ robots step back to the robots they replace)
  var EARLIER = { soldier: 'gunner', mech: 'gunner', hawk: 'drone', grenadier: 'soldier' };
  var LIGHT = { crawler: 1, drone: 1, bomber: 1, gunner: 1, mech: 1, hawk: 1 };
  var ELITE_MUL = 2.5;   // Soldiers and Blade Bots: 2.5x the theme files' counts, light robots make room
  IB.WAVE_MUL = function (L) { return 1.15 + 0.45 * Math.min(1, Math.max(0, (L - 1) / 12)); };
  function total(p) { var t = 0; p.zones.forEach(function (z) { z.waves.forEach(function (w) { w.forEach(function (e) { t += e[1]; }); }); }); return t; }
  // a steady climb: each level has at least 5% more robots than the one before (the extra are light robots)
  var prevTotal = 0;
  function smooth(p) {
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
          while (IB.MIN_LEVEL[id] && L < IB.MIN_LEVEL[id]) id = EARLIER[id] || 'crawler';
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
    IB.lateWaves(p, L);
  }
  /* Levels 20+ (LATE.level): the new robots take over from the old light ones, after the counts above are settled (so
     the level-to-level climb is measured on the same robots as levels 1-19):
       - gunner + bomber -> Robot Trooper ('mech'), LATE.mech per robot (they are tougher than a Gunner): 0.6
       - drone -> Hawk ('hawk'), LATE.hawk per robot: 0.75
       - a quarter of the soldiers -> Grenadier ('grenadier')
     Every share is carried across the waves of the whole level (error diffusion), so the level as a whole holds
     exactly the rounded share and each wave is within one robot of it; a wave that had gunners / bombers keeps at
     least one mech, one that had drones at least one hawk, and a wave of 4 or more soldiers has at least one
     grenadier. Theme options: plan.lateRobots === false keeps the old robots on that level; waves may also name
     'mech', 'hawk' and 'grenadier' directly (they are left as written). Returns the plan. */
  var LATE = IB.LATE_WAVES = { level: 20, mech: 0.6, hawk: 0.75, grenadier: 0.25 };
  IB.lateWaves = function (p, L) {
    if (!p || L < LATE.level || p.lateRobots === false || p.lateDone) return p;
    p.lateDone = true;
    var acc = { mech: [0, 0], hawk: [0, 0], grenadier: [0, 0] };   // [source robots so far, converted so far]
    function share(k, n, minOne) {
      if (n <= 0) return 0;
      var a = acc[k]; a[0] += n;
      var c = Math.round(a[0] * LATE[k]) - a[1];
      c = Math.max(minOne ? 1 : 0, Math.min(k === 'grenadier' ? n : Math.max(1, n), c));
      a[1] += c;
      return c;
    }
    (p.zones || []).forEach(function (z) {
      z.waves = (z.waves || []).map(function (w) {
        var out = {}, order = [];
        w.forEach(function (e) { if (!(e[0] in out)) { out[e[0]] = 0; order.push(e[0]); } out[e[0]] += e[1]; });
        var gb = (out.gunner || 0) + (out.bomber || 0), m = 0, h = 0;
        if (gb) { m = share('mech', gb, true); delete out.gunner; delete out.bomber; out.mech = (out.mech || 0) + m; if (order.indexOf('mech') < 0) order.push('mech'); }
        if (out.drone) { h = share('hawk', out.drone, true); delete out.drone; out.hawk = (out.hawk || 0) + h; if (order.indexOf('hawk') < 0) order.push('hawk'); }
        // the robots the tougher replacements leave out come back as Crawlers, so every level still has more robots
        // than the one before (the threat climbs through the mechs and hawks, the count through cheap fodder)
        var gone = gb - (gb ? m : 0) + (w.reduce(function (a, e) { return a + (e[0] === 'drone' ? e[1] : 0); }, 0)) - (h || 0);
        if (gone > 0) { if (!('crawler' in out)) order.unshift('crawler'); out.crawler = (out.crawler || 0) + gone; }
        if (out.soldier) {
          var g = share('grenadier', out.soldier, out.soldier >= 4);
          out.soldier -= g; if (g) { out.grenadier = (out.grenadier || 0) + g; if (order.indexOf('grenadier') < 0) order.push('grenadier'); }
        }
        return order.filter(function (k) { return out[k] > 0; }).map(function (k) { return [k, out[k]]; });
      });
    });
    return p;
  };
  IB.CAMPAIGN = ORDER.filter(function (id) { return P[id]; });
  IB.CAMPAIGN.forEach(function (id, i) {
    var p = P[id];
    p.level = i + 1;
    p.next = IB.CAMPAIGN[i + 1] || null;
    p.weapons = p.weapons || WEAPONS[i] || [];
    if (i === 0) p.start = p.start || ['pip'];
    tuneWaves(p, i + 1);
  });

})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
