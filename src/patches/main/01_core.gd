# Dice Rush Extended - core patch for main.gd: performance architecture.

const BDRGameScript: = preload("res://bdr/game/bdr_game.gd")
const DiceGridScript: = preload("res://bdr/core/dice_grid.gd")
const DiceBatchScript: = preload("res://bdr/render/dice_batch.gd")
const BDR_HOVER_LAUNCH_CAP: = 400
const BDR_PICK_HALF: = 38.0

var bdr: BDRGameScript
var _grid: DiceGridScript
var _batch: DiceBatchScript
var _cats: Array[DiceActor] = []
var _light_buckets: Dictionary = {}
var _light_next_bucket: int = -1
var _spin3d_active: int = 0
var _edition_full: = true
var _edition_demo: = false
var _tmp_query: Array[DiceActor] = []
var _tmp_pick: Array[DiceActor] = []
var _npc_filter: Callable
var _npc_roll_cache: Dictionary = {}
var _eco_cache: Dictionary = {}
var _eco_dirty: = true
var _eco_cache_msec: = 0
var _dog_power_cache: Dictionary = {}
var _price_memo: Dictionary = {}
var _fs_rolls: = 0
var _fs_gold_boosted: = 0
var _fs_npc_payouts: = 0
var _fs_d4_max: = 0
var _fs_prehistoric_waves: = 0
var _fs_skull_streak: = 0
var _fs_income_dirty: = false
var _fs_gold_earned: = 0
var _fs_landing_sound: = false
var _fs_crypto_best: = 0
var _fs_prehistoric_launch_best: = 0
var developer_console_commands = null


func _dev_log(_method: StringName, _arguments: Array = []) -> void :
	pass


func developer_console_execute(_command_line: String) -> Dictionary:
	return {"ok": false, "summary": "Dice Rush Extended"}


func developer_console_complete(_command_line: String) -> Array[String]:
	return []


func developer_console_status() -> Dictionary:
	return {}


func developer_console_state() -> Dictionary:
	return {}


func _ready() -> void :
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().auto_accept_quit = false
	get_viewport().physics_object_picking = false
	_edition_full = DiceRushEdition.is_full()
	_edition_demo = DiceRushEdition.is_demo()
	_npc_filter = _npc_target_filter
	rng.randomize()
	pixel_font = GameSession.ui_font()
	display_font = GameSession.display_font()
	if not GameSession.gameplay_preferences_changed.is_connected(_on_gameplay_preferences_changed):
		GameSession.gameplay_preferences_changed.connect(_on_gameplay_preferences_changed)
	if not GameSession.npc_skin_changed.is_connected(_on_npc_skin_changed):
		GameSession.npc_skin_changed.connect(_on_npc_skin_changed)
	if not GamepadCursor.primary_pressed.is_connected(_on_gamepad_primary_pressed):
		GamepadCursor.primary_pressed.connect(_on_gamepad_primary_pressed)
	if not GamepadCursor.command_pressed.is_connected(_on_gamepad_command_pressed):
		GamepadCursor.command_pressed.connect(_on_gamepad_command_pressed)
	if not GamepadCursor.navigation_requested.is_connected(_on_gamepad_navigation_requested):
		GamepadCursor.navigation_requested.connect(_on_gamepad_navigation_requested)
	if not AchievementService.steam_shutdown_requested.is_connected(_on_steam_shutdown_requested):
		AchievementService.steam_shutdown_requested.connect(_on_steam_shutdown_requested)
	bdr = BDRGameScript.new()
	bdr.name = "BDRGame"
	add_child(bdr)
	bdr.setup(self)
	_build_payout_audio()
	_initialize_talents()
	var camera: = Camera2D.new()
	camera.position = Vector2(960, 540)
	camera.enabled = true
	add_child(camera)
	_build_world()
	_grid = DiceGridScript.new()
	_grid.setup(BOARD_RECT)
	_batch = DiceBatchScript.new()
	add_child(_batch)
	_batch.build_atlas(bdr.batch_textures(), bdr.batch_sizes())
	_batch.enabled = bdr.batch_enabled()
	_build_shop()
	_build_hud()
	_build_golden_bone_event_ui()
	_build_upgrade_overlay()
	_build_dog_shrine_overlay()
	_build_controller_hints()
	_build_hover_tooltip()
	_build_menu_system()
	bdr.build_ui()
	_fit_all_ui_text.call_deferred()
	get_viewport().size_changed.connect(_apply_safe_area_offsets)
	_apply_safe_area_offsets.call_deferred()
	_build_autosave_timer()
	save_path = GameSession.game_save_path()
	if bdr.is_coop_client():
		bdr.start_coop_client_world()
		return
	if GameSession.launch_mode == "continue":
		if not _load_saved_game_with_recovery():
			GameSession.start_screen_target = "save_slots"
			GameSession.launch_mode = ""
			get_tree().change_scene_to_file(START_MENU_SCENE)
			return
	else:
		if FileAccess.file_exists(save_path):
			GameSession.preserve_file_for_diagnostics(save_path, "pre-new-game")
		_start_fresh_game(true)
	GameSession.launch_mode = ""
	bdr.on_game_ready()


## test harness: per-section timing of the main loop (usec, summed until reset)
var bdr_prof_on: = false
var bdr_prof: Dictionary = {}


func _bdr_pc(key: String, amount: int = 1) -> void:
	bdr_prof[key] = int(bdr_prof.get(key, 0)) + amount


func _bdr_pt(section: String, started: int) -> int:
	var now: = Time.get_ticks_usec()
	bdr_prof[section] = int(bdr_prof.get(section, 0)) + (now - started)
	return now


