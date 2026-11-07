/* Theme: Wide Garden Playground (kit-garden). A wide public park on a sunny afternoon: lawns with mown stripes,
   gravel paths and paving, clipped yew hedges as the zone walls (brick dwarf walls and brick gate piers near the
   gates, the gates are pergola arches with a green roller door), flower beds, box hedges, picket fences, trees,
   benches, picnic tables, lamps, urns, a fountain, a gazebo, a potting shed, a sandpit, swings, a seesaw, monkey
   bars, and in every garden a big climbable playground: the play tower, the three-tower play fort (bridges, stairs,
   a ramp, slides, a climbing wall) and the pirate play ship. Robots walk up the stairs, ramps and bridges too: the
   playground pieces carry walkable collision boxes (<Piece>_WCOL<n>, see src/game/zones.js and src/game/ai.js).
   Built by blender/fam_kit_garden.py; zone layouts by tools/garden_zones.py (src/data/zones/garden_*.txt).

   Symbols (1 cell = 1 m; prefab sizes are [x, z] in cells; built-ins: # hedge, S spawn can, P entry, E entry gate,
   G exit gate, a ammo, h health):
     ,  gravel path            ;  paving                   m  rubber play surface (no collision)
     t  tree (oak, lime, blossom, pine)                     f  flower bed (tulips, roses, daisies)
     =  low box hedge (runs)   -  white picket fence (runs) o  stone urn of flowers      l  lamp post
     i  litter bin             d  birdbath                  b  bench [2, 1]              k  picnic table [2, 2]
     F  fountain [6, 6]        Z  gazebo [6, 6] (raised floor, walkable, open to the south)
     H  potting shed [4, 4]    Q  sandpit [4, 4]            W  swings [4, 2]             w  seesaw [4, 2]
     M  monkey bars [6, 2]     T  play tower [10, 10] (stairs to the south)   U  the same, turned (stairs north)
     X  play fort [30, 16] (towers + links, the middle garden's centrepiece)  Y  pirate play ship [20, 10]
   Wall chooser: hedge modules facing the open side; the two cells either side of a gate are left empty (the gate
   frame's brick piers fill them), the next two get a brick dwarf wall in front of the hedge; corners get the
   all-round corner hedge. */
