import { TRADE_RANGE, dist, uid } from '../../shared/constants.js';
import { addItem, canFit, takeSlot, serializeInv } from './inventory.js';
import { system } from './chat.js';

export function requestTrade(world, player, targetId) {
  if (player.id === targetId) return 'not with yourself';
  const other = world.players.get(targetId);
  if (!other) return 'they are gone';
  if (dist(player, other) > TRADE_RANGE) return 'too far to trade';
  if (player.tradeId || other.tradeId) return 'already trading';
  if (other.hp <= 0 || player.hp <= 0) return 'the dead do not trade';
  other.tradeAsk = player.id;
  player.tradeAskTo = other.id;
  world.to(other, { t: 'trade', p: { phase: 'ask', from: player.name, fromId: player.id } });
  system(world, player, `Trade offered to ${other.name}.`);
  return null;
}

export function respondTrade(world, player, yes) {
  const fromId = player.tradeAsk;
  player.tradeAsk = null;
  const other = fromId ? world.players.get(fromId) : null;
  if (!other) return 'offer expired';
  other.tradeAskTo = null;
  if (!yes) {
    system(world, other, `${player.name} declined the trade.`);
    world.to(player, { t: 'trade', p: { phase: 'cancel', reason: 'declined' } });
    return null;
  }
  if (player.tradeId || other.tradeId) return 'already trading';
  if (dist(player, other) > TRADE_RANGE) return 'too far';
  openSession(world, other, player);
  return null;
}

function openSession(world, a, b) {
  const id = uid('tr');
  const sess = { id, a: a.id, b: b.id, escrowA: [], escrowB: [], lockA: false, lockB: false, acceptA: false, acceptB: false };
  world.trades.set(id, sess);
  a.tradeId = id; b.tradeId = id;
  a.path = []; b.path = [];
  a.action = null; b.action = null;
  push(world, sess);
}

export function offerSlot(world, player, slot, qty) {
  const sess = sessionOf(world, player);
  if (!sess) return 'no trade';
  const side = sideOf(sess, player.id);
  if (sess['lock' + side]) sess.lockA = sess.lockB = sess.acceptA = sess.acceptB = false;
  sess.acceptA = sess.acceptB = false;
  const inv = player.inv;
  if (slot < 0 || slot >= inv.length || !inv[slot]) return 'empty slot';
  const takeQty = qty > 0 ? Math.min(qty, inv[slot].qty) : inv[slot].qty;
  const got = takeSlot(inv, slot, takeQty);
  if (!got) return 'empty slot';
  const escrow = sess['escrow' + side];
  const existing = escrow.find((s) => s.id === got.id);
  if (existing) existing.qty += got.qty;
  else escrow.push(got);
  world.sendInv(player);
  push(world, sess);
  return null;
}

export function takeBack(world, player, escrowIndex) {
  const sess = sessionOf(world, player);
  if (!sess) return 'no trade';
  const side = sideOf(sess, player.id);
  sess.lockA = sess.lockB = sess.acceptA = sess.acceptB = false;
  const escrow = sess['escrow' + side];
  const it = escrow[escrowIndex];
  if (!it) return 'nothing there';
  if (!addItem(player.inv, it.id, it.qty)) return 'inventory full';
  escrow.splice(escrowIndex, 1);
  world.sendInv(player);
  push(world, sess);
  return null;
}

export function setLock(world, player, locked) {
  const sess = sessionOf(world, player);
  if (!sess) return 'no trade';
  const side = sideOf(sess, player.id);
  sess['lock' + side] = !!locked;
  sess.acceptA = sess.acceptB = false;
  if (!sess.lockA || !sess.lockB) sess.acceptA = sess.acceptB = false;
  push(world, sess);
  return null;
}

export function accept(world, player) {
  const sess = sessionOf(world, player);
  if (!sess) return 'no trade';
  if (!sess.lockA || !sess.lockB) return 'both must lock first';
  const side = sideOf(sess, player.id);
  sess['accept' + side] = true;
  if (sess.acceptA && sess.acceptB) {
    const err = settle(world, sess);
    if (err) {
      sess.acceptA = sess.acceptB = false;
      sess.lockA = sess.lockB = false;
      const a = world.players.get(sess.a);
      const b = world.players.get(sess.b);
      if (a) world.to(a, { t: 'notify', p: { text: err, kind: 'warn' } });
      if (b) world.to(b, { t: 'notify', p: { text: err, kind: 'warn' } });
      push(world, sess);
      return err;
    }
    return null;
  }
  push(world, sess);
  return null;
}