func _process(delta: float) -> void :
	var t0: = Time.get_ticks_usec() if bdr_prof_on else 0
	_flush_frame_effects()
	_update_controller_hint_visibility()
	if _visual_overlay_blocks_wave() and not active_wave_layers.is_empty():
		_clear_active_waves()
	_update_hover_tooltip()
	_update_tree_edge_scroll(delta)
	_update_hold_buy(delta)
	bdr.process_always(delta)
	if bdr_prof_on:
		t0 = _bdr_pt("ui", t0)
	if get_tree().paused:
		return
	_process_light_rolls()
	if bdr_prof_on:
		t0 = _bdr_pt("light_rolls", t0)
	if bdr.is_coop_client():
		bdr.process_client(delta)
		return
	if dog_shrine_transaction_active and not bdr.world_runs_during_menus():
		return
	if game_started:
		play_time_seconds += delta
		if cat_pending_births > 0 and _dice_table_has_capacity() and not autosave_pending and pending_safe_action.is_empty():
			_try_pending_cat_birth()
	_update_golden_bone_event(delta)
	if bdr_prof_on:
		t0 = _bdr_pt("golden_bone", t0)
	_update_hover_roll(delta)
	if bdr_prof_on:
		t0 = _bdr_pt("hover_roll", t0)
	_drain_hover_completion_queue(HOVER_COMPLETION_BUDGET_USEC)
	if bdr_prof_on:
		t0 = _bdr_pt("hover_drain", t0)
	if bool(special_dice_unlocked.get("crypto", false)):
		crypto_market_elapsed += delta
		if crypto_market_elapsed >= CRYPTO_REFRESH_SECONDS:
			crypto_market_elapsed = fmod(crypto_market_elapsed, CRYPTO_REFRESH_SECONDS)
			_roll_crypto_market_value()
			_update_all_labels()
	for fog in fog_parts:
		fog.position.x += 10.0 * delta
		if fog.position.x >= fog.size.x:
			fog.position.x -= fog.size.x * 2.0
	for index in range(golden_dice.size() - 1, -1, -1):
		if not is_instance_valid(golden_dice[index]):
			golden_dice.remove_at(index)
	var world_blocked: = _world_blocked_for_auto_rolls()
	for die in golden_dice:
		var id: = die.get_instance_id()
		var time_left: float = golden_timers.get(id, _golden_auto_roll_delay()) - delta
		if time_left <= 0.0 and not die.rolling and not world_blocked and pending_safe_action.is_empty() and not autosave_pending:
			_start_die_roll(die)
			time_left = _golden_auto_roll_delay()
		golden_timers[id] = time_left
	if bdr_prof_on:
		t0 = _bdr_pt("golden_dice", t0)
	bdr.process_world(delta)
	if bdr_prof_on:
		t0 = _bdr_pt("bdr_world", t0)


## True when automatic rolls (golden dice, robots, ...) have to wait (menus open in single player).
func _world_blocked_for_auto_rolls() -> bool:
	if dog_shrine_transaction_active and not bdr.world_runs_during_menus():
		return true
	if upgrade_overlay.visible and not bdr.world_runs_during_menus():
		return true
	return false


func _unhandled_input(event: InputEvent) -> void :
	if DeveloperConsole.is_open():
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		if _try_pick_click(event.position):
			get_viewport().set_input_as_handled()
			return
	if event is InputEventKey and event.pressed and not event.echo:
		if is_instance_valid(dog_shrine_controller) and dog_shrine_controller.visible:
			if event.keycode == KEY_ESCAPE:
				dog_shrine_controller.request_close()
				get_viewport().set_input_as_handled()
			return
		if bdr.handle_key(event):
			get_viewport().set_input_as_handled()
			return
		if event.keycode == KEY_U and game_started:
			_controller_toggle_upgrade_page("tree")
		elif event.keycode == KEY_ESCAPE and upgrade_overlay.visible:
			_close_upgrade()
			get_viewport().set_input_as_handled()
	elif event is InputEventJoypadButton and event.pressed:
		if event.button_index in [JOY_BUTTON_DPAD_UP, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT] and _controller_can_focus_shop():
			_controller_focus_shop(event.button_index)
			get_viewport().set_input_as_handled()


func _try_pick_click(screen_position: Vector2) -> bool:
	if not game_started or get_tree().paused or upgrade_overlay.visible or dog_shrine_transaction_active:
		return false
	if bdr.blocks_board_clicks():
		return false
	var world: = get_viewport().get_canvas_transform().affine_inverse() * screen_position
	var die: = _pick_die_at(world)
	if die == null:
		return false
	if bdr.is_coop_client():
		bdr.coop_request_click(die)
		return true
	_on_die_clicked(die)
	return true


## Finds the top-most dice under a world position (replaces physics picking).
func _pick_die_at(world: Vector2) -> DiceActor:
	var best: DiceActor = null
	var best_z: = -100000
	var best_distance: = INF
	for cat in _cats:
		if not is_instance_valid(cat):
			continue
		var body: Vector2 = cat.debug_body_global_position()
		if absf(body.x - world.x) <= 42.0 and absf(body.y - world.y) <= 40.0:
			var cat_distance: = body.distance_squared_to(world)
			if cat.z_index > best_z or (cat.z_index == best_z and cat_distance < best_distance):
				best = cat
				best_z = cat.z_index
				best_distance = cat_distance
	_tmp_pick.clear()
	var pick_half: float = BDR_PICK_HALF * maxf(0.45, bdr.dice_scale())
	_grid.query_radius(world, pick_half * 1.45, _tmp_pick)
	for die_value in active_animated_roll_ids.values():
		if is_instance_valid(die_value):
			_tmp_pick.append(die_value)
	for die in _tmp_pick:
		if not is_instance_valid(die) or not die.visible:
			continue
		var p: Vector2 = die.position
		if absf(p.x - world.x) > pick_half or absf(p.y - world.y) > pick_half:
			continue
		var distance: = p.distance_squared_to(world)
		if die.z_index > best_z or (die.z_index == best_z and distance < best_distance):
			best = die
			best_z = die.z_index
			best_distance = distance
	return best


