extends Node
## Dice Rush Extended - in-game controller (child of the main game scene "DiceRush").
## main.gd calls the hooks below. The controller owns all mod state of a save slot.

const I18N := preload("res://bdr/core/i18n.gd")
const CatalogScript := preload("res://bdr/core/catalog.gd")
const MechanicsScript := preload("res://bdr/game/mechanics.gd")
const FXScript := preload("res://bdr/render/fx.gd")
const BDRSettings := preload("res://bdr/core/settings.gd")
const GitHubScript := preload("res://bdr/ui/github_button.gd")
const ShopLogicScript := preload("res://bdr/game/shop_logic.gd")
const TalentsExtScript := preload("res://bdr/game/talents_ext.gd")
const LuckyExtScript := preload("res://bdr/game/lucky_ext.gd")
const TarotExtScript := preload("res://bdr/game/tarot_ext.gd")
const StaffScript := preload("res://bdr/game/staff.gd")
const EventsScript := preload("res://bdr/game/events.gd")
const AchievementsScript := preload("res://bdr/game/achievements_ext.gd")
const CoopScript := preload("res://bdr/net/coop.gd")
const CoopUIScript := preload("res://bdr/ui/coop_ui.gd")
const WarmupScript := preload("res://bdr/game/warmup.gd")
const MOD_VERSION := "1.2.0"
const STAFF_POP_MAX := 6
const ROMAN := ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
const FAMILY_COLORS := {"classic": "5dabf6", "material": "c8904f", "meme": "6dbb45", "element": "ff6a1f", "animal": "f2c98c", "tech": "478cbf", "adventure": "c0c6d0", "casino": "e8c02a", "food": "ff7ac8", "spooky": "7fae5a", "vehicle": "e8261c", "cosmic": "b45aff", "luck": "2fa85a"}
const ShopPanelScript := preload("res://bdr/ui/shop_panel.gd")
const UIKit := preload("res://bdr/ui/ui_kit.gd")
const SHOP_ICON := "res://bdr/art/ui/shop_icon.png"
const SAVE_VERSION := 1
const VANILLA_DICE_KINDS := ["50_50", "d4", "3x4", "d2", "777", "prehistoric", "golden", "npc_die", "crypto", "diamond", "pi"]
const VANILLA_SHOP_ORDER := ["50_50", "d4", "npc", "3x4", "d2", "777", "prehistoric", "golden", "npc_die", "crypto", "diamond", "pi", "accountant", "cat"]
const QUEUE_ROLLS_PER_FRAME := 90
## Rolls that effects may start per second (chain reactions). Crowded tables get a smaller
## share per dice, so a full table cannot snowball into thousands of rolls per second.
const EFFECT_ROLLS_PER_SECOND := 900.0
const EFFECT_ROLLS_MIN := 220.0
const QUEUE_CARRY_MAX := 240
const AUTO_MECHS := {"auto": true, "skibidi": true, "divine": true}

var main: Node
var catalog: CatalogScript
var mech: MechanicsScript
var fx: Node2D
var settings: Dictionary = {}

# per save slot
var counts: Dictionary = {}
var unlocked: Dictionary = {}
var stats: Dictionary = {}
var extra: Dictionary = {}          # free-form data of other mod systems

var _kind_dice: Dictionary = {}     # kind -> Array of dice (custom kinds only)
var _queue: Dictionary = {}         # bucket -> Array [die, target]
var _queue_next := -1
var _queue_carry: Array = []
var _queue_tokens := 0.0
var _auto_dice: Array = []
var _auto_due: Dictionary = {}      # instance id -> msec
var _kinds_owned_cache := -1
var _kinds_owned_msec := 0
var _global_mult_cache := 1.0
var _global_mult_msec := -100000
var _custom_shop_kinds: Array[String] = []
var _stat_accum: Dictionary = {}
var _placeholder_texture: Texture2D
var shop: ShopLogicScript
var talent_ext: TalentsExtScript
var lucky: LuckyExtScript
var tarot: TarotExtScript
var staff: StaffScript
var events: EventsScript
var achievements: AchievementsScript
var coop: CoopScript
var coop_ui: CoopUIScript
var warmup: WarmupScript
var _income_rate := 0.0
var _income_last_total := -1.0
var _income_excluded := 0.0
var _income_timer := 0.0
var _staff_pops: Array = []
var _dice_scale := 1.0
var _scale_timer := 0.0
var _scaled_npcs := -1
var _rescue_timer := 2.0
var _bonus_timer := 0.0
var shop_panel: Control
var shop_hud_button: Button
var shop_hud_root: Control


func setup(game: Node) -> void:
	main = game
	process_mode = Node.PROCESS_MODE_ALWAYS
	settings = BDRSettings.load_settings()
	catalog = CatalogScript.new()
	catalog.load_catalog()
	mech = MechanicsScript.new()
	mech.setup(main, self)
	_custom_shop_kinds.clear()
	var ordered: Array = catalog.dice.duplicate()
	ordered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a.tier) < int(b.tier) or (int(a.tier) == int(b.tier) and int(a.price) < int(b.price)))
	for entry in ordered:
		_custom_shop_kinds.append(str(entry.id))
	_register_landmarks()
	shop = ShopLogicScript.new()
	shop.setup(self)
	lucky = LuckyExtScript.new()
	lucky.setup(self)
	tarot = TarotExtScript.new()
	tarot.setup(self)
	staff = StaffScript.new()
	staff.setup(self)
	events = EventsScript.new()
	events.setup(self)
	achievements = AchievementsScript.new()
	achievements.setup(self)
	coop = CoopScript.new()
	add_child(coop)
	coop.setup(self)
	warmup = WarmupScript.new()
	warmup.setup(self)


func _register_landmarks() -> void:
	var visual_script: Script = load("res://scripts/dice_diagonal_visual.gd")
	if visual_script == null:
		return
	for kind in catalog.landmarks:
		var points: Array = catalog.landmarks[kind]
		if points.size() != 7:
			continue
		var vectors: Array = []
		for point in points:
			vectors.append(Vector2(float(point[0]), float(point[1])))
		var art: Dictionary = catalog.get_def(kind).get("art", {})
		visual_script.register_landmarks(kind, vectors, Color(str(art.get("left", "#036fe5"))))


# ---------------------------------------------------------------- settings
func animation_budget() -> int:
	return int(settings.get("anim_budget", 160))


