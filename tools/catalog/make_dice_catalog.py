"""Generates src/bdr/data/dice_catalog.json - the single source of truth for the
100 Dice Rush Extended dice (economy, mechanics, unlock path, art description,
English + German texts). Other languages are produced by the translation step.
"""
import json, os
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

K = 10**3; M = 10**6; B = 10**9; T = 10**12; Q15 = 10**15; Q18 = 10**18

D = []  # list of dice


def die(id, tier, unlock, price, en, de, desc_en, desc_de, mech="faces", faces=(1, 2, 3, 4, 5, 6), pay=1,
        unlock_price=0, npc=True, p=None, art=None, family="misc"):
    D.append({
        "id": id, "tier": tier, "family": family, "unlock": unlock, "price": price,
        "unlock_price": unlock_price, "npc": npc, "mech": mech, "faces": list(faces), "pay": pay,
        "p": p or {}, "name": {"en": en, "de": de}, "desc": {"en": desc_en, "de": desc_de},
        "art": art or {},
    })


def art(top, left, right, glyphs, ink="#ffffff", pattern="none", edge=None, special="", outline="#14101c", rivets=True):
    return {"top": top, "left": left, "right": right, "edge": edge or "#ffffff", "ink": ink,
            "pattern": pattern, "glyphs": glyphs, "special": special, "outline": outline, "rivets": rivets}

# ---------------------------------------------------------------- TIER 1
die("wood", 1, "shop", 1500, "Wooden Dice", "Holzwürfel",
    "Pays {pay}$ times the rolled face.", "Zahlt {pay}$ mal die gewürfelte Augenzahl.",
    pay=10, unlock_price=3000, family="material",
    art=art("#c8904f", "#9a6532", "#7a4c22", ["pip:1", "pip:2", "pip:3"], ink="#3b2210", pattern="wood", edge="#e8b878"))
die("pepe", 1, "shop", 2500, "Pepe Dice", "Pepe-Würfel",
    "Four frog faces pay {pay}$. 'Feels good man' pays x10, the sad frog pays nothing. Sometimes it hops again on its own.",
    "Vier Froschgesichter zahlen {pay}$. „Feels good man“ zahlt x10, der traurige Frosch nichts. Manchmal hüpft er von selbst nochmal.",
    mech="pepe", faces=(1, 1, 1, 1, 10, 0), pay=50, unlock_price=5000, p={"hop_chance": 0.12}, family="meme",
    art=art("#6dbb45", "#4f9a2f", "#3c7a22", ["icon:frog", "icon:frog_smug", "icon:frog"], ink="#1d3a10", pattern="dots", edge="#a8e07a"))
die("sixseven", 1, "shop", 4000, "67 Dice", "67-Würfel",
    "Faces 6 and 7 pay {pay}$ each pip. The 67 face pays 67 pips. A 6 followed by a 7 on the same dice pays x6.7!",
    "Seiten 6 und 7 zahlen {pay}$ pro Auge. Die 67-Seite zählt 67. Eine 6 gefolgt von einer 7 auf demselben Würfel zahlt x6,7!",
    mech="sixseven", faces=(6, 7, 6, 7, 6, 67), pay=4, unlock_price=6700, family="meme",
    art=art("#ff9a3c", "#e0701f", "#b85414", ["num:67", "num:6", "num:7"], ink="#ffffff", pattern="stripes", edge="#ffd08a"))
die("paper", 1, "talent", 2000, "Paper Dice", "Papierwürfel",
    "Light as paper: rolls 2.5x faster. Pays {pay}$ times the face.", "Leicht wie Papier: würfelt 2,5x schneller. Zahlt {pay}$ mal die Augenzahl.",
    mech="fast", pay=8, p={"speed": 2.5}, family="material",
    art=art("#f4f1e6", "#d9d4c2", "#bfb9a3", ["pip:1", "pip:4", "pip:6"], ink="#3d5a8a", pattern="grid", edge="#ffffff"))
die("clover", 1, "lucky", 6000, "Clover Dice", "Kleeblattwürfel",
    "Five faces pay {pay}x3$. The four-leaf clover pays seven times as much.", "Fünf Seiten zahlen {pay}x3$. Das vierblättrige Kleeblatt zahlt das Siebenfache.",
    faces=(3, 3, 3, 3, 3, 21), pay=10, family="luck",
    art=art("#2fa85a", "#22864a", "#186a3a", ["icon:clover", "num:3", "icon:clover"], ink="#e8ffe0", pattern="dots", edge="#7fe0a0"))
die("dnd", 1, "shop", 7500, "D20 Dungeon Dice", "D20-Dungeon-Würfel",
    "A real D20: pays {pay}$ per pip. Natural 20 is a critical hit (x20), natural 1 a critical fail (0$).",
    "Ein echter W20: zahlt {pay}$ pro Auge. Eine natürliche 20 ist ein kritischer Treffer (x20), die 1 ein Patzer (0$).",
    mech="dnd", faces=list(range(1, 21)), pay=6, unlock_price=12000, family="adventure",
    art=art("#8a2be2", "#6a1fb4", "#4f168a", ["num:20", "num:1", "icon:d20"], ink="#ffe27a", pattern="gem", edge="#c58cff"))
die("candy", 1, "shop", 9000, "Candy Dice", "Bonbonwürfel",
    "Pays {pay}$ per pip. Sugar rush: dice within {radius}px earn +{bonus}%.", "Zahlt {pay}$ pro Auge. Zuckerschock: Würfel im Umkreis von {radius}px verdienen +{bonus}%.",
    mech="aura", faces=(2, 2, 3, 3, 4, 4), pay=25, unlock_price=15000, p={"radius": 120, "bonus": 15}, family="food",
    art=art("#ff7ac8", "#e655aa", "#c23d8c", ["icon:candy", "icon:candy", "icon:candy"], ink="#ffffff", pattern="stripes", edge="#ffc2e8"))
die("bubble", 1, "talent", 5000, "Bubble Dice", "Seifenblasenwürfel",
    "Pays {pay}$ per pip and pops when it lands, rolling up to {count} neighbours.", "Zahlt {pay}$ pro Auge und platzt beim Landen – bis zu {count} Nachbarn würfeln mit.",
    mech="neighbors", pay=15, p={"radius": 130, "count": 2}, family="element",
    art=art("#9ee8ff", "#6ccfee", "#45b2d8", ["icon:bubble", "pip:2", "icon:bubble"], ink="#ffffff", pattern="dots", edge="#e0fbff"))
die("cookie", 1, "shop", 12000, "Cookie Dice", "Keks-Würfel",
    "Pays {pay}$ per pip. Rolls you trigger yourself (click or hover) pay x{mult}.", "Zahlt {pay}$ pro Auge. Würfe, die du selbst auslöst (Klick oder Hover), zahlen x{mult}.",
    mech="clicker", pay=25, unlock_price=20000, p={"mult": 5}, family="food",
    art=art("#d9a05b", "#b8803f", "#94632b", ["icon:cookie", "icon:cookie", "icon:cookie"], ink="#4a2a12", pattern="dots", edge="#f2c98c"))
die("snail", 1, "shop", 15000, "Snail Dice", "Schneckenwürfel",
    "Very slow (rolls take 3x longer) but pays {pay}$ per pip.", "Sehr langsam (Würfe dauern 3x länger), zahlt aber {pay}$ pro Auge.",
    mech="slow", faces=(6, 6, 6, 6, 6, 12), pay=60, unlock_price=25000, p={"slow": 3.0}, family="animal",
    art=art("#e8c86a", "#c9a748", "#a8862f", ["icon:snail", "num:6", "icon:shell"], ink="#5a3a12", pattern="swirl", edge="#fff0a8"))

# ---------------------------------------------------------------- TIER 2
die("stone", 2, "shop", 80 * K, "Stone Dice", "Steinwürfel",
    "Heavy and reliable: pays {pay}$ per pip.", "Schwer und zuverlässig: zahlt {pay}$ pro Auge.",
    faces=(5, 5, 5, 5, 5, 30), pay=200, unlock_price=160 * K, family="material",
    art=art("#9a9a9a", "#7c7c7c", "#5f5f5f", ["num:5", "num:5", "num:30"], ink="#2b2b2b", pattern="stone", edge="#c8c8c8"))
