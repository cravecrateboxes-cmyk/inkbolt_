/* Theme: Redwood Hollow (kit-grove) -- an overgrown garden valley on bumpy ground.
   Rolling mounds and diagonal ridges (theme.terrain: a heightfield the player, robots, bullets, pickups and props all
   follow), mossy rock ridges for walls, and giant redwoods ('Z') whose broken, split-down branches spiral up the trunk
   like stairs (0.45 m steps, collision kind 'step') to a ring of limbs at 9 m. Two redwoods on the same rows are
   joined by a rope bridge ('=' in the zone file's "@layer 9" grid). Robots climb the branch stairs too: the nav grid
   holds every walkable surface (ground, steps, limbs, bridge) and the flow field leads them up to a player in a tree.
   Built by blender/fam_kit_grove.py; zone layouts by tools/grove_zones.py (src/data/zones/grove_*.txt).

   Symbols: Z redwood [6,6]  o oak  t fruit tree (apple / orange / pear)  b bush  B berry bush  s sunflowers
            V vegetable bed [2,4]  U pumpkins [2,2]  W lily pond [4,4]  L fallen log [3,1]  r boulder  f fence (runs)
            c fruit crate  g tall grass  l reeds  n fern  w flowers (walk-through)  = bridge (layer 9) */
(function (IB) {
  'use strict';
  function hgt(c, r, zi) {
    var k = zi * 1.7;
    var mounds = 1.15 * Math.sin(0.19 * c + 1.3 + k) * Math.sin(0.17 * r + 0.6 + k) + 0.6 * Math.sin(0.41 * c - 0.27 * r + k);
    var band = ((r + 0.35 * c + 7 * zi) % 18 + 18) % 18, ridge = 1.7 * Math.max(0, 1 - Math.abs(band - 9) / 3.2);
    return Math.max(0, 1.0 + mounds + ridge);
  }
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none') return 'Ridge_Pillar';
    var s = (face === 'S' || face === 'N') ? c : r, line = (face === 'S' || face === 'N') ? r : c;
    var v = 1 + 1.1 * Math.sin(0.33 * s + line * 0.7) + 0.6 * Math.sin(0.9 * s + 1.7);
    return ['Ridge_A', 'Ridge_B', 'Ridge_C'][Math.max(0, Math.min(2, Math.round(v)))];
  }
  var PIECES = ['Ridge_A', 'Ridge_B', 'Ridge_C', 'Ridge_Pillar', 'Landmark_Redwood_A', 'Landmark_Redwood_B', 'Oak_A', 'Oak_B',
    'Fruit_Apple', 'Fruit_Orange', 'Fruit_Pear', 'Grass_A', 'Grass_B', 'Reeds', 'Fern', 'Flowers_A', 'Flowers_B', 'Flowers_C',
    'Sunflowers', 'Bush_A', 'Bush_B', 'Berry', 'VeggieBed', 'Pumpkins', 'Rock_A', 'Rock_B', 'Log', 'Pond', 'Fence', 'Crate',
    'Bridge', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch', 'Backdrop_HillA', 'Backdrop_HillB'];

  IB.registerTheme({
    id: 'grove', name: 'Redwood Hollow', family: 'kit-grove', prefix: 'KIT_GROVE_',
    palette: ['#7CC05E', '#A9583A', '#FFC928', '#B4DD8E'],
    env: { sky: ['#7EC8F0', '#EAF6E4'], fog: { color: '#D9EEDB', near: 44, far: 125 }, sun: [0.45, 0.8, 0.4], clouds: true, ceiling: null },
    floor: { color: '#86C466', trail: '#CDB894', outside: '#86C266' },
    terrain: { height: hgt, flat: 'ZVWULf', ramp: [1, 5], low: '#7DBE5C', high: '#B4DD8E', patch: '#93CC70', top: 4 },
    wall: { height: 6, roof: '#7CC05E', facing: 'open', choose: chooseWall },
    symbols: {
      'Z': { size: [6, 6], pieces: ['Landmark_Redwood_A', 'Landmark_Redwood_B'], face: 0, kind: 'step' },
      'o': { pieces: ['Oak_A', 'Oak_B'], rotate: 'random90', sink: true, kind: 'cover' },
      't': { pieces: ['Fruit_Apple', 'Fruit_Orange', 'Fruit_Pear'], rotate: 'random90', sink: true, kind: 'cover' },
      'b': { pieces: ['Bush_A', 'Bush_B'], rotate: 'random90', sink: true, kind: 'cover' },
      'B': { pieces: ['Berry'], rotate: 'random90', sink: true, kind: 'cover' },
      's': { pieces: ['Sunflowers'], rotate: 'random90', sink: true, kind: 'cover' },
      'V': { size: [2, 4], pieces: ['VeggieBed'], kind: 'cover' },
      'U': { size: [2, 2], pieces: ['Pumpkins'], kind: 'cover' },
      'W': { size: [4, 4], pieces: ['Pond'], collide: false },
      'L': { size: [3, 1], pieces: ['Log'], kind: 'cover' },
      'r': { pieces: ['Rock_A', 'Rock_B'], rotate: 'random90', sink: true, kind: 'cover' },
      'f': { pieces: ['Fence'], rotate: 'run', kind: 'cover' },
      'c': { pieces: ['Crate'], rotate: 'random90', sink: true, kind: 'cover' },
      'g': { pieces: ['Grass_A', 'Grass_B'], rotate: 'random90', sink: true, collide: false },
      'l': { pieces: ['Reeds'], rotate: 'random90', sink: true, collide: false },
      'n': { pieces: ['Fern'], rotate: 'random90', sink: true, collide: false },
      'w': { pieces: ['Flowers_A', 'Flowers_B', 'Flowers_C'], rotate: 'random90', sink: true, collide: false },
      '=': { pieces: ['Bridge'], rotate: 'edge', kind: 'deck' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 2.6 },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: { ring: [
      { piece: 'Backdrop_HillA', count: 6, radius: [62, 84], scale: [1.0, 1.4], squeezeX: 0.85, face: true },
      { piece: 'Backdrop_HillB', count: 8, radius: [48, 66], scale: [0.9, 1.3], squeezeX: 0.7, face: true }
    ] },
    budget: { prop: 1600, landmark: 6000, total: 60000 },
    allPieces: function () { return PIECES; },
    levels: {
      grove: {
        name: 'Redwood Hollow',
        intro: 'Climb the broken branches up the giant redwoods. The robots will climb after you.',
        zones: [
          { map: 'grove_1', waves: [[['crawler', 10], ['gunner', 2]], [['crawler', 10], ['gunner', 3], ['drone', 1]], [['crawler', 12], ['bomber', 3], ['gunner', 2]]] },
          { map: 'grove_2', waves: [[['crawler', 10], ['drone', 2]], [['gunner', 4], ['crawler', 10]], [['bomber', 4], ['crawler', 10], ['drone', 3]]] },
          { map: 'grove_3', waves: [[['crawler', 12], ['gunner', 3]], [['drone', 3], ['bomber', 3], ['crawler', 10]], [['gunner', 6], ['crawler', 14], ['bomber', 3], ['drone', 3]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
