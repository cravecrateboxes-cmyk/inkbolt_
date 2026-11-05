/* INKBOLT asset names the game asks for (brief 3.4 naming). The unit test checks every name exists in the GLBs
   built by blender/build_assets.py, that each family's triangle budget holds, and that the arms rig has 22 bones. */
(function (IB) {
  'use strict';
  IB.ASSET_FILES = { common: 'fps-common.glb', weapons: 'fps-weapons.glb', bots: 'fps-bots.glb', 'kit-toytown': 'fps-kit-toytown.glb' };
  // theme kits: ASCII symbol -> kit meshes (brief 5.12)
  IB.KITS = {
    toytown: {
      family: 'kit-toytown', prefix: 'KIT_TOYTOWN_',
      wallColors: ['tangerine', 'bubblegum', 'purple', 'sky', 'sand', 'coral'], wallKinds: ['Plain', 'Window', 'Door'],
      crate: 'Crate', crateTop: 'CrateB', containers: ['Container_teal', 'Container_tangerine', 'Container_bubblegum', 'Container_sky'],
      low: ['LowWall', 'LowWallB'], landmark: 'Landmark_WaterTower', billboards: ['Billboard_A', 'Billboard_B', 'Billboard_C', 'Billboard_D'],
      gateFrame: 'GateFrame', shutter: 'GateShutter', hatch: 'Hatch', trailWall: 'TrailWall'
    }
  };
  IB.kitAssetNames = function (id) {
    var k = IB.KITS[id], out = [];
    k.wallColors.forEach(function (c) { k.wallKinds.forEach(function (w) { out.push(k.prefix + 'Wall' + w + '_' + c); }); });
    [k.crate, k.crateTop, k.landmark, k.gateFrame, k.shutter, k.hatch, k.trailWall].concat(k.containers, k.low, k.billboards)
      .forEach(function (n) { out.push(k.prefix + n); });
    return out;
  };
  IB.ASSET_NAMES = {
    common: ['Cloud_A', 'Cloud_B', 'Cloud_C', 'Hill', 'Tree', 'TrailArrow', 'SpawnCan', 'InkChunk_0', 'InkChunk_1', 'InkChunk_2', 'InkChunk_3', 'InkChunk_4', 'InkChunk_5'],
    weapons: ['ARMS', 'ARMS_Rig', 'Weapon', 'Mag', 'HAND_R', 'HAND_L', 'PICKUP_Gem', 'PICKUP_Ammo', 'PICKUP_Health',
      'WPN_PIP', 'WPN_PIP_Mag', 'WPN_PIP_MUZZLE', 'WPN_PIP_MAG', 'WPN_PIP_EJECT', 'WPN_BUZZ', 'WPN_BUZZ_Mag', 'WPN_BUZZ_MUZZLE', 'WPN_BUZZ_MAG', 'WPN_BUZZ_EJECT'],
    bots: ['BOT_CRAWLER_Body', 'BOT_CRAWLER_Leg', 'BOT_CRAWLER_Light', 'BOT_CRAWLER_CORE', 'BOT_CRAWLER_HIP0', 'BOT_CRAWLER_HIP1', 'BOT_CRAWLER_HIP2', 'BOT_CRAWLER_HIP3']
  };
  // weapons that have a Blender model + arm actions this round
  IB.MODELLED_WEAPONS = ['pip', 'buzz'];
  IB.ARM_ACTIONS = ['Idle', 'Draw', 'Holster', 'Fire', 'Reload', 'Sprint'];
  // triangle budgets incl. outline hull (brief 3.2); robots count body + legs + light
  IB.TRI_BUDGET = {
    meshes: { WPN_PIP: 1500, WPN_BUZZ: 2000, ARMS: 3000, PICKUP_Gem: 60, PICKUP_Ammo: 300, PICKUP_Health: 300,
      Cloud_A: 300, Cloud_B: 300, Cloud_C: 300, Hill: 300, Tree: 300, SpawnCan: 300, TrailArrow: 300,
      KIT_TOYTOWN_Landmark_WaterTower: 4000 },
    robots: { crawler: { parts: { BOT_CRAWLER_Body: 1, BOT_CRAWLER_Leg: 4, BOT_CRAWLER_Light: 1 }, max: 1200 } },
    kitMax: 40000, kitPropMax: 1200
  };
})(typeof window !== 'undefined' ? (window.IB = window.IB || {}) : (globalThis.IB = globalThis.IB || {}));
