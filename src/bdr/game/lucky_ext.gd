extends RefCounted
## Dice Rush Extended - lucky cube extension:
##  * every owned new dice can get levels from lucky cubes,
##  * 10 dice can only be found in lucky cubes (they join the pool after N opened cubes),
##  * every cube has small chances for extra rewards (cash bag, free dice, lucky streak,
##    talent gold) and to unlock a locked new dice early.

const I18N := preload("res://bdr/core/i18n.gd")
const NumFmt := preload("res://bdr/core/numfmt.gd")
const UIKit := preload("res://bdr/ui/ui_kit.gd")

## Lucky-only dice and the number of opened cubes after which they can drop.
const GATES := {"clover": 10, "bunny": 50, "luckyblock": 110, "owl": 180, "comet": 250,
	"treasure": 320, "quantum": 390, "fox": 460, "timedie": 530, "cosmic": 600}
const GATE_ORDER := ["clover", "bunny", "luckyblock", "owl", "comet", "treasure", "quantum", "fox", "timedie", "cosmic"]
const BONUS_KINDS := ["bdr_cash", "bdr_free", "bdr_boost", "bdr_gold"]
## Chance per opened cube (extra rewards come on top of the normal level drop).
const CHANCE := {"bdr_cash": 0.04, "bdr_free": 0.02, "bdr_boost": 0.008, "bdr_gold": 0.005, "unlock": 0.01}
const MAX_PER_PURCHASE := {"bdr_gold": 2, "unlock": 2}
const CASH_CUBE_PRICES := 2.0
const BOOST_SECONDS := 60.0
const BOOST_MAX_SECONDS := 900.0
const BOOST_MULTIPLIER := 2.0
const FREE_DICE_PER_DROP := 3
const ICONS := {
	"bdr_cash": ["res://bdr/art/ui/lucky_cash.png", "res://assets/art/магаизн 5050.png"],
	"bdr_free": ["res://bdr/art/ui/lucky_free.png", "res://assets/art/cube d6 1.png"],
	"bdr_boost": ["res://bdr/art/ui/lucky_boost.png", "res://bdr/art/dice/clover.png"],
	"bdr_gold": ["res://assets/art/gold.png"],
	"unlock": ["res://bdr/art/ui/lucky_unlock.png", "res://assets/art/lucky_dice/gold_lucky_cube.png"],
}

var game: Node
var main: Node
var rng := RandomNumberGenerator.new()
var _tier_floor: Dictionary = {}
var _box: Control
var _box_icons: Dictionary = {}     # kind -> TextureRect
var _box_labels: Dictionary = {}    # kind -> Label
var _box_checks: Dictionary = {}    # kind -> TextureRect
var _box_next: Label
var _box_signature := ""


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	rng.randomize()


# ---------------------------------------------------------------- pool
## New dice that get levels from lucky cubes: owned ones (and ones that already have levels).
func owned_kinds() -> Array[String]:
	var result: Array[String] = []
	for kind in game.catalog.ids:
		if game.count(kind) > 0 or int(main.die_levels.get(kind, 1)) > 1:
			result.append(kind)
	return result


## Lucky-only dice that are not found yet but already can drop.
func gate_kinds_in_pool(purchase_total: int) -> Array[String]:
	var result: Array[String] = []
	for kind in GATE_ORDER:
		if purchase_total >= int(GATES[kind]) and not game.is_unlocked(kind):
			result.append(kind)
	return result


## Lucky-only dice whose gate is crossed by this purchase: they drop for sure.
func forced_unlocks(old_total: int, new_total: int) -> Array[String]:
	var result: Array[String] = []
	for kind in GATE_ORDER:
		var gate := int(GATES[kind])
		if old_total < gate and new_total >= gate and not game.is_unlocked(kind):
			result.append(kind)
	return result


func gate_of(kind: String) -> int:
	return int(GATES.get(kind, -1))


func is_bonus(kind: String) -> bool:
	return kind in BONUS_KINDS


func is_known_reward(kind: String) -> bool:
	return is_bonus(kind) or game.is_custom(kind)