die("twitch", 2, "shop", 120 * K, "Stream Dice", "Twitch-Würfel",
    "Pays {pay}$ per pip plus 2$ per viewer. Every roll brings viewers; sometimes a RAID rolls 10 dice and pays x10.",
    "Zahlt {pay}$ pro Auge plus 2$ pro Zuschauer. Jeder Wurf bringt Zuschauer; manchmal würfelt ein RAID 10 Würfel und zahlt x10.",
    mech="twitch", pay=300, unlock_price=250 * K, p={"raid_chance": 0.02}, family="tech",
    art=art("#9146ff", "#7432e0", "#5a23b8", ["icon:chat", "icon:chat", "icon:live"], ink="#ffffff", pattern="none", edge="#c9a4ff"))
die("youtube", 2, "shop", 150 * K, "Video Dice", "YouTube-Würfel",
    "Pays {pay}$ per pip plus subscribers/10. Each roll gains subscribers; every milestone (100, 1K, 10K…) pays a play-button bonus.",
    "Zahlt {pay}$ pro Auge plus Abonnenten/10. Jeder Wurf bringt Abonnenten; jeder Meilenstein (100, 1K, 10K…) zahlt einen Play-Button-Bonus.",
    mech="youtube", pay=300, unlock_price=300 * K, family="tech",
    art=art("#ff2a2a", "#d81818", "#ad1010", ["icon:play", "icon:play", "icon:play"], ink="#ffffff", pattern="none", edge="#ff9a9a"))
die("pirate", 2, "shop", 180 * K, "Pirate Dice", "Piratenwürfel",
    "Coins pay {pay}x3$, the skull pays nothing, the chest pays x10 and the parrot rolls a neighbour. Plunders 3% of nearby payouts.",
    "Münzen zahlen {pay}x3$, der Totenkopf nichts, die Truhe x10 und der Papagei würfelt einen Nachbarn. Plündert 3% der Auszahlungen in der Nähe.",
    mech="pirate", faces=(3, 3, 3, 0, 4, 30), pay=500, unlock_price=360 * K, p={"plunder": 3, "radius": 150}, family="adventure",
    art=art("#3d2b1f", "#2c1f16", "#20160f", ["icon:skull", "icon:coin", "icon:chest"], ink="#f2d16b", pattern="wood", edge="#8a6a4a"))
die("console", 2, "shop", 220 * K, "Console Dice", "Konsolen-Würfel",
    "Pays {pay}$ per pip. Rolled again within 4 seconds the combo rises (up to x{maxmult}).", "Zahlt {pay}$ pro Auge. Innerhalb von 4 Sekunden erneut gewürfelt steigt die Kombo (bis x{maxmult}).",
    mech="combo", pay=600, unlock_price=450 * K, p={"window": 4.0, "step": 0.25, "max": 10, "maxmult": 3.5}, family="tech",
    art=art("#3a3f4b", "#2b2f38", "#1e2128", ["icon:gamepad", "icon:btn_a", "icon:btn_b"], ink="#5ff5c8", pattern="grid", edge="#7c8494"))
die("slot", 2, "shop", 260 * K, "Slot Machine Dice", "Spielautomat-Würfel",
    "Spins three reels: 7-7-7 pays x77, three of a kind x10, a pair x2. Base {pay}$.", "Dreht drei Walzen: 7-7-7 zahlt x77, drei Gleiche x10, ein Paar x2. Basis {pay}$.",
    mech="slot", pay=1000, unlock_price=520 * K, family="casino",
    art=art("#e8c02a", "#c99a14", "#a07a0c", ["icon:seven", "icon:cherry", "icon:bell"], ink="#c01818", pattern="stripes", edge="#fff08a"))
die("ice", 2, "talent", 100 * K, "Ice Dice", "Eiswürfel",
    "Pays {pay}$ per pip and freezes dice within {radius}px: their next payout is doubled.", "Zahlt {pay}$ pro Auge und friert Würfel im Umkreis von {radius}px ein: ihre nächste Auszahlung verdoppelt sich.",
    mech="freeze", pay=350, p={"radius": 140, "mult": 2}, family="element",
    art=art("#bfefff", "#8fd8f5", "#62bde6", ["icon:snowflake", "icon:snowflake", "icon:snowflake"], ink="#ffffff", pattern="gem", edge="#ffffff"))
die("fire", 2, "talent", 140 * K, "Fire Dice", "Feuerwürfel",
    "Pays {pay}$ per pip and sets the table on fire: dice within {radius}px roll too (max {count}).", "Zahlt {pay}$ pro Auge und setzt den Tisch in Brand: Würfel im Umkreis von {radius}px würfeln mit (max. {count}).",
    mech="neighbors", pay=400, p={"radius": 110, "count": 6}, family="element",
    art=art("#ff6a1f", "#e04a10", "#b8350a", ["icon:flame", "icon:flame", "icon:flame"], ink="#ffe25a", pattern="none", edge="#ffb070"))
die("bunny", 2, "lucky", 200 * K, "Bunny Dice", "Hasenwürfel",
    "Pays {pay}$ per pip. Bunnies multiply: every {every} bunny rolls a new bunny is born (max {max}).", "Zahlt {pay}$ pro Auge. Hasen vermehren sich: alle {every} Hasenwürfe kommt ein neuer Hase dazu (max. {max}).",
    mech="breeder", faces=(2, 2, 2, 4, 4, 8), pay=700, p={"every": 25, "max": 200}, family="animal",
    art=art("#f4f4f4", "#d8d8d8", "#bcbcbc", ["icon:bunny", "icon:carrot", "icon:bunny"], ink="#ff8fb8", pattern="none", edge="#ffffff", special="ears_bunny"))
die("donut", 2, "tarot", 300 * K, "Donut Dice", "Donut-Würfel",
    "Pays {pay}$ per pip. Face 1 collects a sprinkle; with 6 sprinkles the next donut roll pays x36.", "Zahlt {pay}$ pro Auge. Seite 1 sammelt Streusel; mit 6 Streuseln zahlt der nächste Donut-Wurf x36.",
    mech="donut", pay=900, family="food",
    art=art("#f2a7c8", "#d887ac", "#b86a8e", ["icon:donut", "icon:donut", "icon:donut"], ink="#7a4a2a", pattern="dots", edge="#ffd6e8"))

# ---------------------------------------------------------------- TIER 3
die("godot", 3, "talent", 6 * M, "Godot Dice", "Godot-Würfel",
    "Node tree: pays {pay}$ per pip for every dice type you own. A 6 emits a signal that rolls all other Godot dice.",
    "Node-Baum: zahlt {pay}$ pro Auge für jede Würfelart, die du besitzt. Eine 6 sendet ein Signal, das alle anderen Godot-Würfel würfeln lässt.",
    mech="godot", pay=3000, family="tech",
    art=art("#478cbf", "#3a76a3", "#2c5d82", ["icon:robot_head", "icon:robot_head", "icon:gear"], ink="#ffffff", pattern="none", edge="#9cc8ec"))
die("tetris", 3, "talent", 8 * M, "Block Dice", "Tetris-Würfel",
    "Each roll drops a block. 10 blocks clear a line (all block dice pay x10). Four lines in 30 s: TETRIS (x100)!",
    "Jeder Wurf lässt einen Block fallen. 10 Blöcke räumen eine Reihe (alle Block-Würfel zahlen x10). Vier Reihen in 30 s: TETRIS (x100)!",
    mech="tetris", pay=120 * K, family="tech",
    art=art("#2ad1ff", "#ffd21f", "#ff4fa0", ["icon:tetro_t", "icon:tetro_l", "icon:tetro_s"], ink="#ffffff", pattern="bricks", edge="#ffffff"))
die("vault", 3, "shop", 10 * M, "Vault Dice", "Tresor-Würfel",
    "Pays half of {pay}$ per pip and locks the other half in the vault. Every {every} rolls the vault opens and pays its content x{mult}.",
    "Zahlt die Hälfte von {pay}$ pro Auge und schließt die andere Hälfte im Tresor ein. Alle {every} Würfe öffnet sich der Tresor und zahlt den Inhalt x{mult}.",
    mech="vault", pay=80 * K, unlock_price=20 * M, p={"every": 20, "mult": 3}, family="adventure",
    art=art("#6b7280", "#555b66", "#40454e", ["icon:vault", "icon:dial", "icon:vault"], ink="#ffd66b", pattern="metal", edge="#a8afba"))
die("luckyblock", 3, "lucky", 12 * M, "Lucky Block Dice", "Lucky-Block-Würfel",
    "Every landing opens the block: coins, jackpots, Lucky Cube levels, a dice rain, sometimes even talent gold – or an explosion!",
    "Jede Landung öffnet den Block: Münzen, Jackpots, Glückswürfel-Stufen, ein Würfelregen, manchmal sogar Talent-Gold – oder eine Explosion!",
    mech="luckyblock", faces=(1,), pay=150 * K, family="luck",
    art=art("#ffd23a", "#e8b01c", "#c48c0c", ["icon:question", "icon:question", "icon:question"], ink="#ffffff", pattern="none", edge="#fff2a0"))
