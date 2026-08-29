import { CHANNELS, LOCAL_CHAT_RANGE, MAX_CHAT, dist } from '../../shared/constants.js';

const RATE_MS = 350;

export function handleChat(world, player, channel, text) {
  if (typeof text !== 'string') return;
  text = text.replace(/[\u0000-\u001f]/g, '').trim().slice(0, MAX_CHAT);
  if (!text) return;
  const now = Date.now();
  if (now - (player.lastChat || 0) < RATE_MS) return;
  player.lastChat = now;
  if (text.startsWith('/')) return command(world, player, text);
  const ch = channel === CHANNELS.LOCAL ? CHANNELS.LOCAL : CHANNELS.GLOBAL;
  const msg = { t: 'chat', p: { from: player.name, id: player.id, channel: ch, text, ts: now } };
  if (ch === CHANNELS.LOCAL) {
    for (const o of world.players.values()) {
      if (dist(player, o) <= LOCAL_CHAT_RANGE) world.to(o, msg);
    }
  } else {
    world.broadcast(msg);
  }
}

function command(world, player, text) {
  const [cmd, ...rest] = text.slice(1).split(/\s+/);
  const arg = rest.join(' ');
  if (cmd === 'who' || cmd === 'players') {
    const names = [...world.players.values()].map((p) => p.name).join(', ');
    system(world, player, `Wanderers: ${names}`);
  } else if (cmd === 'help') {
    system(world, player, 'Click ground to walk. Click shops, trees, beasts, players. I pack, T trade. /who /w Name text /emote');
  } else if (cmd === 'emote' || cmd === 'me') {
    world.broadcast({ t: 'chat', p: { from: player.name, id: player.id, channel: CHANNELS.GLOBAL, text: `* ${player.name} ${arg} *`, ts: Date.now(), emote: true } });
  } else if (cmd === 'w' || cmd === 'whisper' || cmd === 'tell') {
    const sp = arg.indexOf(' ');
    if (sp < 1) { system(world, player, 'Usage: /w Name hello'); return; }
    const targetName = arg.slice(0, sp);
    const body = arg.slice(sp + 1).trim();
    if (!body) return;
    let other = null;
    for (const o of world.players.values()) {
      if (o.name.toLowerCase() === targetName.toLowerCase()) { other = o; break; }
    }
    if (!other) { system(world, player, 'No wanderer by that name.'); return; }
    const msg = { t: 'chat', p: { from: player.name, id: player.id, channel: 'whisper', text: body, ts: Date.now(), to: other.name } };
    world.to(player, msg);
    world.to(other, msg);
  } else {
    system(world, player, 'Unknown command. Try /help');
  }
}

export function system(world, player, text) {
  world.to(player, { t: 'chat', p: { from: 'Hollow', id: 'sys', channel: CHANNELS.SYSTEM, text, ts: Date.now() } });
}

export function announce(world, text) {
  world.broadcast({ t: 'chat', p: { from: 'Hollow', id: 'sys', channel: CHANNELS.SYSTEM, text, ts: Date.now() } });
}