function settle(world, sess) {
  const a = world.players.get(sess.a);
  const b = world.players.get(sess.b);
  if (!a || !b) return 'partner left';
  if (dist(a, b) > TRADE_RANGE + 1) return 'too far';
  for (const it of sess.escrowB) if (!canFit(a.inv, it.id, it.qty)) return `${a.name} has no room`;
  for (const it of sess.escrowA) if (!canFit(b.inv, it.id, it.qty)) return `${b.name} has no room`;
  for (const it of sess.escrowB) addItem(a.inv, it.id, it.qty);
  for (const it of sess.escrowA) addItem(b.inv, it.id, it.qty);
  sess.escrowA = []; sess.escrowB = [];
  close(world, sess, 'complete');
  world.sendInv(a); world.sendInv(b);
  world.to(a, { t: 'notify', p: { text: `Trade with ${b.name} complete.`, kind: 'trade' } });
  world.to(b, { t: 'notify', p: { text: `Trade with ${a.name} complete.`, kind: 'trade' } });
  return null;
}

export function cancel(world, player, reason = 'cancelled') {
  const sess = sessionOf(world, player);
  if (!sess) {
    player.tradeAsk = null; player.tradeAskTo = null;
    world.to(player, { t: 'trade', p: { phase: 'cancel', reason } });
    return null;
  }
  close(world, sess, reason);
  return null;
}

function close(world, sess, reason) {
  const a = world.players.get(sess.a);
  const b = world.players.get(sess.b);
  refund(a, sess.escrowA); refund(b, sess.escrowB);
  sess.escrowA = []; sess.escrowB = [];
  if (a) { a.tradeId = null; world.sendInv(a); world.to(a, { t: 'trade', p: { phase: 'cancel', reason } }); }
  if (b) { b.tradeId = null; world.sendInv(b); world.to(b, { t: 'trade', p: { phase: 'cancel', reason } }); }
  world.trades.delete(sess.id);
}

function refund(player, escrow) {
  if (!player) return;
  for (const it of escrow) addItem(player.inv, it.id, it.qty);
}

export function onDisconnect(world, player) {
  if (player.tradeId) cancel(world, player, 'left');
  if (player.tradeAskTo) {
    const o = world.players.get(player.tradeAskTo);
    if (o) o.tradeAsk = null;
  }
}

export function tickTrade(world) {
  for (const sess of [...world.trades.values()]) {
    const a = world.players.get(sess.a);
    const b = world.players.get(sess.b);
    if (!a || !b) {
      if (a) close(world, sess, 'left');
      else if (b) close(world, sess, 'left');
      else world.trades.delete(sess.id);
      continue;
    }
    if (dist(a, b) > TRADE_RANGE + 2) close(world, sess, 'too far');
  }
}

function sessionOf(world, player) { return player.tradeId ? world.trades.get(player.tradeId) : null; }
function sideOf(sess, id) { return sess.a === id ? 'A' : 'B'; }

function push(world, sess) {
  const a = world.players.get(sess.a);
  const b = world.players.get(sess.b);
  if (a) world.to(a, view(sess, 'A', b));
  if (b) world.to(b, view(sess, 'B', a));
}

function view(sess, side, partner) {
  const mine = side === 'A' ? sess.escrowA : sess.escrowB;
  const theirs = side === 'A' ? sess.escrowB : sess.escrowA;
  const lockMe = side === 'A' ? sess.lockA : sess.lockB;
  const lockThem = side === 'A' ? sess.lockB : sess.lockA;
  const accMe = side === 'A' ? sess.acceptA : sess.acceptB;
  const accThem = side === 'A' ? sess.acceptB : sess.acceptA;
  return {
    t: 'trade',
    p: {
      phase: 'open', partner: partner?.name || '?', partnerId: partner?.id,
      you: mine, them: theirs, lockYou: lockMe, lockThem, acceptYou: accMe, acceptThem: accThem,
    },
  };
}

export { serializeInv };