die("zombie", 3, "tarot", 9 * M, "Zombie Dice", "Zombie-Würfel",
    "Pays {pay}$ per pip. Bites: {chance}% chance to turn a nearby 50/50 or D4 into another zombie (max {max}).",
    "Zahlt {pay}$ pro Auge. Beißt: {chance}% Chance, einen nahen 50/50- oder D4-Würfel in einen Zombie zu verwandeln (max. {max}).",
    mech="zombie", pay=100 * K, p={"chance": 8, "radius": 160, "max": 300}, family="spooky",
    art=art("#7fae5a", "#628f43", "#4a7032", ["icon:zombie", "icon:hand", "icon:zombie"], ink="#2a1a1a", pattern="noise", edge="#b2d88f"))
die("lightning", 3, "shop", 14 * M, "Lightning Dice", "Blitzwürfel",
    "Pays {pay}$ per pip and strikes {count} random dice anywhere on the table.", "Zahlt {pay}$ pro Auge und trifft {count} zufällige Würfel irgendwo auf dem Tisch.",
    mech="lightning", pay=120 * K, unlock_price=28 * M, p={"count": 3}, family="element",
    art=art("#3a3f8f", "#2c3070", "#1f2252", ["icon:bolt", "icon:bolt", "icon:cloud"], ink="#fff35a", pattern="none", edge="#8f96ff"))
die("ghost", 3, "shop", 16 * M, "Ghost Dice", "Geisterwürfel",
    "Pays {pay}$ per pip, then haunts a random spot of the table and scares 2 dice into rolling.", "Zahlt {pay}$ pro Auge, spukt dann an einer zufälligen Stelle und erschreckt 2 Würfel.",
    mech="ghost", pay=130 * K, unlock_price=32 * M, p={"count": 2}, family="spooky",
    art=art("#e9ecff", "#c9cdf0", "#a8addb", ["icon:ghost", "icon:ghost", "icon:boo"], ink="#3a3a5a", pattern="none", edge="#ffffff"))
die("stonks", 3, "shop", 18 * M, "Stonks Dice", "Stonks-Würfel",
    "Pays {pay}$ per pip times the Stonks market (x0.5 to x20). The market updates every 45 s and mostly goes up.",
    "Zahlt {pay}$ pro Auge mal dem Stonks-Kurs (x0,5 bis x20). Der Kurs ändert sich alle 45 s und steigt meistens.",
    mech="stonks", pay=150 * K, unlock_price=36 * M, family="meme",
    art=art("#1f3b73", "#172d58", "#10203e", ["icon:arrow_up", "icon:chart", "icon:arrow_up"], ink="#33ff7a", pattern="grid", edge="#5f86d6"))
die("pizza", 3, "shop", 20 * M, "Pizza Dice", "Pizzawürfel",
    "Pays {pay}$ per pip. Every 8th pizza roll is a pizza party: x8!", "Zahlt {pay}$ pro Auge. Jeder 8. Pizza-Wurf ist eine Pizzaparty: x8!",
    mech="every_n", pay=160 * K, unlock_price=40 * M, p={"every": 8, "mult": 8}, family="food",
    art=art("#ffcf5a", "#e8a83a", "#c4842a", ["icon:pizza", "icon:pizza", "icon:pizza"], ink="#c83a1a", pattern="dots", edge="#fff0a0"))
die("robot", 3, "shop", 25 * M, "Robot Dice", "Roboterwürfel",
    "Rolls itself every {interval} s – no worker needed. Pays {pay}$ per pip.", "Würfelt sich alle {interval} s selbst – kein Arbeiter nötig. Zahlt {pay}$ pro Auge.",
    mech="auto", pay=180 * K, unlock_price=50 * M, p={"interval": 2.5}, npc=False, family="tech",
    art=art("#b8c4d0", "#95a3b2", "#748394", ["icon:robot", "icon:bolt_small", "icon:robot"], ink="#ff4a4a", pattern="metal", edge="#e0e8f0"))

# ---------------------------------------------------------------- TIER 4
die("ruby", 4, "shop", 300 * M, "Ruby Dice", "Rubinwürfel",
    "A polished gem: pays {pay}$ per pip.", "Ein geschliffener Edelstein: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=2500 * K, unlock_price=600 * M, family="material",
    art=art("#ff3a5c", "#d81c40", "#a8102e", ["icon:gem", "num:10", "icon:gem"], ink="#ffe0e8", pattern="gem", edge="#ffb0c0"))
die("car", 4, "shop", 450 * M, "Racing Car Dice", "Auto-Würfel",
    "Drives in a straight line until it hits the wall. Every dice in its way rolls. Hitting the wall pays {pay}$ (+2% per dice hit) and sometimes a gold coin.",
    "Fährt geradeaus, bis er gegen die Wand fährt. Jeder Würfel im Weg würfelt. Der Aufprall zahlt {pay}$ (+2% pro getroffenem Würfel) und manchmal eine Goldmünze.",
    mech="car", faces=(1,), pay=20 * M, unlock_price=900 * M, p={"speed": 620, "width": 46, "gold_chance": 0.02}, family="vehicle",
    art=art("#e8261c", "#c41a12", "#9a120c", ["icon:car", "icon:wheel", "icon:wheel"], ink="#ffffff", pattern="stripes", edge="#ff8a80", special="spoiler"))
die("knight", 4, "shop", 500 * M, "Knight Dice", "Ritterwürfel",
    "Pays {pay}$ per pip. Its shield protects dice within {radius}px: +{bonus}% payout.", "Zahlt {pay}$ pro Auge. Sein Schild schützt Würfel im Umkreis von {radius}px: +{bonus}% Auszahlung.",
    mech="aura", pay=3 * M, unlock_price=1 * B, p={"radius": 160, "bonus": 25}, family="adventure",
    art=art("#c0c6d0", "#9aa2ae", "#76808e", ["icon:shield", "icon:sword", "icon:shield"], ink="#c8102e", pattern="metal", edge="#ffffff"))
die("roulette", 4, "shop", 550 * M, "Roulette Dice", "Roulettewürfel",
    "37 pockets: green zero pays x36, red pays x2, black x1. Base {pay}$.", "37 Fächer: die grüne Null zahlt x36, Rot x2, Schwarz x1. Basis {pay}$.",
    mech="roulette", faces=list(range(0, 37)), pay=4 * M, unlock_price=1100 * M, family="casino",
    art=art("#1a8f3a", "#c81e1e", "#1b1b1b", ["icon:wheel_roulette", "num:0", "num:36"], ink="#ffffff", pattern="none", edge="#7fe09a"))
die("bomb", 4, "shop", 600 * M, "Bomb Dice", "Bombenwürfel",
    "Counts down 3-2-1. On zero: BOOM – all dice within {radius}px roll and it pays x10. Base {pay}$.",
    "Zählt 3-2-1 herunter. Bei Null: BUMM – alle Würfel im Umkreis von {radius}px würfeln und er zahlt x10. Basis {pay}$.",
    mech="bomb", faces=(3, 2, 1), pay=6 * M, unlock_price=1200 * M, p={"radius": 220, "count": 30, "mult": 10}, family="element",
    art=art("#2b2b33", "#1f1f26", "#141419", ["icon:bomb", "num:3", "icon:fuse"], ink="#ff5a2a", pattern="none", edge="#6a6a7a"))
die("sushi", 4, "shop", 700 * M, "Sushi Dice", "Sushi-Würfel",
    "Pays {pay}$ per pip, +25% for every other food dice type you own.", "Zahlt {pay}$ pro Auge, +25% für jede andere Essens-Würfelart, die du besitzt.",
    mech="food", pay=3 * M, unlock_price=1400 * M, family="food",
    art=art("#f4f4ec", "#2b3a2a", "#ff7a5a", ["icon:sushi", "icon:nori", "icon:salmon"], ink="#1b1b1b", pattern="none", edge="#ffffff"))
die("dragon", 4, "talent", 800 * M, "Dragon Dice", "Drachenwürfel",
    "Pays {pay}$ per pip and breathes fire in a {radius}px cone – everything in it rolls (max {count}).", "Zahlt {pay}$ pro Auge und speit Feuer in einem {radius}px-Kegel – alles darin würfelt (max. {count}).",
    mech="cone", pay=4 * M, p={"radius": 300, "count": 25, "mult": 1}, family="animal",
    art=art("#2e9a4e", "#227a3c", "#185a2b", ["icon:dragon", "icon:flame", "icon:scales"], ink="#ffd23a", pattern="scales", edge="#7fe0a0", special="horns"))
