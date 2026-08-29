export function handleEntityClick(game, hit) {
  game.hud.setTarget(hit);
  game.state.localPath = [];
  game.state.dest = null;
  if (hit.pick === 'mob') {
    game.net.attack(hit.id);
    game.audio.hit();
  } else if (hit.pick === 'node') {
    game.net.interact(hit.id);
    game.audio.gather();
  } else if (hit.pick === 'npc') {
    game.net.interact(hit.id);
    game.audio.ui();
  } else if (hit.pick === 'ground') {
    game.net.pickup(hit.id);
  } else if (hit.pick === 'player') {
    game.net.tradeReq(hit.id);
    game.hud.toast('Trade offered to ' + hit.name);
  }
}
