"""Dice Shaker rules in Python - a 1:1 model of res://shaker/game/rules.gd for the balance simulation.

Keep both files in sync: every formula here exists with the same name in rules.gd.
"""
import math
import random

import shaker_design as D

B = D.BALANCE
RARITY_INDEX = {r: i for i, r in enumerate(D.RARITIES)}
DICE = {}
for _id, _rarity, _pay, _fx, _p, _faces in D.DICE:
    DICE[_id] = {"id": _id, "rarity": _rarity, "pay": _pay, "fx": _fx, "p": _p, "faces": _faces or [1, 2, 3, 4, 5, 6]}
DICE_BY_RARITY = {r: [d for d in DICE.values() if d["rarity"] == r] for r in D.RARITIES}
TALENTS = {t[0]: {"id": t[0], "col": t[1], "row": t[2], "parents": t[3], "tp": t[4], "money": t[5], "effects": t[6]} for t in D.TALENTS}
TAROT = {t[0]: {"id": t[0], "effects": t[3]} for t in D.TAROT}
BLACK = {b[0]: {"id": b[0], "price": D.BLACK_PRICE["base"] * D.BLACK_PRICE["growth"] ** i, "growth": b[4], "cap": b[5],
                "effects": b[6]} for i, b in enumerate(D.BLACK)}
GAUNTLETS = [{"index": i + 1, "price": D.GAUNTLET_PRICE["base"] * D.GAUNTLET_PRICE["growth"] ** i, "effects": g[3]}
             for i, g in enumerate(D.GAUNTLETS)]
PASSIVE_FX = {"xp": "xp_pct", "tp_luck": "tp_pct", "quick": "speed_pct", "auto": "auto_pct",
              "cheap_lucky": "lucky_discount", "cheap_tarot": "tarot_discount", "combo": "combo_pct"}


# ------------------------------------------------------------------------------------------- stats
def empty_stats():
    stats = {}
    for key, (kind, _en, _de) in D.STATS.items():
        stats[key] = 1.0 if kind == "mul" else 0.0
    return stats


def apply_stat(stats, key, value):
    kind = D.STATS[key][0]
    if kind == "add":
        stats[key] += value
    elif kind == "mul":
        stats[key] *= value
    elif kind == "max":
        stats[key] = max(stats[key], value)
    elif kind == "min":
        stats[key] = value if stats[key] <= 0 else min(stats[key], value)


def compute_stats(state):
    stats = empty_stats()
    for tid in state["talents"]:
        for key, value in TALENTS[tid]["effects"]:
            apply_stat(stats, key, value)
    for cid, copies in state["tarot"].items():
        if copies <= 0:
            continue
        for key, values in TAROT[cid]["effects"]:
            apply_stat(stats, key, values[min(copies, 4) - 1])
    for bid, copies in state["black"].items():
        for _ in range(copies):
            for key, value in BLACK[bid]["effects"]:
                if value == "copies+1":
                    apply_stat(stats, key, copies + 1)
                else:
                    apply_stat(stats, key, value)
    equipped = state.get("gauntlet", 0)
    if equipped:
        for key, value in GAUNTLETS[equipped - 1]["effects"]:
            apply_stat(stats, key, value)
    stats["money_pct"] += B["gauntlet_owned_pct"] * len(state["gauntlets"])
    stats["money_pct"] += B["collection_pct"] * len(state["discovered"])
    for die in state["dice"]:
        d = DICE[die["id"]]
        if d["fx"] in PASSIVE_FX:
            apply_stat(stats, PASSIVE_FX[d["fx"]], d["p"]["pct"])
    return stats


def discount(stats, key):
    return 1.0 - min(stats[key], B["max_discount_pct"]) / 100.0


# ------------------------------------------------------------------------------------- derived
def shake_time(stats):
    return max(B["shake_time_min"], B["shake_time"] / (1.0 + stats["speed_pct"] / 100.0))


def auto_interval(stats):
    if stats["auto_every"] <= 0:
        return 0.0
    return max(shake_time(stats), stats["auto_every"] / ((1.0 + stats["auto_pct"] / 100.0) * stats["auto_x"]))


def xp_need(level, stats):
    need = B["xp_base"] * B["xp_growth"] ** (level - 1) * (1.0 - min(stats["xp_need_pct"], 60.0) / 100.0)
    return max(1.0, math.floor(need))