die("magic8", 4, "talent", 900 * M, "Magic 8-Ball Dice", "Magische-8-Ball-Würfel",
    "YES: dice within {radius}px get double payout on their next roll. NO: nothing. ASK AGAIN: rolls itself again. Base {pay}$.",
    "JA: Würfel im Umkreis von {radius}px bekommen beim nächsten Wurf doppelte Auszahlung. NEIN: nichts. FRAG SPÄTER: würfelt sich erneut. Basis {pay}$.",
    mech="magic8", faces=(1, 0, 2, 1, 0, 1), pay=8 * M, p={"radius": 250}, family="casino",
    art=art("#1b1b22", "#121217", "#0a0a0d", ["num:8", "icon:triangle", "num:8"], ink="#ffffff", pattern="none", edge="#4a4a5a"))
die("owl", 4, "lucky", 1 * B, "Owl Dice", "Eulenwürfel",
    "Wise: pays {pay}$ per pip, +2% for every unlocked achievement.", "Weise: zahlt {pay}$ pro Auge, +2% für jede freigeschaltete Errungenschaft.",
    mech="owl", pay=3 * M, family="animal",
    art=art("#8a6a4a", "#6e5238", "#543d28", ["icon:owl", "icon:feather", "icon:owl"], ink="#ffd23a", pattern="scales", edge="#c8a47a", special="ears_owl"))
die("wizard", 4, "tarot", 1200 * M, "Wizard Dice", "Zaubererwürfel",
    "Pays {pay}$ per pip and enchants a random dice: its next roll pays x10.", "Zahlt {pay}$ pro Auge und verzaubert einen zufälligen Würfel: sein nächster Wurf zahlt x10.",
    mech="enchant", pay=5 * M, p={"mult": 10}, family="adventure",
    art=art("#3a2a8a", "#2c1f6e", "#1f1552", ["icon:hat", "icon:star", "icon:wand"], ink="#ffd23a", pattern="stars", edge="#8a7aff"))

# ---------------------------------------------------------------- TIER 5
die("sapphire", 5, "shop", 20 * B, "Sapphire Dice", "Saphirwürfel",
    "A flawless gem: pays {pay}$ per pip.", "Ein makelloser Edelstein: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=150 * M, unlock_price=40 * B, family="material",
    art=art("#2a6aff", "#1a50d8", "#103aa8", ["icon:gem", "num:10", "icon:gem"], ink="#dfe8ff", pattern="gem", edge="#8ab0ff"))
die("rocket", 5, "shop", 30 * B, "Rocket Dice", "Raketenwürfel",
    "Launches into the sky and crashes down somewhere else: the shockwave rolls dice within {radius}px. Pays {pay}$.",
    "Startet in den Himmel und schlägt woanders ein: die Druckwelle lässt Würfel im Umkreis von {radius}px würfeln. Zahlt {pay}$.",
    mech="rocket", faces=(1,), pay=3 * B, unlock_price=60 * B, p={"radius": 200, "count": 30, "flight": 2.5}, family="vehicle",
    art=art("#e8e8f0", "#c8c8d4", "#a4a4b4", ["icon:rocket", "icon:flame", "icon:rocket"], ink="#e8261c", pattern="none", edge="#ffffff"))
die("doge", 5, "shop", 35 * B, "Doge Dice", "Doge-Würfel",
    "Much random, very wow: pays between x0.1 and x10 of {pay}$. 1% TO THE MOON pays x100.", "Viel Zufall, sehr wow: zahlt zwischen x0,1 und x10 von {pay}$. 1% TO THE MOON zahlt x100.",
    mech="doge", faces=(1,), pay=1 * B, unlock_price=70 * B, family="meme",
    art=art("#e8b45a", "#c9953e", "#a6772a", ["icon:doge", "icon:doge", "text:WOW"], ink="#3a2410", pattern="none", edge="#ffe0a0", special="ears_dog"))
die("viking", 5, "shop", 40 * B, "Viking Dice", "Wikingerwürfel",
    "Pays {pay}$ per pip. A 6 blows the war horn: all Viking dice roll (max {count}).", "Zahlt {pay}$ pro Auge. Eine 6 bläst das Kriegshorn: alle Wikingerwürfel würfeln (max. {count}).",
    mech="horn", pay=250 * M, unlock_price=80 * B, p={"count": 30}, family="adventure",
    art=art("#8a5a2a", "#6e4520", "#523316", ["icon:viking", "icon:axe", "icon:horn"], ink="#e8e8e8", pattern="wood", edge="#c89a6a", special="horns"))
die("troll", 5, "shop", 45 * B, "Troll Dice", "Trollface-Würfel",
    "Problem? 50% pays nothing, 50% pays {pay}$.", "Problem? 50% zahlt nichts, 50% zahlt {pay}$.",
    mech="troll", faces=(0, 1, 0, 1, 0, 1), pay=2 * B, unlock_price=90 * B, family="meme",
    art=art("#f2f2f2", "#d4d4d4", "#b4b4b4", ["icon:troll", "icon:troll", "text:?"], ink="#1b1b1b", pattern="none", edge="#ffffff"))
die("burger", 5, "shop", 50 * B, "Burger Dice", "Burger-Würfel",
    "Stacks up: every roll without a 1 adds +10% (up to +300%). Base {pay}$ per pip.", "Stapelt sich: jeder Wurf ohne 1 bringt +10% (bis +300%). Basis {pay}$ pro Auge.",
    mech="stack", pay=300 * M, unlock_price=100 * B, p={"step": 10, "max": 300}, family="food",
    art=art("#d98a3a", "#8a4a1f", "#4a9a2a", ["icon:burger", "icon:burger", "icon:burger"], ink="#ffe25a", pattern="none", edge="#ffc080"))
die("ninja", 5, "talent", 55 * B, "Ninja Dice", "Ninjawürfel",
    "Strikes in a flash (very fast roll) and throws shuriken at 2 distant dice. Pays {pay}$ per pip.", "Schlägt blitzschnell zu (sehr schneller Wurf) und wirft Shuriken auf 2 entfernte Würfel. Zahlt {pay}$ pro Auge.",
    mech="ninja", pay=300 * M, p={"count": 2, "speed": 3.0}, family="adventure",
    art=art("#22222a", "#18181e", "#0e0e12", ["icon:ninja", "icon:shuriken", "icon:shuriken"], ink="#e8261c", pattern="none", edge="#5a5a6a"))
die("domino", 5, "talent", 60 * B, "Domino Dice", "Domino-Würfel",
    "Topples the next Domino dice, which topples the next… Each step of the chain pays +5% more. Base {pay}$ per pip.", "Stößt den nächsten Domino-Würfel um, der den nächsten umstößt… Jeder Kettenschritt zahlt +5% mehr. Basis {pay}$ pro Auge.",
    mech="domino", pay=300 * M, p={"delay": 0.12, "step": 5}, family="casino",
    art=art("#f8f8f2", "#dcdcd2", "#bcbcb0", ["pip:5", "pip:3", "pip:6"], ink="#1b1b1b", pattern="none", edge="#ffffff"))
die("comet", 5, "lucky", 70 * B, "Comet Dice", "Kometenwürfel",
    "Streaks across the table – every dice along its tail rolls. Pays {pay}$ +3% per dice hit.", "Rast über den Tisch – jeder Würfel entlang seines Schweifs würfelt. Zahlt {pay}$ +3% pro getroffenem Würfel.",
    mech="comet", faces=(1,), pay=1500 * M, p={"width": 60, "count": 40}, family="cosmic",
    art=art("#5ad6ff", "#3ab0e0", "#2088b8", ["icon:comet", "icon:star", "icon:comet"], ink="#ffffff", pattern="stars", edge="#c0f0ff"))
die("vampire", 5, "tarot", 80 * B, "Vampire Dice", "Vampirwürfel",
    "Pays {pay}$ per pip and drains 10% of the last payouts of dice within {radius}px (they keep theirs).", "Zahlt {pay}$ pro Auge und saugt 10% der letzten Auszahlungen von Würfeln im Umkreis von {radius}px ab (sie behalten ihre).",
    mech="drain", pay=350 * M, p={"radius": 150, "percent": 10}, family="spooky",
    art=art("#5a0e1e", "#460a17", "#320710", ["icon:bat", "icon:fangs", "icon:bat"], ink="#ff2a4a", pattern="none", edge="#a8304a"))