## Locked new dice (not lucky-only) that a lucky cube may unlock early.
func unlock_candidates() -> Array[String]:
	var reach := reach_tier()
	var result: Array[String] = []
	for kind in game.catalog.ids:
		if game.is_unlocked(kind) or GATES.has(kind):
			continue
		if int(game.catalog.by_id[kind].tier) <= reach:
			result.append(kind)
	return result


## Highest tier a lucky cube may unlock: one above the best unlocked new dice or above what
## the player can nearly afford.
func reach_tier() -> int:
	var reach := 1
	for kind in game.catalog.ids:
		if game.is_unlocked(kind):
			reach = maxi(reach, int(game.catalog.by_id[kind].tier) + 1)
	var wealth: float = maxf(float(main.money), 0.0) * 10.0
	for tier in range(1, 11):
		if _tier_floor_price(tier) <= wealth:
			reach = maxi(reach, tier + 1)
	return clampi(reach, 1, 10)


func _tier_floor_price(tier: int) -> float:
	if _tier_floor.is_empty():
		for kind in game.catalog.ids:
			var def: Dictionary = game.catalog.by_id[kind]
			var t := int(def.tier)
			var price := float(def.price)
			_tier_floor[t] = minf(float(_tier_floor.get(t, INF)), price)
	return float(_tier_floor.get(tier, INF))


# ---------------------------------------------------------------- rolling
## Extra rewards of one purchase: bonus kinds -> drops, and unlocked dice kinds -> 1.
func roll_extras(purchase_count: int) -> Dictionary:
	var result := {}
	for key in BONUS_KINDS:
		var hits := _binomial(purchase_count, float(CHANCE[key]) * game.tarot.value("lucky_chance"))
		if MAX_PER_PURCHASE.has(key):
			hits = mini(hits, int(MAX_PER_PURCHASE[key]))
		if hits > 0:
			result[key] = hits
	var unlock_hits := mini(_binomial(purchase_count, float(CHANCE.unlock) * game.tarot.value("lucky_unlock")), int(MAX_PER_PURCHASE.unlock))
	if unlock_hits > 0:
		var candidates := unlock_candidates()
		for _index in range(unlock_hits):
			if candidates.is_empty():
				break
			var pick := rng.randi_range(0, candidates.size() - 1)
			result[candidates[pick]] = 1
			candidates.remove_at(pick)
	return result


func _binomial(trials: int, chance: float) -> int:
	if trials <= 0 or chance <= 0.0:
		return 0
	if trials <= 4000:
		var hits := 0
		for _index in range(trials):
			if rng.randf() < chance:
				hits += 1
		return hits
	var mean := float(trials) * chance
	var deviation := sqrt(float(trials) * chance * (1.0 - chance))
	return clampi(int(round(rng.randfn(mean, deviation))), 0, trials)


# ---------------------------------------------------------------- applying rewards
func snapshot() -> Dictionary:
	return {"unlocked": game.unlocked.duplicate(), "extra": game.extra.duplicate(true), "gold": main.golden_coins}


func restore(data: Dictionary) -> void:
	game.unlocked = data.unlocked
	game.extra = data.extra
	main.golden_coins = int(data.gold)


## Applies a bonus reward (part of the lucky transaction) and returns its reward entry.
func apply_bonus(kind: String, drops: int, average_cube_price: float) -> Dictionary:
	var reward := {"kind": kind, "count": drops}
	match kind:
		"bdr_cash":
			var amount: float = minf(1.0e300, average_cube_price * CASH_CUBE_PRICES * float(drops) * game.tarot.value("cash"))
			main.money = minf(1.0e300, float(main.money) + amount)
			reward["amount"] = main._bdr_money_to_save(amount)
		"bdr_free":
			reward["die"] = _free_dice_kind()
			reward["dice"] = drops * FREE_DICE_PER_DROP
		"bdr_boost":
			var seconds := BOOST_SECONDS * float(drops)
			game.extra["lucky_boost"] = minf(BOOST_MAX_SECONDS, boost_left() + seconds)
			reward["seconds"] = int(seconds)
		"bdr_gold":
			main.golden_coins += drops
	return reward


