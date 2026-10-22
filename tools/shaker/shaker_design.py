"""Dice Shaker - the single source of truth for the game data.

make_shaker_data.py turns this into res://shaker/data/shaker_data.json (read by the game) and the
English/German text tables; econ_sim.py uses the same data to check the balance.

Money values are plain floats ($). Percent values are whole numbers (25 = +25 %).
"""

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
RARITY_COLORS = {"common": "#b9c2cf", "uncommon": "#5fd36a", "rare": "#4aa8ff", "epic": "#c46bff", "legendary": "#ffb52e"}
RARITY_NAMES = {
    "common": ("Common", "Gewöhnlich"), "uncommon": ("Uncommon", "Ungewöhnlich"), "rare": ("Rare", "Selten"),
    "epic": ("Epic", "Episch"), "legendary": ("Legendary", "Legendär"),
}

# ------------------------------------------------------------------------------------------------
# Balance knobs (the game reads them from the json, so only change them here)
# ------------------------------------------------------------------------------------------------
BALANCE = {
    "start_die": "wood",
    "max_dice": 12,
    "big_dice_max": 6,              # up to this many dice the dice are big, then they shrink
    "max_level": 100,
    "xp_base": 6.0,                 # xp for level 1 -> 2
    "xp_growth": 1.13,              # every level needs 13 % more xp
    "level_growth": 1.08,           # pay x1.08 per level ...
    "level_milestone": 10,          # ... and x2 at every 10th level
    "level_milestone_mult": 2.0,
    "shake_time": 1.15,             # seconds a shake takes (dice fly, then land)
    "shake_time_min": 0.35,
    "streak_window": 3.0,           # seconds between shakes that still count as "in a row"
    "crit_mult": 3.0,               # a critical shake pays x3
    "combo_group": {"2": 1.25, "3": 1.6, "4": 2.2, "5": 3.0, "6": 4.5},   # dice in a group of equal faces
    "combo_straight": 2.0,          # 1-2-3-4-5-6 in one shake: whole shake x2
    "combo_all_same": 4.0,          # all dice equal (3+ dice): whole shake x4
    "collection_pct": 2,            # +2 % money for every discovered die
    "gauntlet_owned_pct": 2,        # +2 % money for every gauntlet you own
    "market_period": 30.0,          # crypto/stonks dice change their value every 30 s
    "money_cap": 1.0e300,
    "autosave_seconds": 30.0,
    "max_discount_pct": 80,
    "event_every": 300.0,           # a random event every 5 minutes (seconds of play time)
    "events": {                     # random event -> how long it lasts (seconds)
        "shop_sale": 30.0,          # shop and black market 50 % cheaper
        "talent_sale": 30.0,        # talents 50 % cheaper (talent points and money)
        "lucky_sale": 30.0,         # Lucky Cube 50 % cheaper
        "tarot_sale": 30.0,         # tarot draws 50 % cheaper
        "money_rush": 10.0,         # shakes pay x5
        "turbo": 30.0,              # auto-shake 1 s faster, the dice land faster
    },
}

# Gumball machine: money -> talent points. The ball colour shows how many points it holds.
GUMBALL = {
    "base": 25.0,
    "growth": 1.32,
    "colors": [  # ball sprite index, talent points, base weight
        {"ball": 5, "tp": 1, "weight": 40.0, "name": "white"},
        {"ball": 3, "tp": 2, "weight": 28.0, "name": "green"},
        {"ball": 2, "tp": 3, "weight": 17.0, "name": "blue"},
        {"ball": 1, "tp": 5, "weight": 10.0, "name": "yellow"},
        {"ball": 4, "tp": 8, "weight": 4.0, "name": "pink"},
        {"ball": 0, "tp": 13, "weight": 1.0, "name": "red"},
    ],
}

# Lucky Cube: reroll your dice into new ones (levels stay). 5 roll buttons from cheap to expensive.
# odds = chance in % for common, uncommon, rare, epic, legendary
LUCKY = {
    "tiers": [
        {"base": 30.0, "growth": 1.06, "odds": [100, 0, 0, 0, 0]},
        {"base": 5000.0, "growth": 1.08, "odds": [50, 40, 10, 0, 0]},
        {"base": 2000000.0, "growth": 1.10, "odds": [15, 35, 35, 13, 2]},
        {"base": 8000000000.0, "growth": 1.12, "odds": [3, 12, 35, 38, 12]},
        {"base": 20000000000000.0, "growth": 1.15, "odds": [0, 3, 15, 37, 45]},
    ],
}

TAROT_DRAW = {"base": 2000.0, "growth": 1.33, "choices": 3, "max_copies": 4}

# ------------------------------------------------------------------------------------------------
# Dice: (id, art, rarity, pay per pip, effect, params, faces or None for 1-6)
# art "x" = Dice Rush Extended art res://bdr/art/dice/<id>.png, anything else is a vanilla path
# ------------------------------------------------------------------------------------------------
V = "res://assets/dice/"
VANILLA_ART = {
    "50_50": "res://assets/art/магаизн 5050.png", "d4": V + "d4.png", "3x4": V + "three_by_four.png",
    "d2": V + "d_squared.png", "777": V + "dice_777.png", "prehistoric": V + "prehistoric.png",
    "golden": V + "golden.png", "npc_die": V + "npc_die.png", "crypto": V + "crypto.png",
    "diamond": V + "diamond.png", "pi": V + "pi.png",
}