# ---------------------------------------------------------------- TIER 6
die("emerald", 6, "shop", 1 * T, "Emerald Dice", "Smaragdwürfel",
    "A royal gem: pays {pay}$ per pip.", "Ein königlicher Edelstein: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=8 * B, unlock_price=2 * T, family="material",
    art=art("#1fd27a", "#14ae60", "#0c8a4a", ["icon:gem", "num:10", "icon:gem"], ink="#e0ffef", pattern="gem", edge="#90f5c0"))
die("sus", 6, "shop", 1500 * B, "Sus Dice", "Sus-Würfel",
    "Pays {pay}$ per pip. 10%: EMERGENCY MEETING – all dice within {radius}px roll. 5%: ejected, pays nothing.", "Zahlt {pay}$ pro Auge. 10%: NOTFALL-TREFFEN – alle Würfel im Umkreis von {radius}px würfeln. 5%: rausgeworfen, zahlt nichts.",
    mech="sus", pay=12 * B, unlock_price=3 * T, p={"radius": 250, "count": 40}, family="meme",
    art=art("#e8261c", "#c41a12", "#9a120c", ["icon:crewmate", "icon:crewmate", "icon:knife"], ink="#9ee8ff", pattern="none", edge="#ff8a80"))
die("nyan", 6, "shop", 2 * T, "Nyan Dice", "Nyan-Würfel",
    "Flies with a rainbow: every dice under its flight path rolls with +20%. Pays {pay}$ per pip.", "Fliegt mit einem Regenbogen: jeder Würfel unter seiner Flugbahn würfelt mit +20%. Zahlt {pay}$ pro Auge.",
    mech="trail", pay=14 * B, unlock_price=4 * T, p={"width": 50, "count": 25, "bonus": 20}, family="meme",
    art=art("#ffb0d8", "#ff4a4a", "#4a7aff", ["icon:nyan", "icon:rainbow", "icon:nyan"], ink="#3a3a3a", pattern="stars", edge="#ffe0f0"))
die("pumpkin", 6, "shop", 2500 * B, "Pumpkin Dice", "Kürbiswürfel",
    "Grows while it rests: +5% every 10 s since its last roll (up to x10). Workers leave it alone. Base {pay}$ per pip.", "Wächst in Ruhe: +5% alle 10 s seit dem letzten Wurf (bis x10). Arbeiter lassen ihn in Ruhe. Basis {pay}$ pro Auge.",
    mech="grow", pay=16 * B, unlock_price=5 * T, npc=False, family="spooky",
    art=art("#ff8a1f", "#e06a10", "#b8500a", ["icon:jackolantern", "icon:jackolantern", "icon:leaf"], ink="#ffe25a", pattern="stripes", edge="#ffc070"))
die("rickroll", 6, "shop", 3 * T, "Rickroll Dice", "Rickroll-Würfel",
    "Never gonna give you up: it never pays less than 3 pips. A 6 never lets you down: x6! Base {pay}$.", "Never gonna give you up: zahlt nie weniger als 3 Augen. Eine 6 lässt dich nie im Stich: x6! Basis {pay}$.",
    mech="rickroll", pay=20 * B, unlock_price=6 * T, family="meme",
    art=art("#2a2a2a", "#1e1e1e", "#141414", ["icon:mic", "icon:note", "icon:note"], ink="#ffd23a", pattern="none", edge="#6a6a6a"))
die("moon", 6, "shop", 3500 * B, "Moon Dice", "Mondwürfel",
    "Pays {pay}$ per pip – triple while any event is active.", "Zahlt {pay}$ pro Auge – dreifach, solange ein Ereignis aktiv ist.",
    mech="moon", pay=20 * B, unlock_price=7 * T, family="cosmic",
    art=art("#d8dce8", "#b4b8c8", "#8e92a4", ["icon:moon", "icon:crater", "icon:moon"], ink="#3a3e5a", pattern="noise", edge="#ffffff"))
die("gigachad", 6, "talent", 2 * T, "Gigachad Dice", "Gigachad-Würfel",
    "Always rolls a 6. No luck needed. Pays {pay}$ per pip.", "Würfelt immer eine 6. Glück braucht er nicht. Zahlt {pay}$ pro Auge.",
    mech="always_max", faces=(6,), pay=15 * B, family="meme",
    art=art("#9a9a9a", "#7a7a7a", "#5a5a5a", ["icon:chad", "pip:6", "icon:muscle"], ink="#ffffff", pattern="none", edge="#d0d0d0"))
die("samurai", 6, "talent", 4 * T, "Samurai Dice", "Samuraiwürfel",
    "Pays {pay}$ per pip. A 6 slices the table: every dice on its row rolls (max {count}).", "Zahlt {pay}$ pro Auge. Eine 6 zerschneidet den Tisch: jeder Würfel in seiner Reihe würfelt (max. {count}).",
    mech="slash", pay=22 * B, p={"width": 40, "count": 40}, family="adventure",
    art=art("#f2f2f2", "#c41a1a", "#1b1b1b", ["icon:katana", "icon:katana", "icon:sun_jp"], ink="#c41a1a", pattern="none", edge="#ffffff"))
die("treasure", 6, "lucky", 4500 * B, "Treasure Chest Dice", "Schatztruhen-Würfel",
    "Finds a key with 1/3 chance. With 3 keys the chest opens: x50! Otherwise pays {pay}$.", "Findet mit 1/3 Chance einen Schlüssel. Mit 3 Schlüsseln öffnet sich die Truhe: x50! Sonst zahlt sie {pay}$.",
    mech="keys", faces=(1,), pay=20 * B, p={"chance": 0.333, "keys": 3, "mult": 50}, family="adventure",
    art=art("#a8642a", "#8a4e1f", "#6a3a16", ["icon:chest", "icon:key", "icon:lock"], ink="#ffd23a", pattern="wood", edge="#e0a060"))
die("thisisfine", 6, "tarot", 5 * T, "This Is Fine Dice", "Alles-gut-Würfel",
    "Everything is on fire: ignites dice within {radius}px and earns +5% per dice currently rolling (up to x3). Base {pay}$ per pip.",
    "Alles brennt: entzündet Würfel im Umkreis von {radius}px und verdient +5% pro gerade rollendem Würfel (bis x3). Basis {pay}$ pro Auge.",
    mech="chaos", pay=25 * B, p={"radius": 180, "count": 20}, family="meme",
    art=art("#ffb43a", "#ff7a1f", "#e04a10", ["icon:dog_hat", "icon:flame", "icon:mug"], ink="#5a2a10", pattern="none", edge="#ffe0a0"))

# ---------------------------------------------------------------- TIER 7
die("amethyst", 7, "shop", 50 * T, "Amethyst Dice", "Amethystwürfel",
    "A mystic gem: pays {pay}$ per pip.", "Ein mystischer Edelstein: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=400 * B, unlock_price=100 * T, family="material",
    art=art("#b45aff", "#933ae0", "#7024b8", ["icon:gem", "num:10", "icon:gem"], ink="#f5e0ff", pattern="gem", edge="#e0b0ff"))
die("ufo", 7, "shop", 70 * T, "UFO Dice", "UFO-Würfel",
    "Pays {pay}$ per pip and abducts a random dice: it lands somewhere else and pays x3.", "Zahlt {pay}$ pro Auge und entführt einen zufälligen Würfel: er landet woanders und zahlt x3.",
    mech="ufo", pay=600 * B, unlock_price=140 * T, p={"mult": 3}, family="cosmic",
    art=art("#8ae0a0", "#6ac080", "#4a9a60", ["icon:ufo", "icon:alien", "icon:beam"], ink="#2a2a3a", pattern="none", edge="#c0ffd0"))
die("skibidi", 7, "shop", 90 * T, "Skibidi Dice", "Skibidi-Würfel",
    "Spins on its own every {interval} s. Each auto-spin adds +1% brainrot (up to +100%); your click resets it. Base {pay}$ per pip.",
    "Dreht sich alle {interval} s von selbst. Jede Selbstdrehung bringt +1% Brainrot (bis +100%); dein Klick setzt es zurück. Basis {pay}$ pro Auge.",
    mech="skibidi", pay=700 * B, unlock_price=180 * T, p={"interval": 1.5}, npc=False, family="meme",
    art=art("#e8f0f8", "#c8d4e0", "#a4b4c4", ["icon:toilet", "icon:head", "icon:toilet"], ink="#2a3a5a", pattern="bricks", edge="#ffffff"))
die("witch", 7, "shop", 110 * T, "Witch Dice", "Hexenwürfel",
    "Pays {pay}$ per pip. 25%: brews a potion – dice within {radius}px pay x3 on their next roll.", "Zahlt {pay}$ pro Auge. 25%: braut einen Trank – Würfel im Umkreis von {radius}px zahlen beim nächsten Wurf x3.",
    mech="potion", pay=800 * B, unlock_price=220 * T, p={"chance": 0.25, "radius": 200, "mult": 3}, family="spooky",
    art=art("#4a2a6e", "#3a1f58", "#2a1540", ["icon:witch_hat", "icon:cauldron", "icon:potion"], ink="#7aff5a", pattern="stars", edge="#9a6ad0"))
