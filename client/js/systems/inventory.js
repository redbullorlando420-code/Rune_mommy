export function onInv(game, p) {
  game.state.inv = p.inv;
  game.state.equip = p.equip;
  if (game.state.me) {
    game.state.me.inv = p.inv;
    game.state.me.equip = p.equip;
  }
  game.hud.renderInv();
}

export function onBank(game, p) {
  game.state.bank = p.items;
  if (game.state.me) game.state.me.bank = p.items;
  game.hud.renderBank();
  game.hud.bankOpen = true;
  document.getElementById('panelBank').classList.remove('hidden');
  document.getElementById('panelInv').classList.remove('hidden');
}