func _on_gamepad_primary_pressed(cursor_position: Vector2) -> void :
	if not game_started or upgrade_overlay.visible or dog_shrine_transaction_active or _visual_overlay_blocks_wave() or autosave_pending or not pending_safe_action.is_empty():
		return
	var world_cursor: = get_viewport().get_canvas_transform().affine_inverse() * cursor_position
	var nearest: = _pick_die_at(world_cursor)
	if nearest:
		GamepadCursor.consume_primary_input()
		_on_die_clicked(nearest)


func _die_texture_path(kind: String) -> String:
	match kind:
		"50_50":
			return ART + "магаизн 5050.png"
		"d4":
			return DICE_ART + "d4.png"
		"3x4":
			return DICE_ART + "three_by_four.png"
		"d2":
			return DICE_ART + "d_squared.png"
		"777":
			return DICE_ART + "dice_777.png"
		"prehistoric":
			return DICE_ART + "prehistoric.png"
		"golden":
			return DICE_ART + "golden.png"
		"npc_die":
			return DICE_ART + "npc_die.png"
		"crypto":
			return DICE_ART + "crypto.png"
		"diamond":
			return DICE_ART + "diamond.png"
		"pi":
			return DICE_ART + "pi.png"
		"cat":
			return DICE_ART + "cat/idle.png"
	var custom: = bdr.die_texture_path(kind)
	if not custom.is_empty():
		return custom
	return ART + "cube d6 4/фото в магазине 4.png"


func _spawn_die(kind: String, spawn_position: Vector2) -> DiceActor:
	var die: = (CatDiceActorScript.new() if kind == "cat" else DiceActorScript.new()) as DiceActor
	add_child(die)
	die.tree_exiting.connect(_on_die_tree_exiting.bind(die.get_instance_id()))
	die.tree_exiting.connect(_bdr_detach_die.bind(die))
	die.position = spawn_position
	var show_gold_aura: = kind != "golden" or golden_dice.size() < MAX_VISIBLE_GOLD_AURAS
	bdr.prepare_die(die, kind)
	die.configure(kind, _die_texture_path(kind), BOARD_RECT, rng.randi(), Color.WHITE, show_gold_aura)
	die.scale = Vector2.ONE * bdr.dice_scale()
	if kind == "golden":
		die.set_gold_aura_radius(_gold_aura_radius())
	die.roll_completed.connect(_on_die_roll_completed)
	if kind == "cat":
		die.jump_target_picker = _random_roll_target
		die.food_eaten.connect(_on_cat_food_eaten)
		die.replication_ready.connect(_on_cat_replication_ready)
		_cats.append(die)
	else:
		_grid.insert(die, die.position)
		if _batch.add(die):
			die.set_batched(true)
	dice.append(die)
	if kind == "golden":
		golden_dice.append(die)
		golden_timers[die.get_instance_id()] = _golden_auto_roll_delay()
	bdr.on_die_spawned(die)
	return die


## Removes a dice from the grid / batch renderer (call before freeing or hiding it).
func _bdr_detach_die(die: DiceActor) -> void:
	if not is_instance_valid(die):
		return
	if die.grid_cell >= 0:
		_grid.remove(die)
	if die.batch_band != -1:
		_batch.remove(die)
	if die.die_kind == "cat":
		_cats.erase(die)
	if die.spin3d:
		die.spin3d = false
		_spin3d_active = maxi(0, _spin3d_active - 1)
	bdr.on_die_detached(die)


## Puts a resting dice back into the batch renderer.
func _bdr_rest_die(die: DiceActor) -> void:
	if not is_instance_valid(die) or die.die_kind == "cat" or die.special_motion:
		return
	if die.rolling and die.is_animated_roll():
		return
	if die.grid_cell < 0:
		return
	_grid.move(die, die.grid_position())
	if _batch.add(die):
		die.set_batched(true)


func _bdr_unrest_die(die: DiceActor) -> void:
	if die.batch_band != -1:
		_batch.remove(die)
	die.set_batched(false)


func _clear_actors() -> void :
	for die in dice:
		if is_instance_valid(die):
			die.queue_free()
	for npc in npcs:
		if is_instance_valid(npc):
			npc.queue_free()
	dice.clear()
	npcs.clear()
	golden_dice.clear()
	_cats.clear()
	if _grid:
		_grid.clear()
	if _batch:
		_batch.clear_all()
	_light_buckets.clear()
	_light_next_bucket = -1
	_spin3d_active = 0
	active_roll_count = 0
	active_animated_roll_count = 0
	active_roll_ids.clear()
	active_animated_roll_ids.clear()
	active_interactive_animated_roll_ids.clear()
	hover_roll_latched_ids.clear()
	hover_roll_contact_ids.clear()
	hover_roll_cursor_valid = false
	hover_completion_queue.clear()
	hover_completion_queue_head = 0
	hover_completion_pending_ids.clear()
	queued_player_rerolls.clear()
	dice_placement_sequence = 0
	npc_target_scan_cursor = 0
	autosave_pending = false
	golden_timers.clear()
	wave_chains.clear()
	root_wave_merge_chain_id = 0
	root_wave_merge_deadline_msec = 0
	prehistoric_root_batch_frame = -1
	prehistoric_root_batch_serial = 0
	prehistoric_root_batch_chains.clear()
	prehistoric_root_batch_remaining.clear()
	_bdr_root_batch_msec.clear()
	if bdr:
		bdr.on_actors_cleared()


# ---------------------------------------------------------------- lightweight roll scheduler
func _light_schedule(die: DiceActor) -> void:
	var bucket: = die.light_due_msec >> 4
	var list = _light_buckets.get(bucket)
	if list == null:
		list = []
		_light_buckets[bucket] = list
	list.append(die)


func _process_light_rolls() -> void:
	var now_bucket: = Time.get_ticks_msec() >> 4
	if _light_next_bucket < 0:
		_light_next_bucket = now_bucket - 1
	if _light_buckets.is_empty():
		_light_next_bucket = now_bucket + 1
		return
	if now_bucket - _light_next_bucket > 20000:
		_light_next_bucket = now_bucket - 20000
	while _light_next_bucket <= now_bucket:
		var list = _light_buckets.get(_light_next_bucket)
		if list != null:
			_light_buckets.erase(_light_next_bucket)
			if bdr_prof_on:
				_bdr_pc("c_light_land", list.size())
			for die in list:
				if is_instance_valid(die):
					die.finish_light_roll()
		_light_next_bucket += 1