die("sigma", 7, "shop", 130 * T, "Sigma Dice", "Sigma-Würfel",
    "Grindset: +10% for every worker roll in a row (up to x6). Your own click resets the grind. Base {pay}$ per pip.", "Grindset: +10% für jeden Arbeiterwurf in Folge (bis x6). Dein eigener Klick setzt den Grind zurück. Basis {pay}$ pro Auge.",
    mech="sigma", pay=900 * B, unlock_price=260 * T, family="meme",
    art=art("#2a2a3a", "#1e1e2a", "#14141c", ["text:Σ", "icon:wolf", "text:Σ"], ink="#ffd23a", pattern="none", edge="#6a6a8a"))
die("bee", 7, "shop", 150 * T, "Bee Dice", "Bienenwürfel",
    "Collects honey with every roll; a full jar (20) pays x30. Also pollinates a neighbour. Base {pay}$ per pip.", "Sammelt mit jedem Wurf Honig; ein volles Glas (20) zahlt x30. Bestäubt außerdem einen Nachbarn. Basis {pay}$ pro Auge.",
    mech="bee", pay=1 * T, unlock_price=300 * T, p={"jar": 20, "mult": 30}, family="animal",
    art=art("#ffd21f", "#1b1b1b", "#ffd21f", ["icon:bee", "icon:honey", "icon:bee"], ink="#1b1b1b", pattern="stripes", edge="#fff2a0"))
die("aura", 7, "talent", 100 * T, "Aura Dice", "Aura-Würfel",
    "+1000 aura: dice within {radius}px earn +{bonus}%. Pays {pay}$ per pip.", "+1000 Aura: Würfel im Umkreis von {radius}px verdienen +{bonus}%. Zahlt {pay}$ pro Auge.",
    mech="aura", pay=1 * T, p={"radius": 200, "bonus": 50}, family="meme",
    art=art("#fff4c8", "#ffe28a", "#ffcf4a", ["text:+1000", "icon:sparkle", "icon:sparkle"], ink="#b8860b", pattern="stars", edge="#ffffff"))
die("train", 7, "talent", 160 * T, "Train Dice", "Zugwürfel",
    "Races along its row across the whole table, rolling every dice on the track (max {count}). Pays {pay}$ +2% per dice.", "Rast entlang seiner Reihe über den ganzen Tisch und lässt jeden Würfel auf der Strecke würfeln (max. {count}). Zahlt {pay}$ +2% pro Würfel.",
    mech="train", faces=(1,), pay=3 * T, p={"width": 40, "count": 60}, family="vehicle",
    art=art("#2a6a3a", "#1f5a2e", "#164a22", ["icon:train", "icon:wheel", "icon:wheel"], ink="#ffd23a", pattern="none", edge="#6ab07a"))
die("quantum", 7, "lucky", 200 * T, "Quantum Dice", "Quantenwürfel",
    "Superposition: rolls two faces at once and pays both. Double six is entangled: x36. Base {pay}$ per pip.", "Superposition: würfelt zwei Seiten gleichzeitig und zahlt beide. Doppel-Sechs ist verschränkt: x36. Basis {pay}$ pro Auge.",
    mech="quantum", pay=800 * B, family="cosmic",
    art=art("#1a1a3a", "#12122e", "#0a0a20", ["icon:atom", "pip:6", "icon:atom"], ink="#5affff", pattern="stars", edge="#5a5aaa"))
die("skeleton", 7, "tarot", 250 * T, "Skeleton Dice", "Skelettwürfel",
    "Collects bones: every skull rolled by a 50/50 dice adds +0.1% (up to x4). Base {pay}$ per pip.", "Sammelt Knochen: jeder Totenkopf eines 50/50-Würfels bringt +0,1% (bis x4). Basis {pay}$ pro Auge.",
    mech="skeleton", pay=1200 * B, family="spooky",
    art=art("#ececdc", "#cfcfbd", "#b0b09c", ["icon:skull", "icon:bone", "icon:skull"], ink="#1b1b1b", pattern="none", edge="#ffffff"))

# ---------------------------------------------------------------- TIER 8
die("platinum", 8, "shop", 1 * Q15, "Platinum Dice", "Platinwürfel",
    "Pure platinum: pays {pay}$ per pip.", "Reines Platin: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=8 * T, unlock_price=2 * Q15, family="material",
    art=art("#e4ecf2", "#c4ced8", "#a0acb8", ["icon:gem", "num:10", "icon:gem"], ink="#5a6a7a", pattern="metal", edge="#ffffff"))
die("bonk", 8, "shop", 1500 * T, "Bonk Dice", "Bonk-Würfel",
    "Bonks the {count} nearest dice (they roll). +10% per bonk. Base {pay}$ per pip.", "Bonkt die {count} nächsten Würfel (sie würfeln). +10% pro Bonk. Basis {pay}$ pro Auge.",
    mech="bonk", pay=12 * T, unlock_price=3 * Q15, p={"count": 5}, family="meme",
    art=art("#e8c07a", "#c9a05a", "#a6803e", ["icon:doge", "icon:bat_club", "text:BONK"], ink="#3a2410", pattern="none", edge="#ffe8b0", special="ears_dog"))
die("bank", 8, "shop", 2 * Q15, "Bank Dice", "Bankwürfel",
    "Pays interest: 0.2% of your current money per roll (at least {pay}$, at most 50x).", "Zahlt Zinsen: 0,2% deines aktuellen Geldes pro Wurf (mindestens {pay}$, höchstens das 50-fache).",
    mech="bank", faces=(1,), pay=10 * T, unlock_price=4 * Q15, family="casino",
    art=art("#2e7a4a", "#22603a", "#18482a", ["icon:bank", "text:%", "icon:coin"], ink="#ffd23a", pattern="none", edge="#7ac09a"))
die("mahjong", 8, "shop", 2500 * T, "Mahjong Dice", "Mahjong-Würfel",
    "Draws tiles 1-9. Three equal tiles in a row (across all Mahjong dice) call MAHJONG: x13! Base {pay}$ per pip.", "Zieht Steine 1-9. Drei gleiche Steine in Folge (über alle Mahjong-Würfel) rufen MAHJONG: x13! Basis {pay}$ pro Auge.",
    mech="mahjong", faces=list(range(1, 10)), pay=10 * T, unlock_price=5 * Q15, family="casino",
    art=art("#f2f0e0", "#2e8a4a", "#226a38", ["icon:tile", "icon:tile", "icon:tile"], ink="#c41a1a", pattern="none", edge="#ffffff"))
die("cyber", 8, "shop", 3 * Q15, "Cyber Dice", "Cyberwürfel",
    "Pays {pay}$ per pip. 10% chance to glitch: x8!", "Zahlt {pay}$ pro Auge. 10% Chance auf einen Glitch: x8!",
    mech="glitch", pay=20 * T, unlock_price=6 * Q15, p={"chance": 0.1, "mult": 8}, family="tech",
    art=art("#0a0a1a", "#14143a", "#1e1e5a", ["icon:circuit", "text:01", "icon:circuit"], ink="#00ffd0", pattern="glitch", edge="#ff2aaa"))
die("ohio", 8, "shop", 3500 * T, "Ohio Dice", "Ohio-Würfel",
    "Only in Ohio: anything can happen – x20, nothing at all, teleports, or the whole table rolls. Base {pay}$ per pip.", "Nur in Ohio: alles kann passieren – x20, gar nichts, Teleports oder der ganze Tisch würfelt. Basis {pay}$ pro Auge.",
    mech="ohio", pay=22 * T, unlock_price=7 * Q15, family="meme",
    art=art("#c41a1a", "#9a1212", "#6e0c0c", ["text:OH", "icon:corn", "text:IO"], ink="#ffffff", pattern="glitch", edge="#ff7a7a"))
die("blackhole", 8, "talent", 2 * Q15, "Black Hole Dice", "Schwarzes-Loch-Würfel",
    "Gravity pulls dice within {radius}px toward it – they all roll. +1% per dice pulled. Base {pay}$ per pip.", "Die Schwerkraft zieht Würfel im Umkreis von {radius}px an – sie alle würfeln. +1% pro angezogenem Würfel. Basis {pay}$ pro Auge.",
    mech="gravity", pay=15 * T, p={"radius": 250, "count": 30}, family="cosmic",
    art=art("#0a0a14", "#08080e", "#050508", ["icon:blackhole", "icon:swirl", "icon:blackhole"], ink="#b45aff", pattern="stars", edge="#5a2a8a"))
