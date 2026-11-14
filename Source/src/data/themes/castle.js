/* Theme: Castle Courtyard (kit-castle). Three wide wards inside one sandstone curtain wall on a bright summer day:
   battered walls with corbelled parapets and merlons, round drum towers, gatehouses with timber portcullises (the zone
   gates), a market ward with striped stalls, carts, hay and barrels round a well, a training yard with fenced
   sparring rings, dummies, weapon racks and archery butts, and the inner ward round the keep. Higher outer ramparts,
   towers, green hills and a village beyond the walls. Built by blender/fam_kit_castle.py; zone layouts by
   tools/castle_zones.py (src/data/zones/castle_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] cells):
     #  curtain wall (1 cell thick: the module backs are the castle's outer face, seen over the passage walls)
     ,  cobbles      ;  flagstones      g  grass                 (no collision)
     b  barrels      c  crates / grain sacks    y  hay bale      f  fence (runs)     r  weapon rack (runs)
     d  training dummy      x  archery butt (faces south)        i  brazier          n  banner pole
     Y  haystack [2,2]      M  market stall [3,2]                K  cart [2,3]       W  well [3,3] (landmark)
     O  drum tower [5,5] (against the wall)    X / V  stair to the wall walk [2,7], rising north, parapet east / west
     T  the keep [12,12] (landmark, door and forebuilding stair face south)    Q  trebuchet [4,8] (landmark)
   The wall uses facing 'open': the engine turns each module's face to its single open side; the chooser below gives
   a straight run its rhythm (merlon / crenel by position, buttresses, banners, torches, arrow slits, posterns),
   corners, wall ends and gate jambs the four-way corner turret, and the modules beside an inner corner a flush
   face (the perpendicular parapet crosses their front). */
