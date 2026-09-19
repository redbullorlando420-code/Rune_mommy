"""Adult-only mini-games: Neon Toes nail salon + Michelle intimacy scene.

Choice / light timing loops via existing open_panel (keys 1-8). No underage content.
Michelle is first-name only — never deadname.
"""
from __future__ import annotations

import random


# ---------------------------------------------------------------------------
# Nail salon — adult foot / pedicure lounge
# ---------------------------------------------------------------------------

_NAIL_BEATS = (
    {
        'id': 'soak',
        'text': (
            "Vee at Neon Toes pats the pedicure throne. Warm water, rose gel on the tray.\n"
            "\"Sit. Shoes off. Adult lounge rules — no photos, tip in gold.\""
        ),
        'choices': (
            ('Soak and let her work the arch', 'massage'),
            ('Ask for french tips like Michelle wears', 'french'),
            ('Pay for the private worship chair (+18g)', 'worship'),
            ('Just buy polish and leave', 'shop'),
        ),
    },
    {
        'id': 'massage',
        'text': (
            "Thumbs press your soles. Polish fumes and lotion. Vee smirks.\n"
            "\"Michelle books the late chair when she's in Clermont. French tips. Don't tell Dave.\""
        ),
        'choices': (
            ('Lean into the massage', 'polish'),
            ('Ask about Michelle\'s appointment', 'michelle_hook'),
            ('Request faster polish', 'polish'),
        ),
    },
    {
        'id': 'french',
        'text': (
            "White tips, nude base — the Sanctuary Drive special. Vee holds your heel steady.\n"
            "\"She says Alec stares. Good. Keep staring at adult feet only.\""
        ),
        'choices': (
            ('Watch the brush work', 'polish'),
            ('Tip extra and stay quiet', 'polish'),
        ),
    },
    {
        'id': 'worship',
        'text': (
            "Private chair. Curtain pulled. Soft neon on painted toes.\n"
            "Timing: press when the polish glints — too early and Vee scoffs."
        ),
        'choices': (
            ('Hit the beat — kiss the arch (timing OK)', 'polish_good'),
            ('Rush it', 'polish_miss'),
            ('Ask her to edge the session longer', 'polish_good'),
        ),
    },
    {
        'id': 'michelle_hook',
        'text': (
            "\"Michelle — first name only, sugar — likes oil before the tips.\n"
            "Sanctuary Drive. If she offers her feet, you already know the menu.\""
        ),
        'choices': (
            ('Finish the pedicure', 'polish'),
            ('Leave for Sanctuary', 'end_sanctuary'),
        ),
    },
    {
        'id': 'polish',
        'text': "Coat dries under the little UV lamp. Soft feet, loud neon. Session winding down.",
        'choices': (
            ('Pay and flex the toes', 'end_ok'),
            ('Book the worship chair next time', 'end_ok'),
        ),
    },
    {
        'id': 'polish_good',
        'text': "Perfect timing. Vee laughs low. \"Cute. Gold well spent. Come back when your girl needs a touch-up.\"",
        'choices': (('Leave glowing', 'end_ok'),),
    },
    {
        'id': 'polish_miss',
        'text': "You rushed. Smudge on the tip. Vee sighs. \"Adults have patience. Try again next gold.\"",
        'choices': (('Leave embarrassed', 'end_ok'),),
    },
)


def start_nail_salon(game):
    game._nail_score = 0
    _nail_show(game, 'soak')


def _nail_show(game, beat_id):
    beat = next((b for b in _NAIL_BEATS if b['id'] == beat_id), _NAIL_BEATS[0])
    choices = []
    for label, nxt in beat['choices']:
        def make(n=nxt):
            def cb():
                _nail_pick(game, n)
            return cb
        choices.append((label, make()))
    if beat_id == 'shop':
        # fall through handled in pick
        pass
    choices.append(('Leave salon.', game.close_panel))
    game.open_panel('Vee   ·   Neon Toes Nail Salon', beat['text'], choices)


