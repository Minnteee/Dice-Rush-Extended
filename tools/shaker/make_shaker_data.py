"""Writes the Dice Shaker game data and the English/German text tables.

  src/shaker/data/shaker_data.json   everything the game needs (dice, cards, talents, prices, balance)
  src/shaker/i18n/en.json, de.json   texts (other languages: translated from en.json)

usage: python make_shaker_data.py
"""
import json
import os

import shaker_design as D
import shaker_rules as R
import shaker_texts as T

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT_DATA = os.path.join(REPO, "src", "shaker", "data", "shaker_data.json")
OUT_I18N = os.path.join(REPO, "src", "shaker", "i18n")

# names of the original game's dice: GameSession.text(key) or the lucky-cube localisation
VANILLA_NAMES = {
    "50_50": ("game", "die_50"), "d4": ("game", "die_d4"), "3x4": ("game", "die_3x4"), "d2": ("game", "die_d2"),
    "777": ("game", "die_777"), "prehistoric": ("game", "prehistoric"), "golden": ("game", "golden"),
    "npc_die": ("game", "npc_die"), "crypto": ("lucky", "crypto_die"), "diamond": ("lucky", "diamond_die"),
    "pi": ("lucky", "pi_die"),
}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
         "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV", "XXV", "XXVI", "XXVII",
         "XXVIII", "XXIX", "XXX"]


def effects(items):
    return [[key, value] for key, value in items]


def build_data():
    dice = []
    for die_id, rarity, pay, fx, params, faces in D.DICE:
        entry = {"id": die_id, "rarity": rarity, "pay": pay, "fx": fx, "p": params,
                 "faces": faces or [1, 2, 3, 4, 5, 6]}
        if die_id in D.VANILLA_ART:
            entry["art"] = D.VANILLA_ART[die_id]
            entry["name_src"] = list(VANILLA_NAMES[die_id])
        else:
            entry["art"] = "res://bdr/art/dice/%s.png" % die_id
            entry["name_src"] = ["bdr", "dice.%s.name" % die_id]
        dice.append(entry)
    talents = []
    for tid, col, row, parents, tp, money, eff, icon, _en, _de in D.TALENTS:
        talents.append({"id": tid, "col": col, "row": row, "parents": parents, "tp": tp, "money": money,
                        "effects": effects(eff), "icon": icon, "slot": any(k == "slots" for k, _v in eff)})
    data = {
        "version": 1,
        "balance": D.BALANCE,
        "rarities": D.RARITIES,
        "rarity_colors": D.RARITY_COLORS,
        "stats": {key: kind for key, (kind, _en, _de) in D.STATS.items()},
        "passive_fx": R.PASSIVE_FX,
        "dice": dice,
        "gumball": D.GUMBALL,
        "lucky": D.LUCKY,
        "tarot_draw": D.TAROT_DRAW,
        "tarot_ranks": D.TAROT_RANKS,
        "tarot": [{"id": cid, "effects": effects(eff)} for cid, _en, _de, eff in D.TAROT],
        "black": [{"id": b["id"], "price": b["price"], "growth": b["growth"], "cap": b["cap"], "effects": effects(b["effects"])}
                  for b in R.BLACK.values()],
        "gauntlets": [{"index": g["index"], "price": g["price"], "effects": effects(g["effects"])} for g in R.GAUNTLETS],
        "tables": [{"id": i, "price": 0.0 if i == 0 else D.TABLE_PRICE_BASE * D.TABLE_PRICE_GROWTH ** (i - 1)}
                   for i in range(len(D.TABLES))],
        "talents": talents,
        "slot_costs": {str(n): [tp, money] for n, (tp, money) in D.SLOT_COSTS.items()},
    }
    return data


def build_texts():
    en, de = {}, {}

    def put(key, pair):
        en[key], de[key] = pair

    for key, pair in T.UI.items():
        put(key, pair)
    for rarity, pair in D.RARITY_NAMES.items():
        put("rarity." + rarity, pair)
    for fx, pair in D.FX_TEXT.items():
        put("fx." + fx, pair)
    for key, (_kind, text_en, text_de) in D.STATS.items():
        put("stat." + key, (text_en, text_de))
    for cid, name_en, name_de, _eff in D.TAROT:
        put("tarot.%s.name" % cid, (name_en, name_de))
    for bid, name_en, name_de, *_rest in D.BLACK:
        put("black.%s.name" % bid, (name_en, name_de))
    for index, (name_en, name_de, *_rest) in enumerate(D.GAUNTLETS, start=1):
        put("gauntlet.%d.name" % index, (name_en, name_de))
    for index, (name_en, name_de) in enumerate(D.TABLES):
        put("table.%d.name" % index, (name_en, name_de))
    for tid, *_rest, name_en, name_de in D.TALENTS:
        put("talent.%s.name" % tid, (name_en, name_de))
    for rank in D.TAROT_RANKS:
        put("rank." + rank, D.RARITY_NAMES[rank])
    return en, de


def write_json(path, data, indent=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=indent, sort_keys=False)
        handle.write("\n")


def main():
    data = build_data()
    write_json(OUT_DATA, data, indent=1)
    en, de = build_texts()
    write_json(os.path.join(OUT_I18N, "en.json"), en, indent=1)
    write_json(os.path.join(OUT_I18N, "de.json"), de, indent=1)
    print("data: %d dice, %d tarot, %d black, %d gauntlets, %d tables, %d talents; texts: %d keys" % (
        len(data["dice"]), len(data["tarot"]), len(data["black"]), len(data["gauntlets"]), len(data["tables"]),
        len(data["talents"]), len(en)))


if __name__ == "__main__":
    main()