## First unlock of a new dice through a lucky cube.
func apply_unlock(kind: String, drops: int) -> Dictionary:
	game.unlock(kind, false)
	var level := maxi(1, int(main.die_levels.get(kind, 1)))
	if drops > 1:
		level += main._lucky_level_gain(drops - 1)
	main.die_levels[kind] = level
	game.stat("lucky_unlocks", 1)
	return {"kind": kind, "count": drops, "old_level": 0, "new_level": level, "unlock": true}


## Things that may only happen after the purchase was saved (spawning dice actors).
func after_commit(rewards: Array) -> void:
	for reward in rewards:
		if reward is not Dictionary:
			continue
		match str(reward.get("kind", "")):
			"bdr_free":
				var kind := str(reward.get("die", "50_50"))
				for _index in range(int(reward.get("dice", 0))):
					game.spawn_free(kind, main._random_spawn_position())
				game.stat("lucky_free_dice", int(reward.get("dice", 0)))
			"bdr_cash":
				game.stat("lucky_cash_bags", int(reward.get("count", 1)))
			"bdr_boost":
				game.stat("lucky_streaks", int(reward.get("count", 1)))
			"bdr_gold":
				game.stat("lucky_gold", int(reward.get("count", 1)))
	main._invalidate_eco()


func _free_dice_kind() -> String:
	var options: Array[String] = ["50_50"]
	if main.dice_d4_count > 0:
		options.append("d4")
	for kind in game.catalog.ids:
		if game.count(kind) > 0 and game.is_unlocked(kind):
			options.append(kind)
	return options[rng.randi_range(0, options.size() - 1)]


# ---------------------------------------------------------------- lucky streak
func boost_left() -> float:
	return maxf(0.0, float(game.extra.get("lucky_boost", 0.0)))


func boost_multiplier() -> float:
	return BOOST_MULTIPLIER + game.tarot.value("boost_bonus") if boost_left() > 0.0 else 1.0


## Starts (or extends) a lucky streak, e.g. from a tarot card when an event begins.
func add_boost(seconds: float) -> void:
	if seconds <= 0.0:
		return
	game.extra["lucky_boost"] = minf(BOOST_MAX_SECONDS, boost_left() + seconds)


func process(delta: float) -> void:
	var left := boost_left()
	if left <= 0.0:
		return
	left -= delta
	if left <= 0.0:
		game.extra.erase("lucky_boost")
	else:
		game.extra["lucky_boost"] = left


# ---------------------------------------------------------------- texts / icons
static func format_time(seconds: float) -> String:
	var total := maxi(0, int(ceil(seconds)))
	return "%d:%02d" % [total / 60, total % 60]


func icon(kind: String) -> String:
	var paths: Array = ICONS.get(kind, ICONS.unlock)
	for path in paths:
		if ResourceLoader.exists(path) or FileAccess.file_exists(path):
			return path
	return paths[-1]


func bonus_title() -> String:
	return I18N.t("lucky.bonus_title")


func bonus_name(kind: String) -> String:
	return I18N.t("lucky." + kind.trim_prefix("bdr_"))


func reward_detail(reward: Dictionary) -> String:
	var kind := str(reward.get("kind", ""))
	match kind:
		"bdr_cash":
			return I18N.f("lucky.cash_detail", {"v": main._bdr_money_text(main._bdr_parse_money(reward.get("amount", "0")), false)})
		"bdr_free":
			return I18N.f("lucky.free_detail", {"n": int(reward.get("dice", 0)), "name": main._lucky_kind_name(str(reward.get("die", "50_50")))})
		"bdr_boost":
			return I18N.f("lucky.boost_detail", {"t": format_time(float(reward.get("seconds", 0)))})
		"bdr_gold":
			return I18N.f("lucky.gold_detail", {"n": int(reward.get("count", 1))})
	if bool(reward.get("unlock", false)):
		return I18N.t("lucky.unlocked")
	return ""


