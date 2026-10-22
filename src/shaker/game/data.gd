extends RefCounted
## Dice Shaker game data (res://shaker/data/shaker_data.json, made by tools/shaker/make_shaker_data.py).

const PATH := "res://shaker/data/shaker_data.json"

static var loaded := false
static var raw: Dictionary = {}
static var balance: Dictionary = {}
static var rarities: Array = []
static var rarity_colors: Dictionary = {}
static var stat_kinds: Dictionary = {}
static var passive_fx: Dictionary = {}
static var dice: Array = []
static var dice_by_id: Dictionary = {}
static var dice_by_rarity: Dictionary = {}
static var tarot: Array = []
static var tarot_by_id: Dictionary = {}
static var black: Array = []
static var black_by_id: Dictionary = {}
static var gauntlets: Array = []
static var tables: Array = []
static var talents: Array = []
static var talents_by_id: Dictionary = {}
static var slot_costs: Dictionary = {}
static var gumball: Dictionary = {}
static var lucky: Dictionary = {}
static var tarot_draw: Dictionary = {}


static func ensure() -> void:
	if loaded:
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if parsed is not Dictionary:
		push_error("Dice Shaker: game data missing (%s)" % PATH)
		return
	raw = parsed
	balance = raw.get("balance", {})
	rarities = raw.get("rarities", [])
	rarity_colors = raw.get("rarity_colors", {})
	stat_kinds = raw.get("stats", {})
	passive_fx = raw.get("passive_fx", {})
	dice = raw.get("dice", [])
	for rarity in rarities:
		dice_by_rarity[rarity] = []
	for def in dice:
		def["faces"] = (def.get("faces", [1, 2, 3, 4, 5, 6]) as Array).map(func(v: Variant) -> int: return int(v))
		dice_by_id[str(def.id)] = def
		(dice_by_rarity[str(def.rarity)] as Array).append(def)
	tarot = raw.get("tarot", [])
	for card in tarot:
		tarot_by_id[str(card.id)] = card
	black = raw.get("black", [])
	for card in black:
		black_by_id[str(card.id)] = card
	gauntlets = raw.get("gauntlets", [])
	tables = raw.get("tables", [])
	talents = raw.get("talents", [])
	for talent in talents:
		talents_by_id[str(talent.id)] = talent
	slot_costs = raw.get("slot_costs", {})
	gumball = raw.get("gumball", {})
	lucky = raw.get("lucky", {})
	tarot_draw = raw.get("tarot_draw", {})
	loaded = true


static func b(key: String, fallback: Variant = 0.0) -> Variant:
	return balance.get(key, fallback)


static func die(die_id: String) -> Dictionary:
	return dice_by_id.get(die_id, {})


static func rarity_index(rarity: String) -> int:
	return maxi(0, rarities.find(rarity))


static func rarity_color(rarity: String) -> Color:
	return Color(str(rarity_colors.get(rarity, "#ffffff")))


static func gauntlet(index: int) -> Dictionary:
	if index < 1 or index > gauntlets.size():
		return {}
	return gauntlets[index - 1]