def _nail_pick(game, nxt):
    if nxt == 'shop':
        # open stock panel via shake shop pattern
        shops = list((getattr(game, 'shops_data', None) or {}).get('shops') or [])
        shop = next((s for s in shops if s.get('id') == 'nail_salon_clermont'), None)
        if shop and hasattr(game, 'open_shake_shop'):
            game.open_shake_shop({
                'id': 'nail_salon_clermont', 'name': shop.get('name'), 'kind': 'nail_salon',
                'pos': game._actor_pos(), 'shop': shop, 'npc': 'Vee',
            })
            return
        game.close_panel()
        return
    if nxt == 'end_sanctuary':
        game.close_panel()
        game.toast('Sanctuary Drive — Michelle first-name only.')
        return
    if nxt == 'end_ok':
        game._nail_score = int(getattr(game, '_nail_score', 0)) + 1
        if random.random() < 0.4:
            game.pack.append('Rose Gel Polish')
        game.toast('Neon Toes session done.')
        game.close_panel()
        try:
            game._quest_event('nail_salon')
        except Exception:
            pass
        return
    if nxt == 'polish_good':
        game._nail_score = int(getattr(game, '_nail_score', 0)) + 2
        game.breed = min(100, int(getattr(game, 'breed', 0)) + 4)
    if nxt == 'worship':
        if game.gold < 18:
            game.toast('Need 18g for the private chair.')
            _nail_show(game, 'soak')
            return
        game.gold -= 18
    _nail_show(game, nxt)


# ---------------------------------------------------------------------------
# Michelle intimacy mini-game (adult, dressed→nude mesh toggle)
# ---------------------------------------------------------------------------

_SEX_BEATS = (
    {
        'id': 'start',
        'text': (
            "Sanctuary. Door locked. Michelle — fifty, teal dress already riding those thighs — "
            "hooks a french-tipped toe under your belt.\n"
            "\"Dave's in Michigan. Mommy flew here for this. Look at me when you say my name.\""
        ),
        'nude': False,
        'choices': (
            ('Kiss her and start undressing the teal', 'undress'),
            ('Start at her feet — sandals off', 'feet'),
            ('Ask her to keep the dress on a minute', 'dress_tease'),
        ),
    },
    {
        'id': 'undress',
        'text': (
            "Teal hits the floor. Adult hourglass, soft belly, full chest — anime-girl silhouette, "
            "very much fifty and very much not shy.\n"
            "\"Don't you dare call me anything but Michelle. Or Mommy. Your pick.\""
        ),
        'nude': True,
        'choices': (
            ('Call her Michelle and pull her close', 'breed_loop'),
            ('Call her Mommy and go slow', 'mommy'),
            ('Worship her feet first', 'feet_nude'),
        ),
    },
    {
        'id': 'feet',
        'text': (
            "Strappy sandals dangled. French tips in your face — same energy as her foot node, "
            "but this is the full session.\n"
            "\"Kiss. Then breed. Tax season can wait.\""
        ),
        'nude': False,
        'choices': (
            ('Kiss the arch, then undress her', 'undress'),
            ('Oil from the Neon Toes bag if you have it', 'feet_oil'),
            ('Pull her into bed already', 'undress'),
        ),
    },
    {
        'id': 'feet_nude',
        'text': (
            "Nude, on her back, one foot on your chest. Soft sole, loud attitude.\n"
            "\"Neon Toes did the tips. You do the rest. Mommy's waiting.\""
        ),
        'nude': True,
        'choices': (
            ('Timing: kiss on the flex (good)', 'breed_loop'),
            ('Rush and get heel-smirked', 'breed_loop'),
        ),
    },
    {
        'id': 'feet_oil',
        'text': (
            "Pedicure oil if you've got it — warm on her soles. She laughs that Pinckney laugh.\n"
            "\"Vee knows my color. You know my name. Continue.\""
        ),
        'nude': False,
        'choices': (('Undress her', 'undress'), ('Keep going on her feet', 'feet_nude')),
    },
    {
        'id': 'dress_tease',
        'text': (
            "Dress stays — barely. Skirt up those thick thighs, sandals still on.\n"
            "\"Tease yourself. Then take it off me properly.\""
        ),
        'nude': False,
        'choices': (('Take the dress', 'undress'), ('Feet first', 'feet')),
    },
    {
        'id': 'mommy',
        'text': (
            "\"That's it. Mommy. Fifty years and nobody in Michigan says it like you.\"\n"
            "She guides you. Soft, filthy, patient. BREED meter listens."
        ),
        'nude': True,
        'choices': (
            ('Follow her pace (timing good)', 'climax'),
            ('Get greedy', 'breed_loop'),
        ),
    },
    {
        'id': 'breed_loop',
        'text': (
            "Rhythm. Heat. Michelle talks crypto and Michigan football on purpose while you fill the meter.\n"
            "Hit the beat with her hips — or let Mommy set it."
        ),
        'nude': True,
        'choices': (
            ('Match her rhythm', 'climax'),
            ('Go harder — BREED +', 'breed_more'),
            ('Slow down and kiss her feet mid-stroke', 'feet_nude'),
        ),
    },
    {
        'id': 'breed_more',
        'text': "She grips your shoulder. \"Don't pull out. Mommy didn't fly two thousand miles for careful.\"",
        'nude': True,
        'choices': (('Finish with her', 'climax'),),
    },
    {
        'id': 'climax',
        'text': (
            "She finishes talking about a 1031 exchange just to be cruel — then pulls you under.\n"
            "After: teal dress somewhere on the floor, french tips on your chest, first name only."
        ),
        'nude': True,
        'choices': (
            ('Hold Michelle', 'end'),
            ('Help her back into the teal dress', 'end_dress'),
        ),
    },
)