(function (IB) {
  'use strict';
  function wallish(ch) { return ch === '#' || ch === 'G' || ch === 'E'; }
  var BIG = 'OTXVWMK';   // prefabs that stand in front of the wall: keep the module behind them plain
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    if (face === 'corner' || face === 'none' || !face) return 'Corner';
    var ns = face === 'S' || face === 'N', p = ns ? c : r;
    var fc = c + (face === 'E' ? 1 : face === 'W' ? -1 : 0), fr = r + (face === 'S' ? 1 : face === 'N' ? -1 : 0);
    var merlon = p % 2 === 0, h = hash(c * 7 + 3, r * 13 + 1), dc = ns ? 1 : 0, dr = ns ? 0 : 1;
    // beside an inner corner the perpendicular parapet crosses this module's front: nothing proud here
    if (wallish(grid.at(fc - dc, fr - dr)) || wallish(grid.at(fc + dc, fr + dr))) return 'Curtain_Inner';
    // beside a gatehouse or behind a big prefab: plain merlon / crenel
    for (var d = -3; d <= 3; d++) { var q = ns ? grid.at(c + d, r) : grid.at(c, r + d); if (q === 'G' || q === 'E') return merlon ? 'Curtain_M' : 'Curtain_C'; }
    if (BIG.indexOf(grid.at(fc, fr)) >= 0) return merlon ? 'Curtain_M' : 'Curtain_C';
    var k = p % 12;
    if (k === 0) return 'Curtain_Buttress';
    if (k === 7) return Math.floor(p / 12) % 2 ? 'Curtain_BannerB' : 'Curtain_BannerR';
    if (k === 3) return 'Curtain_Torch';
    if (k === 10) return 'Curtain_Slit';
    if (p % 24 === 16) return 'Curtain_Door';
    return merlon ? (h < 0.5 ? 'Curtain_M' : 'Curtain_M2') : (h < 0.5 ? 'Curtain_C' : 'Curtain_C2');
  }
  var WALLS = ['Curtain_M', 'Curtain_M2', 'Curtain_C', 'Curtain_C2', 'Curtain_Slit', 'Curtain_BannerR', 'Curtain_BannerB',
    'Curtain_Torch', 'Curtain_Buttress', 'Curtain_Door', 'Curtain_Inner', 'Corner'];
  function flat(pieces) { return { pieces: pieces, alternate: true, collide: false }; }

  IB.registerTheme({
    id: 'castle', name: 'Castle Courtyard', family: 'kit-castle', prefix: 'KIT_CASTLE_',
    palette: ['#D3C4A6', '#C33F38', '#3D5DA8', '#8FBF5C'],
    // high summer: deep blue sky to a warm pale horizon, light warm haze, a high sun from the south-west
    env: { sky: ['#6FB0EA', '#F6EDD5'], fog: { color: '#E9E4D2', near: 60, far: 165 }, sun: [-0.42, 0.78, 0.46], clouds: true, ceiling: null },
    // packed-earth wards; the passages between wards are cobbled; meadow outside the walls
    floor: { color: '#CDB48A', trail: '#BFB5A2', outside: '#9CC46C' },
    wall: { height: 7.7, roof: '#E6DAC0', facing: 'open', choose: chooseWall },
    symbols: {
      ',': flat(['Cobble', 'CobbleB']),
      ';': flat(['Flag', 'FlagB']),
      'g': flat(['Grass', 'GrassB']),
      'b': { pieces: ['Barrels', 'BarrelStack'], rotate: 'random90', kind: 'cover' },
      'c': { pieces: ['Crates', 'Sacks'], rotate: 'random90', kind: 'cover' },
      'y': { pieces: ['HayBale'], rotate: 'random90', kind: 'cover' },
      'f': { pieces: ['Fence'], rotate: 'run', kind: 'cover' },
      'r': { pieces: ['Rack'], rotate: 'run', kind: 'cover' },
      'd': { pieces: ['Dummy'], rotate: 'random90', kind: 'cover' },
      'x': { pieces: ['Target'], rotate: 0, kind: 'cover' },
      'i': { pieces: ['Brazier'], kind: 'prop' },
      'n': { pieces: ['BannerPoleR', 'BannerPoleB'], alternate: true, kind: 'prop' },
      'Y': { size: [2, 2], pieces: ['HayStack'], flip: true, kind: 'cover', y: 0.03 },
      'M': { size: [3, 2], pieces: ['Stall_A', 'Stall_B', 'Stall_C'], sequence: true, flip: true, kind: 'cover' },
      'K': { size: [2, 3], pieces: ['Cart_Hay', 'Cart_Barrels'], flip: true, kind: 'cover' },
      'W': { size: [3, 3], pieces: ['Landmark_Well'], kind: 'wall' },
      'O': { size: [5, 5], pieces: ['Tower_A', 'Tower_B'], flip: true, kind: 'wall' },
      'X': { size: [2, 7], pieces: ['Stairs'], kind: 'wall' },
      'V': { size: [2, 7], pieces: ['StairsL'], kind: 'wall' },
      'T': { size: [12, 12], pieces: ['Landmark_Keep'], kind: 'wall' },
      'Q': { size: [4, 8], pieces: ['Landmark_Trebuchet'], kind: 'wall' }
    },
    // the zone gates are gatehouses with a timber portcullis; the passages between wards are walled as high as the
    // curtain (merlons on top), so nothing beyond them shows over the top
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    trail: { wall: 'TrailWall', height: 7.7 },
    hatch: 'Hatch', stand: 'Crates',
    backdrop: { ring: [
      // the outer curtain: high ramparts with towers and stairs just outside the wards, seen over the walls
      { piece: 'Backdrop_Rampart', count: 12, radius: [26, 34], scale: [0.95, 1.15], face: true, squeezeX: 0.7 },
      { piece: 'Backdrop_Tower', count: 7, radius: [36, 44], scale: [0.9, 1.2], face: true, squeezeX: 0.72 },
      { piece: 'Backdrop_Village', count: 6, radius: [58, 66], scale: [1.0, 1.2], face: true, squeezeX: 0.8 },
      { piece: 'Backdrop_Hills', count: 9, radius: [76, 92], scale: [1.1, 1.5], face: true, squeezeX: 0.85 }
    ] },
    budget: { prop: 2500, landmark: 8000, total: 70000 },
    allPieces: function () {
      var out = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'Hatch',
        'Backdrop_Rampart', 'Backdrop_Tower', 'Backdrop_Village', 'Backdrop_Hills']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) { sym[ch].pieces.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); }); });
      return out;
    },
    levels: {
      castle: {
        name: 'Castle Courtyard',
        intro: 'The robots have taken the castle. Clear the market, the training yard, then the keep.',
        zones: [
          // Market Ward: crawlers through the stalls, gunners behind the carts, a drone over the well
          { map: 'castle_market', waves: [
            [['crawler', 8], ['gunner', 2]],
            [['crawler', 4], ['gunner', 3], ['blader', 1]],
            [['crawler', 3], ['gunner', 2], ['drone', 1], ['soldier', 1]],
            [['crawler', 3], ['gunner', 2], ['soldier', 1]]] },
          // Training Yard: gunners on the drill ground, bombers across the open grass, a drone over the archery range
          { map: 'castle_yard', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['crawler', 3], ['bomber', 3], ['blader', 1]],
            [['gunner', 3], ['drone', 1], ['crawler', 2], ['soldier', 1]],
            [['crawler', 3], ['bomber', 2], ['gunner', 2], ['soldier', 1]]] },
          // Inner Ward: everything round the keep
          { map: 'castle_keep', waves: [
            [['crawler', 6], ['gunner', 3]],
            [['bomber', 3], ['crawler', 2], ['drone', 1], ['blader', 2]],
            [['gunner', 3], ['crawler', 2], ['soldier', 2]],
            [['crawler', 3], ['bomber', 2], ['gunner', 2], ['blader', 1]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
