/* Theme: Galleria Mall (kit-mall) -- a two-storey shopping mall under skylights.
   Each zone is an atrium: shop fronts on two storeys (9.5 m walls), a 7 m mezzanine ring at 4.5 m ('u' in the
   "@layer 4.5" grid of the zone file) with glass rails ('r') over the open atrium, two escalators ('N' rises north,
   'V' rises south) and an automatic glass elevator ('L' door west, 'J' door east) that shuttles between the floors.
   Robots spawn on both floors and climb the escalators (stair-block collision, kind 'step') to reach the player.
   Built by blender/fam_kit_mall.py; zone layouts by tools/mall_zones.py (src/data/zones/mall_*.txt).

   Symbols (floor plan)                                       Symbols (mezzanine layer)
     N / V  escalator [2,10] rising north / south               u  deck   r  glass rail (links into runs)
     L / J  glass elevator [3,3], door west / east              o  planter  B  bench  c  bin  S a h
     F  fountain [4,4]   Q  Guest Services desk [4,4]
     O  big planter [2,2]  o  planter  B  bench [2,1]  c  bin  d  ad pillar
     K  kiosk [3,2]  T  food-court table [2,2]  D  display stand [2,1] */
(function (IB) {
  'use strict';
  var SHOPS = ['rose', 'mint', 'gold', 'sky', 'violet', 'orange'];
  function shopAt(s, line) { var h = Math.sin((Math.floor((s + 2) / 6) + line * 7.13) * 12.9898) * 43758.5453; return SHOPS[Math.floor((h - Math.floor(h)) * SHOPS.length)]; }
  // shop fronts in 6 m bays: a pilaster at each bay edge, a door mid-bay, glass between; corners get a pillar
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none') return 'Corner';
    var s = (face === 'S' || face === 'N') ? c : r, line = (face === 'S' || face === 'N') ? r : c + 100;
    var k = ((s + 2) % 6 + 6) % 6;
    if (k === 0) return 'Pilaster';
    if ((face === 'E' || face === 'W') && hash(c * 3 + 1, r * 7 + 2) < 0.18) return 'Blank';
    return (k === 3 ? 'ShopDoor_' : 'Shop_') + shopAt(s, line);
  }
  var WALLS = ['Pilaster', 'Corner', 'Blank'];
  SHOPS.forEach(function (c) { WALLS.push('Shop_' + c, 'ShopDoor_' + c); });
  var OTHER = ['Rail', 'RailFull', 'RailPost', 'Escalator', 'Landmark_ElevatorShaft', 'Elevator_Cab', 'Planter', 'BigPlanter', 'Bench', 'Bin',
    'AdPillar', 'Kiosk_A', 'Kiosk_B', 'FoodTable', 'Display', 'Skylight', 'Landmark_Fountain', 'Landmark_GuestDesk',
    'GateFrame', 'GateShutter', 'TrailWall', 'Hatch'];
  var LIFT = { top: 4.5, wait: 3.2, speed: 1.5, cab: 'Elevator_Cab', inner: [2.5, 2.5], floor: 0.06 };

  IB.registerTheme({
    id: 'mall', name: 'Galleria Mall', family: 'kit-mall', prefix: 'KIT_MALL_',
    palette: ['#F27D8E', '#62C9AE', '#F2BE48', '#EFE6D6'],
    env: {
      sky: null, clear: '#F4EDE2', fog: { color: '#F4EDE2', near: 46, far: 130 }, clouds: false,
      // low southern light (like the office): floors and south faces lit, the ceiling in the light 0.9 band, not the shadow band
      sun: [0.3, 0.45, 0.84],
      ceiling: { height: 9.5, color: '#FBF6EE', light: 'Skylight', every: 6, clear: '#LJ', clearR: 2 }
    },
    // polished cream stone tiles, 2 m grid
    floor: {
      color: '#EFE6D6', trail: '#E8DECD', outside: '#EFE6D6',
      lines: [{ dir: 'x', every: 2, width: 0.035, color: '#E2D5C0', y: 0.008 }, { dir: 'z', every: 2, width: 0.035, color: '#E2D5C0', y: 0.0105 }]
    },
    wall: { height: 9.5, roof: '#E9E0D2', facing: 'open', choose: chooseWall },
    symbols: {
      'N': { size: [2, 10], pieces: ['Escalator'], face: 0, kind: 'step' },
      'V': { size: [2, 10], pieces: ['Escalator'], face: Math.PI, kind: 'step' },
      'L': { size: [3, 3], pieces: ['Landmark_ElevatorShaft'], face: -Math.PI / 2, kind: 'wall', elevator: LIFT },
      'J': { size: [3, 3], pieces: ['Landmark_ElevatorShaft'], face: Math.PI / 2, kind: 'wall', elevator: LIFT },
      'F': { size: [4, 4], pieces: ['Landmark_Fountain'], kind: 'cover' },
      'Q': { size: [4, 4], pieces: ['Landmark_GuestDesk'], kind: 'cover' },
      'O': { size: [2, 2], pieces: ['BigPlanter'], kind: 'cover' },
      'o': { pieces: ['Planter'], rotate: 'random90', kind: 'cover' },
      'B': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
      'c': { pieces: ['Bin'], rotate: 'random90', kind: 'cover' },
      'd': { pieces: ['AdPillar'], kind: 'cover' },
      'K': { size: [3, 2], pieces: ['Kiosk_A', 'Kiosk_B'], flip: true, kind: 'cover' },
      'T': { size: [2, 2], pieces: ['FoodTable'], kind: 'cover' },
      'D': { size: [2, 1], pieces: ['Display'], flip: true, kind: 'cover' },
      // mezzanine
      'u': { deck: { thick: 0.4, color: '#F1E8DA', edge: '#E6DACA', under: '#F6F0E6', with: '*' } },
      'r': { pieces: ['Rail'], full: 'RailFull', links: 'r', post: 'RailPost', kind: 'wall' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.5, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 9.5 },
    hatch: 'Hatch', stand: 'Planter',
    backdrop: null,
    budget: { prop: 3200, landmark: 4000, total: 70000 },
    allPieces: function () { return WALLS.concat(OTHER); },
    levels: {
      mall: {
        name: 'Galleria Mall',
        intro: 'Robots have taken both floors. The escalators and the glass lift go up to the mezzanine.',
        zones: [
          // Grand Atrium: fountain court; Gunners hold the mezzanine rails from the second wave
          { map: 'mall_1', waves: [[['crawler', 9], ['gunner', 2]], [['crawler', 8], ['gunner', 3], ['drone', 1]], [['crawler', 10], ['bomber', 3], ['gunner', 2]]] },
          // Food Court: tables for cover, Drones over the atrium
          { map: 'mall_2', waves: [[['crawler', 10], ['drone', 2]], [['gunner', 4], ['crawler', 8]], [['bomber', 4], ['crawler', 10], ['drone', 2]]] },
          // Department Store: displays, the lift on the east side, a heavy last wave
          { map: 'mall_3', waves: [[['crawler', 10], ['gunner', 3]], [['drone', 3], ['bomber', 3], ['crawler', 8]], [['gunner', 5], ['crawler', 12], ['bomber', 3], ['drone', 2]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
