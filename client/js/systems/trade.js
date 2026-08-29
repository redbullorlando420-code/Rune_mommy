export function onTrade(game, p) {
  if (p.phase === 'open') game.audio.ui();
  if (p.reason === 'complete') game.audio.trade();
  game.hud.trade(p);
}

export function requestTrade(game, playerId) {
  game.net.tradeReq(playerId);
}