# ---------------------------------------------------------------- roll start
func _animated_roll_budget() -> int:
	var setting: = bdr.animation_budget()
	if dice.size() >= 4000:
		return mini(64, setting)
	if dice.size() >= 2000:
		return mini(96, setting)
	if dice.size() >= 1000:
		return mini(160, setting)
	return setting


func _hover_animated_roll_budget() -> int:
	return mini(dice.size(), bdr.hover_animation_budget())


func _start_die_roll(die: DiceActor, chain_id: int = 0, forced_target: Vector2 = Vector2(-1.0, -1.0), play_roll_sound: bool = true, internal_continuation: bool = false, interactive_motion: bool = false, force_lightweight: bool = false) -> void :
	if not is_instance_valid(die) or die.rolling\
	or ((autosave_pending or not pending_safe_action.is_empty() or (dog_shrine_transaction_active and not bdr.world_runs_during_menus())) and not internal_continuation):
		return
	if die.die_kind == "cat" or die.special_motion:
		return
	var die_id: = die.get_instance_id()
	active_roll_count += 1
	active_roll_ids[die_id] = die
	var animate_motion: = not force_lightweight and (interactive_motion or active_animated_roll_count < _animated_roll_budget())
	if bdr_prof_on:
		_bdr_pc("c_start_" + ("hover" if interactive_motion else "auto") + ("_anim" if animate_motion else "_light"))
	if animate_motion:
		active_animated_roll_count += 1
		active_animated_roll_ids[die_id] = die
		if interactive_motion:
			active_interactive_animated_roll_ids[die_id] = die
		_bdr_unrest_die(die)
		die.spin3d = _spin3d_active < bdr.spin3d_budget()
		die.diagonal_spin_enabled = die.spin3d
		if die.spin3d:
			_spin3d_active += 1
	if die.die_kind == "prehistoric" and chain_id == 0:
		var launch_frame: = Engine.get_process_frames()
		if launch_frame != prehistoric_root_batch_frame:
			prehistoric_root_batch_frame = launch_frame
			prehistoric_root_batch_serial += 1
		die.set_meta("prehistoric_root_batch", prehistoric_root_batch_serial)
		var root_batch: = int(die.get_meta("prehistoric_root_batch", 0))
		prehistoric_root_batch_remaining[root_batch] = int(prehistoric_root_batch_remaining.get(root_batch, 0)) + 1
		_bdr_root_batch_msec[root_batch] = Time.get_ticks_msec()
	if play_roll_sound:
		GameSession.play_sfx("roll")
	var dynamic_value: = 0
	if die.die_kind == "npc_die":
		dynamic_value = npc_count * _npc_die_pay_per_worker()
	elif die.die_kind == "crypto":
		dynamic_value = crypto_market_value
	var resolved_target: = forced_target
	if resolved_target.x < 0.0 or resolved_target.y < 0.0:
		resolved_target = _random_roll_target(die.position)
	else:
		resolved_target = _clamp_die_position(resolved_target)
	die.player_rolled = interactive_motion
	die.start_roll(
		chain_id,
		dynamic_value,
		resolved_target,
		animate_motion,
		dice.size(),
		interactive_motion and not animate_motion,
		interactive_motion
	)
	_grid.move(die, die.grid_position())
	if not animate_motion:
		_light_schedule(die)
	bdr.on_roll_started(die, resolved_target, animate_motion, interactive_motion)


# ---------------------------------------------------------------- economy caches
func _invalidate_eco() -> void:
	_eco_dirty = true


func _dog_card_rank(card_id: String) -> int:
	if not _edition_full or not dog_shrine_blessing_ranks.has(card_id):
		return 0
	return maxi(0, int(dog_shrine_blessing_ranks.get(card_id, 0)))


func _dog_card_effect_power(card_id: String) -> float:
	if _eco_dirty:
		_refresh_eco_cache()
	var cached = _dog_power_cache.get(card_id)
	if cached != null:
		return cached
	var power: = _dog_effect_power_for_rank(_dog_card_rank(card_id))
	_dog_power_cache[card_id] = power
	return power


func _refresh_eco_cache() -> void:
	_eco_dirty = false
	_eco_cache.clear()
	_dog_power_cache.clear()
	_npc_roll_cache.clear()
	_eco_cache_msec = Time.get_ticks_msec()


## [flat_always, flat_if_positive, percent, lucky_level, kind_multiplier]
func _eco_kind(kind: String) -> Array:
	if _eco_dirty or Time.get_ticks_msec() - _eco_cache_msec > 1500:
		_refresh_eco_cache()
	var cached = _eco_cache.get(kind)
	if cached != null:
		return cached
	var flat_always: = _guaranteed_income_bonus()
	var flat_positive: = 0
	if kind == "50_50":
		flat_always = _safe_add_int64(flat_always, _fifty_profit_bonus())
	elif kind == "d2":
		flat_always = _safe_add_int64(flat_always, _d2_guaranteed_bonus())
	elif kind == "d4":
		flat_positive = _d4_income_bonus()
	var synergy_percent: = _amplified_synergy_percent(_ordinary_synergy_percent(kind) + _special_synergy_percent(kind))
	var dog_percent: = _dog_shrine_bonus_percent(kind, 0, false, synergy_percent)
	var percent: = synergy_percent + dog_percent + bdr.kind_percent_bonus(kind)
	var entry: = [flat_always, flat_positive, percent, _die_level(kind), bdr.kind_multiplier(kind)]
	_eco_cache[kind] = entry
	return entry