def start_michelle_sex(game):
    """Entry from dialogue action or house room."""
    game._sex_breed_bonus = 0
    _sex_show(game, 'start')


def _sex_show(game, beat_id):
    beat = next((b for b in _SEX_BEATS if b['id'] == beat_id), _SEX_BEATS[0])
    try:
        set_michelle_nude(game, bool(beat.get('nude')))
    except Exception as exc:
        print('  michelle mesh toggle skip:', exc)
    choices = []
    for label, nxt in beat['choices']:
        def make(n=nxt):
            def cb():
                _sex_pick(game, n)
            return cb
        choices.append((label, make()))
    choices.append(('Stop / get dressed', lambda: _sex_pick(game, 'end_dress')))
    game.open_panel('Michelle', beat['text'], choices, portrait=True,
                    portrait_tex=(game._michelle_portrait() if hasattr(game, '_michelle_portrait') else None))


def _sex_pick(game, nxt):
    if nxt == 'breed_more':
        game.breed = min(100, int(getattr(game, 'breed', 0)) + 22)
        game._sex_breed_bonus = int(getattr(game, '_sex_breed_bonus', 0)) + 22
        game.toast('BREED  %d%%' % int(game.breed))
        _sex_show(game, 'breed_loop')
        return
    if nxt == 'climax':
        game.breed = min(100, int(getattr(game, 'breed', 0)) + 28)
        game.toast('BREED  %d%%' % int(game.breed))
        beat = next(b for b in _SEX_BEATS if b['id'] == 'climax')
        try:
            set_michelle_nude(game, True)
        except Exception:
            pass
        def _hold():
            _sex_pick(game, 'end')
        def _dress():
            _sex_pick(game, 'end_dress')
        game.open_panel('Michelle', beat['text'], [
            ('Hold Michelle', _hold),
            ('Help her into the teal dress', _dress),
        ], portrait=True, portrait_tex=(game._michelle_portrait() if hasattr(game, '_michelle_portrait') else None))
        return
    if nxt == 'end':
        game.close_panel()
        game.toast('Michelle stays close. First name only.')
        try:
            game._quest_event('michelle_intimacy')
        except Exception:
            pass
        if int(getattr(game, 'breed', 0)) >= 100 and not getattr(game, 'preg', False):
            try:
                game.open_michelle('bun')
            except Exception:
                pass
        return
    if nxt == 'end_dress':
        try:
            set_michelle_nude(game, False)
        except Exception:
            pass
        game.close_panel()
        game.toast('Teal dress back on. Sanctuary quiet.')
        try:
            game._quest_event('michelle_intimacy')
        except Exception:
            pass
        return
    _sex_show(game, nxt)


def set_michelle_nude(game, nude: bool):
    """Swap Michelle mesh between teal dress and adult nude anime-feminine variant."""
    from models3d._actors import attach_humanoid_parts, clear_humanoid_parts
    m = getattr(game, 'michelle', None)
    if not m:
        return
    Entity = game.Entity
    color = game.color
    want = 'michelle_nude' if nude else 'michelle'
    if getattr(m, 'humanoid_style', None) == want and getattr(m, '_parts_ready', False):
        return
    clear_humanoid_parts(m)
    shirt = color.rgb32(46, 196, 182)  # teal fabric even when nude unused
    pants = color.rgb32(46, 196, 182)
    skin = color.rgb32(255, 206, 166)
    attach_humanoid_parts(
        Entity, color, m, shirt, pants, skin=skin,
        hitbox=False, detail='named', style=want,
    )
    m.humanoid_style = want
    m._parts_ready = True
    if getattr(game, 'preg', False):
        try:
            game._apply_preg_look()
        except Exception:
            pass