func hover_animation_budget() -> int:
	return int(settings.get("hover_budget", 220))


func spin3d_budget() -> int:
	return int(settings.get("spin3d_budget", 120))


func batch_enabled() -> bool:
	return bool(settings.get("batch", true))


# ---------------------------------------------------------------- textures
func die_texture_path(kind: String) -> String:
	if not catalog.has(kind):
		return ""
	var path := catalog.texture_path(kind)
	if FileAccess.file_exists(path):
		return path
	return ""


func icon_path(kind: String) -> String:
	if staff.has(kind):
		return staff.icon_path(kind)
	if catalog.has(kind):
		var path := die_texture_path(kind)
		return path if not path.is_empty() else main.ART + "cube d6 4/фото в магазине 4.png"
	return ""


func batch_textures() -> Dictionary:
	var result := {}
	for kind in VANILLA_DICE_KINDS:
		result[kind] = CleanTextureLoader.load_texture(main._die_texture_path(kind))
	for kind in catalog.ids:
		result[kind] = CleanTextureLoader.load_texture(main._die_texture_path(kind))
	return result


func batch_sizes() -> Dictionary:
	var result := {}
	for kind in batch_textures().keys():
		result[kind] = 66.0 if kind == "50_50" else 62.0
	return result


# ---------------------------------------------------------------- kinds / counts
## New dice kinds AND new staff types (both are shop products of the mod).
func is_custom(kind: String) -> bool:
	return catalog.has(kind) or staff.has(kind)


func is_custom_die(kind: String) -> bool:
	return catalog.has(kind)


func def_for(kind: String) -> Variant:
	return catalog.by_id.get(kind)


func count(kind: String) -> int:
	return int(counts.get(kind, 0))


func set_count(kind: String, value: int) -> void:
	counts[kind] = maxi(0, value)
	_kinds_owned_cache = -1


func custom_dice_counts() -> Dictionary:
	var result := {}
	for kind in counts:
		if catalog.has(kind) and int(counts[kind]) > 0:
			result[kind] = int(counts[kind])
	return result


func total_custom_dice() -> int:
	var total := 0
	for kind in counts:
		if catalog.has(kind):
			total += int(counts[kind])
	return total


func total_dice_count() -> int:
	return main.dice.size()


func kinds_owned_count() -> int:
	var now := Time.get_ticks_msec()
	if _kinds_owned_cache >= 0 and now - _kinds_owned_msec < 1000:
		return _kinds_owned_cache
	var total := 0
	for kind in VANILLA_DICE_KINDS:
		if main._owned_die_count(kind) > 0:
			total += 1
	if main.cat_count > 0:
		total += 1
	for kind in counts:
		if catalog.has(kind) and int(counts[kind]) > 0:
			total += 1
	_kinds_owned_cache = total
	_kinds_owned_msec = now
	return total


func is_unlocked(kind: String) -> bool:
	if staff.has(kind):
		return staff.is_available(kind)
	return bool(unlocked.get(kind, false))


func unlock(kind: String, announce: bool = true) -> void:
	if not catalog.has(kind) or is_unlocked(kind):
		return
	unlocked[kind] = true
	if not main.die_levels.has(kind):
		main.die_levels[kind] = 1
	stat("dice_unlocked", 1)
	if announce:
		toast(I18N.f("ui.dice_unlocked", {"name": display_name(kind)}))
	main._update_all_labels()


func display_name(kind: String) -> String:
	if catalog.has(kind):
		return catalog.name_of(kind)
	if staff.has(kind):
		return staff.name_of(kind)
	return kind


func card_title(kind: String) -> String:
	return display_name(kind)


func kind_color(kind: String) -> Color:
	var art: Dictionary = catalog.get_def(kind).get("art", {})
	return Color(str(art.get("top", "#ffffff")))


func npc_can_roll(kind: String) -> bool:
	var def: Dictionary = catalog.get_def(kind)
	if def.is_empty() or not bool(def.get("npc", true)):
		return false
	var tier := int(def.tier)
	return tier <= worker_training_tier()


func worker_training_tier() -> int:
	var tier := 2
	if main._is_talent_owned("bdr_training_1"):
		tier = 4
	if main._is_talent_owned("bdr_training_2"):
		tier = 7
	if main._is_talent_owned("bdr_training_3"):
		tier = 10
	return tier


func shop_custom_kinds() -> Array[String]:
	return _custom_shop_kinds


func shop_order() -> Array:
	var result: Array = VANILLA_SHOP_ORDER.duplicate()
	result.append_array(StaffScript.ORDER)
	result.append_array(_custom_shop_kinds)
	return result


## Every product card of the mod in the shop: staff first, then the new dice.
func shop_product_kinds() -> Array[String]:
	var result: Array[String] = []
	for kind in StaffScript.ORDER:
		result.append(kind)
	result.append_array(_custom_shop_kinds)
	return result


func product_limit(kind: String) -> int:
	if staff.has(kind):
		return staff.limit(kind)
	return -1


func custom_next_price(kind: String, owned: int) -> float:
	if staff.has(kind):
		return staff.price(kind, owned)
	if not catalog.has(kind):
		return -2.0
	var def: Dictionary = catalog.get_def(kind)
	return CatalogScript.grown_price(float(def.price), owned)


func price_factor(kind: String) -> float:
	if not catalog.has(kind):
		return 1.0
	return (1.0 - tarot.value("price_discount")) * (1.0 - staff.price_discount())


func lucky_price_divisor() -> float:
	var divisor := 1.25 if main._is_talent_owned("bdr_lucky_discount") else 1.0
	return divisor / maxf(0.4, 1.0 - tarot.value("lucky_discount"))


func event_reward_multiplier() -> float:
	return (2.0 if main._is_talent_owned("bdr_event_reward") else 1.0) * tarot.value("event_reward")


## Extra percent for one landing dice; also rolls tarot critical hits (multiplies pending_mult).
func positional_percent(die: DiceActor) -> int:
	var crit := tarot.roll_crit()
	if crit > 1.0:
		die.pending_mult *= crit
		stat("crits", 1)
		mech._popup(die, "fx.crit", {"n": int(crit)})
	events.on_landing(die)
	return 0


func staff_buy_callable(kind: String) -> Callable:
	return staff.buy.bind(kind) if staff.has(kind) else Callable()


func dice_of_kind(kind: String) -> Array:
	return _kind_dice.get(kind, [])


