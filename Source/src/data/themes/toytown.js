/* Theme: Toy Town (kit-toytown). Bright pastel town; the reference video's look. */
(function (IB) {
  'use strict';
  var COLORS = ['tangerine', 'bubblegum', 'purple', 'sky', 'sand', 'coral'];
  var CONTAINERS = ['Container_teal', 'Container_tangerine', 'Container_bubblegum', 'Container_sky'];
  var BILLBOARDS = ['Billboard_A', 'Billboard_B', 'Billboard_C', 'Billboard_D'];
  IB.registerTheme({
    id: 'toytown', name: 'Toy Town', family: 'kit-toytown', prefix: 'KIT_TOYTOWN_',
    palette: ['#FF9E5C', '#FF94BE', '#9C82E0', '#F8DE91'],
    env: { sky: ['#8ED2FF', '#FFF1D6'], fog: { color: '#FFF0DC', near: 45, far: 120 }, clouds: true, ceiling: null },
    floor: { color: '#F8DE91', trail: '#EFD58A', lot: true },
    wall: {
      height: 3, roof: '#D9D2E6',
      // shop fronts: runs of 4 cells share a colour; windows most of the way, the odd door
      choose: function (c, r, horiz, corner, hash) {
        var run = horiz ? Math.floor(c / 4) * 31 + r : Math.floor(r / 4) * 31 + c * 7;
        var color = COLORS[Math.floor(hash(run, horiz ? 3 : 5) * COLORS.length)];
        var h = hash(c * 13, r * 17), kind = corner ? 'Plain' : (h < 0.12 ? 'Door' : h < 0.72 ? 'Window' : 'Plain');
        return 'Wall' + kind + '_' + color;
      }
    },
    symbols: {
      '=': { pieces: ['LowWall', 'LowWallB'], h: 1, rotate: 'run', alternate: true, kind: 'cover' },
      'c': { pieces: ['Crate'], h: 1, rotate: 'random90', stack: { piece: 'CrateB', chance: 0.22, h: 1 }, kind: 'cover' },
      'C': { size: [2, 2], pieces: CONTAINERS, h: 2.5, kind: 'cover' },
      'T': { size: [3, 3], pieces: ['Landmark_WaterTower'], kind: 'wall',
        cols: [-1.3, 1.3].reduce(function (a, x) { return a.concat([-1.3, 1.3].map(function (z) { return { x: x, y: 3.75, z: z, hx: 0.2, hy: 3.75, hz: 0.2 }; })); }, []) },
      'p': { pieces: BILLBOARDS, collide: false, sequence: true }
    },
    gate: { frame: 'GateFrame', shutter: 'GateShutter', height: 3.2 },
    trail: { wall: 'TrailWall', height: 2.6 },
    hatch: 'Hatch', stand: 'Crate',
    backdrop: { ring: [{ piece: 'Hill', count: 26, radius: [70, 80], scale: [0.9, 1.5], y: -2, squash: [0.8, 1.3] }, { piece: 'Tree', count: 27, radius: [62, 70], scale: [1, 1] }] },
    budget: { prop: 1200, landmark: 4000, total: 40000 },
    allPieces: function () {
      var out = [];
      COLORS.forEach(function (c) { ['Plain', 'Window', 'Door'].forEach(function (k) { out.push('Wall' + k + '_' + c); }); });
      return out.concat(['LowWall', 'LowWallB', 'Crate', 'CrateB', 'Landmark_WaterTower', 'GateFrame', 'GateShutter', 'TrailWall', 'Hatch'], CONTAINERS, BILLBOARDS);
    },
    levels: {}
  });
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