die("phoenix", 8, "talent", 4 * Q15, "Phoenix Dice", "Phönixwürfel",
    "Rolling a 1 burns it to ashes (0$) – the next roll is a rebirth paying x10. Base {pay}$ per pip.", "Eine 1 verbrennt ihn zu Asche (0$) – der nächste Wurf ist eine Wiedergeburt mit x10. Basis {pay}$ pro Auge.",
    mech="phoenix", pay=25 * T, family="animal",
    art=art("#ff7a1f", "#e8501a", "#c43010", ["icon:phoenix", "icon:flame", "icon:feather"], ink="#ffe25a", pattern="scales", edge="#ffc070"))
die("fox", 8, "lucky", 4500 * T, "Fox Dice", "Fuchswürfel",
    "Clever: adds the highest recent payout of a dice within {radius}px to its own {pay}$ per pip.", "Schlau: addiert die höchste letzte Auszahlung eines Würfels im Umkreis von {radius}px zu seinen {pay}$ pro Auge.",
    mech="copycat", pay=25 * T, p={"radius": 200}, family="animal",
    art=art("#ff8a2a", "#e06a1a", "#b84e10", ["icon:fox", "icon:fox", "icon:tail"], ink="#ffffff", pattern="none", edge="#ffc080", special="ears_fox"))
die("lava", 8, "tarot", 5 * Q15, "Lava Dice", "Lavawürfel",
    "Every 10th roll erupts: all dice within {radius}px roll and pay double. Base {pay}$ per pip.", "Jeder 10. Wurf bricht aus: alle Würfel im Umkreis von {radius}px würfeln und zahlen doppelt. Basis {pay}$ pro Auge.",
    mech="eruption", pay=30 * T, p={"every": 10, "radius": 300, "count": 50, "mult": 2}, family="element",
    art=art("#3a1a10", "#2a120a", "#1e0c06", ["icon:volcano", "icon:lava", "icon:flame"], ink="#ff6a1f", pattern="noise", edge="#ff4a1f"))

# ---------------------------------------------------------------- TIER 9
die("obsidian", 9, "shop", 20 * Q15, "Obsidian Dice", "Obsidianwürfel",
    "Volcanic glass: pays {pay}$ per pip.", "Vulkanglas: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=150 * T, unlock_price=40 * Q15, family="material",
    art=art("#2a2238", "#1e182a", "#14101c", ["icon:gem", "num:10", "icon:gem"], ink="#b49aff", pattern="gem", edge="#6a5a8a"))
die("galaxy", 9, "shop", 30 * Q15, "Galaxy Dice", "Galaxiewürfel",
    "Pays {pay}$ per pip, +1% for every 10 dice you own.", "Zahlt {pay}$ pro Auge, +1% für je 10 Würfel, die du besitzt.",
    mech="galaxy", pay=200 * T, unlock_price=60 * Q15, family="cosmic",
    art=art("#2a1a5a", "#1e1248", "#140c34", ["icon:galaxy", "icon:star", "icon:galaxy"], ink="#ffb0ff", pattern="stars", edge="#7a5aca"))
die("crown", 9, "shop", 40 * Q15, "Crown Dice", "Kronenwürfel",
    "Royal decree: every Crown dice adds +1% to ALL income (up to +50%). Pays {pay}$ per pip.", "Königlicher Erlass: jeder Kronenwürfel bringt +1% auf ALLE Einnahmen (bis +50%). Zahlt {pay}$ pro Auge.",
    mech="global_bonus", pay=250 * T, unlock_price=80 * Q15, p={"per": 1, "max": 50}, family="adventure",
    art=art("#ffd23a", "#e8b01c", "#c48c0c", ["icon:crown", "icon:gem", "icon:crown"], ink="#c41a3a", pattern="none", edge="#fff2a0"))
die("meteor", 9, "shop", 50 * Q15, "Meteorite Dice", "Meteoritenwürfel",
    "Impacts the table: dice within {radius}px roll with +50%. Pays {pay}$ per pip.", "Schlägt auf dem Tisch ein: Würfel im Umkreis von {radius}px würfeln mit +50%. Zahlt {pay}$ pro Auge.",
    mech="impact", pay=300 * T, unlock_price=100 * Q15, p={"radius": 260, "count": 40, "bonus": 50}, family="cosmic",
    art=art("#6a4a3a", "#523828", "#3a281c", ["icon:meteor", "icon:crater", "icon:flame"], ink="#ff8a2a", pattern="stone", edge="#a8806a"))
die("jackpot", 9, "shop", 60 * Q15, "Jackpot Dice", "Jackpot-Würfel",
    "Every roll feeds the progressive jackpot; 1% chance to win the whole pot! Base {pay}$ per pip.", "Jeder Wurf füttert den progressiven Jackpot; 1% Chance, den ganzen Topf zu gewinnen! Basis {pay}$ pro Auge.",
    mech="jackpot", pay=300 * T, unlock_price=120 * Q15, p={"chance": 0.01}, family="casino",
    art=art("#c41a3a", "#9a122e", "#6e0c20", ["text:JP", "icon:seven", "icon:coin"], ink="#ffd23a", pattern="stripes", edge="#ff7a9a"))
die("nebula", 9, "shop", 70 * Q15, "Nebula Dice", "Nebelwürfel",
    "Cosmic aura: dice within {radius}px earn +{bonus}%. Pays {pay}$ per pip.", "Kosmische Aura: Würfel im Umkreis von {radius}px verdienen +{bonus}%. Zahlt {pay}$ pro Auge.",
    mech="aura", pay=350 * T, unlock_price=140 * Q15, p={"radius": 160, "bonus": 100}, family="cosmic",
    art=art("#ff5ac8", "#a43ae0", "#4a2ab8", ["icon:nebula", "icon:star", "icon:nebula"], ink="#ffffff", pattern="stars", edge="#ffb0f0"))
die("sun", 9, "talent", 50 * Q15, "Sun Dice", "Sonnenwürfel",
    "Sunshine: every Sun dice adds +3% to ALL income (up to +150%). Pays {pay}$ per pip.", "Sonnenschein: jeder Sonnenwürfel bringt +3% auf ALLE Einnahmen (bis +150%). Zahlt {pay}$ pro Auge.",
    mech="global_bonus", pay=300 * T, p={"per": 3, "max": 150}, family="cosmic",
    art=art("#ffe25a", "#ffc21f", "#ff9a0c", ["icon:sun", "icon:sun", "icon:sun"], ink="#ff5a0c", pattern="none", edge="#fff8c0"))
die("golem", 9, "talent", 80 * Q15, "Golem Dice", "Golemwürfel",
    "A slow giant: rolls take 3x longer but pay {pay}$ per pip.", "Ein langsamer Riese: Würfe dauern 3x länger, zahlen aber {pay}$ pro Auge.",
    mech="slow", pay=1 * Q15, p={"slow": 3.0}, family="material",
    art=art("#8a8070", "#6e6658", "#524c40", ["icon:golem", "icon:rune", "icon:golem"], ink="#5affd0", pattern="stone", edge="#b8ae9a"))
die("timedie", 9, "lucky", 90 * Q15, "Time Dice", "Zeitwürfel",
    "Rewind: 25% chance to land again and pay again (up to 3 times). Base {pay}$ per pip.", "Zurückspulen: 25% Chance, erneut zu landen und erneut zu zahlen (bis zu 3-mal). Basis {pay}$ pro Auge.",
    mech="rewind", pay=350 * T, p={"chance": 0.25, "max": 3}, family="cosmic",
    art=art("#c8a44a", "#a8862f", "#86681c", ["icon:hourglass", "icon:clock", "icon:hourglass"], ink="#2a1a0a", pattern="none", edge="#ffe0a0"))
die("kraken", 9, "tarot", 100 * Q15, "Kraken Dice", "Krakenwürfel",
    "Eight tentacles roll {count} random dice anywhere on the table. Pays {pay}$ per pip.", "Acht Tentakel lassen {count} zufällige Würfel irgendwo auf dem Tisch würfeln. Zahlt {pay}$ pro Auge.",
    mech="lightning", pay=400 * T, p={"count": 8}, family="animal",
    art=art("#8a2a6a", "#6e1f55", "#521640", ["icon:kraken", "icon:tentacle", "icon:tentacle"], ink="#ffd0f0", pattern="scales", edge="#d06ab0"))