func random_owned_level_kind() -> String:
	var pool: Array = []
	for kind in VANILLA_DICE_KINDS:
		if main._owned_die_count(kind) > 0:
			pool.append(kind)
	for kind in counts:
		if catalog.has(kind) and int(counts[kind]) > 0:
			pool.append(kind)
	if pool.is_empty():
		return ""
	return pool[main.rng.randi_range(0, pool.size() - 1)]


func random_buildable_kind() -> String:
	var pool: Array = ["50_50", "d4"]
	for kind in counts:
		var def: Dictionary = catalog.get_def(kind)
		if not def.is_empty() and int(counts[kind]) > 0 and int(def.tier) <= 5 and not str(def.mech) in ["breeder", "builder"]:
			pool.append(kind)
	return pool[main.rng.randi_range(0, pool.size() - 1)]


# ---------------------------------------------------------------- spawning / changing dice
func prepare_die(die: DiceActor, kind: String) -> void:
	var def = catalog.by_id.get(kind)
	if def != null:
		mech.prepare(die, def)


func on_die_spawned(die: DiceActor) -> void:
	coop.on_spawn(die)
	var kind := die.die_kind
	if not catalog.has(kind):
		return
	var list: Array = _kind_dice.get(kind, [])
	list.append(die)
	_kind_dice[kind] = list
	var def: Dictionary = catalog.get_def(kind)
	if AUTO_MECHS.has(str(def.mech)):
		_auto_dice.append(die)
		_auto_due[die.get_instance_id()] = Time.get_ticks_msec() + int(main.rng.randf_range(0.5, 1.0) * float(def.get("p", {}).get("interval", 2.5)) * 1000.0)


func on_die_detached(die: DiceActor) -> void:
	coop.on_remove(die)
	var kind := die.die_kind
	if _kind_dice.has(kind):
		(_kind_dice[kind] as Array).erase(die)
	if _auto_due.has(die.get_instance_id()):
		_auto_due.erase(die.get_instance_id())
		_auto_dice.erase(die)


func on_actors_cleared() -> void:
	_kind_dice.clear()
	_queue.clear()
	_queue_carry.clear()
	_queue_next = -1
	_auto_dice.clear()
	_auto_due.clear()
	if mech:
		mech._motions.clear()


## Spawns a free dice of a kind (counts +1) - bunnies, architect, lucky block...
func spawn_free(kind: String, position: Vector2) -> void:
	if not main._dice_table_has_capacity():
		return
	if kind == "50_50":
		main.dice_50_count += 1
	elif kind == "d4":
		main.dice_d4_count += 1
	elif catalog.has(kind):
		set_count(kind, count(kind) + 1)
	else:
		return
	main._spawn_die(kind, main._clamp_die_position(position))
	main._request_all_labels_update()


## Replaces a dice by another kind at the same place (zombie bite).
func convert_die(victim: DiceActor, new_kind: String) -> void:
	if not is_instance_valid(victim) or victim.rolling:
		return
	var old_kind := victim.die_kind
	var position := victim.position
	main._set_owned_die_count(old_kind, main._owned_die_count(old_kind) - 1)
	remove_die_actor(victim)
	set_count(new_kind, count(new_kind) + 1)
	main._spawn_die(new_kind, position)
	main._request_all_labels_update()


## Removes a dice actor from the table (counts must be adjusted by the caller).
func remove_die_actor(die: DiceActor) -> void:
	if not is_instance_valid(die):
		return
	if die.rolling:
		main.active_roll_ids.erase(die.get_instance_id())
		main.active_roll_count = maxi(0, main.active_roll_count - 1)
		if main.active_animated_roll_ids.has(die.get_instance_id()):
			main.active_animated_roll_ids.erase(die.get_instance_id())
			main.active_animated_roll_count = maxi(0, main.active_animated_roll_count - 1)
		main.active_interactive_animated_roll_ids.erase(die.get_instance_id())
		die.abort_roll()
	main._release_npc_targeting(die)
	main._bdr_detach_die(die)
	main.dice.erase(die)
	main.golden_dice.erase(die)
	main.golden_timers.erase(die.get_instance_id())
	die.visible = false
	die.process_mode = Node.PROCESS_MODE_DISABLED
	die.queue_free()


func teleport_die(die: DiceActor, target: Vector2) -> void:
	if not is_instance_valid(die) or die.rolling:
		return
	die.position = main._clamp_die_position(target)
	die.z_index = 12 + int(die.position.y / 100.0)
	coop.on_move(die)
	if die.grid_cell >= 0:
		main._grid.move(die, die.position)
	if die.batch_band != -1:
		main._batch.remove(die)
		if main._batch.add(die):
			die.set_batched(true)


func board_safe_rect() -> Rect2:
	return Rect2(100, 201, 898, 753).grow(-40.0)


# ---------------------------------------------------------------- rolling
func on_roll_started(die: DiceActor, target: Vector2 = Vector2(-1.0, -1.0), animated: bool = false, interactive: bool = false) -> void:
	if coop.is_client():
		return
	coop.on_roll(die, target if target.x >= 0.0 else die.position, animated, interactive)
	var def = catalog.by_id.get(die.die_kind)
	if def != null:
		mech.on_roll_started(die, def)


func queue_roll(die: DiceActor, delay: float, target: Vector2 = Vector2(-1.0, -1.0)) -> void:
	var due := Time.get_ticks_msec() + int(maxf(0.0, delay) * 1000.0)
	var bucket := due >> 4
	var list = _queue.get(bucket)
	if list == null:
		list = []
		_queue[bucket] = list
	list.append([die, target])


func _process_queue(delta: float = 0.016) -> void:
	var now_bucket := Time.get_ticks_msec() >> 4
	if _queue_next < 0:
		_queue_next = now_bucket - 1
	var table: float = maxf(1500.0, float(main.dice.size()))
	var rate := maxf(EFFECT_ROLLS_MIN, EFFECT_ROLLS_PER_SECOND * 1500.0 / table)
	_queue_tokens = minf(rate * 0.25, _queue_tokens + rate * delta)
	var budget := mini(QUEUE_ROLLS_PER_FRAME, int(_queue_tokens))
	var pending: Array = _queue_carry
	_queue_carry = []
	if _queue.is_empty() and pending.is_empty():
		_queue_next = now_bucket + 1
		return
	if now_bucket - _queue_next > 20000:
		_queue_next = now_bucket - 20000
	while _queue_next <= now_bucket:
		var list = _queue.get(_queue_next)
		if list != null:
			_queue.erase(_queue_next)
			pending.append_array(list)
		_queue_next += 1
	for index in range(pending.size()):
		var item: Array = pending[index]
		if budget <= 0:
			_queue_carry.append(item)
			continue
		var die = item[0]
		if not is_instance_valid(die) or die.rolling or die.special_motion:
			continue
		main._start_die_roll(die, 0, item[1], false, true)
		if main.bdr_prof_on:
			main._bdr_pc("c_fx_roll")
		budget -= 1
		_queue_tokens -= 1.0
	if _queue_carry.size() > QUEUE_CARRY_MAX:
		_queue_carry.resize(QUEUE_CARRY_MAX)


