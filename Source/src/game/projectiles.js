/* INKBOLT enemy projectiles and explosions (Gunner bolts, Drone bursts, Bomber blasts).
   Contract used by game.js:
     IB.Projectiles.init(scene)
     IB.Projectiles.clear()
     IB.Projectiles.update(dt, ctx)  ctx = {player, world, hurt(source, dmg), shake(trauma)}
*/
(function (IB) {
  'use strict';
  IB.Projectiles = {
    init: function () { },
    clear: function () { },
    update: function () { }
  };
})(window.IB = window.IB || {});