DICE = [
    # ---- common (30) ----
    ("wood", "common", 1.0, "none", {}, None),
    ("50_50", "common", 1.0, "gamble", {"chance": 50, "mult": 3}, None),
    ("d4", "common", 1.1, "high", {"face": 4, "mult": 2}, [1, 2, 3, 4]),
    ("pepe", "common", 0.8, "ones", {"mult": 8}, None),
    ("sixseven", "common", 0.55, "pair", {"pct": 20}, [6, 7, 6, 7, 6, 7]),
    ("paper", "common", 0.9, "quick", {"pct": 4}, None),
    ("clover", "common", 0.75, "crit", {"chance": 7, "mult": 7}, None),
    ("dnd", "common", 0.25, "d20", {"mult": 5}, list(range(1, 21))),
    ("candy", "common", 0.9, "aura", {"pct": 4}, None),
    ("bubble", "common", 0.95, "pair", {"pct": 25}, None),
    ("cookie", "common", 0.9, "streak", {"step": 1, "max": 30}, None),
    ("snail", "common", 0.5, "every", {"n": 10, "mult": 12}, None),
    ("stone", "common", 1.25, "none", {}, None),
    ("twitch", "common", 0.8, "streak", {"step": 2, "max": 40}, None),
    ("youtube", "common", 0.85, "xp", {"pct": 5}, None),
    ("pirate", "common", 0.9, "jackpot", {"chance": 1, "mult": 10}, None),
    ("console", "common", 0.9, "combo", {"pct": 15}, None),
    ("slot", "common", 0.85, "jackpot", {"chance": 2, "mult": 7}, None),
    ("ice", "common", 0.75, "even", {"mult": 1.6}, None),
    ("fire", "common", 0.7, "high", {"face": 5, "mult": 1.8}, None),
    ("bunny", "common", 0.85, "tp_luck", {"pct": 5}, None),
    ("donut", "common", 0.75, "odd", {"mult": 1.8}, None),
    ("tetris", "common", 0.85, "per_die", {"pct": 3}, None),
    ("vault", "common", 0.5, "every", {"n": 25, "mult": 30}, None),
    ("zombie", "common", 0.8, "grow", {"step": 2, "max": 60}, None),
    ("ghost", "common", 0.9, "echo", {"chance": 2}, None),
    ("stonks", "common", 0.7, "market", {"min": 0.5, "max": 2.5}, None),
    ("pizza", "common", 0.6, "every", {"n": 8, "mult": 8}, None),
    ("robot", "common", 0.85, "auto", {"pct": 6}, None),
    ("luckyblock", "common", 0.85, "cheap_lucky", {"pct": 4}, None),
    # ---- uncommon (25) ----
    ("3x4", "uncommon", 3.5, "pair", {"pct": 15}, [3, 4, 3, 4, 3, 4]),
    ("d2", "uncommon", 4.2, "crit", {"chance": 10, "mult": 10}, [1, 2]),
    ("godot", "uncommon", 3.03, "xp", {"pct": 8}, None),
    ("ruby", "uncommon", 3.97, "none", {}, None),
    ("car", "uncommon", 3.03, "quick", {"pct": 6}, None),
    ("knight", "uncommon", 3.03, "aura", {"pct": 8}, None),
    ("roulette", "uncommon", 2.1, "crit", {"chance": 2.7, "mult": 36}, None),
    ("bomb", "uncommon", 1.47, "bomb", {"mult": 6}, None),
    ("sushi", "uncommon", 3.03, "share", {"pct": 1.5}, None),
    ("dragon", "uncommon", 2.8, "high", {"face": 5, "mult": 2.2}, None),
    ("magic8", "uncommon", 3.03, "meteor", {"chance": 2}, None),
    ("owl", "uncommon", 2.8, "xp", {"pct": 10}, None),
    ("wizard", "uncommon", 3.03, "cheap_tarot", {"pct": 6}, None),
    ("sapphire", "uncommon", 4.2, "none", {}, None),
    ("rocket", "uncommon", 3.03, "auto", {"pct": 10}, None),
    ("doge", "uncommon", 2.8, "gamble", {"chance": 60, "mult": 2.2}, None),
    ("viking", "uncommon", 3.03, "combo", {"pct": 25}, None),
    ("troll", "uncommon", 2.33, "ones", {"mult": 10}, None),
    ("burger", "uncommon", 3.03, "per_die", {"pct": 4}, None),
    ("ninja", "uncommon", 2.8, "quick", {"pct": 8}, None),
    ("domino", "uncommon", 2.8, "streak", {"step": 3, "max": 60}, None),
    ("comet", "uncommon", 2.22, "every", {"n": 7, "mult": 7}, None),
    ("vampire", "uncommon", 2.8, "swallow", {"mult": 3}, None),
    ("emerald", "uncommon", 4.43, "none", {}, None),
    ("pumpkin", "uncommon", 2.57, "grow", {"step": 3, "max": 90}, None),
    # ---- rare (20) ----
    ("777", "rare", 9.6, "seven", {"mult": 3}, None),
    ("prehistoric", "rare", 10.6, "echo", {"chance": 6}, None),
    ("npc_die", "rare", 10.1, "teacher", {"xp": 3}, None),
    ("sus", "rare", 10.6, "copy", {"pct": 15}, None),
    ("rickroll", "rare", 5.28, "every", {"n": 13, "mult": 20}, None),
    ("moon", "rare", 7.68, "even", {"mult": 2}, None),
    ("gigachad", "rare", 7.2, "max", {}, None),
    ("samurai", "rare", 7.44, "crit", {"chance": 12, "mult": 6}, None),
    ("treasure", "rare", 11.0, "tp_luck", {"pct": 10}, None),
    ("thisisfine", "rare", 8.16, "grow", {"step": 4, "max": 120}, None),
    ("amethyst", "rare", 12.5, "none", {}, None),
    ("ufo", "rare", 10.1, "rarity_aura", {"rarity": "common", "pct": 50}, None),
    ("skibidi", "rare", 10.1, "auto", {"pct": 15}, None),
    ("witch", "rare", 10.6, "cheap_tarot", {"pct": 10}, None),
    ("sigma", "rare", 6.72, "per_level", {"pct": 2}, None),
    ("bee", "rare", 10.6, "pair", {"pct": 30}, None),
    ("aura", "rare", 10.1, "aura", {"pct": 12}, None),
    ("train", "rare", 10.1, "per_die", {"pct": 5}, None),
    ("quantum", "rare", 11.0, "wild", {}, None),
    ("skeleton", "rare", 6.48, "high", {"face": 6, "mult": 4}, None),
    # ---- epic (15) ----
    ("golden", "epic", 36.8, "share", {"pct": 5}, None),
    ("crypto", "epic", 21.0, "market", {"min": 0.2, "max": 4.0}, None),
    ("platinum", "epic", 45.2, "none", {}, None),
    ("bonk", "epic", 22.1, "crit", {"chance": 15, "mult": 8}, None),
    ("bank", "epic", 15.8, "every", {"n": 20, "mult": 40}, None),
    ("mahjong", "epic", 37.8, "combo", {"pct": 40}, None),
    ("ohio", "epic", 30.5, "gamble", {"chance": 33, "mult": 4.5}, None),
    ("blackhole", "epic", 36.8, "swallow", {"mult": 5}, None),
    ("phoenix", "epic", 37.8, "echo", {"chance": 10}, None),
    ("fox", "epic", 37.8, "copy", {"pct": 30}, None),
    ("lava", "epic", 20.5, "high", {"face": 4, "mult": 2.5}, None),
    ("obsidian", "epic", 47.2, "none", {}, None),
    ("meteor", "epic", 37.8, "meteor", {"chance": 5}, None),
    ("jackpot", "epic", 36.8, "jackpot", {"chance": 4, "mult": 10}, None),
    ("timedie", "epic", 38.9, "quick", {"pct": 12}, None),
    # ---- legendary (10) ----
    ("diamond", "legendary", 68.0, "crit", {"chance": 20, "mult": 10}, None),
    ("pi", "legendary", 38.0, "pi", {"mult": 3.14}, [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9]),
    ("galaxy", "legendary", 130.0, "per_rarity", {"pct": 25}, None),
    ("crown", "legendary", 140.0, "rarity_aura", {"rarity": "legendary", "pct": 40}, None),
    ("mithril", "legendary", 180.0, "none", {}, None),
    ("divine", "legendary", 140.0, "global", {"pct": 15}, None),
    ("architect", "legendary", 130.0, "per_die", {"pct": 8}, None),
    ("ascension", "legendary", 90.0, "per_level", {"pct": 3}, None),
    ("infinity", "legendary", 100.0, "grow", {"step": 5, "max": 300}, None),
    ("cosmic", "legendary", 140.0, "share", {"pct": 10}, None),
]

