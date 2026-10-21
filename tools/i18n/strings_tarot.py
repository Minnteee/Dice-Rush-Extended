# Dice Rush Extended - tarot strings (English, German): 40 minor arcana + offering UI.
SUITS = {
    "wands": ("Wands", "Stäbe"),
    "cups": ("Cups", "Kelche"),
    "swords": ("Swords", "Schwerter"),
    "pentacles": ("Pentacles", "Münzen"),
}
NUMBERS = {
    1: ("Ace", "Ass"), 2: ("Two", "Zwei"), 3: ("Three", "Drei"), 4: ("Four", "Vier"), 5: ("Five", "Fünf"),
    6: ("Six", "Sechs"), 7: ("Seven", "Sieben"), 8: ("Eight", "Acht"), 9: ("Nine", "Neun"), 10: ("Ten", "Zehn"),
}
FAMILY = {  # card -> (english family dice, german family dice)
    "m_wands_2": ("Element dice", "Element-Würfel"),
    "m_wands_3": ("Vehicle dice", "Fahrzeug-Würfel"),
    "m_wands_4": ("Tech dice", "Technik-Würfel"),
    "m_cups_2": ("Food dice", "Essens-Würfel"),
    "m_cups_3": ("Animal dice", "Tier-Würfel"),
    "m_cups_4": ("Luck dice", "Glücks-Würfel"),
    "m_swords_2": ("Meme dice", "Meme-Würfel"),
    "m_swords_3": ("Spooky dice", "Grusel-Würfel"),
    "m_swords_4": ("Adventure dice", "Abenteuer-Würfel"),
    "m_pentacles_2": ("Material dice", "Material-Würfel"),
    "m_pentacles_3": ("Casino dice", "Casino-Würfel"),
    "m_pentacles_4": ("Cosmic dice", "Kosmos-Würfel"),
}
DESC = {
    "m_wands_1": ("2% chance per roll and point of Power that a roll pays x10.",
                  "Pro Wurf und Stärkepunkt 2 % Chance, dass ein Wurf x10 auszahlt."),
    "m_wands_5": ("Self-rolling dice roll 10% more often per point of Power.",
                  "Selbstwürfelnde Würfel würfeln pro Stärkepunkt 10 % öfter."),
    "m_wands_6": ("All new dice earn +10% per point of Power.", "Alle neuen Würfel bringen +10 % pro Stärkepunkt."),
    "m_wands_7": ("Dice that make other dice roll push 15% more of them per point of Power.",
                  "Würfel, die andere Würfel anstoßen, stoßen pro Stärkepunkt 15 % mehr an."),
    "m_wands_8": ("Random events last 20% longer per point of Power.", "Zufallsereignisse dauern pro Stärkepunkt 20 % länger."),
    "m_wands_9": ("3% chance per roll and point of Power that a roll pays x5.",
                  "Pro Wurf und Stärkepunkt 3 % Chance, dass ein Wurf x5 auszahlt."),
    "m_wands_10": ("+3% income per point of Power for every different dice type you own.",
                   "+3 % Einkommen pro Stärkepunkt für jede Würfelart, die du besitzt."),
    "m_cups_1": ("Per point of Power: lucky cubes cost 15% less and unlock new dice 50% more often.",
                 "Pro Stärkepunkt: Glückswürfel kosten 15 % weniger und schalten 50 % öfter neue Würfel frei."),
    "m_cups_5": ("Lucky cubes cost 5% less per point of Power.", "Glückswürfel kosten pro Stärkepunkt 5 % weniger."),
    "m_cups_6": ("Random events happen 15% more often per point of Power.", "Zufallsereignisse passieren pro Stärkepunkt 15 % öfter."),
    "m_cups_7": ("Rewards of random events +25% per point of Power.", "Belohnungen von Zufallsereignissen +25 % pro Stärkepunkt."),
    "m_cups_8": ("Bonus rewards from lucky cubes drop 50% more often per point of Power.",
                 "Bonus-Belohnungen aus Glückswürfeln fallen pro Stärkepunkt 50 % öfter."),
    "m_cups_9": ("Lucky streaks pay x0.5 more per point of Power.", "Glückssträhnen zahlen pro Stärkepunkt x0,5 mehr."),
    "m_cups_10": ("Every random event also starts a lucky streak (20 s per point of Power).",
                  "Jedes Zufallsereignis startet zusätzlich eine Glückssträhne (20 s pro Stärkepunkt)."),
    "m_swords_1": ("Per point of Power: area effects reach 20% farther and chain dice push 20% more dice.",
                   "Pro Stärkepunkt: Flächeneffekte reichen 20 % weiter und Kettenwürfel stoßen 20 % mehr an."),
    "m_swords_5": ("Area effects of the new dice reach 10% farther per point of Power.",
                   "Flächeneffekte der neuen Würfel reichen pro Stärkepunkt 10 % weiter."),
    "m_swords_6": ("New dice of tier 6-10 earn +20% per point of Power.", "Neue Würfel der Stufen 6-10 bringen +20 % pro Stärkepunkt."),
    "m_swords_7": ("New dice of tier 1-5 earn +30% per point of Power.", "Neue Würfel der Stufen 1-5 bringen +30 % pro Stärkepunkt."),
    "m_swords_8": ("Sacrificed dice count 25% more for tarot cards per point of Power.",
                   "Geopferte Würfel zählen pro Stärkepunkt 25 % mehr für Tarotkarten."),
    "m_swords_9": ("Selling dice returns 10% more per point of Power.", "Würfel verkaufen bringt pro Stärkepunkt 10 % mehr."),
    "m_swords_10": ("Offerings show 4 cards to choose from. Sacrificed dice count 20% more per point of Power.",
                    "Opfer zeigen 4 Karten zur Auswahl. Geopferte Würfel zählen pro Stärkepunkt 20 % mehr."),
    "m_pentacles_1": ("All new dice earn +40% per point of Power.", "Alle neuen Würfel bringen +40 % pro Stärkepunkt."),
    "m_pentacles_5": ("The original dice of the game earn +25% per point of Power.",
                      "Die Original-Würfel des Spiels bringen +25 % pro Stärkepunkt."),
    "m_pentacles_6": ("New dice cost 5% less per point of Power.", "Neue Würfel kosten pro Stärkepunkt 5 % weniger."),
    "m_pentacles_7": ("All income +15% per point of Power.", "Alle Einnahmen +15 % pro Stärkepunkt."),
    "m_pentacles_8": ("Cash bags from lucky cubes are worth 100% more per point of Power.",
                      "Geldsäcke aus Glückswürfeln sind pro Stärkepunkt 100 % mehr wert."),
    "m_pentacles_9": ("+25% income per point of Power while a random event is active.",
                      "+25 % Einkommen pro Stärkepunkt, solange ein Zufallsereignis läuft."),
    "m_pentacles_10": ("Per point of Power: new dice cost 10% less and selling returns 25% more.",
                       "Pro Stärkepunkt: neue Würfel kosten 10 % weniger und Verkaufen bringt 25 % mehr."),
}