func _eco_global(key: String) -> Variant:
	if _eco_dirty or Time.get_ticks_msec() - _eco_cache_msec > 1500:
		_refresh_eco_cache()
	var cache_key: = "@" + key
	if _eco_cache.has(cache_key):
		return _eco_cache[cache_key]
	var value: Variant = 0
	match key:
		"three_by_four_tier":
			value = _three_by_four_multiplier_tier()
		"golden_payout":
			value = _golden_payout_value()
		"diamond_payout":
			value = _diamond_payout_value()
		"pi_payout":
			value = _pi_payout_value()
		"seven_combo_target":
			value = _seven_combo_target()
		"accountant_percent":
			value = _accountant_total_bonus_percent()
		"repeat_chance":
			value = _worker_repeat_roll_chance()
		"hermit_power":
			value = _dog_card_effect_power("l_hermit")
		"seven_combo_extra":
			var base_combo_target: = 2 if bool(upgrades.get("seven_combo", false)) else 3
			var payout_power: = maxf(0.0, _dog_card_effect_power("l_judgement") - float(base_combo_target - 1))
			value = roundi(payout_power * 100.0)
	_eco_cache[cache_key] = value
	return value


func _hermit_income_multiplier(source: DiceActor) -> float:
	var power: float = _eco_global("hermit_power")
	if power <= 0.0:
		return 1
	if _grid.any_within(source.position, 175.0, source):
		return 1
	return 1.0 + power


func _npc_target_filter(die: DiceActor) -> bool:
	if die.rolling or die.reserved_by != 0 or die.special_motion:
		return false
	var allowed = _npc_roll_cache.get(die.die_kind)
	if allowed == null:
		allowed = _npc_can_roll(die.die_kind)
		_npc_roll_cache[die.die_kind] = allowed
	return allowed


func _on_npc_target_needed(npc: NPCActor) -> void :
	if bdr.is_coop_client():
		return
	if lucky_transaction_active or (dog_shrine_transaction_active and not bdr.world_runs_during_menus()) or autosave_pending or not pending_safe_action.is_empty():
		return
	if _eco_dirty:
		_refresh_eco_cache()
	var nearest: = _grid.nearest(npc.position, _npc_filter)
	if nearest:
		nearest.reserved_by = npc.actor_id
		npc.assign_target(nearest)


# ---------------------------------------------------------------- landing
func _on_die_roll_completed(die: DiceActor, reward: int, _result_text: String, result_value: int, chain_id: int) -> void :
	if bdr.is_coop_client():
		_coop_client_landed(die)
		return
	var pt0: = Time.get_ticks_usec() if bdr_prof_on else 0
	if bdr_prof_on:
		bdr_prof["landings"] = int(bdr_prof.get("landings", 0)) + 1
	active_roll_count = maxi(0, active_roll_count - 1)
	var die_id: = die.get_instance_id()
	active_roll_ids.erase(die_id)
	hover_roll_latched_ids.erase(die_id)
	if active_animated_roll_ids.has(die_id):
		active_animated_roll_ids.erase(die_id)
		active_animated_roll_count = maxi(0, active_animated_roll_count - 1)
	active_interactive_animated_roll_ids.erase(die_id)
	if die.spin3d:
		die.spin3d = false
		_spin3d_active = maxi(0, _spin3d_active - 1)
	var strength_eligible: = false
	if die.has_meta("dog_strength_eligible"):
		strength_eligible = bool(die.get_meta("dog_strength_eligible", false))
		die.remove_meta("dog_strength_eligible")
	_fs_rolls += 1
	_fs_landing_sound = true
	if first_roll_hint_layer:
		_complete_first_roll_hint()
	var kind: = die.die_kind
	var triggered_777_combo: = false
	var payout: float = float(reward)
	var custom_def = bdr.def_for(kind)
	if custom_def != null:
		payout = bdr.base_reward(die, result_value, custom_def)
	else:
		if kind == "777":
			if result_value == 7:
				die.streak_777 += 1
				if die.streak_777 >= int(_eco_global("seven_combo_target")):
					die.streak_777 = 0
					payout = 777.0
					triggered_777_combo = true
			else:
				die.streak_777 = 0
				die.streak_777_combos = 0
		elif kind == "50_50":
			if result_value == 0:
				die.streak_50_skulls += 1
				_fs_skull_streak = maxi(_fs_skull_streak, die.streak_50_skulls)
				bdr.on_skull()
			else:
				die.streak_50_skulls = 0
		if kind == "3x4":
			var multiplier_tier: int = _eco_global("three_by_four_tier")
			if multiplier_tier > 0:
				payout = float(_three_by_four_reward(result_value, multiplier_tier))
		elif kind == "golden":
			var golden_reward: int = _eco_global("golden_payout")
			if golden_reward > 0:
				payout = float(golden_reward)
		elif kind == "diamond":
			payout = float(_eco_global("diamond_payout"))
		elif kind == "pi":
			payout = float(_eco_global("pi_payout"))
	if bdr_prof_on:
		pt0 = _bdr_pt("land_reward", pt0)
	var eco: Array = _eco_kind(kind)
	if kind == "d4" and payout > 0.0:
		if result_value == 4:
			_fs_d4_max += 1
		payout += float(eco[1])
	payout += float(eco[0])
	var percent: int = eco[2] + bdr.positional_percent(die)
	if triggered_777_combo:
		percent += int(_eco_global("seven_combo_extra"))
	if payout > 0.0 and percent > 0:
		payout *= 1.0 + float(percent) / 100.0
	var achievement_percent: = _achievement_income_percent()
	if payout > 0.0 and achievement_percent > 0:
		payout *= 1.0 + float(achievement_percent) / 100.0
	if payout > 0.0:
		var queued_spatial_request: Dictionary = queued_player_rerolls.get(die_id, {})
		var has_hover_spatial_snapshot: = bool(queued_spatial_request.get("hover_spatial_snapshot", false))
		var income_multiplier: = float(queued_spatial_request.get("hover_gold_multiplier", 1.0)) if has_hover_spatial_snapshot else (_gold_income_multiplier(die) if not golden_dice.is_empty() else 1.0)
		if income_multiplier > 1:
			payout *= income_multiplier
			_fs_gold_boosted += 1
		var hermit_multiplier: = float(queued_spatial_request.get("hover_hermit_multiplier", 1.0)) if has_hover_spatial_snapshot else _hermit_income_multiplier(die)
		if hermit_multiplier > 1:
			payout *= hermit_multiplier
		var lucky_level: int = eco[3]
		if lucky_level > 1:
			payout *= float(lucky_level)
		if accountant_count > 0:
			var total_percent: int = _eco_global("accountant_percent")
			if total_percent > 0:
				payout *= 1.0 + float(total_percent) / 100.0
		if golden_bone_luck_time_left > 0.0:
			payout *= float(_golden_bone_luck_multiplier())
		payout *= float(eco[4]) * bdr.global_multiplier() * die.pending_mult
		payout = minf(payout, BDR_MONEY_CAP)
	die.pending_mult = 1.0
	if bdr_prof_on:
		pt0 = _bdr_pt("land_mult", pt0)
	if triggered_777_combo:
		GameSession.play_sfx("rare")
		AchievementService.increment_stat("seven_combos")
		die.streak_777_combos += 1
		AchievementService.report_stat("seven_combo_streak", die.streak_777_combos)
		if chain_id > 0:
			AchievementService.report_stat("prehistoric_777_combo", 1)
	if kind == "npc_die" and payout > 0.0:
		_fs_npc_payouts += 1
	if kind == "crypto" and payout >= 1000000.0:
		_fs_crypto_best = maxi(_fs_crypto_best, _bdr_int_stat(payout))
	if payout > 0.0:
		_play_payout_sound()
	_add_money(payout)
	die.last_payout = payout
	die.last_payout_msec = Time.get_ticks_msec()
	var payout_positive: = payout > 0.0
	if _can_show_reward_popup(payout_positive):
		_show_reward(die.position, _bdr_money_text(payout), payout_positive)
	if bdr_prof_on:
		pt0 = _bdr_pt("land_money", pt0)
	if kind == "prehistoric":
		_fs_prehistoric_waves += 1
		var root_batch: = int(die.get_meta("prehistoric_root_batch", 0))
		if die.has_meta("prehistoric_root_batch"):
			die.remove_meta("prehistoric_root_batch")
		_trigger_prehistoric_wave(die, chain_id, root_batch)
	if bdr_prof_on:
		pt0 = _bdr_pt("la_prehistoric", pt0)
	if chain_id > 0:
		_finish_wave_roll(chain_id)
	if bdr_prof_on:
		pt0 = _bdr_pt("la_wave_finish", pt0)
	if custom_def != null:
		bdr.after_landing(die, payout, result_value, custom_def)
		if bdr_prof_on:
			pt0 = _bdr_pt("la_mech_" + str(custom_def.mech), pt0)
	bdr.on_any_landing(die, payout)
	if bdr_prof_on:
		pt0 = _bdr_pt("land_after", pt0)
	var player_restarted: = _consume_queued_player_reroll(die)
	if not player_restarted and strength_eligible and not dog_shrine_transaction_active\
	and is_instance_valid(die) and not die.rolling:
		var repeat_chance: float = _eco_global("repeat_chance")
		if repeat_chance > 0.0 and rng.randf() < repeat_chance:
			_start_die_roll(die, 0, Vector2(-1.0, -1.0), true, true)
	if is_instance_valid(die):
		if not die.rolling:
			hover_roll_contact_ids.erase(die_id)
		_bdr_rest_die(die)
	_finish_pending_safe_action()
	_finish_pending_autosave()
	if bdr_prof_on:
		_bdr_pt("land_tail", pt0)