# Effect descriptions (die effects). {rarity} is replaced by the rarity name.
FX_TEXT = {
    "none": ("A solid classic: pays its face.", "Ein solider Klassiker: zahlt seine Augenzahl."),
    "gamble": ("{chance}% chance to pay x{mult}, otherwise nothing.", "{chance}% Chance auf x{mult}, sonst nichts."),
    "high": ("A {face} or more pays x{mult}.", "Eine {face} oder mehr zahlt x{mult}."),
    "ones": ("A rolled 1 pays x{mult}.", "Eine gewürfelte 1 zahlt x{mult}."),
    "pair": ("+{pct}% for every other die with the same face.", "+{pct}% für jeden anderen Würfel mit gleicher Augenzahl."),
    "quick": ("Shakes are {pct}% faster.", "Schütteln geht {pct}% schneller."),
    "crit": ("{chance}% chance to pay x{mult}.", "{chance}% Chance auf x{mult}."),
    "d20": ("Rolls 1 to 20. A natural 20 pays x{mult}.", "Würfelt 1 bis 20. Eine 20 zahlt x{mult}."),
    "aura": ("All other dice pay +{pct}%.", "Alle anderen Würfel zahlen +{pct}%."),
    "streak": ("+{step}% for every shake in a row (max +{max}%).", "+{step}% für jedes Schütteln am Stück (max. +{max}%)."),
    "every": ("Every {n}th shake it pays x{mult}.", "Jedes {n}. Schütteln zahlt er x{mult}."),
    "xp": ("All dice gain +{pct}% XP.", "Alle Würfel bekommen +{pct}% EP."),
    "jackpot": ("{chance}% chance: the whole shake pays x{mult}.", "{chance}% Chance: das ganze Schütteln zahlt x{mult}."),
    "combo": ("Combos pay +{pct}% more.", "Kombos zahlen +{pct}% mehr."),
    "even": ("Even faces pay x{mult}.", "Gerade Augenzahlen zahlen x{mult}."),
    "odd": ("Odd faces pay x{mult}.", "Ungerade Augenzahlen zahlen x{mult}."),
    "tp_luck": ("Gumballs give +{pct}% talent points.", "Kaugummis geben +{pct}% Talentpunkte."),
    "per_die": ("+{pct}% for every die in the glass ball.", "+{pct}% für jeden Würfel in der Glaskugel."),
    "grow": ("+{step}% per shake (max +{max}%). A 1 resets it.", "+{step}% pro Schütteln (max. +{max}%). Eine 1 setzt zurück."),
    "echo": ("{chance}% chance to pay the whole shake again.", "{chance}% Chance, das ganze Schütteln nochmal zu zahlen."),
    "market": ("Its value changes every 30 s: x{min} to x{max}.", "Sein Wert ändert sich alle 30 s: x{min} bis x{max}."),
    "auto": ("Auto-shake is {pct}% faster.", "Auto-Schütteln ist {pct}% schneller."),
    "cheap_lucky": ("Lucky Cube rolls cost {pct}% less.", "Glückswürfel-Würfe kosten {pct}% weniger."),
    "bomb": ("A 6 pays x{mult}, a 1 pays nothing.", "Eine 6 zahlt x{mult}, eine 1 zahlt nichts."),
    "share": ("Adds {pct}% of the whole shake.", "Gibt {pct}% des ganzen Schüttelns dazu."),
    "meteor": ("{chance}% chance: all dice roll their highest face.", "{chance}% Chance: alle Würfel zeigen ihre höchste Zahl."),
    "cheap_tarot": ("Tarot draws cost {pct}% less.", "Tarot-Ziehungen kosten {pct}% weniger."),
    "swallow": ("Swallows the weakest die's payout and pays it x{mult}.", "Schluckt den schwächsten Würfel und zahlt ihn x{mult}."),
    "seven": ("If all faces add up to a multiple of 7, the whole shake pays x{mult}.", "Ist die Summe aller Augen durch 7 teilbar, zahlt das ganze Schütteln x{mult}."),
    "teacher": ("Gives the lowest-level die +{xp} XP every shake.", "Gibt dem Würfel mit dem niedrigsten Level +{xp} EP pro Schütteln."),
    "copy": ("Adds {pct}% of the best other die.", "Gibt {pct}% des besten anderen Würfels dazu."),
    "max": ("Always rolls its highest face.", "Würfelt immer seine höchste Zahl."),
    "rarity_aura": ("{rarity} dice pay +{pct}%.", "{rarity}-Würfel zahlen +{pct}%."),
    "per_level": ("+{pct}% for each of its levels.", "+{pct}% für jedes seiner Level."),
    "wild": ("Joker: counts as any face for combos.", "Joker: zählt bei Kombos als jede Zahl."),
    "global": ("All dice, itself too, pay +{pct}%.", "Alle Würfel, auch er selbst, zahlen +{pct}%."),
    "pi": ("Rolls the digits of pi in order and pays x{mult}.", "Würfelt die Ziffern von Pi der Reihe nach und zahlt x{mult}."),
    "per_rarity": ("+{pct}% for every different rarity in the ball.", "+{pct}% für jede verschiedene Seltenheit in der Kugel."),
}

