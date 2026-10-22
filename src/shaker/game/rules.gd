extends RefCounted
## Dice Shaker rules - the same formulas as tools/shaker/shaker_rules.py (the balance simulation).
## Keep both in sync.

const Data := preload("res://shaker/game/data.gd")


# ---------------------------------------------------------------------------------------- stats
static func empty_stats() -> Dictionary:
	var stats := {}
	for key in Data.stat_kinds:
		stats[key] = 1.0 if str(Data.stat_kinds[key]) == "mul" else 0.0
	return stats


static func apply_stat(stats: Dictionary, key: String, value: float) -> void:
	match str(Data.stat_kinds.get(key, "add")):
		"add":
			stats[key] = float(stats.get(key, 0.0)) + value
		"mul":
			stats[key] = float(stats.get(key, 1.0)) * value
		"max":
			stats[key] = maxf(float(stats.get(key, 0.0)), value)
		"min":
			var current := float(stats.get(key, 0.0))
			stats[key] = value if current <= 0.0 else minf(current, value)


static func compute_stats(state: Dictionary) -> Dictionary:
	var stats := empty_stats()
	for talent_id in state.get("talents", []):
		var talent: Dictionary = Data.talents_by_id.get(str(talent_id), {})
		for effect in talent.get("effects", []):
			apply_stat(stats, str(effect[0]), float(effect[1]))
	var tarot_state: Dictionary = state.get("tarot", {})
	for card_id in tarot_state:
		var copies := clampi(int(tarot_state[card_id]), 0, 4)
		if copies <= 0 or not Data.tarot_by_id.has(card_id):
			continue
		for effect in Data.tarot_by_id[card_id].effects:
			apply_stat(stats, str(effect[0]), float((effect[1] as Array)[copies - 1]))
	var black_state: Dictionary = state.get("black", {})
	for card_id in black_state:
		var copies := int(black_state[card_id])
		if copies <= 0 or not Data.black_by_id.has(card_id):
			continue
		for _copy in range(copies):
			for effect in Data.black_by_id[card_id].effects:
				var value = effect[1]
				if value is String and value == "copies+1":
					apply_stat(stats, str(effect[0]), float(copies + 1))
				else:
					apply_stat(stats, str(effect[0]), float(value))
	var equipped := Data.gauntlet(int(state.get("gauntlet", 0)))
	for effect in equipped.get("effects", []):
		apply_stat(stats, str(effect[0]), float(effect[1]))
	stats["money_pct"] = float(stats.money_pct) + float(Data.b("gauntlet_owned_pct", 2)) * (state.get("gauntlets", []) as Array).size()
	stats["money_pct"] = float(stats.money_pct) + float(Data.b("collection_pct", 2)) * (state.get("discovered", []) as Array).size()
	for die in state.get("dice", []):
		var def := Data.die(str(die.id))
		var fx := str(def.get("fx", ""))
		if Data.passive_fx.has(fx):
			apply_stat(stats, str(Data.passive_fx[fx]), float(def.p.pct))
	return stats


static func discount(stats: Dictionary, key: String) -> float:
	return 1.0 - minf(float(stats.get(key, 0.0)), float(Data.b("max_discount_pct", 80))) / 100.0


# -------------------------------------------------------------------------------------- derived
static func shake_time(stats: Dictionary) -> float:
	var normal := maxf(float(Data.b("shake_time_min", 0.35)), float(Data.b("shake_time", 1.15)) / (1.0 + float(stats.speed_pct) / 100.0))
	if turbo(stats):
		return maxf(0.25, normal * 0.55)   # turbo event: the dice land faster
	return normal


static func auto_interval(stats: Dictionary) -> float:
	var normal := 0.0
	if float(stats.auto_every) > 0.0:
		normal = maxf(shake_time(stats), float(stats.auto_every) / ((1.0 + float(stats.auto_pct) / 100.0) * float(stats.auto_x)))
	if turbo(stats):
		# turbo event: auto-shake 1 s faster (and at least every second, also without the auto-shake talent)
		var base := normal if normal > 0.0 else 2.0
		return maxf(shake_time(stats), minf(base, 2.0) - 1.0)
	return normal