(function (IB) {
  'use strict';
  var SOLID = '#GE';
  function solid(grid, c, r) { return SOLID.indexOf(grid.at(c, r)) >= 0; }
  // distance (cells) from a wall cell on the north / south edge to the centre of that edge's gate
  function gateDist(grid, c, r) {
    if (r !== 0 && r !== grid.h - 1) return 99;
    var ch = r === 0 ? 'G' : 'E', a = -1, b = -1;
    for (var x = 0; x < grid.w; x++) if (grid.at(x, r) === ch) { if (a < 0) a = x; b = x; }
    return a < 0 ? 99 : Math.abs(c + 0.5 - (a + b + 1) / 2);
  }
  var HEDGES = ['Hedge_A', 'Hedge_A', 'Hedge_B', 'Hedge_A', 'Hedge_C', 'Hedge_A', 'Hedge_B'];
  function chooseWall(c, r, horiz, corner, hash, grid, face) {
    var gd = gateDist(grid, c, r);
    if (gd < 2.6) return null;               // the gate frame's brick piers stand here
    if (face === 'none' || face === 'corner') return 'Hedge_Corner';
    if (gd < 4.6) return 'Hedge_Brick';
    var oS = !solid(grid, c, r + 1), oN = !solid(grid, c, r - 1), oE = !solid(grid, c + 1, r), oW = !solid(grid, c - 1, r);
    if (oS + oN + oE + oW !== 1) return 'Hedge_Corner';
    return HEDGES[Math.min(HEDGES.length - 1, Math.floor(hash(c * 7 + 3, r * 13 + 1) * HEDGES.length))];
  }
  var WALLS = ['Hedge_A', 'Hedge_B', 'Hedge_C', 'Hedge_Brick', 'Hedge_Corner'];

  IB.registerTheme({
    id: 'garden', name: 'Wide Garden Playground', family: 'kit-garden', prefix: 'KIT_GARDEN_',
    palette: ['#7CC35A', '#3D8BE0', '#FFC93C', '#E8413B'],
    // a warm, sunny afternoon: deep blue sky to a pale gold horizon, light haze
    env: { sky: ['#5FA8E8', '#FFF1C8'], fog: { color: '#E6EED8', near: 55, far: 160 }, sun: [0.45, 0.82, 0.35], clouds: true, ceiling: null },
    // mown lawn: 2 m stripes of a lighter green; a gravel path between the gardens; lawn outside
    floor: { color: '#7CC35A', trail: '#DCCBA4', outside: '#78BA58',
      lines: [{ dir: 'z', every: 4, width: 2, color: '#8DCF68', y: 0.008 }] },
    wall: { height: 3.4, roof: '#55A84A', facing: 'open', choose: chooseWall },
    symbols: {
      ',': { pieces: ['Path_A', 'Path_B'], alternate: true, collide: false },
      ';': { pieces: ['Pave_A', 'Pave_B'], alternate: true, collide: false },
      'm': { pieces: ['Mat_A', 'Mat_A', 'Mat_A', 'Mat_B'], collide: false },
      't': { pieces: ['Tree_Oak', 'Tree_Lime', 'Tree_Blossom', 'Tree_Oak', 'Tree_Pine'], rotate: 'random90', kind: 'cover' },
      'f': { pieces: ['Bed_Tulip', 'Bed_Rose', 'Bed_Daisy'], alternate: true, rotate: 'random90', kind: 'cover' },
      '=': { pieces: ['LowHedge'], rotate: 'run', kind: 'cover' },
      '-': { pieces: ['Picket'], rotate: 'run', kind: 'cover' },
      'o': { pieces: ['Urn'], kind: 'cover' },
      'l': { pieces: ['Lamp'], kind: 'prop' },
      'i': { pieces: ['Bin'], kind: 'cover' },
      'd': { pieces: ['Birdbath'], kind: 'cover' },
      'b': { size: [2, 1], pieces: ['Bench'], flip: true, kind: 'cover' },
      'k': { size: [2, 2], pieces: ['Picnic'], flip: true, kind: 'cover' },
      'F': { size: [6, 6], pieces: ['Landmark_Fountain'], kind: 'wall' },
      'Z': { size: [6, 6], pieces: ['Landmark_Gazebo'], kind: 'wall' },
      'H': { size: [4, 4], pieces: ['Shed'], flip: true, kind: 'wall' },
      'Q': { size: [4, 4], pieces: ['Sandpit'], kind: 'cover' },
      'W': { size: [4, 2], pieces: ['Swings'], kind: 'prop' },
      'w': { size: [4, 2], pieces: ['Seesaw'], kind: 'cover' },
      'M': { size: [6, 2], pieces: ['MonkeyBars'], kind: 'prop' },
      // the playgrounds (walkable decks, stairs, ramps and bridges; see the header)
      'T': { size: [10, 10], pieces: ['Landmark_PlayTower'], kind: 'wall' },
      'U': { size: [10, 10], pieces: ['Landmark_PlayTower'], turn: Math.PI, kind: 'wall' },
      'X': { size: [30, 16], pieces: ['Landmark_PlayFort'], with: { Landmark_PlayFort: ['Landmark_PlayFortLinks'] }, kind: 'wall' },
      'Y': { size: [20, 10], pieces: ['Landmark_PlayShip'], kind: 'wall' }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2, shutterHeight: 3.05 },
    // the gravel path between gardens runs between tall hedges: lamps, roses and a bird box mixed in per module
    trail: { wall: 'TrailWall', height: 3.4, variants: ['TrailWall', 'TrailWall_Lamp', 'TrailWall_Rose', 'TrailWall', 'TrailWall_Box'] },
    hatch: 'Hatch', stand: 'Stand',
    // park trees just past the hedges, the suburb's houses further out
    backdrop: { ring: [
      { piece: 'Backdrop_Trees', count: 4, radius: [40, 40], scale: [1, 1], squeezeX: 0.36, face: true },
      { piece: 'Backdrop_Houses', count: 4, radius: [62, 62], scale: [1, 1], squeezeX: 0.4, face: true }
    ] },
    budget: { prop: 2500, landmark: 5000, total: 70000 },
    allPieces: function () {
      var out = WALLS.concat(['GateFrame', 'GateShutter', 'TrailWall', 'TrailWall_Lamp', 'TrailWall_Rose', 'TrailWall_Box', 'Hatch', 'Stand',
        'Backdrop_Trees', 'Backdrop_Houses']);
      var sym = this.symbols;
      Object.keys(sym).forEach(function (ch) {
        var d = sym[ch], list = d.pieces.slice();
        if (d.with) Object.keys(d.with).forEach(function (n) { list = list.concat(d.with[n]); });
        list.forEach(function (n) { if (out.indexOf(n) < 0) out.push(n); });
      });
      return out;
    },
    levels: {
      garden: {
        name: 'Wide Garden Playground',
        intro: 'They have taken over the park. Climb the playgrounds, shoot from the decks, and mind: they climb too.',
        zones: [
          // The Lawns: the play tower among swings, sandpit and flower beds; 38 robots
          { map: 'garden_lawns', waves: [
            [['crawler', 7], ['gunner', 2]],
            [['crawler', 5], ['bomber', 2], ['drone', 1], ['blader', 1]],
            [['gunner', 3], ['crawler', 4], ['soldier', 2]],
            [['crawler', 5], ['bomber', 3], ['drone', 2], ['blader', 1]]] },
          // The Fort: the big three-tower play fort in the middle, the gazebo and the fountain; 43 robots
          { map: 'garden_fort', waves: [
            [['crawler', 8], ['gunner', 2]],
            [['drone', 2], ['crawler', 4], ['bomber', 2], ['soldier', 2]],
            [['gunner', 3], ['crawler', 5], ['drone', 1], ['blader', 2]],
            [['crawler', 4], ['bomber', 3], ['gunner', 2], ['drone', 1], ['soldier', 2]]] },
          // Pirate Cove: the play ship, a second tower, the potting shed and picnic lawn; 46 robots, the finale
          { map: 'garden_cove', waves: [
            [['crawler', 8], ['gunner', 3]],
            [['drone', 2], ['bomber', 3], ['crawler', 4], ['blader', 2]],
            [['gunner', 3], ['crawler', 5], ['drone', 2], ['soldier', 2]],
            [['crawler', 3], ['bomber', 3], ['gunner', 2], ['drone', 1], ['soldier', 2], ['blader', 1]]] }
        ]
      }
    }
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