# ------------------------------------------------------------------------------------------------
# Stats: every bonus in the game is one of these. kind: "add" = values are added up,
# "mul" = values are multiplied, "max" = the biggest value wins.
# ------------------------------------------------------------------------------------------------
STATS = {
    "money_pct": ("add", "Money +{v}%", "Geld +{v}%"),
    "money_x": ("mul", "Money x{v}", "Geld x{v}"),
    "manual_pct": ("add", "Your own shakes pay +{v}%", "Eigenes Schütteln zahlt +{v}%"),
    "xp_pct": ("add", "XP +{v}%", "EP +{v}%"),
    "xp_x": ("mul", "XP x{v}", "EP x{v}"),
    "combo_pct": ("add", "Combos +{v}%", "Kombos +{v}%"),
    "combo_x": ("mul", "Combos x{v}", "Kombos x{v}"),
    "crit_chance": ("add", "Critical shake chance +{v}%", "Kritisches Schütteln +{v}% Chance"),
    "crit_mult": ("add", "Critical shake multiplier +{v} (base x3)", "Multiplikator für kritisches Schütteln +{v} (Basis x3)"),
    "speed_pct": ("add", "Shakes {v}% faster", "Schütteln {v}% schneller"),
    "auto_pct": ("add", "Auto-shake {v}% faster", "Auto-Schütteln {v}% schneller"),
    "auto_x": ("mul", "Auto-shake x{v} speed", "Auto-Schütteln x{v} Tempo"),
    "auto_every": ("min", "Shakes by itself every {v} s", "Schüttelt von selbst alle {v} s"),
    "echo_chance": ("add", "{v}% chance to pay a shake twice", "{v}% Chance, ein Schütteln doppelt zu zahlen"),
    "double_chance": ("add", "{v}% chance to double a shake", "{v}% Chance, ein Schütteln zu verdoppeln"),
    "common_pct": ("add", "Common dice +{v}%", "Gewöhnliche Würfel +{v}%"),
    "uncommon_pct": ("add", "Uncommon dice +{v}%", "Ungewöhnliche Würfel +{v}%"),
    "rare_pct": ("add", "Rare dice +{v}%", "Seltene Würfel +{v}%"),
    "epic_pct": ("add", "Epic dice +{v}%", "Epische Würfel +{v}%"),
    "legendary_pct": ("add", "Legendary dice +{v}%", "Legendäre Würfel +{v}%"),
    "common_x": ("mul", "Common dice x{v}", "Gewöhnliche Würfel x{v}"),
    "uncommon_x": ("mul", "Uncommon dice x{v}", "Ungewöhnliche Würfel x{v}"),
    "rare_x": ("mul", "Rare dice x{v}", "Seltene Würfel x{v}"),
    "epic_x": ("mul", "Epic dice x{v}", "Epische Würfel x{v}"),
    "legendary_x": ("mul", "Legendary dice x{v}", "Legendäre Würfel x{v}"),
    "six_x": ("mul", "Sixes pay x{v}", "Sechsen zahlen x{v}"),
    "min_face": ("max", "Every die rolls at least a {v}", "Jeder Würfel zeigt mindestens eine {v}"),
    "ones_as_six": ("max", "Ones count as sixes", "Einsen zählen als Sechsen"),
    "best_pct": ("add", "Your best die pays +{v}% extra", "Dein bester Würfel zahlt +{v}% extra"),
    "bell_x": ("mul", "Every 10th shake pays x{v}", "Jedes 10. Schütteln zahlt x{v}"),
    "treasure_n": ("add", "Every 25th shake: a treasure worth {v} shakes", "Jedes 25. Schütteln: ein Schatz im Wert von {v} Schüttel-Runden"),
    "coin_chance": ("add", "{v}% chance per shake for a coin bag worth 20 shakes", "{v}% Chance pro Schütteln auf einen Geldbeutel im Wert von 20 Schüttel-Runden"),
    "lucky_discount": ("add", "Lucky Cube {v}% cheaper", "Glückswürfel {v}% billiger"),
    "lucky_odds": ("add", "Lucky Cube: +{v}% chance for Epic and Legendary", "Glückswürfel: +{v}% Chance auf Episch und Legendär"),
    "reroll_levels": ("add", "Rerolled dice gain +{v} levels", "Neu gewürfelte Würfel bekommen +{v} Level"),
    "tarot_discount": ("add", "Tarot draws {v}% cheaper", "Tarot-Ziehungen {v}% billiger"),
    "tarot_choices": ("add", "+{v} card to choose from", "+{v} Karte zur Auswahl"),
    "gumball_discount": ("add", "Gumballs {v}% cheaper", "Kaugummis {v}% billiger"),
    "gumball_luck": ("add", "Better gumballs (+{v}% luck)", "Bessere Kaugummis (+{v}% Glück)"),
    "gumball_slow": ("add", "Gumball prices grow {v}% slower", "Kaugummi-Preise steigen {v}% langsamer"),
    "tp_pct": ("add", "+{v}% talent points from gumballs", "+{v}% Talentpunkte aus Kaugummis"),
    "tp_extra": ("add", "+{v} talent points per gumball", "+{v} Talentpunkte pro Kaugummi"),
    "double_ball": ("add", "{v}% chance for a second gumball", "{v}% Chance auf einen zweiten Kaugummi"),
    "talent_discount": ("add", "Talents cost {v}% less money", "Talente kosten {v}% weniger Geld"),
    "shop_discount": ("add", "Shop {v}% cheaper", "Shop {v}% billiger"),
    "black_discount": ("add", "Black market {v}% cheaper", "Schwarzmarkt {v}% billiger"),
    "xp_need_pct": ("add", "Dice need {v}% less XP", "Würfel brauchen {v}% weniger EP"),
    "catchup_x": ("mul", "The lowest-level die gets x{v} XP", "Der Würfel mit dem niedrigsten Level bekommt x{v} EP"),
    "black_market": ("max", "Unlocks the black market in the shop", "Schaltet den Schwarzmarkt im Shop frei"),
    "slots": ("add", "+{v} die in the glass ball", "+{v} Würfel in der Glaskugel"),
    "compact": ("max", "Dice shrink so up to 12 fit into the ball", "Würfel schrumpfen, damit bis zu 12 in die Kugel passen"),
}