# ------------------------------------------------------------------------------- random events
## Multiplier of a running random event (shop / talent / lucky / tarot sale, money rush), 1 = none.
static func event_mult(stats: Dictionary, key: String) -> float:
	return float(stats.get("event_" + key, 1.0))


static func turbo(stats: Dictionary) -> bool:
	return float(stats.get("event_turbo", 0.0)) > 0.0


static func xp_need(level: int, stats: Dictionary) -> float:
	var need := float(Data.b("xp_base", 6.0)) * pow(float(Data.b("xp_growth", 1.13)), level - 1) * (1.0 - minf(float(stats.xp_need_pct), 60.0) / 100.0)
	return maxf(1.0, floorf(need))


static func level_mult(level: int) -> float:
	return pow(float(Data.b("level_growth", 1.08)), level - 1) * pow(float(Data.b("level_milestone_mult", 2.0)), level / int(Data.b("level_milestone", 10)))


static func rarity_mult(stats: Dictionary, rarity: String) -> float:
	return (1.0 + float(stats.get(rarity + "_pct", 0.0)) / 100.0) * float(stats.get(rarity + "_x", 1.0))


static func combo_boost(stats: Dictionary, mult: float) -> float:
	return 1.0 + (mult - 1.0) * (1.0 + float(stats.combo_pct) / 100.0) * float(stats.combo_x)


static func group_mult(stats: Dictionary, size: int) -> float:
	if size < 2:
		return 1.0
	var table: Dictionary = Data.b("combo_group", {})
	return combo_boost(stats, float(table.get(str(mini(size, 6)), 1.0)))


static func crit_total(stats: Dictionary) -> float:
	return float(Data.b("crit_mult", 3.0)) + float(stats.crit_mult)


static func money_mult(stats: Dictionary) -> float:
	return (1.0 + float(stats.money_pct) / 100.0) * float(stats.money_x)


static func xp_gain(stats: Dictionary) -> float:
	return maxf(0.05, (1.0 + float(stats.xp_pct) / 100.0) * float(stats.xp_x))


static func max_dice() -> int:
	return int(Data.b("max_dice", 12))


static func big_dice_max() -> int:
	return int(Data.b("big_dice_max", 6))


