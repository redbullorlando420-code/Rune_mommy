export function sendChat(game, text, channel) {
  const t = String(text || '').trim();
  if (!t) return;
  game.net.chat(t, channel);
}

export function onChat(game, payload) {
  game.hud.chat(payload);
}