# ------------------------------------------------------------------------------------------------
# 30 fortune tarot cards: values for 1, 2, 3, 4 copies (common, rare, epic, legendary)
# ------------------------------------------------------------------------------------------------
TAROT_RANKS = ["common", "rare", "epic", "legendary"]
TAROT = [
    ("crystal_ball", "The Crystal Ball", "Die Kristallkugel", [("money_pct", [20, 45, 80, 130])]),
    ("candle", "The Candle", "Die Kerze", [("auto_pct", [10, 20, 35, 50])]),
    ("raven", "The Raven", "Der Rabe", [("combo_pct", [10, 22, 36, 55])]),
    ("moon_moth", "The Moon Moth", "Die Mondmotte", [("xp_pct", [15, 35, 60, 100])]),
    ("open_hand", "The Open Hand", "Die Offene Hand", [("manual_pct", [20, 45, 80, 130])]),
    ("third_eye", "The Third Eye", "Das Dritte Auge", [("crit_chance", [1, 2, 3.5, 5])]),
    ("key", "The Key", "Der Schlüssel", [("lucky_discount", [5, 10, 15, 20])]),
    ("hourglass", "The Hourglass", "Die Sanduhr", [("speed_pct", [4, 8, 13, 20])]),
    ("serpent", "The Serpent", "Die Schlange", [("money_x", [1.05, 1.1, 1.17, 1.25])]),
    ("mask", "The Mask", "Die Maske", [("gumball_discount", [5, 10, 15, 20])]),
    ("lantern", "The Lantern", "Die Laterne", [("common_pct", [25, 55, 90, 140]), ("uncommon_pct", [25, 55, 90, 140])]),
    ("crown", "The Crown", "Die Krone", [("legendary_pct", [15, 35, 60, 100])]),
    ("chalice", "The Chalice", "Der Kelch", [("epic_pct", [20, 45, 75, 120])]),
    ("coin", "The Coin", "Die Münze", [("coin_chance", [0.5, 1, 1.5, 2.5])]),
    ("star", "The Star", "Der Stern", [("rare_pct", [25, 55, 90, 140])]),
    ("comet", "The Comet", "Der Komet", [("echo_chance", [0.5, 1, 2, 3])]),
    ("tower", "The Tower", "Der Turm", [("crit_mult", [0.25, 0.5, 0.75, 1.0])]),
    ("wheel", "The Wheel", "Das Rad", [("lucky_odds", [8, 18, 30, 45])]),
    ("feather", "The Feather", "Die Feder", [("catchup_x", [1.5, 2, 3, 4])]),
    ("anchor", "The Anchor", "Der Anker", [("money_x", [1.05, 1.12, 1.2, 1.3])]),
    ("mirror", "The Mirror", "Der Spiegel", [("best_pct", [10, 25, 45, 70])]),
    ("bell", "The Bell", "Die Glocke", [("bell_x", [1.5, 2, 3, 4])]),
    ("lotus", "The Lotus", "Der Lotus", [("xp_need_pct", [3, 6, 10, 15])]),
    ("dagger", "The Dagger", "Der Dolch", [("six_x", [1.15, 1.3, 1.5, 1.8])]),
    ("cauldron", "The Cauldron", "Der Kessel", [("tarot_discount", [5, 10, 15, 20])]),
    ("owl", "The Owl", "Die Eule", [("talent_discount", [5, 10, 15, 25])]),
    ("sun", "The Sun", "Die Sonne", [("money_pct", [15, 35, 60, 100])]),
    ("spider", "The Spider", "Die Spinne", [("gumball_luck", [8, 16, 26, 40])]),
    ("fox", "The Fox", "Der Fuchs", [("shop_discount", [4, 8, 12, 16]), ("black_discount", [4, 8, 12, 16])]),
    ("phoenix", "The Phoenix", "Der Phönix", [("double_chance", [1, 2, 3.5, 5])]),
]