# ---------------------------------------------------------------- TIER 10
die("mithril", 10, "shop", 300 * Q15, "Mithril Dice", "Mithrilwürfel",
    "Legendary metal: pays {pay}$ per pip.", "Legendäres Metall: zahlt {pay}$ pro Auge.",
    faces=(2, 2, 3, 3, 4, 10), pay=2 * Q15, unlock_price=600 * Q15, family="material",
    art=art("#c8f0ff", "#9ad8f0", "#6ab8d8", ["icon:gem", "num:10", "icon:gem"], ink="#1a4a6a", pattern="metal", edge="#ffffff"))
die("divine", 10, "shop", 500 * Q15, "Divine Dice", "Götterwürfel",
    "Blesses everything: each Divine dice adds +5% to ALL income (up to +100%) and rolls itself every {interval} s. Pays {pay}$ per pip.",
    "Segnet alles: jeder Götterwürfel bringt +5% auf ALLE Einnahmen (bis +100%) und würfelt sich alle {interval} s selbst. Zahlt {pay}$ pro Auge.",
    mech="divine", pay=3 * Q15, unlock_price=1 * Q18, p={"per": 5, "max": 100, "interval": 6.0}, npc=False, family="cosmic",
    art=art("#fff8e0", "#ffe8a0", "#ffd25a", ["icon:halo", "icon:wing", "icon:wing"], ink="#c89a1a", pattern="stars", edge="#ffffff"))
die("supernova", 10, "shop", 600 * Q15, "Supernova Dice", "Supernova-Würfel",
    "Charges up for 10 rolls, then explodes: up to {count} dice all over the table roll and pay double. Base {pay}$ per pip.", "Lädt sich 10 Würfe lang auf und explodiert dann: bis zu {count} Würfel auf dem ganzen Tisch würfeln und zahlen doppelt. Basis {pay}$ pro Auge.",
    mech="supernova", pay=4 * Q15, unlock_price=1200 * Q15, p={"charge": 10, "count": 400, "mult": 2}, family="cosmic",
    art=art("#ffffff", "#ffd2f0", "#ff8ad8", ["icon:supernova", "icon:star", "icon:supernova"], ink="#ff2a8a", pattern="stars", edge="#ffffff"))
die("omega", 10, "shop", 1 * Q18, "Omega Dice", "Omega-Würfel",
    "The final dice: five sixes and one 66. Pays {pay}$ per pip.", "Der letzte Würfel: fünf Sechsen und eine 66. Zahlt {pay}$ pro Auge.",
    faces=(6, 6, 6, 6, 6, 66), pay=1 * Q15, unlock_price=2 * Q18, family="cosmic",
    art=art("#1a1a1a", "#c89a1a", "#8a6a0c", ["text:Ω", "num:66", "text:Ω"], ink="#ffd23a", pattern="none", edge="#ffe8a0"))
die("architect", 10, "shop", 700 * Q15, "Architect Dice", "Architektenwürfel",
    "Builds: every {every} rolls it constructs a free dice of a type you own. Pays {pay}$ per pip.", "Baut: alle {every} Würfe errichtet er gratis einen Würfel einer Art, die du besitzt. Zahlt {pay}$ pro Auge.",
    mech="builder", pay=4 * Q15, unlock_price=1400 * Q15, p={"every": 30}, family="adventure",
    art=art("#4a6a9a", "#3a5480", "#2a3e60", ["icon:blueprint", "icon:hammer", "icon:brick"], ink="#ffffff", pattern="grid", edge="#9ab8e8"))
die("ascension", 10, "shop", 800 * Q15, "Ascension Dice", "Aufstiegswürfel",
    "Grows forever: every roll permanently adds +1% to this dice (up to x10). Base {pay}$ per pip.", "Wächst für immer: jeder Wurf bringt diesem Würfel dauerhaft +1% (bis x10). Basis {pay}$ pro Auge.",
    mech="ascend", pay=3 * Q15, unlock_price=1600 * Q15, p={"step": 1, "max": 900}, family="cosmic",
    art=art("#e0f8ff", "#a8e0ff", "#70c0f0", ["icon:arrow_up", "icon:wing", "icon:arrow_up"], ink="#2a5a9a", pattern="stars", edge="#ffffff"))
die("infinity", 10, "talent", 1 * Q18, "Infinity Dice", "Unendlichkeitswürfel",
    "Pays {pay}$ per pip, +5% per achievement and +4% per dice type owned.", "Zahlt {pay}$ pro Auge, +5% pro Errungenschaft und +4% pro besessener Würfelart.",
    mech="infinity", pay=4 * Q15, family="cosmic",
    art=art("#5a2aa8", "#4a1f8a", "#36146a", ["text:∞", "text:∞", "text:∞"], ink="#ffd23a", pattern="stars", edge="#b08aff"))
die("rainbow", 10, "talent", 1200 * Q15, "Rainbow Dice", "Regenbogenwürfel",
    "Counts as every type: +5% per dice type you own. Pays {pay}$ per pip.", "Zählt als jede Art: +5% pro Würfelart, die du besitzt. Zahlt {pay}$ pro Auge.",
    mech="rainbow", pay=3 * Q15, family="luck",
    art=art("#ff4a4a", "#ffd21f", "#4a7aff", ["icon:rainbow", "icon:rainbow", "icon:rainbow"], ink="#ffffff", pattern="none", edge="#ffffff"))
die("cosmic", 10, "lucky", 1300 * Q15, "Cosmic Dice", "Kosmischer Würfel",
    "Pays {pay}$ per pip, multiplied by (1 + active events), doubled during Golden Luck.", "Zahlt {pay}$ pro Auge, multipliziert mit (1 + aktive Ereignisse), verdoppelt während Goldenem Glück.",
    mech="cosmic", pay=5 * Q15, family="cosmic",
    art=art("#14143a", "#0e0e2a", "#08081a", ["icon:planet", "icon:star", "icon:planet"], ink="#5affff", pattern="stars", edge="#5a5aca"))
die("elderdragon", 10, "tarot", 1500 * Q15, "Elder Dragon Dice", "Uralter-Drache-Würfel",
    "Ancient fire: a {radius}px cone of flames rolls up to {count} dice that pay x3. Base {pay}$ per pip.", "Uraltes Feuer: ein {radius}px-Flammenkegel lässt bis zu {count} Würfel würfeln, die x3 zahlen. Basis {pay}$ pro Auge.",
    mech="cone", pay=6 * Q15, p={"radius": 420, "count": 60, "mult": 3}, family="animal",
    art=art("#2a1a4a", "#1f1238", "#140c26", ["icon:dragon", "icon:flame", "icon:crown"], ink="#ff5a1f", pattern="scales", edge="#7a5aca", special="horns"))

# ---- big-number economy: spread the tiers exponentially (tier t starts near 10^(3t)).
OLD_BASE = {1: 1500, 2: 80 * K, 3: 6 * M, 4: 300 * M, 5: 20 * B, 6: 1 * T, 7: 50 * T, 8: 1 * Q15, 9: 20 * Q15, 10: 300 * Q15}
NEW_BASE = {1: 1.5e3, 2: 1.0e6, 3: 1.0e9, 4: 1.0e12, 5: 1.0e15, 6: 1.0e18, 7: 1.0e21, 8: 1.0e24, 9: 1.0e27, 10: 1.0e30}
for d in D:
    factor = NEW_BASE[d["tier"]] / float(OLD_BASE[d["tier"]])
    d["price"] = float(round(d["price"] * factor))
    d["unlock_price"] = float(round(d["unlock_price"] * factor))
    d["pay"] = float(max(1, round(d["pay"] * factor)))

# ---- balance (Dice Rush Extended 1.0): later tiers cost relatively more (longer payback),
# a shop unlock is a real step (10x the first price) and needs dice of the tier below
# (see shop_logic.gd). Payouts stay the same.
TIER_GROWTH = 1.6
for d in D:
    growth = TIER_GROWTH ** (d["tier"] - 1)
    d["price"] = float(round(d["price"] * growth))
    if d["unlock"] == "shop":
        d["unlock_price"] = float(round(d["price"] * 10))
    else:
        d["unlock_price"] = float(round(d["unlock_price"] * growth))

assert len(D) == 100, len(D)
ids = [d["id"] for d in D]
assert len(set(ids)) == 100
for tier in range(1, 11):
    assert sum(1 for d in D if d["tier"] == tier) == 10, tier

out = {"schema": "bdr-dice-v1", "dice": D}
path = os.path.join(os.path.join(REPO, "src", "bdr", "data"), "dice_catalog.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1)
from collections import Counter
print("dice:", len(D), Counter(d["unlock"] for d in D), Counter(d["mech"] for d in D).most_common(60))