func _process_auto(_delta: float) -> void:
	if _auto_dice.is_empty() or main._world_blocked_for_auto_rolls():
		return
	if main.autosave_pending or not main.pending_safe_action.is_empty():
		return
	var now := Time.get_ticks_msec()
	for die in _auto_dice:
		if not is_instance_valid(die):
			continue
		var id: int = die.get_instance_id()
		var due := int(_auto_due.get(id, now))
		if now < due or die.rolling or die.special_motion:
			continue
		var def: Dictionary = catalog.get_def(die.die_kind)
		var interval := float(def.get("p", {}).get("interval", 2.5))
		_auto_due[id] = now + int(interval * 1000.0 / maxf(0.1, auto_speed_multiplier()))
		if str(def.mech) == "skibidi":
			die.mstate["brainrot"] = mini(100, int(die.mstate.get("brainrot", 0)) + 1)
		main._start_die_roll(die, 0, Vector2(-1.0, -1.0), false, true)


func auto_speed_multiplier() -> float:
	return (1.43 if main._is_talent_owned("bdr_auto_speed") else 1.0) * tarot.value("auto_speed")


func effect_radius_mult() -> float:
	return (1.3 if main._is_talent_owned("bdr_aura_radius") else 1.0) * tarot.value("radius") * _dice_scale


# ---------------------------------------------------------------- crowded tables
## [minimum dice, size factor]: from 200 dice on the dice get smaller (the table looks bigger).
const SCALE_STEPS := [[200, 0.85], [600, 0.72], [1500, 0.6], [3000, 0.5], [5000, 0.42], [6000, 0.38]]


func dice_scale() -> float:
	return _dice_scale


func _scale_for(count_value: int) -> float:
	var result := 1.0
	for step in SCALE_STEPS:
		if count_value >= int(step[0]):
			result = float(step[1])
	return result


## Checks the dice count twice a second. Growing back needs 10% fewer dice (no flickering).
func _update_dice_scale(delta: float) -> void:
	_scale_timer -= delta
	if _scale_timer > 0.0:
		return
	_scale_timer = 0.5
	var total: int = main.dice.size()
	var wanted := _scale_for(total)
	if wanted > _dice_scale:
		wanted = maxf(_dice_scale, _scale_for(int(float(total) / 0.9)))
	if not is_equal_approx(wanted, _dice_scale):
		apply_dice_scale(wanted)
	elif main.npcs.size() != _scaled_npcs:
		_scale_npcs()


func apply_dice_scale(value: float) -> void:
	_dice_scale = value
	var node_scale := Vector2.ONE * value
	for die in main.dice:
		if is_instance_valid(die):
			die.scale = node_scale
	if main._batch:
		main._batch.set_scale_factor(value)
	_scale_npcs()
	invalidate_global_multiplier()


func _scale_npcs() -> void:
	_scaled_npcs = main.npcs.size()
	var npc_scale := Vector2.ONE * lerpf(1.0, _dice_scale, 0.7)
	for npc in main.npcs:
		if is_instance_valid(npc):
			npc.scale = npc_scale


func effect_count_mult() -> float:
	return (1.5 if main._is_talent_owned("bdr_chain_power") else 1.0) * tarot.value("count")


func base_reward(die: DiceActor, value: int, def: Variant) -> float:
	return mech.base_reward(die, value, def)


func after_landing(die: DiceActor, reward: float, value: int, def: Variant) -> void:
	mech.after_landing(die, reward, value, def)


func on_any_landing(_die: DiceActor, _reward: float) -> void:
	pass


func on_skull() -> void:
	mech.on_skull()


func on_purchased(kind: String, amount: int) -> void:
	stat("bought_custom", amount)
	_kinds_owned_cache = -1


# ---------------------------------------------------------------- economy hooks
func kind_percent_bonus(kind: String) -> int:
	var percent := 0
	if talent_ext:
		var family := "classic"
		var def = catalog.by_id.get(kind)
		if def != null:
			family = str(def.family)
		percent += talent_ext.family_bonus_percent(family, main._is_talent_owned)
		percent += int(round(staff.family_percent(family)))
	percent += int(round(tarot.kind_percent(kind)))
	return percent


func kind_multiplier(_kind: String) -> float:
	return 1.0


func global_multiplier() -> float:
	var now := Time.get_ticks_msec()
	if now - _global_mult_msec < 250:
		return _global_mult_cache
	_global_mult_msec = now
	var percent := 0.0
	for kind in ["crown", "sun", "divine"]:
		var n := count(kind)
		if n <= 0:
			continue
		var p: Dictionary = catalog.get_def(kind).get("p", {})
		percent += minf(float(p.get("max", 50)), float(p.get("per", 1)) * n)
	_global_mult_cache = (1.0 + percent / 100.0) * lucky.boost_multiplier() * tarot.global_multiplier() * staff.global_multiplier() * events.global_multiplier()
	return _global_mult_cache


func any_event_active() -> bool:
	return active_event_count() > 0


func active_event_count() -> int:
	var total := 0
	if main.golden_bone_luck_time_left > 0.0:
		total += 1
	if main.golden_bone_storm_time_left > 0.0:
		total += 1
	if events.is_active():
		total += 1
	return total


func invalidate_global_multiplier() -> void:
	_global_mult_msec = -100000



# ---------------------------------------------------------------- per-frame
func process_always(_delta: float) -> void:
	if not warmup.is_done():
		warmup.process()


## True while a menu (tarot shrine) waits for a quiet table: no new rolls from the mod then.
func world_frozen_for_menu() -> bool:
	return bool(main.dog_shrine_transaction_active) and not world_runs_during_menus()