# ------------------------------------------------------------------------------------------------
# 30 black market cards: price of the first copy, price growth per copy, max copies,
# effects per copy (add stats add up, mul stats multiply per copy)
# ------------------------------------------------------------------------------------------------
BLACK = [
    ("loaded_dice", "Loaded Dice", "Gezinkte Würfel", 0, 30, 3, [("min_face", "copies+1")]),
    ("counterfeit", "Counterfeit Money", "Falschgeld", 0, 12, 5, [("money_x", 1.25)]),
    ("rigged_shaker", "Rigged Shaker", "Manipulierte Kugel", 0, 12, 4, [("speed_pct", 8)]),
    ("smuggled_gumballs", "Smuggled Gumballs", "Geschmuggelte Kaugummis", 0, 25, 3, [("tp_extra", 1)]),
    ("forged_diploma", "Forged Diploma", "Gefälschtes Diplom", 0, 12, 4, [("xp_pct", 75)]),
    ("pickpocket", "Pickpocket", "Taschendieb", 0, 10, 5, [("coin_chance", 0.5)]),
    ("insider_tip", "Insider Tip", "Insidertipp", 0, 12, 5, [("lucky_odds", 15)]),
    ("bribed_croupier", "Bribed Croupier", "Bestochener Croupier", 0, 14, 4, [("combo_pct", 25)]),
    ("cursed_idol", "Cursed Idol", "Verfluchtes Götzenbild", 0, 25, 3, [("money_x", 1.5), ("xp_pct", -10)]),
    ("weighted_coin", "Weighted Coin", "Gezinkte Münze", 0, 15, 3, [("crit_chance", 2)]),
    ("black_cat_bone", "Black Cat Bone", "Knochen der schwarzen Katze", 0, 15, 5, [("echo_chance", 1)]),
    ("snake_oil", "Snake Oil", "Schlangenöl", 0, 12, 3, [("auto_pct", 25)]),
    ("fake_crown", "Fake Crown", "Falsche Krone", 0, 20, 3, [("legendary_pct", 60)]),
    ("stolen_lantern", "Stolen Lantern", "Gestohlene Laterne", 0, 15, 3, [("common_pct", 80), ("uncommon_pct", 60)]),
    ("marked_cards", "Marked Cards", "Markierte Karten", 0, 40, 2, [("tarot_choices", 1), ("tarot_discount", 10)]),
    ("hot_dice", "Hot Dice", "Heiße Würfel", 0, 15, 4, [("six_x", 1.25)]),
    ("ghost_hand", "Ghost Hand", "Geisterhand", 0, 15, 3, [("auto_pct", 30)]),
    ("mirror_trick", "Mirror Trick", "Spiegeltrick", 0, 1, 1, [("best_pct", 100)]),
    ("shadow_ledger", "Shadow Ledger", "Schattenbuch", 0, 15, 4, [("talent_discount", 10)]),
    ("silver_tongue", "Silver Tongue", "Silberzunge", 0, 15, 3, [("shop_discount", 8), ("black_discount", 8)]),
    ("crooked_scale", "Crooked Scale", "Krumme Waage", 0, 20, 3, [("gumball_slow", 2)]),
    ("smoke_lamp", "Smoke Lamp", "Rauchlampe", 0, 1, 1, [("ones_as_six", 1)]),
    ("grave_dust", "Grave Dust", "Grabstaub", 0, 15, 4, [("xp_need_pct", 5)]),
    ("voodoo_doll", "Voodoo Doll", "Voodoo-Puppe", 0, 20, 3, [("crit_mult", 0.5)]),
    ("smugglers_map", "Smuggler's Map", "Schmugglerkarte", 0, 15, 4, [("treasure_n", 8)]),
    ("poisoned_ring", "Poisoned Ring", "Giftring", 0, 20, 3, [("epic_pct", 60)]),
    ("phantom_coin", "Phantom Coin", "Phantommünze", 0, 15, 5, [("double_chance", 2)]),
    ("underworld_pass", "Underworld Pass", "Unterwelt-Pass", 0, 20, 5, [("reroll_levels", 1)]),
    ("devils_deal", "Devil's Deal", "Teufelspakt", 0, 100, 2, [("money_x", 2.0)]),
    ("skeleton_key", "Skeleton Key", "Dietrich", 0, 20, 4, [("lucky_discount", 8), ("rare_pct", 60)]),
]

# ------------------------------------------------------------------------------------------------
# 30 gauntlets (mouse cursors). price, effects while equipped. Every owned gauntlet also gives
# BALANCE["gauntlet_owned_pct"] % money.
# ------------------------------------------------------------------------------------------------
GAUNTLETS = [
    ("Leather Glove", "Lederhandschuh", 0, [("manual_pct", 25)]),
    ("Wool Mitten", "Wollfäustling", 0, [("xp_pct", 25)]),
    ("Iron Gauntlet", "Eisenhandschuh", 0, [("crit_chance", 2)]),
    ("Bronze Gauntlet", "Bronzehandschuh", 0, [("combo_pct", 20)]),
    ("Silver Gauntlet", "Silberhandschuh", 0, [("money_pct", 50)]),
    ("Golden Gauntlet", "Goldhandschuh", 0, [("money_pct", 80)]),
    ("Crystal Gauntlet", "Kristallhandschuh", 0, [("lucky_discount", 15), ("money_pct", 50)]),
    ("Ruby Gauntlet", "Rubinhandschuh", 0, [("common_pct", 100), ("uncommon_pct", 100)]),
    ("Emerald Gauntlet", "Smaragdhandschuh", 0, [("xp_pct", 80), ("money_pct", 60)]),
    ("Sapphire Gauntlet", "Saphirhandschuh", 0, [("rare_pct", 120)]),
    ("Obsidian Gauntlet", "Obsidianhandschuh", 0, [("crit_chance", 4), ("crit_mult", 0.5)]),
    ("Bone Hand", "Knochenhand", 0, [("tp_pct", 20), ("money_pct", 100)]),
    ("Thief's Glove", "Diebeshandschuh", 0, [("shop_discount", 12), ("black_discount", 12), ("money_pct", 120)]),
    ("Wizard's Glove", "Zaubererhandschuh", 0, [("tarot_discount", 20), ("money_pct", 140)]),
    ("Fortune Teller's Hand", "Hand der Wahrsagerin", 0, [("combo_pct", 60), ("money_pct", 150)]),
    ("Knight's Gauntlet", "Ritterhandschuh", 0, [("money_pct", 300)]),
    ("Samurai Gauntlet", "Samuraihandschuh", 0, [("speed_pct", 25), ("money_pct", 250)]),
    ("Frost Gauntlet", "Frosthandschuh", 0, [("auto_pct", 60), ("money_pct", 250)]),
    ("Flame Gauntlet", "Flammenhandschuh", 0, [("six_x", 1.5), ("money_pct", 300)]),
    ("Storm Gauntlet", "Sturmhandschuh", 0, [("echo_chance", 4), ("money_pct", 350)]),
    ("Nature Glove", "Naturhandschuh", 0, [("xp_pct", 200), ("money_pct", 350)]),
    ("Cosmic Gauntlet", "Kosmischer Handschuh", 0, [("epic_pct", 200), ("money_pct", 400)]),
    ("Shadow Glove", "Schattenhandschuh", 0, [("crit_chance", 6), ("money_pct", 450)]),
    ("Royal Glove", "Königshandschuh", 0, [("legendary_pct", 200), ("money_pct", 450)]),
    ("Clockwork Gauntlet", "Uhrwerkhandschuh", 0, [("auto_pct", 100), ("speed_pct", 15), ("money_pct", 500)]),
    ("Pirate Glove", "Piratenhandschuh", 0, [("treasure_n", 30), ("money_pct", 550)]),
    ("Dragon Claw", "Drachenklaue", 0, [("money_pct", 1000)]),
    ("Angel Gauntlet", "Engelshandschuh", 0, [("xp_pct", 300), ("money_pct", 800)]),
    ("Demon Claw", "Dämonenklaue", 0, [("money_x", 2), ("xp_pct", -50)]),
    ("Diamond Gauntlet", "Diamanthandschuh", 0, [("money_x", 1.5), ("money_pct", 1000), ("combo_pct", 50), ("crit_chance", 5)]),
]

