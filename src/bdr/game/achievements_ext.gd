extends RefCounted
## Dice Rush Extended - 67 new achievements (dice, talents, tarot, lucky cubes, events, staff, shop, money).
## They are stored in their own file, so the original achievements.json stays untouched.
## In coop only the host earns them.

const I18N := preload("res://bdr/core/i18n.gd")
const NumFmt := preload("res://bdr/core/numfmt.gd")
const TalentsExt := preload("res://bdr/game/talents_ext.gd")
const LuckyExt := preload("res://bdr/game/lucky_ext.gd")
const EventsExt := preload("res://bdr/game/events.gd")

const SAVE_PATH := "user://bdr_achievements.json"
const SAVE_VERSION := 1
const EVALUATE_EVERY := 2.0
const D := "res://bdr/art/dice/"
const T := "res://bdr/art/tarot/"
const E := "res://bdr/art/events/"
const S := "res://bdr/art/staff/"
const U := "res://bdr/art/ui/"

## id, metric, target, icon, [hidden], [money = progress shown as money]
const CATALOG := [
	{"id": "bdr_unlock_1", "metric": "dice_unlocked", "target": 1, "icon": D + "paper.png"},
	{"id": "bdr_unlock_10", "metric": "dice_unlocked", "target": 10, "icon": D + "candy.png"},
	{"id": "bdr_unlock_25", "metric": "dice_unlocked", "target": 25, "icon": D + "ruby.png"},
	{"id": "bdr_unlock_50", "metric": "dice_unlocked", "target": 50, "icon": D + "dragon.png"},
	{"id": "bdr_unlock_100", "metric": "dice_unlocked", "target": 100, "icon": D + "cosmic.png"},
	{"id": "bdr_kinds_25", "metric": "kinds_owned", "target": 25, "icon": D + "rainbow.png"},
	{"id": "bdr_kinds_60", "metric": "kinds_owned", "target": 60, "icon": D + "galaxy.png"},
	{"id": "bdr_kinds_100", "metric": "kinds_owned", "target": 100, "icon": D + "infinity.png"},
	{"id": "bdr_custom_100", "metric": "custom_dice", "target": 100, "icon": D + "wood.png"},
	{"id": "bdr_custom_1000", "metric": "custom_dice", "target": 1000, "icon": D + "stone.png"},
	{"id": "bdr_tier_5", "metric": "max_tier", "target": 5, "icon": D + "comet.png"},
	{"id": "bdr_tier_10", "metric": "max_tier", "target": 10, "icon": D + "elderdragon.png"},
	{"id": "bdr_sixseven", "metric": "sixseven", "target": 1, "icon": D + "sixseven.png"},
	{"id": "bdr_tetris", "metric": "tetris_tetris", "target": 1, "icon": D + "tetris.png"},
	{"id": "bdr_car_walls", "metric": "car_walls", "target": 100, "icon": D + "car.png"},
	{"id": "bdr_zombies", "metric": "zombie_bites", "target": 50, "icon": D + "zombie.png"},
	{"id": "bdr_nat20", "metric": "nat20", "target": 10, "icon": D + "dnd.png"},
	{"id": "bdr_jackpot", "metric": "jackpot", "target": 1, "icon": D + "jackpot.png"},
	{"id": "bdr_rickroll", "metric": "rickroll", "target": 1, "icon": D + "rickroll.png", "hidden": true},
	{"id": "bdr_doge", "metric": "doge_moon", "target": 1, "icon": D + "doge.png"},
	{"id": "bdr_vault", "metric": "vault_open", "target": 10, "icon": D + "vault.png"},
	{"id": "bdr_supernova", "metric": "supernova", "target": 1, "icon": D + "supernova.png"},
	{"id": "bdr_crit_1", "metric": "crits", "target": 1, "icon": T + "m_wands_9.png"},
	{"id": "bdr_crit_1000", "metric": "crits", "target": 1000, "icon": T + "m_wands_1.png"},
	{"id": "bdr_talent_1", "metric": "talents_bdr", "target": 1, "icon": "res://assets/art/talents/synergy_master.png"},
	{"id": "bdr_talent_25", "metric": "talents_bdr", "target": 25, "icon": "res://assets/art/talents/synergy_master.png"},
	{"id": "bdr_talent_all", "metric": "talents_bdr", "target": 67, "icon": "res://assets/art/talents/synergy_master.png"},
	{"id": "bdr_families", "metric": "family_talents", "target": 13, "icon": D + "pizza.png"},
	{"id": "bdr_workers_100", "metric": "worker_limit", "target": 100, "icon": "res://assets/art/lucky_dice/accountant.png"},
	{"id": "bdr_tarot_big", "metric": "tarot_big_offer", "target": 1, "icon": "res://assets/art/dog_shrine/tarot_grimoire_icon.png"},
	{"id": "bdr_tarot_huge", "metric": "tarot_huge_offer", "target": 1, "icon": "res://assets/art/dog_shrine/tarot_grimoire_icon.png"},
	{"id": "bdr_minor_1", "metric": "minor_cards", "target": 1, "icon": T + "m_cups_2.png"},
	{"id": "bdr_minor_20", "metric": "minor_cards", "target": 20, "icon": T + "m_swords_7.png"},
	{"id": "bdr_minor_40", "metric": "minor_cards", "target": 40, "icon": T + "m_pentacles_10.png"},
	{"id": "bdr_tarot_61", "metric": "tarot_cards_distinct", "target": 61, "icon": "res://assets/art/dog_shrine/tarot_1x/20_Judgement.png"},
	{"id": "bdr_epic", "metric": "tarot_epic", "target": 1, "icon": T + "m_cups_1.png"},
	{"id": "bdr_legendary", "metric": "tarot_legendary", "target": 1, "icon": "res://assets/art/dog_shrine/tarot_1x/19_The Sun.png"},
	{"id": "bdr_sacrificed_1000", "metric": "tarot_dice_sacrificed", "target": 1000, "icon": "res://assets/art/dog_shrine/tarot_grimoire_icon.png"},
	{"id": "bdr_lucky_100", "metric": "lucky_cubes", "target": 100, "icon": "res://assets/art/lucky_dice/gold_lucky_cube.png"},
	{"id": "bdr_lucky_1000", "metric": "lucky_cubes", "target": 1000, "icon": "res://assets/art/lucky_dice/gold_lucky_cube.png"},
	{"id": "bdr_lucky_only", "metric": "lucky_only_found", "target": 10, "icon": D + "clover.png"},
	{"id": "bdr_lucky_unlock", "metric": "lucky_unlocks", "target": 5, "icon": U + "lucky_unlock.png"},
	{"id": "bdr_lucky_gold", "metric": "lucky_gold", "target": 1, "icon": "res://assets/art/gold.png"},
	{"id": "bdr_lucky_streak", "metric": "lucky_streaks", "target": 10, "icon": U + "lucky_boost.png"},
	{"id": "bdr_event_1", "metric": "events_seen", "target": 1, "icon": U + "event_icon.png"},
	{"id": "bdr_event_50", "metric": "events_seen", "target": 50, "icon": U + "event_icon.png"},
	{"id": "bdr_event_all", "metric": "event_kinds", "target": 9, "icon": E + "rainbow.png"},
	{"id": "bdr_coins_500", "metric": "event_coins", "target": 500, "icon": E + "coin_rain.png"},
	{"id": "bdr_chest_10", "metric": "event_chests", "target": 10, "icon": E + "treasure_chest.png"},
	{"id": "bdr_thief_10", "metric": "event_thieves_caught", "target": 10, "icon": E + "thief.png"},
	{"id": "bdr_robbed", "metric": "event_thief_escaped", "target": 1, "icon": E + "thief.png", "hidden": true},
	{"id": "bdr_cat_10", "metric": "event_cats_petted", "target": 10, "icon": E + "black_cat.png"},
	{"id": "bdr_clover_25", "metric": "event_clovers", "target": 25, "icon": E + "lucky_clover.png"},
	{"id": "bdr_meteor_100", "metric": "event_meteor_hits", "target": 100, "icon": E + "meteor_shower.png"},
	{"id": "bdr_tornado_500", "metric": "event_tornado_dice", "target": 500, "icon": E + "tornado.png"},
	{"id": "bdr_staff_1", "metric": "staff_total", "target": 1, "icon": S + "mechanic.png"},
	{"id": "bdr_staff_kinds", "metric": "staff_kinds", "target": 10, "icon": S + "banker.png"},
	{"id": "bdr_staff_100", "metric": "staff_total", "target": 100, "icon": S + "merchant.png"},
	{"id": "bdr_dj_50", "metric": "staff_beat_drops", "target": 50, "icon": S + "dj.png"},
	{"id": "bdr_science", "metric": "staff_levels", "target": 25, "icon": S + "scientist.png"},
	{"id": "bdr_sold_100", "metric": "dice_sold", "target": 100, "icon": U + "sell_icon.png"},
	{"id": "bdr_designs_5", "metric": "designs_bought", "target": 5, "icon": U + "design_icon.png"},
	{"id": "bdr_designs_all", "metric": "designs_bought", "target": 20, "icon": U + "design_icon.png"},
	{"id": "bdr_money_24", "metric": "money", "target": 24, "icon": U + "lucky_cash.png", "money": true},
	{"id": "bdr_money_33", "metric": "money", "target": 33, "icon": U + "lucky_cash.png", "money": true},
	{"id": "bdr_money_50", "metric": "money", "target": 50, "icon": U + "lucky_cash.png", "money": true},
	{"id": "bdr_money_100", "metric": "money", "target": 100, "icon": U + "lucky_cash.png", "money": true},
]