# ---------------------------------------------------------------------------------------- shake
## Faces for the next shake (also advances the pi dice). Returns {faces, meteor}.
static func roll_faces(state: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var dice: Array = state.dice
	var faces: Array[int] = []
	for die in dice:
		var def := Data.die(str(die.id))
		var options: Array = def.faces
		match str(def.fx):
			"max":
				faces.append(int(options.max()))
			"pi":
				var index := int(die.get("pi", 0))
				faces.append(int(options[index % options.size()]))
				die["pi"] = index + 1
			_:
				faces.append(int(options[rng.randi_range(0, options.size() - 1)]))
	for die in dice:
		var def := Data.die(str(die.id))
		if str(def.fx) == "meteor" and rng.randf() * 100.0 < float(def.p.chance):
			for i in dice.size():
				faces[i] = int((Data.die(str(dice[i].id)).faces as Array).max())
			return {"faces": faces, "meteor": true}
	return {"faces": faces, "meteor": false}


## One shake. `faces` come from roll_faces. Returns the payout and what happened (for the effects).
static func resolve(state: Dictionary, stats: Dictionary, faces_in: Array, rng: RandomNumberGenerator, manual: bool) -> Dictionary:
	var dice: Array = state.dice
	var n := dice.size()
	var faces: Array[int] = []
	var min_face := int(stats.min_face)
	for i in n:
		var face := int(faces_in[i])
		if min_face > 0 and face < min_face:
			face = min_face
		if float(stats.ones_as_six) > 0.0 and face == 1:
			face = 6
		faces.append(face)
	var defs: Array = []
	for die in dice:
		defs.append(Data.die(str(die.id)))
	# combos: jokers join the biggest group
	var combo_faces: Array[int] = faces.duplicate()
	var wild: Array[int] = []
	for i in n:
		if str(defs[i].fx) == "wild":
			wild.append(i)
	if not wild.is_empty():
		var counts := {}
		for i in n:
			if i not in wild:
				counts[combo_faces[i]] = int(counts.get(combo_faces[i], 0)) + 1
		if not counts.is_empty():
			var best_face := -1
			var best_count := -1
			for face in counts:
				if int(counts[face]) > best_count or (int(counts[face]) == best_count and int(face) > best_face):
					best_count = int(counts[face])
					best_face = int(face)
			for i in wild:
				combo_faces[i] = best_face
	var groups := {}
	for i in n:
		groups[combo_faces[i]] = int(groups.get(combo_faces[i], 0)) + 1
	var shake_mult := 1.0
	var events: Array[String] = []
	var straight := n >= 6
	if straight:
		for value in range(1, 7):
			if not groups.has(value):
				straight = false
				break
	if straight:
		shake_mult *= combo_boost(stats, float(Data.b("combo_straight", 2.0)))
		events.append("straight")
	if n >= 3 and groups.size() == 1:
		shake_mult *= combo_boost(stats, float(Data.b("combo_all_same", 4.0)))
		events.append("all_same")
	var best_group := 1
	for face in groups:
		best_group = maxi(best_group, int(groups[face]))
	# auras
	var rarity_set := {}
	var aura_all := 0.0
	var aura_rarity := {}
	var aura_others := 0.0
	for i in n:
		rarity_set[str(defs[i].rarity)] = true
		match str(defs[i].fx):
			"global":
				aura_all += float(defs[i].p.pct)
			"rarity_aura":
				var target := str(defs[i].p.rarity)
				aura_rarity[target] = float(aura_rarity.get(target, 0.0)) + float(defs[i].p.pct)
			"aura":
				aura_others += float(defs[i].p.pct)
	var streak := int(state.get("streak", 0))
	var next_shake := int(state.get("shakes", 0)) + 1
	var values: Array[float] = []
	var group_of: Array[int] = []
	for i in n:
		var die: Dictionary = dice[i]
		var def: Dictionary = defs[i]
		var p: Dictionary = def.p
		var face := faces[i]
		var m := 1.0
		match str(def.fx):
			"gamble":
				m = float(p.mult) if rng.randf() * 100.0 < float(p.chance) else 0.0
			"high":
				m = float(p.mult) if face >= int(p.face) else 1.0
			"ones":
				m = float(p.mult) if face == 1 else 1.0
			"pair":
				m = 1.0 + float(p.pct) / 100.0 * float(int(groups[combo_faces[i]]) - 1)
			"crit":
				m = float(p.mult) if rng.randf() * 100.0 < float(p.chance) else 1.0
			"d20":
				m = float(p.mult) if face == 20 else 1.0
			"streak":
				m = 1.0 + minf(float(p.step) * streak, float(p.max)) / 100.0
			"every":
				m = float(p.mult) if next_shake % int(p.n) == 0 else 1.0
			"grow":
				m = 1.0 + minf(float(p.step) * int(die.get("grow", 0)), float(p.max)) / 100.0
			"market":
				m = float(die.get("market", (float(p.min) + float(p.max)) * 0.5))
			"per_level":
				m = 1.0 + float(p.pct) / 100.0 * int(die.level)
			"per_die":
				m = 1.0 + float(p.pct) / 100.0 * n
			"per_rarity":
				m = 1.0 + float(p.pct) / 100.0 * rarity_set.size()
			"bomb":
				m = float(p.mult) if face == 6 else (0.0 if face == 1 else 1.0)
			"even":
				m = float(p.mult) if face % 2 == 0 else 1.0
			"odd":
				m = float(p.mult) if face % 2 == 1 else 1.0
			"pi":
				m = float(p.mult)
		if face == 6:
			m *= float(stats.six_x)
		var aura := aura_all + float(aura_rarity.get(str(def.rarity), 0.0)) + aura_others
		if str(def.fx) == "aura":
			aura -= float(p.pct)   # an aura die helps the others, not itself
		var group_size := int(groups[combo_faces[i]])
		group_of.append(group_size)
		var value := face * float(def.pay) * level_mult(int(die.level)) * rarity_mult(stats, str(def.rarity)) * m
		value *= (1.0 + aura / 100.0) * group_mult(stats, group_size)
		values.append(value)
		if str(def.fx) == "grow":
			die["grow"] = 0 if face == 1 else int(die.get("grow", 0)) + 1
	# swallow / copy / best die
	for i in n:
		if str(defs[i].fx) != "swallow":
			continue
		var weakest := -1
		for j in n:
			if j == i or values[j] <= 0.0 or str(defs[j].fx) == "swallow":
				continue
			if weakest < 0 or values[j] < values[weakest]:
				weakest = j
		if weakest >= 0:
			values[i] += values[weakest] * float(defs[i].p.mult)
			values[weakest] = 0.0
	var copies: Array = []
	for i in n:
		if str(defs[i].fx) == "copy" and n > 1:
			var best := 0.0
			for j in n:
				if j != i:
					best = maxf(best, values[j])
			copies.append([i, best * float(defs[i].p.pct) / 100.0])
	for entry in copies:
		values[int(entry[0])] += float(entry[1])
	if float(stats.best_pct) > 0.0 and n > 0:
		var top := 0
		for j in n:
			if values[j] > values[top]:
				top = j
		values[top] *= 1.0 + float(stats.best_pct) / 100.0
	var total := 0.0
	for value in values:
		total += value
	var share := 0.0
	for def in defs:
		if str(def.fx) == "share":
			share += float(def.p.pct)
	total *= 1.0 + share / 100.0
	# the whole shake
	var face_sum := 0
	for face in faces:
		face_sum += face
	for def in defs:
		match str(def.fx):
			"seven":
				if face_sum % 7 == 0:
					shake_mult *= float(def.p.mult)
					events.append("seven")
			"jackpot":
				if rng.randf() * 100.0 < float(def.p.chance):
					shake_mult *= float(def.p.mult)
					events.append("jackpot")
	var crit := rng.randf() * 100.0 < minf(float(stats.crit_chance), 50.0)
	if crit:
		shake_mult *= crit_total(stats)
		events.append("crit")
	if float(stats.double_chance) > 0.0 and rng.randf() * 100.0 < float(stats.double_chance):
		shake_mult *= 2.0
		events.append("double")
	if float(stats.bell_x) > 1.0 and next_shake % 10 == 0:
		shake_mult *= float(stats.bell_x)
		events.append("bell")
	var mult := money_mult(stats)
	if manual:
		mult *= 1.0 + float(stats.manual_pct) / 100.0
	total *= shake_mult * mult * event_mult(stats, "money")
	var echo := float(stats.echo_chance)
	for def in defs:
		if str(def.fx) == "echo":
			echo += float(def.p.chance)
	if rng.randf() * 100.0 < minf(echo, 50.0):
		total *= 2.0
		events.append("echo")
	# coin bags and treasures are worth "average shakes" (never a share of the income)
	var average := float(state.get("avg_shake", 0.0))
	state["avg_shake"] = total if average <= 0.0 else average * 0.98 + total * 0.02
	if float(stats.treasure_n) > 0.0 and next_shake % 25 == 0:
		total += float(stats.treasure_n) * float(state.avg_shake)
		events.append("treasure")
	if float(stats.coin_chance) > 0.0 and rng.randf() * 100.0 < float(stats.coin_chance):
		total += 20.0 * float(state.avg_shake)
		events.append("coin")
	state["shakes"] = next_shake
	return {"total": total, "faces": faces, "values": values, "groups": group_of, "best_group": best_group, "events": events, "crit": crit}


## XP for every die after a shake. Returns the indices of dice that levelled up.
static func give_xp(state: Dictionary, stats: Dictionary) -> Array[int]:
	var dice: Array = state.dice
	var leveled: Array[int] = []
	if dice.is_empty():
		return leveled
	var gain := xp_gain(stats)
	var lowest := 0
	for j in dice.size():
		var a: Dictionary = dice[j]
		var b: Dictionary = dice[lowest]
		if int(a.level) < int(b.level) or (int(a.level) == int(b.level) and float(a.xp) < float(b.xp)):
			lowest = j
	var teacher := 0.0
	for die in dice:
		var def := Data.die(str(die.id))
		if str(def.fx) == "teacher":
			teacher += float(def.p.xp)
	for i in dice.size():
		var amount := gain
		if i == lowest:
			amount = gain * float(stats.catchup_x) + teacher * gain
		if add_xp(dice[i], amount, stats):
			leveled.append(i)
	return leveled


static func add_xp(die: Dictionary, amount: float, stats: Dictionary) -> bool:
	var max_level := int(Data.b("max_level", 100))
	if int(die.level) >= max_level:
		return false
	var before := int(die.level)
	die["xp"] = float(die.get("xp", 0.0)) + amount
	while int(die.level) < max_level:
		var need := xp_need(int(die.level), stats)
		if float(die.xp) < need:
			break
		die["xp"] = float(die.xp) - need
		die["level"] = int(die.level) + 1
	if int(die.level) >= max_level:
		die["xp"] = 0.0
	return int(die.level) > before


# --------------------------------------------------------------------------------------- prices
static func gumball_price(state: Dictionary, stats: Dictionary) -> float:
	var growth := maxf(1.05, float(Data.gumball.get("growth", 1.32)) - float(stats.gumball_slow) / 100.0)
	return float(Data.gumball.get("base", 25.0)) * pow(growth, int(state.get("gumballs", 0))) * discount(stats, "gumball_discount")


static func gumball_weights(stats: Dictionary) -> Array[float]:
	var luck := 1.0 + float(stats.gumball_luck) / 100.0
	var weights: Array[float] = []
	var colors: Array = Data.gumball.get("colors", [])
	for i in colors.size():
		weights.append(float(colors[i].weight) * pow(luck, i))
	return weights


## Draws one gumball: {"color": index, "ball": sprite index, "tp": talent points}
static func roll_gumball(stats: Dictionary, rng: RandomNumberGenerator) -> Dictionary:
	var weights := gumball_weights(stats)
	var total := 0.0
	for w in weights:
		total += w
	var roll := rng.randf() * total
	var colors: Array = Data.gumball.get("colors", [])
	var chosen := 0
	for i in weights.size():
		roll -= weights[i]
		if roll <= 0.0:
			chosen = i
			break
	var color: Dictionary = colors[chosen]
	var amount := float(color.tp) * (1.0 + float(stats.tp_pct) / 100.0) + float(stats.tp_extra)
	var whole := floori(amount)
	if rng.randf() < amount - whole:
		whole += 1
	return {"color": chosen, "ball": int(color.ball), "tp": maxi(1, whole)}


static func is_slot_talent(talent: Dictionary) -> bool:
	return bool(talent.get("slot", false))


## [talent points, money]
static func talent_cost(state: Dictionary, stats: Dictionary, talent_id: String) -> Array:
	var talent: Dictionary = Data.talents_by_id.get(talent_id, {})
	var tp := int(talent.get("tp", 0))
	var money := float(talent.get("money", 0.0))
	if is_slot_talent(talent):
		var next := mini((state.dice as Array).size() + 1, max_dice())
		var cost: Array = Data.slot_costs.get(str(next), [99, 1.0e300])
		tp = int(cost[0])
		money = float(cost[1])
	var sale := event_mult(stats, "talent")
	return [int(ceilf(tp * sale)), money * discount(stats, "talent_discount") * sale]


## "" when the talent can be learned now (money and points aside), otherwise the reason key.
static func talent_block(state: Dictionary, talent_id: String) -> String:
	var talent: Dictionary = Data.talents_by_id.get(talent_id, {})
	var owned: Array = state.get("talents", [])
	if talent_id in owned:
		return "talents.learned"
	var connected := false
	for parent in talent.get("parents", []):
		if str(parent) in owned:
			connected = true
			break
	if not connected:
		return "talents.locked"
	if is_slot_talent(talent):
		var count := (state.dice as Array).size()
		if count >= max_dice():
			return "talents.full"
		if count >= big_dice_max() and "compact" not in owned:
			return "talents.need_compact"
	return ""


static func lucky_odds(stats: Dictionary, tier: int) -> Array[float]:
	var tiers: Array = Data.lucky.get("tiers", [])
	var odds: Array[float] = []
	for value in tiers[tier].odds:
		odds.append(float(value))
	var boost := 1.0 + float(stats.lucky_odds) / 100.0
	odds[3] *= boost
	odds[4] *= boost
	var total := 0.0
	for o in odds:
		total += o
	for i in odds.size():
		odds[i] = odds[i] * 100.0 / total
	return odds


static func lucky_price(state: Dictionary, stats: Dictionary, tier: int, count: int) -> float:
	var tiers: Array = Data.lucky.get("tiers", [])
	var data: Dictionary = tiers[tier]
	var done := int((state.get("lucky_rolled", [0, 0, 0, 0, 0]) as Array)[tier])
	var total := 0.0
	for k in count:
		total += float(data.base) * pow(float(data.growth), done + k)
	return total * discount(stats, "lucky_discount") * event_mult(stats, "lucky")


static func tarot_price(state: Dictionary, stats: Dictionary) -> float:
	return float(Data.tarot_draw.get("base", 2000.0)) * pow(float(Data.tarot_draw.get("growth", 1.33)), int(state.get("tarot_draws", 0))) * discount(stats, "tarot_discount") * event_mult(stats, "tarot")


static func tarot_choices(stats: Dictionary) -> int:
	return int(Data.tarot_draw.get("choices", 3)) + int(stats.tarot_choices)


static func black_price(state: Dictionary, stats: Dictionary, card_id: String) -> float:
	var card: Dictionary = Data.black_by_id.get(card_id, {})
	var copies := int((state.get("black", {}) as Dictionary).get(card_id, 0))
	return float(card.get("price", 1.0e300)) * pow(float(card.get("growth", 10.0)), copies) * discount(stats, "black_discount") * event_mult(stats, "shop")


static func gauntlet_price(stats: Dictionary, index: int) -> float:
	return float(Data.gauntlet(index).get("price", 1.0e300)) * discount(stats, "shop_discount") * event_mult(stats, "shop")


static func table_price(stats: Dictionary, table_id: int) -> float:
	if table_id < 0 or table_id >= Data.tables.size():
		return 1.0e300
	return float(Data.tables[table_id].price) * discount(stats, "shop_discount") * event_mult(stats, "shop")


# ---------------------------------------------------------------------------------------- state
static func new_state() -> Dictionary:
	var start := str(Data.b("start_die", "wood"))
	return {
		"mode": "dice_shaker", "version": 1,
		"money": 0.0, "total_earned": 0.0, "tp": 0, "tp_total": 0,
		"shakes": 0, "gumballs": 0, "tarot_draws": 0, "avg_shake": 0.0,
		"dice": [{"id": start, "level": 1, "xp": 0.0, "locked": false}],
		"talents": ["shaker"], "tarot": {}, "black": {},
		"gauntlets": [], "gauntlet": 0, "tables": [0], "table": 0,
		"discovered": [start], "lucky_rolled": [0, 0, 0, 0, 0],
		"play_time": 0.0, "created": int(Time.get_unix_time_from_system()), "tarot_offer": [],
		"event": "", "event_left": 0.0, "event_timer": float(Data.b("event_every", 300.0)), "last_event": "",
		"hint_done": false,
	}


## Repairs a loaded save (missing keys, unknown dice ...).
static func sanitize(state: Dictionary) -> Dictionary:
	var fresh := new_state()
	for key in fresh:
		if not state.has(key):
			state[key] = fresh[key]
	var dice: Array = []
	for die in state.get("dice", []):
		if die is Dictionary and Data.dice_by_id.has(str(die.get("id", ""))):
			dice.append({
				"id": str(die.id), "level": clampi(int(die.get("level", 1)), 1, int(Data.b("max_level", 100))),
				"xp": maxf(0.0, float(die.get("xp", 0.0))), "locked": bool(die.get("locked", false)),
				"grow": int(die.get("grow", 0)), "pi": int(die.get("pi", 0)),
			})
	if dice.is_empty():
		dice = fresh.dice
	if dice.size() > max_dice():
		dice.resize(max_dice())
	state["dice"] = dice
	state["money"] = clampf(float(state.money), 0.0, float(Data.b("money_cap", 1.0e300)))
	state["tp"] = maxi(0, int(state.tp))
	var talents: Array = []
	for talent_id in state.get("talents", []):
		if Data.talents_by_id.has(str(talent_id)) and str(talent_id) not in talents:
			talents.append(str(talent_id))
	if "shaker" not in talents:
		talents.append("shaker")
	state["talents"] = talents
	# JSON stores every number as a float: turn counters and ids back into ints / strings
	for key in ["tarot", "black"]:
		var cleaned := {}
		if state[key] is Dictionary:
			for card_id in state[key]:
				cleaned[str(card_id)] = maxi(0, int(state[key][card_id]))
		state[key] = cleaned
	for key in ["gauntlets", "tables"]:
		var ints: Array = []
		for value in state.get(key, []):
			if int(value) not in ints:
				ints.append(int(value))
		state[key] = ints
	if 0 not in state.tables:
		(state.tables as Array).append(0)
	state["gauntlet"] = int(state.get("gauntlet", 0))
	state["table"] = int(state.get("table", 0))
	if state.gauntlet != 0 and state.gauntlet not in state.gauntlets:
		state["gauntlet"] = 0
	if state.table not in state.tables:
		state["table"] = 0
	var found: Array = []
	for die_id in state.get("discovered", []):
		if Data.dice_by_id.has(str(die_id)) and str(die_id) not in found:
			found.append(str(die_id))
	for die in dice:
		if str(die.id) not in found:
			found.append(str(die.id))
	state["discovered"] = found
	var events: Dictionary = Data.b("events", {})
	if not events.has(str(state.get("event", ""))):
		state["event"] = ""
		state["event_left"] = 0.0
	state["event_left"] = maxf(0.0, float(state.get("event_left", 0.0)))
	state["event_timer"] = clampf(float(state.get("event_timer", 300.0)), 0.0, float(Data.b("event_every", 300.0)))
	var offer: Array = []
	for card_id in state.get("tarot_offer", []):
		if Data.tarot_by_id.has(str(card_id)):
			offer.append(str(card_id))
	state["tarot_offer"] = offer
	for key in ["shakes", "gumballs", "tarot_draws", "tp_total", "lucky_tier"]:
		state[key] = maxi(0, int(state.get(key, 0)))
	var rolled: Array = []
	for value in state.get("lucky_rolled", []):
		rolled.append(maxi(0, int(value)))
	while rolled.size() < 5:
		rolled.append(0)
	state["lucky_rolled"] = rolled
	return state
