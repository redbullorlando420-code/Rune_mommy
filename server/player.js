/** Authoritative player: stats, pack, bank, equipment, skills. */
import { SPAWN, INV_SIZE, BANK_SIZE, EQUIP_SLOTS, uid, ACTION, xpToLevel, hueFromName } from '../shared/constants.js';
import { pack, S2C } from '../shared/protocol.js';
import { item, playerStats, skillLevel } from '../shared/catalog.js';
import {
  emptyInv, addItem as invAdd, removeItem as invRemove, countOf, canFit,
  serializeInv,
} from './systems/inventory.js';

export class Player {
  constructor(ws, name) {
    this.id = uid('p');
    this.ws = ws;
    this.name = name;
    this.x = SPAWN.x;
    this.y = SPAWN.y;
    this.dir = 0;
    this.path = [];
    this.hp = 40;
    this.maxHp = 40;
    this.inv = emptyInv(INV_SIZE);
    this.bank = emptyInv(BANK_SIZE);
    this.equip = { weapon: null, armor: null, charm: null };
    this.skills = { combat: { xp: 0 }, foraging: { xp: 0 }, binding: { xp: 0 } };
    this.action = ACTION.IDLE;
    this.target = null;
    this.tradeId = null;
    this.intent = null;
    this.channel = null;
    this.buff = null;
    this.lastSwing = 0;
    this.atk = 4;
    this.def = 2;
    this.joinedAt = Date.now();
    this.lastChat = 0;
    this.regenAcc = 0;
    this.hue = hueFromName(name);
  }

  send(type, payload) {
    if (this.ws && this.ws.readyState === 1) {
      try { this.ws.send(pack(type, payload)); } catch { /* closed */ }
    }
  }

  addItem(id, qty) { return invAdd(this.inv, id, qty); }
  removeItem(id, qty) { return invRemove(this.inv, id, qty); }
  countItem(id) { return countOf(this.inv, id); }
  hasItems(list) {
    for (const { id, qty } of list) if (countOf(this.inv, id) < qty) return false;
    return true;
  }
  canFit(id, qty) { return canFit(this.inv, id, qty); }

  bonusAtk() {
    let n = 0;
    for (const slot of EQUIP_SLOTS) {
      const it = this.equip[slot] ? item(this.equip[slot]) : null;
      if (it) n += it.atk || 0;
    }
    return n;
  }
  bonusDef() {
    let n = 0;
    for (const slot of EQUIP_SLOTS) {
      const it = this.equip[slot] ? item(this.equip[slot]) : null;
      if (it) n += it.def || 0;
    }
    return n;
  }
  bonusHp() {
    let n = 0;
    for (const slot of EQUIP_SLOTS) {
      const it = this.equip[slot] ? item(this.equip[slot]) : null;
      if (it) n += it.hp || 0;
    }
    return n;
  }

  refresh() {
    const s = playerStats(this);
    const ratio = this.maxHp > 0 ? this.hp / this.maxHp : 1;
    this.maxHp = s.maxHp;
    this.atk = s.atk;
    this.def = s.def;
    this.hp = Math.max(0, Math.min(s.maxHp, Math.round(ratio * s.maxHp)));
  }

  addXp(skillId, amount) {
    if (!this.skills[skillId]) this.skills[skillId] = { xp: 0 };
    const before = skillLevel(this, skillId);
    this.skills[skillId].xp += Math.max(0, amount | 0);
    const after = skillLevel(this, skillId);
    const prog = xpToLevel(this.skills[skillId].xp);
    this.send(S2C.XP, {
      skill: skillId, xp: this.skills[skillId].xp, amount, level: after,
      into: prog.into, need: prog.need,
    });
    if (after > before) {
      this.refresh();
      this.hp = Math.min(this.maxHp, this.hp + 8);
      this.send(S2C.NOTIFY, { text: `${labelSkill(skillId)} rises to ${after}.`, kind: 'xp' });
    }
    return after;
  }

  publicView() {
    return {
      id: this.id,
      name: this.name,
      x: r2(this.x),
      y: r2(this.y),
      hp: Math.round(this.hp),
      maxHp: this.maxHp,
      action: this.action,
      dir: r2(this.dir),
      hue: this.hue,
    };
  }

  privateView() {
    return {
      ...this.publicView(),
      inv: serializeInv(this.inv),
      bank: serializeInv(this.bank),
      equip: { weapon: this.equip.weapon, armor: this.equip.armor, charm: this.equip.charm },
      skills: {
        combat: this.skills.combat.xp,
        foraging: this.skills.foraging.xp,
        binding: this.skills.binding.xp,
      },
      atk: this.atk,
      def: this.def,
      target: this.target,
      coins: this.countItem('ember_coin'),
      channel: this.channel ? { type: this.channel.type, until: this.channel.until } : null,
    };
  }
}

function labelSkill(id) {
  return { combat: 'Ashen Combat', foraging: 'Dusk Foraging', binding: 'Hearth Binding' }[id] || id;
}

function r2(n) { return Math.round(n * 100) / 100; }

export function giveStarter(player) {
  player.equip.weapon = 'worn_dirk';
  player.equip.armor = 'cloth_wrap';
  invAdd(player.inv, 'hearthbread', 3);
  invAdd(player.inv, 'ember_coin', 80);
  invAdd(player.inv, 'tutor_note', 1);
  player.refresh();
  player.hp = player.maxHp;
}

export { serializeInv, EQUIP_SLOTS, ACTION };