var game: Node
var main: Node
var unlocked: Dictionary = {}
var progress: Dictionary = {}     # metric -> best value ever reached
var _by_id: Dictionary = {}
var _unlocked_count := 0
var _timer := 0.0
var _dirty := false


func setup(controller: Node) -> void:
	game = controller
	main = controller.main
	for entry in CATALOG:
		_by_id[str(entry.id)] = entry
	_load()


func entries() -> Array:
	return CATALOG


func entry(achievement_id: String) -> Dictionary:
	return _by_id.get(achievement_id, {})


func is_mod_achievement(achievement_id: String) -> bool:
	return _by_id.has(achievement_id)


func is_unlocked(achievement_id: String) -> bool:
	return bool(unlocked.get(achievement_id, false))


func unlocked_count() -> int:
	return _unlocked_count


func total() -> int:
	return CATALOG.size()


func title(achievement_id: String) -> String:
	return I18N.t("ach.%s.name" % achievement_id)


func description(achievement_id: String) -> String:
	return I18N.t("ach.%s.desc" % achievement_id)


func icon(achievement_id: String) -> String:
	return str(entry(achievement_id).get("icon", "res://assets/art/achievements/trophy.png"))


func progress_value(achievement_id: String) -> float:
	return float(progress.get(str(entry(achievement_id).get("metric", "")), 0.0))


