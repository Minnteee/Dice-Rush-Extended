extends RefCounted
## Dice Rush Extended - tarot extension:
##  * 40 minor arcana (common / rare / epic) next to the 21 legendary major arcana,
##  * the offering value (amount x value of the sacrificed dice) decides the card rarities,
##  * card effects (collected here and used by the controller hooks),
##  * 9 new dice are unlocked by the first copy of a tarot card.

const I18N := preload("res://bdr/core/i18n.gd")
const NumFmt := preload("res://bdr/core/numfmt.gd")

const AMOUNTS := [10, 25, 50, 100, 250]
const RARITIES := ["common", "rare", "epic", "legendary"]
const RARITY_COLORS := {"common": Color("c3cad7"), "rare": Color("4fa3ff"), "epic": Color("c56bff"), "legendary": Color("ffc93c")}
## Value of one sacrificed dice. New dice: 2 x tier.
const VANILLA_WORTH := {"50_50": 1, "d4": 1, "3x4": 1, "d2": 2, "777": 2, "prehistoric": 3, "golden": 3,
	"npc_die": 3, "crypto": 4, "diamond": 5, "pi": 6}
## [minimum score, common %, rare %, epic %, legendary %]; score = log2(offering value / 10)
const ODDS := [
	[7.0, 0, 0, 15, 85],
	[6.0, 0, 0, 35, 65],
	[5.0, 0, 10, 45, 45],
	[4.0, 0, 30, 45, 25],
	[3.0, 15, 40, 35, 10],
	[2.0, 35, 45, 18, 2],
	[1.0, 60, 35, 5, 0],
	[-1000.0, 85, 15, 0, 0],
]
const UNLOCK_BY_CARD := {"m_cups_2": "donut", "m_swords_3": "zombie", "m_wands_6": "wizard", "m_cups_7": "vampire",
	"m_swords_7": "thisisfine", "m_swords_9": "skeleton", "m_wands_10": "lava", "m_cups_10": "kraken", "m_swords_1": "elderdragon"}
const FAMILY_CARDS := {"m_wands_2": "element", "m_wands_3": "vehicle", "m_wands_4": "tech", "m_cups_2": "food",
	"m_cups_3": "animal", "m_cups_4": "luck", "m_swords_2": "meme", "m_swords_3": "spooky", "m_swords_4": "adventure",
	"m_pentacles_2": "material", "m_pentacles_3": "casino", "m_pentacles_4": "cosmic", "m_pentacles_5": "classic"}
const SUIT_NAMES := ["wands", "cups", "swords", "pentacles"]

var game: Node
var main: Node
var rng := RandomNumberGenerator.new()
var _fx: Dictionary = {}
var _fx_valid := false


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	rng.randomize()


func invalidate() -> void:
	_fx_valid = false


func power(card_id: String) -> float:
	return float(main._dog_card_effect_power(card_id))


# ---------------------------------------------------------------- offering
func worth(kind: String) -> int:
	if VANILLA_WORTH.has(kind):
		return int(VANILLA_WORTH[kind])
	var def = game.catalog.by_id.get(kind)
	if def != null:
		return 2 * int(def.tier)
	return 1


func min_amount() -> int:
	return int(AMOUNTS[0])


func clamp_amount(amount: int) -> int:
	return amount if amount in AMOUNTS else int(AMOUNTS[0])


func points_multiplier() -> float:
	_ensure()
	var multiplier := 1.0 + float(_fx.points)
	if main._is_talent_owned("bdr_offering_bonus"):
		multiplier += 0.5
	return multiplier + game.staff.offering_bonus()


func points(kind: String, amount: int) -> float:
	return float(amount) * float(worth(kind)) * points_multiplier()


func odds(offering_points: float) -> Array:
	var score := log(maxf(1.0, offering_points) / 10.0) / log(2.0)
	for row in ODDS:
		if score >= float(row[0]):
			return [int(row[1]), int(row[2]), int(row[3]), int(row[4])]
	return [100, 0, 0, 0]


func offer_size() -> int:
	return 4 if int(main._dog_card_rank("m_swords_10")) > 0 else 3