# ---------------------------------------------------------------- info box (left lucky panel)
func refresh_box() -> void:
	if not is_instance_valid(main.lucky_panel):
		return
	if not is_instance_valid(_box):
		_build_box()
	var parts: Array[String] = [str(main.lucky_cubes_purchased)]
	for kind in GATE_ORDER:
		parts.append("1" if game.is_unlocked(kind) else "0")
	var signature := ",".join(parts) + str(GameSession.language)
	if signature == _box_signature:
		return
	_box_signature = signature
	var total: int = main.lucky_cubes_purchased
	var next_kind := ""
	for kind in GATE_ORDER:
		var found: bool = game.is_unlocked(kind)
		var open := total >= int(GATES[kind])
		var tex: TextureRect = _box_icons[kind]
		tex.modulate = Color.WHITE if found else (Color(0.55, 0.62, 0.55, 0.9) if open else Color(0.0, 0.0, 0.0, 0.75))
		var label: Label = _box_labels[kind]
		label.text = "" if found else ("?" if open else str(GATES[kind]))
		(_box_checks[kind] as TextureRect).visible = found
		label.add_theme_color_override("font_color", Color("75ff64") if found else (Color("ffd166") if open else Color("c9d7c9")))
		if next_kind.is_empty() and not found:
			next_kind = kind
	if next_kind.is_empty():
		_box_next.text = I18N.t("lucky.all_found")
	elif total >= int(GATES[next_kind]):
		_box_next.text = I18N.f("lucky.next_ready", {"name": I18N.upper(str(game.display_name(next_kind)))})
	else:
		_box_next.text = I18N.f("lucky.next_gate", {"name": "???", "n": int(GATES[next_kind])})
	UIKit.fit(_box_next)


func _build_box() -> void:
	_box = Control.new()
	_box.name = "BDRLuckyOnlyDice"
	_box.position = Vector2(220, 560)
	_box.size = Vector2(302, 360)
	_box.z_index = 3
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main.lucky_panel.add_child(_box)
	var title := UIKit.label(_box, I18N.t("lucky.exclusive_title"), Rect2(0, 0, 302, 40), 13, HORIZONTAL_ALIGNMENT_CENTER, Color("ffd166"))
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	for index in range(GATE_ORDER.size()):
		var kind: String = GATE_ORDER[index]
		var column := index % 5
		var row := index / 5
		var cell := Control.new()
		cell.position = Vector2(6 + column * 59, 40 + row * 88)
		cell.size = Vector2(56, 84)
		cell.mouse_filter = Control.MOUSE_FILTER_STOP
		_box.add_child(cell)
		var tex := UIKit.texture(cell, game.icon_path(kind), Rect2(2, 0, 52, 52))
		_box_icons[kind] = tex
		var label := UIKit.label(cell, "", Rect2(0, 52, 56, 28), 11, HORIZONTAL_ALIGNMENT_CENTER)
		_box_labels[kind] = label
		var check := TextureRect.new()
		check.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		check.texture = main.talent_check_texture
		check.position = Vector2(34, 32)
		check.size = Vector2(22, 22)
		check.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		check.mouse_filter = Control.MOUSE_FILTER_IGNORE
		check.visible = false
		cell.add_child(check)
		_box_checks[kind] = check
		cell.mouse_entered.connect(_show_gate_tooltip.bind(kind))
		cell.mouse_exited.connect(game.hide_tooltip)
	_box_next = UIKit.paragraph(_box, "", Rect2(0, 218, 302, 54), 11, HORIZONTAL_ALIGNMENT_CENTER, Color("e8f5e8"))
	UIKit.paragraph(_box, I18N.t("lucky.chance_note"), Rect2(0, 274, 302, 86), 10, HORIZONTAL_ALIGNMENT_CENTER, Color("9fd7a7"))


func _show_gate_tooltip(kind: String) -> void:
	var found: bool = game.is_unlocked(kind)
	var name: String = game.display_name(kind) if found or main.lucky_cubes_purchased >= int(GATES[kind]) else "???"
	var text := "[color=#ffd166][font_size=18]%s[/font_size][/color]\n\n%s" % [name, I18N.f("lucky.gate_tip", {"n": int(GATES[kind])})]
	if found:
		text += "\n" + I18N.t("ui.unlocked")
	game.show_text_tooltip(text, 150.0)