func _flush_frame_effects() -> void:
	if _fs_rolls > 0:
		AchievementService.increment_stat("rolls", _fs_rolls)
		_fs_rolls = 0
	if _fs_landing_sound:
		_fs_landing_sound = false
		GameSession.play_sfx("landing")
	if _fs_income_dirty:
		_fs_income_dirty = false
		AchievementService.report_stat("income", _bdr_int_stat(total_money_earned))
	if _fs_gold_earned > 0:
		AchievementService.increment_stat("gold_earned", _fs_gold_earned)
		_fs_gold_earned = 0
	if _fs_gold_boosted > 0:
		AchievementService.increment_stat("gold_boosted_rolls", _fs_gold_boosted)
		_fs_gold_boosted = 0
	if _fs_npc_payouts > 0:
		AchievementService.increment_stat("npc_die_payouts", _fs_npc_payouts)
		_fs_npc_payouts = 0
	if _fs_d4_max > 0:
		AchievementService.increment_stat("d4_max_rolls", _fs_d4_max)
		_fs_d4_max = 0
	if _fs_prehistoric_waves > 0:
		AchievementService.increment_stat("prehistoric_waves", _fs_prehistoric_waves)
		_fs_prehistoric_waves = 0
	if _fs_skull_streak > 0:
		AchievementService.report_stat("fifty_skull_streak", _fs_skull_streak)
		_fs_skull_streak = 0
	if _fs_crypto_best > 0:
		AchievementService.report_stat("crypto_single_payout", _fs_crypto_best)
		_fs_crypto_best = 0
	if _fs_prehistoric_launch_best > 0:
		AchievementService.report_stat("prehistoric_launch_count", _fs_prehistoric_launch_best)
		_fs_prehistoric_launch_best = 0
	bdr.flush_frame()


# ---------------------------------------------------------------- hover roll (grid based)
func _hover_dice_near(cursor_position: Vector2, radius: float) -> Array[DiceActor]:
	var nearby: Array[DiceActor] = []
	_tmp_query.clear()
	_grid.query_radius(cursor_position, radius, _tmp_query)
	var radius_squared: = radius * radius
	for die in _tmp_query:
		if die.is_animated_roll():
			continue
		nearby.append(die)
	for die_value in active_animated_roll_ids.values():
		if not is_instance_valid(die_value):
			continue
		var moving: = die_value as DiceActor
		if moving.position.distance_squared_to(cursor_position) <= radius_squared:
			nearby.append(moving)
	return nearby