func roll_offer(kind: String, amount: int) -> Array[Dictionary]:
	var row := odds(points(kind, amount))
	var choices: Array[Dictionary] = []
	var used: Array[String] = []
	for _index in range(offer_size()):
		var rarity := _roll_rarity(row)
		var card_id := _pick_card(rarity, used)
		if card_id.is_empty():
			break
		used.append(card_id)
		choices.append({"id": card_id, "rarity": DogShrineCards.rarity(card_id)})
	return choices


func _roll_rarity(row: Array) -> String:
	var total := 0
	for weight in row:
		total += int(weight)
	var pick := rng.randi_range(1, maxi(1, total))
	for index in range(RARITIES.size()):
		pick -= int(row[index])
		if pick <= 0:
			return RARITIES[index]
	return RARITIES[0]


## A random card of the rarity that is not in the offer yet (falls back to neighbour rarities).
func _pick_card(rarity: String, used: Array[String]) -> String:
	var start := RARITIES.find(rarity)
	var order: Array[int] = [start]
	for distance in range(1, RARITIES.size()):
		if start - distance >= 0:
			order.append(start - distance)
		if start + distance < RARITIES.size():
			order.append(start + distance)
	for index in order:
		var pool: Array[String] = []
		for card_value in DogShrineCards.ids_for_rarity(RARITIES[index]):
			if str(card_value) not in used:
				pool.append(str(card_value))
		if not pool.is_empty():
			return pool[rng.randi_range(0, pool.size() - 1)]
	return ""


## Owned new dice that can be sacrificed, sorted by tier.
func offerable_custom_kinds() -> Array[String]:
	var result: Array[String] = []
	for kind in game.shop_custom_kinds():
		if game.count(kind) > 0:
			result.append(kind)
	return result


# ---------------------------------------------------------------- cards gained
func on_card_gained(card_id: String, old_rank: int) -> void:
	invalidate()
	game.stat("tarot_cards", 1)
	if card_id.begins_with("m_"):
		game.stat("tarot_minor", 1)
	var rarity := DogShrineCards.rarity(card_id)
	if not rarity.is_empty():
		game.stat("tarot_" + rarity, 1)
	if old_rank <= 0 and UNLOCK_BY_CARD.has(card_id):
		var kind: String = UNLOCK_BY_CARD[card_id]
		if game.is_unlocked(kind):
			main.die_levels[kind] = main._die_level(kind) + 3
		else:
			game.unlock(kind)
	main._invalidate_eco()


func unlock_card_for(kind: String) -> String:
	for card_id in UNLOCK_BY_CARD:
		if UNLOCK_BY_CARD[card_id] == kind:
			return card_id
	return ""


# ---------------------------------------------------------------- effects
func _ensure() -> void:
	if _fx_valid:
		return
	var fx := {}
	var family := {}
	for card_id in FAMILY_CARDS:
		var p := power(card_id)
		if p > 0.0:
			family[FAMILY_CARDS[card_id]] = float(family.get(FAMILY_CARDS[card_id], 0.0)) + 25.0 * p
	fx["family"] = family
	fx["new_dice"] = 10.0 * power("m_wands_6") + 40.0 * power("m_pentacles_1")
	fx["tier_high"] = 20.0 * power("m_swords_6")
	fx["tier_low"] = 30.0 * power("m_swords_7")
	fx["global"] = 15.0 * power("m_pentacles_7")
	fx["per_kind"] = 3.0 * power("m_wands_10")
	fx["event_active"] = 25.0 * power("m_pentacles_9")
	fx["price_discount"] = minf(0.6, 0.05 * power("m_pentacles_6") + 0.10 * power("m_pentacles_10"))
	fx["sell"] = 0.10 * power("m_swords_9") + 0.25 * power("m_pentacles_10")
	fx["lucky_discount"] = minf(0.6, 0.05 * power("m_cups_5") + 0.15 * power("m_cups_1"))
	fx["lucky_chance"] = 1.0 + 0.5 * power("m_cups_8")
	fx["lucky_unlock"] = 1.0 + 0.5 * power("m_cups_1")
	fx["boost_bonus"] = 0.5 * power("m_cups_9")
	fx["cash"] = 1.0 + power("m_pentacles_8")
	fx["auto_speed"] = 1.0 + 0.1 * power("m_wands_5")
	fx["radius"] = 1.0 + 0.1 * power("m_swords_5") + 0.2 * power("m_swords_1")
	fx["count"] = 1.0 + 0.15 * power("m_wands_7") + 0.2 * power("m_swords_1")
	fx["event_freq"] = 1.0 + 0.15 * power("m_cups_6")
	fx["event_reward"] = 1.0 + 0.25 * power("m_cups_7")
	fx["event_duration"] = 1.0 + 0.2 * power("m_wands_8")
	fx["event_streak"] = 20.0 * power("m_cups_10")
	fx["crit5"] = minf(0.3, 0.03 * power("m_wands_9"))
	fx["crit10"] = minf(0.2, 0.02 * power("m_wands_1"))
	fx["points"] = 0.25 * power("m_swords_8") + 0.2 * power("m_swords_10")
	_fx = fx
	_fx_valid = true