def level_mult(level):
    return B["level_growth"] ** (level - 1) * B["level_milestone_mult"] ** (level // B["level_milestone"])


def rarity_mult(stats, rarity):
    return (1.0 + stats[rarity + "_pct"] / 100.0) * stats[rarity + "_x"]


def combo_boost(stats, mult):
    return 1.0 + (mult - 1.0) * (1.0 + stats["combo_pct"] / 100.0) * stats["combo_x"]


def group_mult(stats, size):
    if size < 2:
        return 1.0
    return combo_boost(stats, B["combo_group"][str(min(size, 6))])


def crit_total(stats):
    return B["crit_mult"] + stats["crit_mult"]


def dice_size_big(count):
    return count <= B["big_dice_max"]


# ------------------------------------------------------------------------------------------- shake
def roll_faces(state, rng):
    faces = []
    for die in state["dice"]:
        d = DICE[die["id"]]
        if d["fx"] == "max":
            face = max(d["faces"])
        elif d["fx"] == "pi":
            face = d["faces"][die.get("pi", 0) % len(d["faces"])]
            die["pi"] = die.get("pi", 0) + 1
        else:
            face = rng.choice(d["faces"])
        faces.append(face)
    for i, die in enumerate(state["dice"]):
        d = DICE[die["id"]]
        if d["fx"] == "meteor" and rng.random() * 100.0 < d["p"]["chance"]:
            return [max(DICE[x["id"]]["faces"]) for x in state["dice"]], True
    return faces, False


def shake(state, stats, rng, manual=True, income_per_sec=0.0):
    """One shake. Returns (money, info). Updates per-die counters (grow, pi) and xp."""
    dice = state["dice"]
    n = len(dice)
    faces, meteor = roll_faces(state, rng)
    min_face = int(stats["min_face"])
    for i in range(n):
        if min_face and faces[i] < min_face:
            faces[i] = min_face
        if stats["ones_as_six"] and faces[i] == 1:
            faces[i] = 6
    # combos (wild dice join the biggest group)
    combo_faces = list(faces)
    wild = [i for i in range(n) if DICE[dice[i]["id"]]["fx"] == "wild"]
    if wild:
        counts = {}
        for i in range(n):
            if i not in wild:
                counts[combo_faces[i]] = counts.get(combo_faces[i], 0) + 1
        if counts:
            best = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
            for i in wild:
                combo_faces[i] = best
    groups = {}
    for i in range(n):
        groups[combo_faces[i]] = groups.get(combo_faces[i], 0) + 1
    shake_mult = 1.0
    combos = []
    if n >= 6 and all(v in groups for v in range(1, 7)):
        shake_mult *= combo_boost(stats, B["combo_straight"])
        combos.append("straight")
    if n >= 3 and len(groups) == 1:
        shake_mult *= combo_boost(stats, B["combo_all_same"])
        combos.append("all_same")
    best_group = max(groups.values()) if groups else 1
    if best_group >= 2:
        combos.append("group%d" % min(best_group, 6))
    # auras
    rarities_in_ball = len({DICE[d["id"]]["rarity"] for d in dice})
    aura_all = 0.0
    aura_rarity = {}
    for i in range(n):
        d = DICE[dice[i]["id"]]
        if d["fx"] == "global":
            aura_all += d["p"]["pct"]
        elif d["fx"] == "rarity_aura":
            aura_rarity[d["p"]["rarity"]] = aura_rarity.get(d["p"]["rarity"], 0.0) + d["p"]["pct"]
    values = []
    for i in range(n):
        die = dice[i]
        d = DICE[die["id"]]
        fx, p, face = d["fx"], d["p"], faces[i]
        m = 1.0
        if fx == "gamble":
            m = p["mult"] if rng.random() * 100.0 < p["chance"] else 0.0
        elif fx == "high":
            m = p["mult"] if face >= p["face"] else 1.0
        elif fx == "ones":
            m = p["mult"] if face == 1 else 1.0
        elif fx == "pair":
            m = 1.0 + p["pct"] / 100.0 * (groups[combo_faces[i]] - 1)
        elif fx == "crit":
            m = p["mult"] if rng.random() * 100.0 < p["chance"] else 1.0
        elif fx == "d20":
            m = p["mult"] if face == 20 else 1.0
        elif fx == "streak":
            m = 1.0 + min(p["step"] * state.get("streak", 0), p["max"]) / 100.0
        elif fx == "every":
            m = p["mult"] if (state["shakes"] + 1) % p["n"] == 0 else 1.0
        elif fx == "grow":
            m = 1.0 + min(p["step"] * die.get("grow", 0), p["max"]) / 100.0
        elif fx == "market":
            m = die.get("market", (p["min"] + p["max"]) / 2.0)
        elif fx == "per_level":
            m = 1.0 + p["pct"] / 100.0 * die["level"]
        elif fx == "per_die":
            m = 1.0 + p["pct"] / 100.0 * n
        elif fx == "per_rarity":
            m = 1.0 + p["pct"] / 100.0 * rarities_in_ball
        elif fx == "bomb":
            m = p["mult"] if face == 6 else (0.0 if face == 1 else 1.0)
        elif fx == "even":
            m = p["mult"] if face % 2 == 0 else 1.0
        elif fx == "odd":
            m = p["mult"] if face % 2 == 1 else 1.0
        elif fx == "pi":
            m = p["mult"]
        if face == 6:
            m *= stats["six_x"]
        aura = aura_all + aura_rarity.get(d["rarity"], 0.0)
        for j in range(n):
            if j != i and DICE[dice[j]["id"]]["fx"] == "aura":
                aura += DICE[dice[j]["id"]]["p"]["pct"]
        value = face * d["pay"] * level_mult(die["level"]) * rarity_mult(stats, d["rarity"]) * m
        value *= (1.0 + aura / 100.0) * group_mult(stats, groups[combo_faces[i]])
        values.append(value)
        # per-die counters
        if fx == "grow":
            die["grow"] = 0 if face == 1 else die.get("grow", 0) + 1
    # swallow / copy
    for i in range(n):
        fx = DICE[dice[i]["id"]]["fx"]
        if fx == "swallow":
            others = [j for j in range(n) if j != i and values[j] > 0 and DICE[dice[j]["id"]]["fx"] != "swallow"]
            if others:
                k = min(others, key=lambda j: values[j])
                values[i] += values[k] * DICE[dice[i]["id"]]["p"]["mult"]
                values[k] = 0.0
    copies = []
    for i in range(n):
        if DICE[dice[i]["id"]]["fx"] == "copy" and n > 1:
            best = max(values[j] for j in range(n) if j != i)
            copies.append((i, best * DICE[dice[i]["id"]]["p"]["pct"] / 100.0))
    for i, extra in copies:
        values[i] += extra
    if stats["best_pct"] > 0 and values:
        k = max(range(n), key=lambda j: values[j])
        values[k] *= 1.0 + stats["best_pct"] / 100.0
    total = sum(values)
    share = sum(DICE[d["id"]]["p"]["pct"] for d in dice if DICE[d["id"]]["fx"] == "share")
    total *= 1.0 + share / 100.0
    # whole shake
    face_sum = sum(faces)
    for d in dice:
        dd = DICE[d["id"]]
        if dd["fx"] == "seven" and face_sum % 7 == 0:
            shake_mult *= dd["p"]["mult"]
            combos.append("seven")
        elif dd["fx"] == "jackpot" and rng.random() * 100.0 < dd["p"]["chance"]:
            shake_mult *= dd["p"]["mult"]
            combos.append("jackpot")
    crit = rng.random() * 100.0 < min(stats["crit_chance"], 50.0)
    if crit:
        shake_mult *= crit_total(stats)
    if stats["double_chance"] > 0 and rng.random() * 100.0 < stats["double_chance"]:
        shake_mult *= 2.0
    shake_index = state["shakes"] + 1
    if stats["bell_x"] > 1.0 and shake_index % 10 == 0:
        shake_mult *= stats["bell_x"]
    money_mult = (1.0 + stats["money_pct"] / 100.0) * stats["money_x"]
    if manual:
        money_mult *= 1.0 + stats["manual_pct"] / 100.0
    total *= shake_mult * money_mult * stats.get("event_money", 1.0)
    echo = stats["echo_chance"] + sum(DICE[d["id"]]["p"]["chance"] for d in dice if DICE[d["id"]]["fx"] == "echo")
    if rng.random() * 100.0 < min(echo, 50.0):
        total *= 2.0
    # coin bags and treasures are worth "average shakes" (never a share of the income: no feedback)
    average = state.get("avg_shake", 0.0)
    state["avg_shake"] = total if average <= 0.0 else average * 0.98 + total * 0.02
    if stats["treasure_n"] > 0 and shake_index % 25 == 0:
        total += stats["treasure_n"] * state["avg_shake"]
    if stats["coin_chance"] > 0 and rng.random() * 100.0 < stats["coin_chance"]:
        total += 20.0 * state["avg_shake"]
    state["shakes"] = shake_index
    give_xp(state, stats)
    return total, {"faces": faces, "crit": crit, "combos": combos, "meteor": meteor}


def give_xp(state, stats):
    dice = state["dice"]
    gain = (1.0 + stats["xp_pct"] / 100.0) * stats["xp_x"]
    lowest = min(range(len(dice)), key=lambda j: (dice[j]["level"], dice[j]["xp"]))
    teacher = sum(DICE[d["id"]]["p"]["xp"] for d in dice if DICE[d["id"]]["fx"] == "teacher")
    for i, die in enumerate(dice):
        amount = gain
        if i == lowest:
            amount = gain * stats["catchup_x"] + teacher * gain
        add_xp(die, amount, stats)


def add_xp(die, amount, stats):
    if die["level"] >= B["max_level"]:
        return
    die["xp"] += amount
    while die["level"] < B["max_level"]:
        need = xp_need(die["level"], stats)
        if die["xp"] < need:
            break
        die["xp"] -= need
        die["level"] += 1
    if die["level"] >= B["max_level"]:
        die["xp"] = 0.0


# ------------------------------------------------------------------------------------------- prices
def gumball_price(state, stats):
    growth = max(1.05, D.GUMBALL["growth"] - stats["gumball_slow"] / 100.0)
    return D.GUMBALL["base"] * growth ** state["gumballs"] * discount(stats, "gumball_discount")


def gumball_weights(stats):
    luck = 1.0 + stats["gumball_luck"] / 100.0
    return [c["weight"] * luck ** i for i, c in enumerate(D.GUMBALL["colors"])]


def gumball_tp_expected(stats):
    w = gumball_weights(stats)
    tp = sum(wi * c["tp"] for wi, c in zip(w, D.GUMBALL["colors"])) / sum(w)
    balls = 1.0 + min(stats["double_ball"], 100.0) / 100.0
    return (tp * (1.0 + stats["tp_pct"] / 100.0) + stats["tp_extra"]) * balls


def roll_gumball(stats, rng):
    w = gumball_weights(stats)
    r = rng.random() * sum(w)
    for wi, c in zip(w, D.GUMBALL["colors"]):
        r -= wi
        if r <= 0:
            break
    raw = c["tp"] * (1.0 + stats["tp_pct"] / 100.0) + stats["tp_extra"]
    whole = math.floor(raw)
    if rng.random() < raw - whole:
        whole += 1
    return int(whole), c


def talent_cost(state, stats, tid):
    t = TALENTS[tid]
    effects = dict(t["effects"])
    if "slots" in effects:
        tp, money = D.SLOT_COSTS[len(state["dice"]) + 1]
    else:
        tp, money = t["tp"], t["money"]
    return tp, money * discount(stats, "talent_discount")


def talent_available(state, tid):
    t = TALENTS[tid]
    if tid in state["talents"]:
        return False
    if not any(p in state["talents"] for p in t["parents"]):
        return False
    effects = dict(t["effects"])
    if "slots" in effects:
        n = len(state["dice"])
        if n >= B["max_dice"]:
            return False
        if n >= B["big_dice_max"] and "compact" not in state["talents"]:
            return False
    return True


def lucky_odds(stats, tier):
    odds = list(D.LUCKY["tiers"][tier]["odds"])
    boost = 1.0 + stats["lucky_odds"] / 100.0
    odds[3] *= boost
    odds[4] *= boost
    total = sum(odds)
    return [o * 100.0 / total for o in odds]


def lucky_price(state, stats, tier, count):
    t = D.LUCKY["tiers"][tier]
    done = state["lucky_rolled"][tier]
    total = 0.0
    for k in range(count):
        total += t["base"] * t["growth"] ** (done + k)
    return total * discount(stats, "lucky_discount")


def tarot_price(state, stats):
    return D.TAROT_DRAW["base"] * D.TAROT_DRAW["growth"] ** state["tarot_draws"] * discount(stats, "tarot_discount")


def black_price(state, stats, bid):
    b = BLACK[bid]
    return b["price"] * b["growth"] ** state["black"].get(bid, 0) * discount(stats, "black_discount")


def gauntlet_price(stats, index):
    return GAUNTLETS[index - 1]["price"] * discount(stats, "shop_discount")


def new_state():
    return {
        "money": 0.0, "tp": 0, "shakes": 0, "streak": 0, "gumballs": 0, "tarot_draws": 0,
        "dice": [{"id": B["start_die"], "level": 1, "xp": 0.0, "locked": False}],
        "talents": {"shaker"}, "tarot": {}, "black": {}, "gauntlets": set(), "gauntlet": 0,
        "discovered": {B["start_die"]}, "lucky_rolled": [0, 0, 0, 0, 0],
    }