func _hover_dice_along(cursor_start: Vector2, cursor_end: Vector2, radius: float) -> Array[DiceActor]:
	var segment: = cursor_end - cursor_start
	if segment.length_squared() <= 0.0001:
		return _hover_dice_near(cursor_end, radius)
	var nearby: Array[DiceActor] = []
	_tmp_query.clear()
	_grid.query_segment(cursor_start, cursor_end, radius, _tmp_query)
	var radius_squared: = radius * radius
	for die in _tmp_query:
		if die.is_animated_roll():
			continue
		nearby.append(die)
	for die_value in active_animated_roll_ids.values():
		if not is_instance_valid(die_value):
			continue
		var moving: = die_value as DiceActor
		var closest: = _closest_point_on_hover_segment(moving.position, cursor_start, cursor_end)
		if moving.position.distance_squared_to(closest) <= radius_squared:
			nearby.append(moving)
	return nearby


func _update_hover_moving_contacts(cursor_position: Vector2) -> void :
	var radius_squared: = _hover_roll_radius() * _hover_roll_radius()
	var entered: Array[DiceActor] = []
	for die_value in active_animated_roll_ids.values():
		if not is_instance_valid(die_value):
			continue
		var die: = die_value as DiceActor
		var die_id: = die.get_instance_id()
		if die.position.distance_squared_to(cursor_position) <= radius_squared:
			if not hover_roll_contact_ids.has(die_id):
				entered.append(die)
			hover_roll_contact_ids[die_id] = true
		else:
			hover_roll_contact_ids.erase(die_id)
	if bdr_prof_on:
		_bdr_pc("c_moving_entered", entered.size())
	if not entered.is_empty():
		_launch_hover_dice_along(entered, cursor_position, cursor_position, true)


func _drain_hover_completion_queue(budget_usec: int) -> void :
	if hover_completion_queue_head >= hover_completion_queue.size():
		if not hover_completion_queue.is_empty():
			hover_completion_queue.clear()
		hover_completion_queue_head = 0
		return
	var started_usec: = Time.get_ticks_usec()
	var processed: = 0
	while hover_completion_queue_head < hover_completion_queue.size():
		var die: DiceActor = hover_completion_queue[hover_completion_queue_head]
		hover_completion_queue_head += 1
		if is_instance_valid(die):
			var die_id: = die.get_instance_id()
			hover_completion_pending_ids.erase(die_id)
			if die.rolling and queued_player_rerolls.has(die_id):
				die.complete_roll_now(true)
		processed += 1
		if processed > 0 and Time.get_ticks_usec() - started_usec >= budget_usec:
			break
	if bdr_prof_on:
		_bdr_pc("c_hover_completed", processed)
		_bdr_pc("c_hover_backlog", hover_completion_queue.size() - hover_completion_queue_head)
	if hover_completion_queue_head >= hover_completion_queue.size():
		hover_completion_queue.clear()
		hover_completion_queue_head = 0
	elif hover_completion_queue_head >= 256 and hover_completion_queue_head * 2 >= hover_completion_queue.size():
		var remaining: Array[DiceActor] = []
		for index in range(hover_completion_queue_head, hover_completion_queue.size()):
			remaining.append(hover_completion_queue[index])
		hover_completion_queue = remaining
		hover_completion_queue_head = 0


func _build_hover_spatial_context() -> Dictionary:
	return {"grid": true}


func _snapshot_hover_spatial_bonuses(die: DiceActor, _context: Dictionary) -> void :
	if not is_instance_valid(die):
		return
	var die_id: = die.get_instance_id()
	if not queued_player_rerolls.has(die_id):
		return
	var request: Dictionary = queued_player_rerolls[die_id]
	if bool(request.get("hover_spatial_snapshot", false)):
		return
	var logical_landing: = die.persistent_position()
	var hermit_multiplier: = 1.0
	var hermit_power: float = _eco_global("hermit_power")
	if hermit_power > 0.0 and not _grid.any_within(logical_landing, 175.0, die):
		hermit_multiplier = 1.0 + hermit_power
	request["hover_spatial_snapshot"] = true
	request["hover_gold_multiplier"] = _gold_income_multiplier_at(die, logical_landing, {}) if not golden_dice.is_empty() else 1.0
	request["hover_hermit_multiplier"] = hermit_multiplier
	queued_player_rerolls[die_id] = request


func _launch_hover_dice_along(
	nearby: Array[DiceActor],
	cursor_start: Vector2,
	cursor_end: Vector2,
	queue_rolling: bool
) -> bool:
	if nearby.is_empty():
		return false
	var candidates: Array[DiceActor] = []
	var trigger_positions: Array[Vector2] = []
	var queued_sound: = false
	for index in nearby.size():
		var die: = nearby[index]
		if die.die_kind == "cat" or die.special_motion:
			continue
		var die_id: = die.get_instance_id()
		var trigger_position: = _closest_point_on_hover_segment(die.position, cursor_start, cursor_end)
		if die.rolling:
			if queue_rolling:
				var target: = _hover_roll_target(die, trigger_position, index, nearby.size())
				var play_sound: = not queued_sound
				var queued_new: = _queue_player_reroll(die, target, play_sound, true)
				if queued_new or queued_player_rerolls.has(die_id):
					var queued_request: Dictionary = queued_player_rerolls.get(die_id, {})
					if not bool(queued_request.get("hover_spatial_snapshot", false)):
						_snapshot_hover_spatial_bonuses(die, {})
					var promote_lightweight: = active_interactive_animated_roll_ids.size() < _hover_animated_roll_budget()
					var was_registered_animated: = active_animated_roll_ids.has(die_id)
					if promote_lightweight and not was_registered_animated:
						_bdr_unrest_die(die)
					var redirected: = die.redirect_roll_visual(target, promote_lightweight)
					if redirected and promote_lightweight and not was_registered_animated:
						active_animated_roll_ids[die_id] = die
						active_interactive_animated_roll_ids[die_id] = die
						active_animated_roll_count += 1
					_enqueue_hover_completion(die)
					hover_roll_latched_ids[die_id] = true
				queued_sound = queued_new or queued_sound
			if bdr_prof_on:
				_bdr_pc("c_hover_requeue")
			continue
		candidates.append(die)
		trigger_positions.append(trigger_position)
		if candidates.size() >= BDR_HOVER_LAUNCH_CAP:
			break
	if bdr_prof_on:
		_bdr_pc("c_hover_fresh", candidates.size())
		_bdr_pc("c_hover_calls")
	if candidates.is_empty():
		return true
	var free_animation_slots: = maxi(0, _hover_animated_roll_budget() - active_interactive_animated_roll_ids.size())
	var animated_count: = mini(candidates.size(), free_animation_slots)
	var batch_size: = candidates.size()
	for index in batch_size:
		var die: = candidates[index]
		if not is_instance_valid(die) or die.rolling:
			continue
		var die_id: = die.get_instance_id()
		hover_roll_latched_ids[die_id] = true
		var target: = _hover_roll_target(die, trigger_positions[index], index, batch_size)
		_launch_player_die(die, target, index == 0 and not queued_sound, index >= animated_count)
	return true