func target(achievement_id: String) -> float:
	return float(entry(achievement_id).get("target", 1))


## "current / target" for the achievement list.
func progress_text(achievement_id: String) -> String:
	var data := entry(achievement_id)
	if bool(data.get("money", false)):
		var current := float(main.total_money_earned)
		return "%s / %s" % [NumFmt.compact(current), NumFmt.compact(pow(10.0, target(achievement_id)))]
	return "%s / %s" % [NumFmt.compact(minf(progress_value(achievement_id), target(achievement_id))), NumFmt.compact(target(achievement_id))]


## 0..1 for the progress bar (money achievements use a log scale).
func progress_ratio(achievement_id: String) -> float:
	return clampf(progress_value(achievement_id) / maxf(1.0, target(achievement_id)), 0.0, 1.0)


# ---------------------------------------------------------------- evaluation
func process(delta: float) -> void:
	_timer += delta
	if _timer < EVALUATE_EVERY:
		return
	_timer = 0.0
	evaluate()


func evaluate() -> void:
	if game.is_coop_client():
		return
	var values := {}
	for data in CATALOG:
		var metric := str(data.metric)
		if not values.has(metric):
			values[metric] = _metric(metric)
			if float(values[metric]) > float(progress.get(metric, 0.0)):
				progress[metric] = float(values[metric])
				_dirty = true
	for data in CATALOG:
		var achievement_id := str(data.id)
		if is_unlocked(achievement_id):
			continue
		if float(progress.get(str(data.metric), 0.0)) >= float(data.target):
			_unlock(achievement_id)
	if _dirty:
		_save()


