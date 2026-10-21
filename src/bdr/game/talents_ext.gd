extends RefCounted
## Dice Rush Extended - new talent tree nodes (positions are in the tree canvas space after
## the original nodes were moved by ORIGINAL_OFFSET).

const ORIGINAL_OFFSET := Vector2(1318, 1778)
const TREE_SIZE := Vector2(7720, 8000)
const STEP := 260.0

## Dice that are unlocked through the talent tree, by tier (spine, leaf).
const UNLOCKS := [
	["paper", "bubble"], ["ice", "fire"], ["godot", "tetris"], ["dragon", "magic8"], ["ninja", "domino"],
	["gigachad", "samurai"], ["aura", "train"], ["blackhole", "phoenix"], ["sun", "golem"], ["infinity", "rainbow"],
]
const FAMILY_ROWS := [["classic", "material", "meme", "food", "animal", "element", "luck"], ["tech", "casino", "adventure", "spooky", "vehicle", "cosmic"]]
const FAMILIES := ["classic", "material", "meme", "food", "animal", "element", "luck", "tech", "casino", "adventure", "spooky", "vehicle", "cosmic"]
const FAMILY_ICON := {"classic": "50_50", "material": "ruby", "meme": "pepe", "element": "fire", "animal": "bunny", "tech": "godot",
	"adventure": "pirate", "casino": "slot", "food": "pizza", "spooky": "zombie", "vehicle": "car", "cosmic": "galaxy", "luck": "clover"}
const UTILITY := ["bdr_sell_1", "bdr_sell_2", "bdr_event_freq_1", "bdr_event_freq_2", "bdr_event_reward", "bdr_lucky_discount",
	"bdr_offering_bonus", "bdr_staff_limit_1", "bdr_staff_limit_2", "bdr_auto_speed", "bdr_aura_radius", "bdr_chain_power"]

var defs: Dictionary = {}      # key -> {prereq, pos, cost, type, ...}
var order: Array[String] = []


func build(original_positions: Dictionary) -> void:
	defs.clear()
	order.clear()
	var root: Vector2 = original_positions.get("d4", Vector2(2082, 3182))
	var fifty_top: Vector2 = original_positions.get("fifty_profit_6", root + Vector2(0, -1560))
	# --- dice lab: a spine going up from the top of the 50/50 branch, one tier per step
	var previous := "fifty_profit_6"
	for tier in range(10):
		var spine_key := "bdr_unlock_" + str(UNLOCKS[tier][0])
		var leaf_key := "bdr_unlock_" + str(UNLOCKS[tier][1])
		var spine_pos := fifty_top + Vector2(0, -STEP * (tier + 1))
		_add(spine_key, previous, spine_pos, _unlock_cost(tier + 1), "unlock", {"kind": UNLOCKS[tier][0], "tier": tier + 1})
		_add(leaf_key, spine_key, spine_pos + Vector2(STEP if tier % 2 == 0 else -STEP, 0), _unlock_cost(tier + 1), "unlock", {"kind": UNLOCKS[tier][1], "tier": tier + 1})
		previous = spine_key
	# --- more workers: continue the worker row to the left
	var workers_50: Vector2 = original_positions.get("workers_50", root + Vector2(-1300, 0))
	previous = "workers_50"
	var worker_steps := [60, 70, 80, 90, 100]
	for index in range(worker_steps.size()):
		var key := "bdr_workers_%d" % worker_steps[index]
		_add(key, previous, workers_50 + Vector2(-STEP * (index + 1), 0), [2, 2, 3, 3, 5][index], "workers", {"limit": worker_steps[index]})
		previous = key
	# --- worker training (which dice tiers workers may roll), below the new worker row
	previous = "bdr_workers_60"
	for index in range(3):
		var key := "bdr_training_%d" % (index + 1)
		_add(key, previous, workers_50 + Vector2(-STEP * (index + 1), STEP), [2, 3, 5][index], "training", {"tier": [4, 7, 10][index]})
		previous = key
	# --- dice families (tier I and II) to the right of the prehistoric branch
	var right_anchor: Vector2 = original_positions.get("prehistoric_radius", root + Vector2(1300, 0))
	var hub := right_anchor + Vector2(STEP, 0)
	_add("bdr_families", "prehistoric_radius", hub, 2, "families", {})
	# two combs: the upper row grows its level II nodes upwards, the lower row downwards
	for row in range(FAMILY_ROWS.size()):
		var direction := -1.0 if row == 0 else 1.0
		var row_families: Array = FAMILY_ROWS[row]
		previous = "bdr_families"
		for index in range(row_families.size()):
			var family: String = row_families[index]
			var base := hub + Vector2(STEP * (index + 1), STEP * direction)
			var first_key := "bdr_family_%s_1" % family
			_add(first_key, previous, base, 3, "family", {"family": family, "level": 1})
			_add("bdr_family_%s_2" % family, first_key, base + Vector2(0, STEP * direction), 6, "family", {"family": family, "level": 2})
			previous = first_key
	# --- utility row below the diamond branch
	var bottom_anchor: Vector2 = original_positions.get("diamond_payout_3", root + Vector2(1300, 1800))
	previous = "diamond_payout_3"
	for index in range(UTILITY.size()):
		var key: String = UTILITY[index]
		_add(key, previous, bottom_anchor + Vector2(-STEP * index, STEP), [2, 3, 2, 3, 3, 3, 3, 3, 5, 3, 3, 5][index], "utility", {})
		previous = key


func _unlock_cost(tier: int) -> int:
	# Balance (v1.0): the new talents cost about 1.5x more than in the first version.
	return [2, 2, 3, 3, 5, 5, 6, 6, 8, 8][clampi(tier, 1, 10) - 1]


func _add(key: String, prereq: String, pos: Vector2, cost: int, type: String, data: Dictionary) -> void:
	var entry := data.duplicate()
	entry["prereq"] = prereq
	entry["pos"] = pos
	entry["cost"] = cost
	entry["type"] = type
	defs[key] = entry
	order.append(key)


func has(key: String) -> bool:
	return defs.has(key)


func cost(key: String) -> int:
	return int(defs.get(key, {}).get("cost", 1))


func family_bonus_percent(family: String, owned: Callable) -> int:
	var percent := 0
	if owned.call("bdr_family_%s_1" % family):
		percent += 50
	if owned.call("bdr_family_%s_2" % family):
		percent += 150
	return percent
