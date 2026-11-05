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
  var ORDER = ['mountains', 'smallcity', 'classroom', 'office', 'bedroom', 'tt1', 'tt2', 'tt3'];
  // new weapons waiting at the start of each campaign level (index = level - 1)
  var WEAPONS = [['buzz'], ['rivet', 'handcannon'], ['triplet', 'whisk'], ['longtom', 'hornet'], ['brick', 'twintap'], ['needle'], [], []];
  IB.CAMPAIGN = ORDER.filter(function (id) { return P[id]; });
  IB.CAMPAIGN.forEach(function (id, i) {
    var p = P[id];
    p.level = i + 1;
    p.next = IB.CAMPAIGN[i + 1] || null;
    p.weapons = p.weapons || WEAPONS[i] || [];
    if (i === 0) p.start = p.start || ['pip'];
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