func _unlock(achievement_id: String) -> void:
	unlocked[achievement_id] = true
	_unlocked_count += 1
	_dirty = true
	main._invalidate_eco()
	if main.menu_controller and main.menu_controller.has_method("_on_achievement_unlocked"):
		main.menu_controller._on_achievement_unlocked(achievement_id)


func _metric(metric: String) -> float:
	match metric:
		"dice_unlocked":
			var total_unlocked := 0
			for kind in game.unlocked:
				if bool(game.unlocked[kind]):
					total_unlocked += 1
			return float(total_unlocked)
		"kinds_owned":
			return float(game.kinds_owned_count())
		"custom_dice":
			return float(game.total_custom_dice())
		"max_tier":
			var best := 0
			for kind in game.counts:
				if game.catalog.has(kind) and int(game.counts[kind]) > 0:
					best = maxi(best, int(game.catalog.by_id[kind].tier))
			return float(best)
		"talents_bdr":
			var owned := 0
			if game.talent_ext:
				for key in game.talent_ext.order:
					if main._is_talent_owned(key):
						owned += 1
			return float(owned)
		"family_talents":
			var families := 0
			for family in TalentsExt.FAMILIES:
				if main._is_talent_owned("bdr_family_%s_1" % family):
					families += 1
			return float(families)
		"worker_limit":
			return float(main._worker_limit())
		"minor_cards":
			var minors := 0
			for card_id in DogShrineCards.MINOR_IDS:
				if main._dog_card_rank(card_id) > 0:
					minors += 1
			return float(minors)
		"tarot_cards_distinct":
			var cards := 0
			for card_id in DogShrineCards.ALL_IDS:
				if main._dog_card_rank(str(card_id)) > 0:
					cards += 1
			return float(cards)
		"lucky_only_found":
			var found := 0
			for kind in LuckyExt.GATE_ORDER:
				if game.is_unlocked(kind):
					found += 1
			return float(found)
		"event_kinds":
			var kinds := 0
			for event_id in EventsExt.IDS:
				if int(game.stats.get("event_" + event_id, 0)) > 0:
					kinds += 1
			return float(kinds)
		"staff_total":
			return float(game.staff.total_staff())
		"staff_kinds":
			return float(game.staff.kinds_hired())
		"money":
			var earned := float(main.total_money_earned)
			return floorf(log(maxf(1.0, earned)) / log(10.0) + 1e-9)
	return float(game.stats.get(metric, 0))


# ---------------------------------------------------------------- storage
func _load() -> void:
	unlocked.clear()
	progress.clear()
	_unlocked_count = 0
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if parsed is not Dictionary:
		return
	var saved_unlocked = parsed.get("unlocked", {})
	if saved_unlocked is Dictionary:
		for achievement_id in saved_unlocked:
			if _by_id.has(str(achievement_id)) and bool(saved_unlocked[achievement_id]):
				unlocked[str(achievement_id)] = true
				_unlocked_count += 1
	var saved_progress = parsed.get("progress", {})
	if saved_progress is Dictionary:
		for metric in saved_progress:
			progress[str(metric)] = maxf(0.0, float(str(saved_progress[metric])))


func _save() -> void:
	_dirty = false
	var saved_progress := {}
	for metric in progress:
		saved_progress[metric] = str(progress[metric])
	var data := {"version": SAVE_VERSION, "unlocked": unlocked.duplicate(), "progress": saved_progress}
	var temporary := SAVE_PATH + ".tmp"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return
	file.store_string(JSON.stringify(data))
	file.close()
	DirAccess.rename_absolute(ProjectSettings.globalize_path(temporary), ProjectSettings.globalize_path(SAVE_PATH))
