/** Client-side click-to-move prediction. Server remains authoritative. */
export function handleGroundClick(game, wx, wy) {
  const dest = game.state.clickMove(wx, wy);
  if (dest) {
    game.net.move(dest.x, dest.y);
    game.audio.click();
    game.particles.emit(dest.x, dest.y, 4, { col: 'rgba(240,212,138,.7)', speed: 8, life: 280 });
  }
}