# 20 table designs (cloth + cushion), cosmetic only. id 0 is free and owned from the start.
TABLES = [
    ("Royal Purple", "Königslila"), ("Midnight Blue", "Mitternachtsblau"), ("Crimson Velvet", "Purpursamt"),
    ("Emerald Silk", "Smaragdseide"), ("Golden Sun", "Goldene Sonne"), ("Black Lace", "Schwarze Spitze"),
    ("Rose Garden", "Rosengarten"), ("Ocean Wave", "Meereswelle"), ("Forest Moss", "Waldmoos"),
    ("Lavender Stars", "Lavendelsterne"), ("Moon Phases", "Mondphasen"), ("Desert Sand", "Wüstensand"),
    ("Frozen Lake", "Gefrorener See"), ("Ember", "Glut"), ("Candy Pink", "Bonbonrosa"),
    ("Galaxy Swirl", "Galaxiewirbel"), ("Chess Board", "Schachbrett"), ("Rune Circle", "Runenkreis"),
    ("Tarot Tapestry", "Tarot-Teppich"), ("Peacock", "Pfau"),
]
TABLE_PRICE_BASE = 1000.0   # table designs are looks only: cheap
TABLE_PRICE_GROWTH = 6.0


# ------------------------------------------------------------------------------------------------
# Talent tree on an 11 x 7 grid (column 0-10, row 0-6). "parents" = ANY of them must be owned.
# Slot nodes ("slot" in the effects) cost SLOT_COSTS[number of dice after buying] instead of their
# own price, so the 7th die always costs the same, whichever "Extra Die" node is bought first.
# icon: "die:<id>", "tarot:<id>", "black:<id>", "gum", "cube"
# ------------------------------------------------------------------------------------------------
SLOT_COSTS = {  # dice after buying -> (talent points, money)
    2: (1, 50), 3: (2, 1000), 4: (3, 15000), 5: (4, 150000), 6: (6, 2e+06),
    7: (8, 3e+07), 8: (10, 3e+09), 9: (12, 3e+11), 10: (14, 3e+13), 11: (17, 3e+15), 12: (20, 3e+17),
}