S = {
    "tarot.rarity.common": ("COMMON", "GEWÖHNLICH"),
    "tarot.rarity.rare": ("RARE", "SELTEN"),
    "tarot.rarity.epic": ("EPIC", "EPISCH"),
    "tarot.rarity.legendary": ("LEGENDARY", "LEGENDÄR"),
    "tarot.offer_size": ("OFFERING SIZE", "OPFERGRÖSSE"),
    "tarot.select_dice": ("Choose a dice type below", "Wähle unten eine Würfelart"),
    "tarot.points": ("OFFERING VALUE: {n}", "OPFERWERT: {n}"),
    "tarot.worth": ("VALUE {w} PER DICE", "WERT {w} PRO WÜRFEL"),
    "tarot.need": ("{n} DICE OF THIS KIND REQUIRED", "{n} WÜRFEL DIESER ART NÖTIG"),
    "tarot.unlocks_dice": ("The first copy unlocks the {name}.", "Die erste Karte schaltet den {name} frei."),
    "fx.crit": ("CRIT x{n}!", "KRITISCH x{n}!"),
    "tarot.owned": ("OWNED ×{n}", "IM BESITZ ×{n}"),
}

for suit, (suit_en, suit_de) in SUITS.items():
    for number in range(1, 11):
        card = "m_%s_%d" % (suit, number)
        num_en, num_de = NUMBERS[number]
        S["tarot.%s.name" % card] = ("%s of %s" % (num_en, suit_en), "%s der %s" % (num_de, suit_de))
        if card in FAMILY:
            fam_en, fam_de = FAMILY[card]
            desc = ("%s earn +25%% per point of Power." % fam_en, "%s bringen +25 %% pro Stärkepunkt." % fam_de)
        else:
            desc = DESC[card]
        S["tarot.%s.desc" % card] = desc