func value(key: String) -> float:
	_ensure()
	return float(_fx.get(key, 0.0))


## Percent bonus for one dice kind (family cards, new dice cards, tier cards).
func kind_percent(kind: String) -> float:
	_ensure()
	var def = game.catalog.by_id.get(kind)
	var family := "classic" if def == null else str(def.family)
	var percent := float((_fx.family as Dictionary).get(family, 0.0))
	if def != null:
		percent += float(_fx.new_dice)
		if int(def.tier) >= 6:
			percent += float(_fx.tier_high)
		else:
			percent += float(_fx.tier_low)
	return percent


func global_multiplier() -> float:
	_ensure()
	var multiplier := 1.0 + float(_fx.global) / 100.0
	if float(_fx.per_kind) > 0.0:
		multiplier *= 1.0 + float(_fx.per_kind) * float(game.kinds_owned_count()) / 100.0
	if float(_fx.event_active) > 0.0 and game.any_event_active():
		multiplier *= 1.0 + float(_fx.event_active) / 100.0
	return multiplier


## Critical roll multiplier (1 = no crit).
func roll_crit() -> float:
	_ensure()
	if float(_fx.crit10) > 0.0 and rng.randf() < float(_fx.crit10):
		return 10.0
	if float(_fx.crit5) > 0.0 and rng.randf() < float(_fx.crit5):
		return 5.0
	return 1.0


# ---------------------------------------------------------------- texts
func amounts() -> Array:
	return AMOUNTS


func offer_size_title() -> String:
	return I18N.t("tarot.offer_size")


func select_text() -> String:
	return I18N.t("tarot.select_dice")


func card_name(card_id: String) -> String:
	return I18N.t("tarot.%s.name" % card_id)


func card_description(card_id: String) -> String:
	var text := I18N.t("tarot.%s.desc" % card_id)
	if UNLOCK_BY_CARD.has(card_id):
		text += " " + I18N.f("tarot.unlocks_dice", {"name": game.display_name(UNLOCK_BY_CARD[card_id])})
	return text


func rarity_name(rarity: String) -> String:
	return I18N.t("tarot.rarity." + rarity)


## Badge on offered cards the player already has ("OWNED x3").
func owned_text(rank: int) -> String:
	return I18N.f("tarot.owned", {"n": rank})


func rarity_color(rarity: String) -> Color:
	return RARITY_COLORS.get(rarity, Color.WHITE)


func need_text(count: int) -> String:
	return I18N.f("tarot.need", {"n": count})


func worth_text(kind: String) -> String:
	return I18N.f("tarot.worth", {"w": worth(kind)})


func points_text(kind: String, amount: int) -> String:
	return I18N.f("tarot.points", {"n": int(round(points(kind, amount)))})


## BBCode text with the rarity chances of an offering (two lines, two rarities each).
func odds_bbcode(kind: String, amount: int) -> String:
	var row := odds(points(kind, amount))
	var parts: Array[String] = []
	for index in range(RARITIES.size()):
		var rarity: String = RARITIES[index]
		var percent := int(row[index])
		var color := rarity_color(rarity) if percent > 0 else Color("5a606c")
		parts.append("[color=#%s]%s %d%%[/color]" % [color.to_html(false), rarity_name(rarity), percent])
	return "[center]%s     %s\n%s     %s[/center]" % [parts[0], parts[1], parts[2], parts[3]]