TALENTS = [
    # id, col, row, parents, tp, money, effects, icon, EN, DE
    ("shaker", 5, 0, [], 0, 0, [], "die:wood", "The Glass Ball", "Die Glaskugel"),
    # centre: more dice
    ("slot2", 5, 1, ["shaker"], 0, 0, [("slots", 1)], "die:stone", "Second Die", "Zweiter Würfel"),
    ("slot3", 5, 2, ["slot2"], 0, 0, [("slots", 1)], "die:ruby", "Third Die", "Dritter Würfel"),
    ("slot4", 5, 3, ["slot3"], 0, 0, [("slots", 1)], "die:sapphire", "Fourth Die", "Vierter Würfel"),
    ("slot5", 5, 4, ["slot4"], 0, 0, [("slots", 1)], "die:emerald", "Fifth Die", "Fünfter Würfel"),
    ("slot6", 5, 5, ["slot5"], 0, 0, [("slots", 1)], "die:amethyst", "Sixth Die", "Sechster Würfel"),
    ("compact", 5, 6, ["slot6"], 8, 5e+07, [("compact", 1)], "die:quantum", "Compact Dice", "Kompakte Würfel"),
    ("extra1", 4, 6, ["compact"], 0, 0, [("slots", 1)], "die:platinum", "Extra Die I", "Extra-Würfel I"),
    ("extra2", 3, 6, ["extra1"], 0, 0, [("slots", 1)], "die:obsidian", "Extra Die II", "Extra-Würfel II"),
    ("extra3", 2, 6, ["extra2"], 0, 0, [("slots", 1)], "die:mithril", "Extra Die III", "Extra-Würfel III"),
    ("extra4", 6, 6, ["compact"], 0, 0, [("slots", 1)], "die:galaxy", "Extra Die IV", "Extra-Würfel IV"),
    ("extra5", 7, 6, ["extra4"], 0, 0, [("slots", 1)], "die:divine", "Extra Die V", "Extra-Würfel V"),
    ("extra6", 8, 6, ["extra5"], 0, 0, [("slots", 1)], "die:cosmic", "Extra Die VI", "Extra-Würfel VI"),
    # left: money, combos, critical shakes, gumballs, black market
    ("fortune1", 4, 1, ["shaker"], 1, 0, [("money_pct", 25)], "tarot:crystal_ball", "Fortune I", "Vermögen I"),
    ("fortune2", 3, 1, ["fortune1"], 3, 5000, [("money_pct", 50)], "tarot:crystal_ball", "Fortune II", "Vermögen II"),
    ("fortune3", 2, 1, ["fortune2"], 6, 5e+06, [("money_pct", 100)], "tarot:crystal_ball", "Fortune III", "Vermögen III"),
    ("fortune4", 1, 1, ["fortune3"], 10, 1.6e+11, [("money_pct", 200)], "tarot:coin", "Fortune IV", "Vermögen IV"),
    ("fortune5", 0, 1, ["fortune4"], 15, 3.2e+15, [("money_pct", 400)], "tarot:coin", "Fortune V", "Vermögen V"),
    ("touch", 4, 2, ["fortune1", "slot3"], 3, 2000, [("manual_pct", 50)], "tarot:open_hand", "Golden Touch", "Goldene Berührung"),
    ("combo1", 3, 2, ["touch"], 2, 0, [("combo_pct", 20)], "tarot:raven", "Pair Up", "Paarweise"),
    ("combo2", 2, 2, ["combo1"], 6, 5e+06, [("combo_pct", 40)], "tarot:serpent", "Full House", "Full House"),
    ("combo3", 1, 2, ["combo2"], 12, 6.4e+13, [("combo_pct", 80)], "tarot:serpent", "Royal Flush", "Royal Flush"),
    ("crit1", 4, 3, ["touch", "slot4"], 3, 0, [("crit_chance", 3)], "tarot:third_eye", "Lucky Strike", "Glückstreffer"),
    ("crit2", 3, 3, ["crit1"], 6, 3e+07, [("crit_chance", 4)], "tarot:third_eye", "Lucky Strike II", "Glückstreffer II"),
    ("crit3", 2, 3, ["crit2"], 8, 2e+10, [("crit_mult", 1)], "tarot:dagger", "Heavy Hit", "Wuchtiger Treffer"),
    ("echo", 1, 3, ["crit3"], 10, 4e+11, [("echo_chance", 2)], "tarot:comet", "Déjà Vu", "Déjà-vu"),
    ("gum1", 4, 4, ["crit1", "slot5"], 1, 0, [("gumball_discount", 20)], "gum", "Sticky Fingers", "Klebrige Finger"),
    ("gum2", 3, 4, ["gum1"], 4, 500000, [("gumball_luck", 35)], "gum", "Lucky Gumballs", "Glückskaugummis"),
    ("gum3", 2, 4, ["gum2"], 8, 1e+08, [("double_ball", 15)], "gum", "Double Gumball", "Doppelter Kaugummi"),
    ("gum4", 1, 4, ["gum3"], 12, 7.9e+12, [("gumball_luck", 35)], "gum", "Lucky Gumballs II", "Glückskaugummis II"),
    ("gum5", 0, 4, ["gum4"], 18, 7.8e+15, [("gumball_slow", 3)], "gum", "Bubble Gum Factory", "Kaugummifabrik"),
    ("black1", 4, 5, ["gum1", "slot6"], 15, 2e+10, [("black_market", 1)], "black:skeleton_key", "Black Market Contact", "Schwarzmarkt-Kontakt"),
    ("black2", 3, 5, ["black1"], 20, 2.6e+16, [("black_discount", 25)], "black:shadow_ledger", "Smuggler Ties", "Schmuggler-Kontakte"),
    # right: speed, experience, auto-shake, lucky cube, tarot
    ("quick1", 6, 1, ["shaker"], 1, 0, [("speed_pct", 12)], "tarot:hourglass", "Quick Wrist I", "Flinkes Handgelenk I"),
    ("quick2", 7, 1, ["quick1"], 4, 200000, [("speed_pct", 12)], "tarot:hourglass", "Quick Wrist II", "Flinkes Handgelenk II"),
    ("quick3", 8, 1, ["quick2"], 9, 2.5e+09, [("speed_pct", 16)], "tarot:hourglass", "Quick Wrist III", "Flinkes Handgelenk III"),
    ("xp1", 6, 2, ["quick1", "slot3"], 1, 0, [("xp_pct", 30)], "tarot:moon_moth", "Practice", "Übung"),
    ("xp2", 7, 2, ["xp1"], 4, 100000, [("xp_pct", 60)], "tarot:moon_moth", "Training", "Training"),
    ("mentor", 8, 2, ["xp2"], 5, 0, [("catchup_x", 3)], "tarot:feather", "Mentor", "Mentor"),
    ("xp3", 9, 2, ["mentor"], 8, 2e+08, [("xp_pct", 120)], "tarot:lotus", "Mastery", "Meisterschaft"),
    ("xp4", 10, 2, ["xp3"], 14, 3.2e+12, [("xp_pct", 250)], "tarot:lotus", "Grandmaster", "Großmeister"),
    ("auto1", 6, 3, ["xp1", "slot4"], 3, 10000, [("auto_every", 6)], "tarot:candle", "Auto Shaker", "Auto-Schüttler"),
    ("auto2", 7, 3, ["auto1"], 6, 2e+06, [("auto_every", 4)], "tarot:candle", "Auto Shaker II", "Auto-Schüttler II"),
    ("auto3", 8, 3, ["auto2"], 10, 8.1e+09, [("auto_every", 2.5)], "tarot:candle", "Auto Shaker III", "Auto-Schüttler III"),
    ("auto4", 9, 3, ["auto3"], 15, 1.6e+14, [("auto_every", 1.5)], "tarot:candle", "Perpetual Motion", "Perpetuum mobile"),
    ("lucky1", 6, 4, ["auto1", "slot5"], 2, 0, [("lucky_discount", 15)], "cube", "Lucky Fingers", "Glücksfinger"),
    ("lucky2", 7, 4, ["lucky1"], 8, 5e+08, [("lucky_odds", 30)], "tarot:wheel", "Loaded Cube", "Gezinkter Würfel"),
    ("lucky3", 8, 4, ["lucky2"], 10, 3.2e+12, [("lucky_discount", 20)], "cube", "Lucky Fingers II", "Glücksfinger II"),
    ("heirloom", 9, 4, ["lucky3"], 12, 1.3e+15, [("reroll_levels", 1)], "tarot:key", "Heirloom", "Erbstück"),
    ("tarot1", 6, 5, ["lucky1", "slot6"], 3, 0, [("tarot_discount", 15)], "tarot:cauldron", "Fortune's Favour", "Gunst des Schicksals"),
    ("tarot2", 7, 5, ["tarot1"], 8, 1e+09, [("tarot_choices", 1)], "tarot:mirror", "Fourth Card", "Vierte Karte"),
    ("tarot3", 8, 5, ["tarot2"], 12, 7.9e+12, [("tarot_discount", 20)], "tarot:cauldron", "Fortune's Favour II", "Gunst des Schicksals II"),
]

# Price ladders (the n-th item costs base * growth^(n-1))
GAUNTLET_PRICE = {"base": 200.0, "growth": 3.5}
BLACK_PRICE = {"base": 5e10, "growth": 1.75}   # first copy of black market card n (list order)
