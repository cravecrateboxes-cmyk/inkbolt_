/* INKBOLT campaign: authored level plans for the runtime (big zones, waves, new weapons per level).
   Waves are lists of [robotId, count]; the next wave drops in when 4 or fewer robots are left (or after 25 s).
   A robot type without a model yet falls back to the Crawler. `weapons` are placed leaning on crates just
   ahead of the start of the level; walking up to one picks it up (it replaces the weapon of the same class).
   Zone maps: src/data/zones/*.txt (tools/gen_zones.py), bundled to zones.gen.js. */
(function (IB) {
  'use strict';
  var TOYTOWN = { id: 'toytown', name: 'Toy Town', palette: ['#FF9E5C', '#FF94BE', '#9C82E0', '#F8DE91'] };
  IB.LEVEL_PLANS = {
    tt1: {
      id: 'tt1', level: 1, name: 'Main Street', themeId: 'toytown', theme: TOYTOWN,
      intro: 'Clear each block. Gates open when the last robot drops.',
      start: ['pip'], weapons: ['buzz'],
      zones: [
        { map: 'tt_main_street', waves: [[['crawler', 8]], [['crawler', 10]], [['crawler', 12]]] },
        { map: 'tt_market', waves: [[['crawler', 10]], [['crawler', 8], ['gunner', 3]], [['crawler', 12], ['gunner', 3]], [['crawler', 10], ['bomber', 3]]] }
      ],
      next: 'tt2'
    },
    tt2: {
      id: 'tt2', level: 2, name: 'The Depot', themeId: 'toytown', theme: TOYTOWN,
      intro: 'Gunners hold the yard. Use the containers for cover.',
      weapons: ['rivet', 'handcannon'],
      zones: [
        { map: 'tt_depot', waves: [[['crawler', 10], ['gunner', 2]], [['crawler', 10], ['gunner', 4]], [['crawler', 8], ['bomber', 4], ['gunner', 3]]] },
        { map: 'tt_rail_yard', waves: [[['crawler', 12], ['gunner', 4]], [['bomber', 5], ['crawler', 8]], [['gunner', 6], ['crawler', 10]], [['drone', 4], ['crawler', 8]]] }
      ],
      next: 'tt3'
    },
    tt3: {
      id: 'tt3', level: 3, name: 'Billboard Row', themeId: 'toytown', theme: TOYTOWN,
      intro: 'Drones overhead. Keep moving.',
      weapons: ['triplet', 'whisk'],
      zones: [
        { map: 'tt_billboard_row', waves: [[['crawler', 12], ['gunner', 4]], [['drone', 5], ['crawler', 8]], [['bomber', 5], ['gunner', 5], ['crawler', 6]]] },
        { map: 'tt_water_works', waves: [[['crawler', 14], ['gunner', 5]], [['drone', 6], ['bomber', 4]], [['gunner', 8], ['crawler', 12]], [['drone', 6], ['crawler', 14], ['bomber', 4]]] }
      ],
      next: null
    }
  };
  IB.CAMPAIGN = ['tt1', 'tt2', 'tt3'];
  // kept for the old smoke tests / ?plan=greybox
  IB.LEVEL_PLANS.greybox = {
    id: 'greybox', level: 1, name: 'Toy Town', themeId: 'toytown', theme: TOYTOWN, intro: 'Clear each zone to open its gate.',
    start: ['pip', 'buzz'], weapons: [],
    zones: [
      { map: 'toytown_lot', waves: [[['crawler', 4]], [['crawler', 5]]] },
      { map: 'toytown_yard', waves: [[['crawler', 5]], [['crawler', 6]]] }
    ],
    next: null
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