func process_world(delta: float) -> void:
	if world_frozen_for_menu():
		return
	var on: bool = main.bdr_prof_on
	var t0 := Time.get_ticks_usec() if on else 0
	_update_dice_scale(delta)
	_process_queue(delta)
	if on:
		t0 = main._bdr_pt("w_queue", t0)
	_process_auto(delta)
	if on:
		t0 = main._bdr_pt("w_auto", t0)
	mech.process(delta)
	if on:
		t0 = main._bdr_pt("w_mech", t0)
	lucky.process(delta)
	staff.process(delta)
	if on:
		t0 = main._bdr_pt("w_staff", t0)
	events.process(delta)
	achievements.process(delta)
	_track_income(delta)
	_rescue_timer -= delta
	if _rescue_timer <= 0.0:
		_rescue_timer = 10.0
		rescue_stray_dice()
	_bonus_timer += delta
	if _bonus_timer >= 1.0:
		_grow_bonus_budget(_bonus_timer)
		_bonus_timer = 0.0
	if on:
		t0 = main._bdr_pt("w_other", t0)


# ---------------------------------------------------------------- bonus limiter (balance)
## Random talent gold (lucky block, cars, chests) and random free dice levels (lucky block)
## share a slow budget, so they stay a nice surprise instead of flooding the talent tree
## and the income. The budget is saved with the game.
const BONUS_SECONDS := {"gold": 600.0, "level": 90.0, "free_die": 60.0}
const BONUS_BANK := 2.0


func _grow_bonus_budget(seconds: float) -> void:
	var budget: Dictionary = extra.get("bonus_budget", {})
	for key in BONUS_SECONDS:
		budget[key] = minf(BONUS_BANK, float(budget.get(key, 1.0)) + seconds / float(BONUS_SECONDS[key]))
	extra["bonus_budget"] = budget


## Takes one bonus of the given kind ("gold", "level", "free_die") if the budget allows it.
func try_bonus(key: String) -> bool:
	var budget: Dictionary = extra.get("bonus_budget", {})
	var value := float(budget.get(key, 1.0))
	if value < 1.0:
		return false
	budget[key] = value - 1.0
	extra["bonus_budget"] = budget
	return true


## Version 1.0 pulled the flight targets on crowded tables towards the dice itself, so over time
## the dice gathered in the middle of the table. Saves from that version are spread out evenly
## once after loading (an even spread has about 25% of the dice in the middle quarter).
func spread_dice_if_clustered() -> int:
	if main.dice.size() < 200:
		return 0
	var safe: Rect2 = board_safe_rect()
	var middle := Rect2(safe.position + safe.size * 0.25, safe.size * 0.5)
	var counted := 0
	var inside := 0
	for die in main.dice:
		if not is_instance_valid(die) or die.die_kind == "cat":
			continue
		counted += 1
		if middle.has_point(die.position):
			inside += 1
	if counted == 0 or float(inside) / float(counted) < 0.4:
		return 0
	var moved := 0
	for die in main.dice:
		if not is_instance_valid(die) or die.rolling or die.special_motion or die.die_kind == "cat":
			continue
		teleport_die(die, main._bdr_random_felt_point())
		moved += 1
	return moved


## Puts dice that ended up outside the board (older versions could let cars drive off the
## table) back onto the felt. Runs after loading and every 10 seconds.
func rescue_stray_dice() -> int:
	var board: Rect2 = main.BOARD_RECT
	var rescued := 0
	for die in main.dice:
		if not is_instance_valid(die) or die.rolling or die.special_motion:
			continue
		if board.has_point(die.position):
			continue
		teleport_die(die, main._clamp_die_position(die.position))
		rescued += 1
	return rescued


func flush_frame() -> void:
	if _stat_accum.is_empty():
		return
	for key in _stat_accum:
		stats[key] = int(stats.get(key, 0)) + int(_stat_accum[key])
	_stat_accum.clear()


func stat(key: String, amount: int) -> void:
	_stat_accum[key] = int(_stat_accum.get(key, 0)) + amount


func report_snapshot() -> void:
	pass


func on_labels_updated() -> void:
	pass


# ---------------------------------------------------------------- effects
func _ensure_fx() -> void:
	if fx == null or not is_instance_valid(fx):
		fx = FXScript.new()
		main.add_child(fx)


func fx_ring(center: Vector2, radius: float, color: Color) -> void:
	coop.on_ring(center, radius, color)
	_ensure_fx()
	fx.ring(center, radius, color)


func fx_lines(from: Vector2, targets: Array, color: Color) -> void:
	_ensure_fx()
	fx.lines(from, targets, color)


func fx_cone(center: Vector2, direction: Vector2, radius: float, color: Color) -> void:
	_ensure_fx()
	fx.cone(center, direction, radius, color)


func fx_trail(from: Vector2, to: Vector2) -> void:
	_ensure_fx()
	fx.trail(from, to)


func fx_slash(y: float) -> void:
	_ensure_fx()
	var safe := board_safe_rect()
	fx.slash(y, safe.position.x, safe.end.x)


func toast(text: String) -> void:
	coop.on_toast(text)
	if main.has_method("_show_golden_bone_banner"):
		main._show_golden_bone_banner(text)


# ---------------------------------------------------------------- UI / misc hooks (filled by later systems)
func build_ui() -> void:
	UIKit.setup(main.pixel_font, main.display_font)
	_build_shop_hud_button()
	shop_panel = ShopPanelScript.new()
	main.upgrade_canvas_layer.add_child(shop_panel)
	shop_panel.setup(self)
	events.build_hud()
	coop_ui = CoopUIScript.new()
	add_child(coop_ui)
	coop_ui.setup(self)


func _build_shop_hud_button() -> void:
	shop_hud_root = Control.new()
	shop_hud_root.name = "BDRShopHud"
	shop_hud_root.position = Vector2(1655, 678)
	shop_hud_root.size = Vector2(190, 190)
	shop_hud_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	shop_hud_root.z_index = 23
	main.add_child(shop_hud_root)
	var visual := Control.new()
	visual.size = shop_hud_root.size
	visual.pivot_offset = visual.size * 0.5
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	shop_hud_root.add_child(visual)
	main._add_texture(main.HUD_MENU_FRAME_TEXTURE, Rect2(3, 0, 184, 184), 0, visual)
	var icon_path := SHOP_ICON if FileAccess.file_exists(SHOP_ICON) else "res://assets/art/lucky_dice/gold_lucky_cube.png"
	var icon: TextureRect = main._add_texture(icon_path, Rect2(35, 30, 120, 120), 1, visual)
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	shop_hud_button = main._make_invisible_button(Rect2(0, 0, 190, 190), open_shop, 12, I18N.t("ui.shop"), shop_hud_root)
	shop_hud_button.name = "BDRShopHudButton"
	shop_hud_button.focus_mode = Control.FOCUS_ALL
	main._wire_ui_feedback(shop_hud_button, visual, 1.055, 0.95)
	# GitHub logo at the bottom right of the table screen (same as in the main menu)
	GitHubScript.make(main, Rect2(1840, 998, 60, 60), 23)