func _try_hover_launch_along(cursor_start: Vector2, cursor_end: Vector2, queue_rolling: bool = false) -> bool:
	if not bool(upgrades.get("hover_roll", false)) or not game_started or (dog_shrine_transaction_active and not bdr.world_runs_during_menus()) or _visual_overlay_blocks_wave() or autosave_pending or not pending_safe_action.is_empty():
		return false
	if bdr.is_coop_client():
		bdr.coop_send_hover(cursor_start, cursor_end)
		return false
	var nearby: = _hover_dice_along(cursor_start, cursor_end, _hover_roll_radius())
	var radius_squared: = _hover_roll_radius() * _hover_roll_radius()
	var endpoint_contacts: Dictionary = {}
	var entered: Array[DiceActor] = []
	for die in nearby:
		if not is_instance_valid(die):
			continue
		var die_id: = die.get_instance_id()
		var inside_start: = die.position.distance_squared_to(cursor_start) <= radius_squared
		var inside_end: = die.position.distance_squared_to(cursor_end) <= radius_squared
		if inside_end:
			endpoint_contacts[die_id] = true
		if not hover_roll_contact_ids.has(die_id) or not inside_start:
			entered.append(die)
	hover_roll_contact_ids = endpoint_contacts
	if entered.is_empty():
		return not nearby.is_empty()
	return _launch_hover_dice_along(entered, cursor_start, cursor_end, queue_rolling)


# ---------------------------------------------------------------- prehistoric wave (grid based)
func _trigger_prehistoric_wave(source: DiceActor, chain_id: int, root_batch: int = 0) -> void :
	if root_batch > 0:
		var roots_remaining: = maxi(0, int(prehistoric_root_batch_remaining.get(root_batch, 0)) - 1)
		if roots_remaining > 0:
			prehistoric_root_batch_remaining[root_batch] = roots_remaining
		else:
			prehistoric_root_batch_remaining.erase(root_batch)
	var root_chain: = chain_id == 0
	var now_msec: = Time.get_ticks_msec()
	if root_chain and root_batch > 0 and prehistoric_root_batch_chains.has(root_batch) and wave_chains.has(int(prehistoric_root_batch_chains[root_batch])):
		chain_id = int(prehistoric_root_batch_chains[root_batch])
		root_chain = false
	elif root_chain and root_batch <= 0 and now_msec <= root_wave_merge_deadline_msec and wave_chains.has(root_wave_merge_chain_id):
		chain_id = root_wave_merge_chain_id
		root_chain = false
	if root_chain:
		next_wave_chain_id += 1
		chain_id = next_wave_chain_id
		wave_chains[chain_id] = {"visited": {source.get_instance_id(): true}, "active": 0, "root_batch": root_batch, "idle_expire_msec": 0}
		root_wave_merge_chain_id = chain_id
		root_wave_merge_deadline_msec = now_msec + 450
		if root_batch > 0:
			prehistoric_root_batch_chains[root_batch] = chain_id
	if not wave_chains.has(chain_id):
		return
	var state: Dictionary = wave_chains[chain_id]
	state["bdr_touch"] = now_msec
	var visited: Dictionary = state.visited
	visited[source.get_instance_id()] = true
	var radius: = _prehistoric_wave_radius()
	_show_wave(source.position, radius)
	var candidates: Array[Dictionary] = []
	if visited.size() < dice.size():
		_tmp_query.clear()
		_grid.query_radius(source.position, radius, _tmp_query)
		for other in _tmp_query:
			if not is_instance_valid(other) or other == source or other.special_motion:
				continue
			var other_id: = other.get_instance_id()
			if visited.has(other_id):
				continue
			visited[other_id] = true
			if other.rolling:
				continue
			var distance: = other.position.distance_to(source.position)
			state.active = int(state.active) + 1
			candidates.append({"die": other, "distance": distance})
	state.visited = visited
	if int(state.active) > 0:
		state.idle_expire_msec = 0
	wave_chains[chain_id] = state
	candidates.sort_custom( func(a: Dictionary, b: Dictionary) -> bool: return float(a.distance) < float(b.distance))
	for candidate in candidates:
		var delay: = clampf(float(candidate.distance) / radius, 0.0, 1.0) * PREHISTORIC_WAVE_DURATION
		_launch_wave_target_after_delay(candidate.die as DiceActor, chain_id, delay)
	_fs_prehistoric_launch_best = maxi(_fs_prehistoric_launch_best, candidates.size())
	if int(state.active) == 0:
		_expire_idle_wave_chain_after_grace(chain_id)


func _any_die_rolling() -> bool:
	return active_roll_count > 0


