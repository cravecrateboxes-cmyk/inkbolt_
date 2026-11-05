/* INKBOLT authored level plans for the runtime (zones + waves). Round 1: the M1 Toy Town greybox.
   Waves are lists of [robotId, count]. Zone maps live in src/data/zones/*.txt (bundled to zones.gen.js). */
(function (IB) {
  'use strict';
  IB.LEVEL_PLANS = {
    greybox: {
      id: 'greybox', level: 1, name: 'Toy Town', themeId: 'toytown',
      theme: { id: 'toytown', name: 'Toy Town', palette: ['#FF8A3D', '#FF7FB0', '#8A6CD8', '#F6D57A'] },
      intro: 'Clear each zone to open its gate.',
      zones: [
        { map: 'toytown_lot', waves: [[['crawler', 4]], [['crawler', 5]]] },
        { map: 'toytown_yard', waves: [[['crawler', 5]], [['crawler', 6]]] }
      ]
    }
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