func open_shop() -> void:
	if not main.game_started or not main.pending_safe_action.is_empty():
		return
	if main.upgrade_overlay.visible or (is_instance_valid(main.dog_shrine_controller) and main.dog_shrine_controller.visible):
		return
	main._hide_hover_tooltip()
	if main.menu_controller:
		main.menu_controller.set_game_hud_visible(false)
	shop_panel.open()
	on_menu_state_changed()


func on_shop_closed() -> void:
	if main.menu_controller:
		main.menu_controller.set_game_hud_visible(true)
	main._hide_hover_tooltip()
	get_viewport().gui_release_focus()
	on_menu_state_changed()


func on_menu_state_changed() -> void:
	pass


func overlay_open() -> bool:
	return is_instance_valid(shop_panel) and shop_panel.visible


# ---------------------------------------------------------------- shop facade (coop aware)
func sell_value(kind: String, amount: int) -> float:
	return shop.sell_value(kind, amount)


func max_sellable(kind: String) -> int:
	return shop.max_sellable(kind)


func sell_rate_bonus() -> float:
	var bonus := 0.0
	if main._is_talent_owned("bdr_sell_1"):
		bonus += 0.1
	if main._is_talent_owned("bdr_sell_2"):
		bonus += 0.2
	return bonus + tarot.value("sell") + staff.sell_bonus()


func shop_sell(kind: String, amount: int) -> Dictionary:
	if is_coop_client():
		coop_request("sell", [kind, amount])
		return {"ok": true, "sold": amount, "refund": shop.sell_value(kind, amount)}
	return shop.sell(kind, amount)


func is_revealed(kind: String) -> bool:
	return shop.is_revealed(kind)


func reveal_threshold(kind: String) -> float:
	return shop.reveal_threshold(kind)


func shop_unlock(kind: String) -> void:
	if is_coop_client():
		coop_request("unlock", [kind])
		return
	shop.unlock(kind)


func tarot_unlock_card_name(kind: String) -> String:
	var card_id := tarot.unlock_card_for(kind)
	return tarot.card_name(card_id) if not card_id.is_empty() else "?"


func design_preview_path(design_type: String, index: int) -> String:
	return shop.preview_path(design_type, index)


func design_name(design_type: String, index: int) -> String:
	return shop.display_name(design_type, index)


func design_owned(design_type: String, index: int) -> bool:
	return shop.owned(design_type, index)


func design_equipped(design_type: String) -> int:
	if design_type == "cursor":
		return shop.local_cursor_design()
	return shop.equipped(design_type)


func design_price(design_type: String, index: int) -> float:
	return shop.price(design_type, index)


func design_buy(design_type: String, index: int) -> void:
	if is_coop_client():
		coop_request("design_buy", [design_type, index])
		return
	shop.buy(design_type, index)


func design_equip(design_type: String, index: int) -> void:
	if is_coop_client():
		if design_type == "cursor":
			# the mouse design is personal: the guest keeps it locally and sends it with the cursor
			shop.remember_cursor(index)
			shop.apply()
			return
		coop_request("design_equip", [design_type, index])
		return
	shop.equip(design_type, index)
	main._save_game(true)


func show_dice_tooltip(kind: String) -> void:
	if main.has_method("_show_product_tooltip"):
		main._show_product_tooltip(kind)


func hide_tooltip() -> void:
	main._hide_hover_tooltip()


## Shows a free text in the game's hover tooltip (BBCode allowed).
func show_text_tooltip(text: String, height: float = 150.0) -> void:
	if not is_instance_valid(main.hover_tooltip):
		return
	main.hover_tooltip_type = "bdr_text"
	main.hover_tooltip_key = ""
	main.hover_tooltip.size.y = height
	main.hover_tooltip_text.size.y = height - 36.0
	main.hover_tooltip_text.text = text
	main.hover_tooltip.visible = true


func tooltip_text(kind: String) -> String:
	var def: Dictionary = catalog.get_def(kind)
	if def.is_empty():
		return kind
	var count_owned := count(kind)
	var price: float = main._next_price(kind, main._price_progress_count(kind, count_owned))
	var faces := ""
	var face_list: Array = def.get("faces", [])
	if face_list.size() <= 8:
		var parts: Array = []
		for face in face_list:
			parts.append(str(int(face)))
		faces = "  ·  ".join(parts)
	else:
		faces = "%d – %d" % [int(face_list[0]), int(face_list[-1])]
	return "[color=#ffd166][font_size=18]%s[/font_size][/color]
[color=#8aa0bd]%s[/color]

[color=#3ee6d0]%s[/color]
%s

[color=#3ee6d0]%s[/color]
%s

[color=#8aa0bd]%s:[/color] %s
[color=#8aa0bd]%s:[/color] [color=#3ee6d0]%s[/color]" % [
		display_name(kind), I18N.f("ui.tier", {"n": int(def.tier)}),
		GameSession.text("faces"), faces,
		GameSession.text("effect"), catalog.description_of(kind),
		GameSession.text("quantity"), str(count_owned),
		GameSession.text("next_price"), main._bdr_money_text(price),
	]


func on_game_ready() -> void:
	shop.apply()
	var launch := CoopScript.launch()
	if str(launch.get("mode", "")) == "host":
		CoopScript.clear_launch()
		coop.start_host(int(launch.get("port", CoopScript.DEFAULT_PORT)))


func report_hold_purchase(amount: int) -> void:
	if int(stats.get("hold_best", 0)) < amount:
		stats["hold_best"] = amount


func is_staff(kind: String) -> bool:
	return staff.has(kind)


func staff_tooltip_text(kind: String) -> String:
	return staff.tooltip(kind) if staff.has(kind) else kind


func handle_key(_event: InputEventKey) -> bool:
	return false


func blocks_board_clicks() -> bool:
	return false


func world_runs_during_menus() -> bool:
	return coop.world_runs_during_menus()


func is_coop_client() -> bool:
	return coop.is_client()


func is_coop_active() -> bool:
	return coop.is_active()


func t(key: String) -> String:
	return I18N.t(key)


## Client: main.gd skipped loading a save - connect to the host and wait for its table.
func start_coop_client_world() -> void:
	var launch := CoopScript.launch()
	main.game_started = false
	coop_ui.show_connecting(str(launch.get("address", "")))
	coop.start_client(str(launch.get("address", "127.0.0.1")), int(launch.get("port", CoopScript.DEFAULT_PORT)))


func coop_request_click(die: DiceActor) -> void:
	if is_instance_valid(die) and die.net_id > 0:
		coop.request("click", [die.net_id])


func coop_request(action: String, args: Array) -> void:
	coop.request(action, args)


func coop_send_hover(_from: Vector2, _to: Vector2) -> void:
	pass


func coop_popup(at: Vector2, text: String, positive: bool) -> void:
	coop.on_popup(at, text, positive)


## Client wants to quit or go back to the main menu: no save needed, just leave the session.
func coop_leave(action: String) -> bool:
	if action != "main_menu" and action != "quit":
		return false
	coop.stop(false)
	CoopScript.clear_launch()
	AchievementService.set_progress_suppressed(false)
	get_tree().paused = false
	if action == "quit":
		get_tree().quit()
	else:
		get_tree().change_scene_to_file(main.START_MENU_SCENE)
	return true


## Client: only the visible part of the world runs (event visuals, puppets are moved by coop.gd).
func process_client(delta: float) -> void:
	_update_dice_scale(delta)
	events.process(delta)


## Client: takes over counters, unlocks and designs of the host without resetting anything.
func coop_apply_data(data: Variant) -> void:
	if data is not Dictionary:
		return
	var saved_counts = data.get("counts", {})
	if saved_counts is Dictionary:
		counts.clear()
		for kind in saved_counts:
			if catalog.has(str(kind)) or staff.has(str(kind)):
				counts[str(kind)] = maxi(0, int(saved_counts[kind]))
	var saved_unlocked = data.get("unlocked", {})
	if saved_unlocked is Dictionary:
		unlocked.clear()
		for kind in saved_unlocked:
			if catalog.has(str(kind)) and bool(saved_unlocked[kind]):
				unlocked[str(kind)] = true
	var saved_extra = data.get("extra", {})
	if saved_extra is Dictionary:
		var boost = extra.get("lucky_boost")
		var old_cosmetics = extra.get("cosmetics", {}).duplicate(true) if extra.get("cosmetics") is Dictionary else {}
		extra = saved_extra.duplicate(true)
		if boost != null:
			extra["lucky_boost"] = boost
		if old_cosmetics != extra.get("cosmetics", {}):
			shop.apply()
	_kinds_owned_cache = -1
	invalidate_global_multiplier()


# ---------------------------------------------------------------- save / load
func reset_progress() -> void:
	counts.clear()
	unlocked.clear()
	stats.clear()
	extra.clear()
	_stat_accum.clear()
	_kinds_owned_cache = -1
	if mech:
		mech.reset_state()
	if tarot:
		tarot.invalidate()
	if events:
		events.reset()
	_income_rate = 0.0
	_income_last_total = -1.0


func on_new_game() -> void:
	pass


func on_loaded() -> void:
	shop.apply()
	rescue_stray_dice()
	spread_dice_if_clustered()


func save_data() -> Dictionary:
	flush_frame()
	var saved_counts := {}
	for kind in counts:
		if int(counts[kind]) > 0:
			saved_counts[kind] = int(counts[kind])
	var saved_stats := {}
	for key in stats:
		saved_stats[key] = str(stats[key])
	return {
		"version": SAVE_VERSION,
		"counts": saved_counts,
		"unlocked": unlocked.duplicate(),
		"stats": saved_stats,
		"mech": mech.save_state(),
		"extra": extra.duplicate(true),
	}


func load_data(data: Variant) -> void:
	reset_progress()
	if data is not Dictionary:
		return
	var saved_counts = data.get("counts", {})
	if saved_counts is Dictionary:
		for kind in saved_counts:
			if catalog.has(str(kind)) or staff.has(str(kind)):
				counts[str(kind)] = maxi(0, int(saved_counts[kind]))
	var saved_unlocked = data.get("unlocked", {})
	if saved_unlocked is Dictionary:
		for kind in saved_unlocked:
			if catalog.has(str(kind)) and bool(saved_unlocked[kind]):
				unlocked[str(kind)] = true
	var saved_stats = data.get("stats", {})
	if saved_stats is Dictionary:
		for key in saved_stats:
			stats[str(key)] = int(str(saved_stats[key]))
	mech.load_state(data.get("mech", {}))
	var saved_extra = data.get("extra", {})
	if saved_extra is Dictionary:
		extra = saved_extra.duplicate(true)


func die_save_state(die: DiceActor) -> Dictionary:
	if die.mstate.is_empty():
		return {}
	var out := {}
	for key in die.mstate:
		if key in ["fx_cd", "trail_from", "last_ms", "meeting", "teleport", "everything", "boom", "answer"]:
			continue
		var value = die.mstate[key]
		if value is int or value is float or value is bool or value is String:
			out[key] = value
	return out


func die_load_state(die: DiceActor, state: Variant) -> void:
	if state is not Dictionary:
		return
	for key in state:
		die.mstate[str(key)] = state[key]


# ---------------------------------------------------------------- talent tree
func talent_offset() -> Vector2:
	return TalentsExtScript.ORIGINAL_OFFSET


func talents_ext(original_positions: Dictionary) -> TalentsExtScript:
	if talent_ext == null:
		talent_ext = TalentsExtScript.new()
		talent_ext.build(original_positions)
	return talent_ext


func talent_cost(key: String) -> int:
	if talent_ext and talent_ext.has(key):
		return talent_ext.cost(key)
	return 1


func talent_cost_text(cost: int) -> String:
	return GameSession.text("one_gold") if cost == 1 else I18N.f("ui.gold_cost", {"n": cost})


func _talent_def(key: String) -> Dictionary:
	return talent_ext.defs.get(key, {}) if talent_ext else {}


func talent_color(key: String) -> Color:
	var def := _talent_def(key)
	match str(def.get("type", "")):
		"unlock":
			return kind_color(str(def.kind)).lerp(Color("5dabf6"), 0.35)
		"workers", "training":
			return Color("b18cff")
		"family", "families":
			return Color(str(FAMILY_COLORS.get(str(def.get("family", "classic")), "74ce95")))
	return Color("3ee6d0")


func talent_title(key: String) -> String:
	var def := _talent_def(key)
	match str(def.get("type", "")):
		"unlock":
			return I18N.upper(display_name(str(def.kind)))
		"workers":
			return GameSession.text("workers") % int(def.limit)
		"training":
			return I18N.f("talent.training", {"r": ROMAN[clampi(int(key.trim_prefix("bdr_training_")) - 1, 0, 9)]})
		"families":
			return I18N.t("talent.families")
		"family":
			return I18N.f("talent.family", {"family": I18N.upper(I18N.t("family." + str(def.family))), "r": ROMAN[int(def.level) - 1]})
	return I18N.t("talent." + key)


func talent_effect(key: String) -> String:
	var def := _talent_def(key)
	match str(def.get("type", "")):
		"unlock":
			return I18N.f("talent.unlock_desc", {"name": display_name(str(def.kind)), "tier": int(def.tier)})
		"workers":
			return GameSession.text("talent_workers_effect") % int(def.limit)
		"training":
			return I18N.f("talent.training_desc", {"n": int(def.tier)})
		"families":
			return I18N.t("talent.families_desc")
		"family":
			return I18N.f("talent.family_desc", {"family": I18N.t("family." + str(def.family)), "p": 50 if int(def.level) == 1 else 150})
	return I18N.t("talent." + key + "_desc")


func talent_icon(key: String) -> String:
	var def := _talent_def(key)
	match str(def.get("type", "")):
		"unlock":
			return icon_path(str(def.kind))
		"training":
			return "res://assets/art/скилз/npc_speed.png"
		"families":
			return "res://assets/art/talents/synergy_master.png"
		"family":
			var icon_kind: String = TalentsExtScript.FAMILY_ICON.get(str(def.family), "50_50")
			return main._lucky_kind_icon_path(icon_kind)
	match key:
		"bdr_sell_1", "bdr_sell_2":
			return _first_existing(["res://bdr/art/ui/sell_icon.png", "res://assets/art/gold.png"])
		"bdr_event_freq_1", "bdr_event_freq_2", "bdr_event_reward":
			return "res://assets/art/events/golden_bone.png"
		"bdr_lucky_discount":
			return "res://assets/art/lucky_dice/gold_lucky_cube.png"
		"bdr_offering_bonus":
			return "res://assets/art/dog_shrine/tarot_grimoire_icon.png"
		"bdr_staff_limit_1", "bdr_staff_limit_2":
			return "res://assets/art/lucky_dice/accountant.png"
		"bdr_auto_speed":
			return icon_path("robot")
		"bdr_aura_radius":
			return icon_path("aura")
		"bdr_chain_power":
			return icon_path("fire")
	return "res://assets/art/talents/synergy_master.png"


func _first_existing(paths: Array) -> String:
	for path in paths:
		if FileAccess.file_exists(path) or ResourceLoader.exists(path):
			return path
	return paths[-1]


func talent_tier(key: String) -> int:
	var def := _talent_def(key)
	match str(def.get("type", "")):
		"family":
			return int(def.level)
		"training":
			return int(key.trim_prefix("bdr_training_"))
	return 0


func on_talent_bought(key: String) -> void:
	if not key.begins_with("bdr_"):
		return
	var def := _talent_def(key)
	stat("talents_bought", 1)
	if str(def.get("type", "")) == "unlock":
		var kind := str(def.kind)
		if is_unlocked(kind):
			main.die_levels[kind] = main._die_level(kind) + 3
			toast(I18N.f("fx.lb_level", {"name": display_name(kind)}) + " ×3")
		else:
			unlock(kind)
	main._invalidate_eco()


# ---------------------------------------------------------------- income tracking
## Income per second of the dice (bonus money from events and staff is not counted).
func income_rate() -> float:
	return _income_rate


func _track_income(delta: float) -> void:
	_income_timer += delta
	if _income_timer < 1.0:
		return
	var total: float = float(main.total_money_earned)
	if _income_last_total < 0.0 or total < _income_last_total:
		_income_last_total = total
		_income_excluded = 0.0
		_income_timer = 0.0
		return
	var earned := maxf(0.0, total - _income_last_total - _income_excluded)
	var per_second := earned / _income_timer
	_income_rate = per_second if _income_rate <= 0.0 else lerpf(_income_rate, per_second, 0.15)
	_income_last_total = total
	_income_excluded = 0.0
	_income_timer = 0.0


## Pays bonus money (events, miners...) without feeding it back into the income rate.
func pay_bonus(amount: float, at: Vector2 = Vector2(-1.0, -1.0)) -> void:
	if amount <= 0.0:
		return
	_income_excluded += amount
	main._add_money(minf(amount, 1.0e300))
	if at.x >= 0.0 and main._can_show_reward_popup(true):
		main._show_reward(at, main._bdr_money_text(amount, true), true)


func popup_at(at: Vector2, key: String, params: Dictionary = {}) -> void:
	if main._can_show_reward_popup(true):
		main._show_reward(at + Vector2(0, -26), I18N.f(key, params), true)


## Shows a staff member for a moment at the place where they work.
func fx_staff(path: String, at: Vector2) -> void:
	coop.on_event_message(["staff_pop", path, at])
	for index in range(_staff_pops.size() - 1, -1, -1):
		if not is_instance_valid(_staff_pops[index]):
			_staff_pops.remove_at(index)
	if _staff_pops.size() >= STAFF_POP_MAX:
		return
	var pop := TextureRect.new()
	pop.texture = CleanTextureLoader.load_texture(path)
	pop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	pop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pop.size = Vector2(72, 72)
	pop.pivot_offset = pop.size * 0.5
	pop.position = main._clamp_die_position(at + Vector2(34, -40)) - pop.size * 0.5
	pop.z_index = 60
	pop.scale = Vector2(0.3, 0.3)
	main.add_child(pop)
	_staff_pops.append(pop)
	var tween := pop.create_tween()
	tween.tween_property(pop, "scale", Vector2.ONE, 0.16).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_interval(0.5)
	tween.tween_property(pop, "modulate:a", 0.0, 0.25)
	tween.tween_callback(pop.queue_free)
