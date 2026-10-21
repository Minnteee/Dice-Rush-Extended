# Dice Rush Extended - main.gd patch: saving / loading of the mod data.
# Mod data lives in the regular save file under the key "bdr"; the original game ignores it,
# so a save stays loadable even without the mod.

func _reset_progress_state() -> void :
	_clear_actors()
	trailer_first_die = null
	trailer_first_die_reward_verified = false
	_despawn_golden_bone_offer(false)
	_clear_golden_bone_storm()
	_clear_golden_bone_banner()
	golden_bone_next_spawn = rng.randf_range(GOLDEN_BONE_MIN_INTERVAL, GOLDEN_BONE_MAX_INTERVAL)
	golden_bone_luck_time_left = 0.0
	golden_bone_storm_time_left = 0.0
	golden_bone_storm_wave_time_left = 0.0
	golden_bone_last_effect = -1
	golden_bone_storm_bank_snapshot = 0.0
	golden_bone_storm_collected_this_event = 0
	_update_golden_bone_effect_icon()
	money = 0.0
	developer_modified = false
	AchievementService.set_developer_progress_blocked(false)
	play_time_seconds = 0.0
	quadrillion_story_seen = false
	quadrillion_story_active = false
	total_money_earned = 0.0
	golden_coins = 0
	next_golden_coin = 100.0
	dice_50_count = 1
	dice_d4_count = 0
	npc_count = 0
	next_npc_id = 0
	lucky_transaction_id = 0
	lucky_cubes_purchased = 0
	lucky_transaction_active = false
	pending_lucky_reward.clear()
	dog_shrine_transaction_id = 0
	dog_shrine_transaction_active = false
	dog_shrine_entry_draining = false
	dog_shrine_entry_serial += 1
	pending_dog_shrine_offer.clear()
	dog_shrine_offerings_made = 0
	dog_shrine_donated_counts.clear()
	for kind in DOG_SHRINE_DICE_KINDS:
		dog_shrine_donated_counts[kind] = 0
	dog_shrine_blessing_ranks = DogShrineCards.empty_ranks()
	for kind in DOG_SHRINE_DICE_KINDS:
		dog_shrine_die_bonus_percent[kind] = 0
	for alias_id in dog_shrine_legacy_alias_ranks:
		dog_shrine_legacy_alias_ranks[alias_id] = 0
	dog_shrine_legacy_talents_migrated = true
	accountant_count = 0
	accountant_unlocked = false
	cat_unlocked = false
	cat_purchased = false
	cat_count = 0
	cat_pending_births = 0
	demo_dice_reserve.clear()
	die_levels = {
		"50_50": 1, "d4": 1, "3x4": 1, "d2": 1, "777": 1, "prehistoric": 1,
		"golden": 1, "npc_die": 1, "crypto": 1, "diamond": 1, "pi": 1, "accountant": 1,
	}
	special_dice_counts = {"crypto": 0, "diamond": 0, "pi": 0}
	special_dice_unlocked = {
		"crypto": DiceRushEdition.is_demo(),
		"diamond": DiceRushEdition.is_demo(),
		"pi": DiceRushEdition.is_demo(),
	}
	cat_unlocked = DiceRushEdition.is_demo()
	crypto_market_value = CRYPTO_MIN_VALUE
	crypto_market_elapsed = 0.0
	extra_counts = {"3x4": 0, "d2": 0, "777": 0, "prehistoric": 0, "golden": 0, "npc_die": 0}
	for key in upgrades.keys():
		upgrades[key] = false
	talents.clear()
	talent_prerequisites.clear()
	_initialize_talents()
	next_wave_chain_id = 0
	root_wave_merge_chain_id = 0
	root_wave_merge_deadline_msec = 0
	prehistoric_root_batch_frame = -1
	prehistoric_root_batch_serial = 0
	prehistoric_root_batch_chains.clear()
	prehistoric_root_batch_remaining.clear()
	wave_chains.clear()
	last_stolen_worker_id = 0
	same_worker_steal_streak = 0
	npc_target_scan_cursor = 0
	hover_roll_cooldown = 0.0
	hover_roll_latched_ids.clear()
	hover_roll_contact_ids.clear()
	hover_roll_cursor_valid = false
	hover_completion_queue.clear()
	hover_completion_queue_head = 0
	hover_completion_pending_ids.clear()
	queued_player_rerolls.clear()
	dice_placement_sequence = 0
	_price_memo.clear()
	bdr.reset_progress()
	_invalidate_eco()


func _dice_save_entry(die: DiceActor, saved_position: Vector2) -> Dictionary:
	var entry: = {
		"kind": die.die_kind,
		"x": saved_position.x,
		"y": saved_position.y,
		"streak_777": die.streak_777,
		"streak_50_skulls": die.streak_50_skulls,
		"streak_777_combos": die.streak_777_combos,
	}
	if die.die_kind == "cat":
		entry["cat_eaten"] = die.eaten_count
		entry["cat_pending"] = die.pending_feeds_count()
	var state: = bdr.die_save_state(die)
	if not state.is_empty():
		entry["m"] = state
	return entry


func _save_game(allow_transient_rolls: = false, compact_actor_snapshot: = false) -> bool:
	if not game_started:
		return false
	if bdr.is_coop_client():
		return false
	if not allow_transient_rolls and (_synchronize_active_roll_count() > 0 or _has_pending_wave_work()):
		return false
	var dice_state: Array = []
	for die in dice:
		if not is_instance_valid(die):
			continue
		var has_streak_state: = die.streak_777 > 0 or die.streak_50_skulls > 0 or die.streak_777_combos > 0 or not die.mstate.is_empty()
		if compact_actor_snapshot and not has_streak_state and die.die_kind != "cat":
			continue
		var saved_position: = die.persistent_position() if allow_transient_rolls or die.die_kind == "cat" else die.position
		if allow_transient_rolls:
			saved_position.x = clampf(saved_position.x, BOARD_RECT.position.x, BOARD_RECT.end.x)
			saved_position.y = clampf(saved_position.y, BOARD_RECT.position.y, BOARD_RECT.end.y)
		dice_state.append(_dice_save_entry(die, saved_position))
	var npc_state: Array = []
	if not compact_actor_snapshot:
		for npc in npcs:
			if not is_instance_valid(npc):
				continue
			npc_state.append({"x": npc.position.x, "y": npc.position.y})
	var data: = _bdr_save_dict(dice_state, npc_state)
	return _write_validated_json(save_path, data)


## The complete save dictionary (also used for the coop snapshot).
func _bdr_save_dict(dice_state: Array, npc_state: Array) -> Dictionary:
	var data: = {
		"version": SAVE_VERSION,
		"save_version": SAVE_VERSION,
		"board_layout_version": BOARD_LAYOUT_VERSION,
		"game_version": GameSession.GAME_VERSION,
		"edition": DiceRushEdition.current(),
		"author": "Arlekino",
		"developer_modified": developer_modified,
		"updated_unix": int(Time.get_unix_time_from_system()),
		"money": _bdr_money_to_save(money),
		"play_time_seconds": play_time_seconds,
		"quadrillion_story_seen": quadrillion_story_seen,
		"total_money_earned": _bdr_money_to_save(total_money_earned),
		"golden_coins": str(golden_coins),
		"next_golden_coin": _bdr_money_to_save(next_golden_coin),
		"dice_50_count": dice_50_count,
		"dice_d4_count": dice_d4_count,
		"npc_count": npc_count,
		"extra_counts": extra_counts.duplicate(true),
		"upgrades": upgrades.duplicate(true),
		"talents": talents.duplicate(true),
		"golden_bone_event": {
			"next_spawn": golden_bone_next_spawn,
			"offer_left": golden_bone_offer_time_left,
			"luck_left": golden_bone_luck_time_left,
			"storm_left": golden_bone_storm_time_left,
			"storm_bank": _bdr_money_to_save(golden_bone_storm_bank_snapshot),
			"last_effect": golden_bone_last_effect,
			"storm_collected": golden_bone_storm_collected_this_event,
		},
		"lucky": _lucky_save_data(),
		"cat": _cat_save_data(),
		"dog_shrine": _dog_shrine_save_data(),
		"dice": dice_state,
		"npcs": npc_state,
		"bdr": bdr.save_data(),
	}
	if not demo_dice_reserve.is_empty():
		data["demo_dice_reserve"] = demo_dice_reserve.duplicate(true)
	return data


func _save_lucky_state_immediately() -> bool:
	if bdr.is_coop_client():
		return true
	var saved: = GameSession.read_valid_game_save(save_path)
	if bool(saved.get("ok", false)):
		var data: Dictionary = (saved.get("data", {}) as Dictionary).duplicate(true)
		data["edition"] = DiceRushEdition.current()
		data["updated_unix"] = int(Time.get_unix_time_from_system())
		data["lucky"] = _lucky_save_data()
		data["cat"] = _cat_save_data()
		var saved_actors: Array = data.get("dice", [])
		saved_actors = saved_actors.filter( func(entry: Variant) -> bool: return entry is Dictionary and str(entry.get("kind", "")) != "cat")
		for die in dice:
			if is_instance_valid(die) and die.die_kind == "cat":
				saved_actors.append(_dice_save_entry(die, die.persistent_position()))
		data["dice"] = saved_actors
		data["money"] = _bdr_money_to_save(money)
		data["play_time_seconds"] = play_time_seconds
		data["total_money_earned"] = _bdr_money_to_save(maxf(_bdr_parse_money(data.get("total_money_earned", "0")), total_money_earned))
		data["golden_coins"] = str(golden_coins)
		data["next_golden_coin"] = _bdr_money_to_save(next_golden_coin)
		data["upgrades"] = upgrades.duplicate(true)
		data["talents"] = talents.duplicate(true)
		data["dice_50_count"] = dice_50_count
		data["dice_d4_count"] = dice_d4_count
		data["npc_count"] = npc_count
		data["extra_counts"] = extra_counts.duplicate(true)
		data["dog_shrine"] = _dog_shrine_save_data()
		data["bdr"] = bdr.save_data()
		if not demo_dice_reserve.is_empty():
			data["demo_dice_reserve"] = demo_dice_reserve.duplicate(true)
		else:
			data.erase("demo_dice_reserve")
		return _write_validated_json(save_path, data)
	return _save_game()


func _load_saved_game() -> bool:
	var result: = GameSession.read_valid_game_save(save_path)
	if not bool(result.ok):
		return false
	var data: Dictionary = result.data
	if not _prepare_demo_count_migration_backup(data):
		return false
	return _bdr_load_data(data)


## Loads a save dictionary (from the save file or from the coop host).
func _bdr_load_data(data: Dictionary) -> bool:
	var saved_cat: Dictionary = data.get("cat", {})
	var migrate_board_layout: = int(data.get("board_layout_version", 0)) < BOARD_LAYOUT_VERSION
	get_tree().paused = false
	_reset_progress_state()
	demo_dice_reserve = (data.get("demo_dice_reserve", {}) as Dictionary).duplicate(true)
	if DiceRushEdition.has_cat_die():
		cat_unlocked = bool(saved_cat.get("unlocked", false))
		cat_purchased = bool(saved_cat.get("purchased", false))
		cat_count = int(saved_cat.get("count", 0))
		cat_pending_births = int(saved_cat.get("pending_births", 0))
	developer_modified = bool(data.get("developer_modified", false))
	AchievementService.set_developer_progress_blocked(developer_modified)
	money = _bdr_parse_money(data.get("money", "0"))
	play_time_seconds = maxf(0.0, float(data.get("play_time_seconds", 0.0)))
	quadrillion_story_seen = bool(data.get("quadrillion_story_seen", false))
	total_money_earned = _bdr_parse_money(data.get("total_money_earned", "0"))
	golden_coins = maxi(0, int(str(data.get("golden_coins", "0"))))
	next_golden_coin = maxf(100.0, _bdr_parse_money(data.get("next_golden_coin", "100")))
	bdr.load_data(data.get("bdr", {}))
	_load_dog_shrine_save_data(data.get("dog_shrine", {}))
	var saved_golden_bone = data.get("golden_bone_event", {})
	if saved_golden_bone is Dictionary and not saved_golden_bone.is_empty():
		golden_bone_next_spawn = clampf(float(saved_golden_bone.get("next_spawn", GOLDEN_BONE_MIN_INTERVAL)), 0.0, GOLDEN_BONE_MAX_INTERVAL * _golden_bone_interval_scale())
		golden_bone_offer_time_left = clampf(float(saved_golden_bone.get("offer_left", 0.0)), 0.0, GOLDEN_BONE_OFFER_DURATION)
		golden_bone_luck_time_left = clampf(float(saved_golden_bone.get("luck_left", 0.0)), 0.0, _golden_bone_luck_duration())
		golden_bone_storm_time_left = clampf(float(saved_golden_bone.get("storm_left", 0.0)), 0.0, _golden_bone_storm_duration())
		golden_bone_storm_bank_snapshot = _bdr_parse_money(saved_golden_bone.get("storm_bank", "0")) if golden_bone_storm_time_left > 0.0 else 0.0
		golden_bone_last_effect = clampi(int(saved_golden_bone.get("last_effect", -1)), -1, 1)
		golden_bone_storm_collected_this_event = maxi(0, int(saved_golden_bone.get("storm_collected", 0)))
	dice_50_count = maxi(1, int(data.get("dice_50_count", 1)))
	dice_d4_count = maxi(0, int(data.get("dice_d4_count", 0)))
	npc_count = maxi(0, int(data.get("npc_count", 0)))
	var saved_lucky = data.get("lucky", {})
	if saved_lucky is Dictionary and not saved_lucky.is_empty():
		lucky_transaction_id = maxi(0, int(str(saved_lucky.get("transaction_id", "0"))))
		lucky_cubes_purchased = maxi(0, int(str(saved_lucky.get("cubes_purchased", "0"))))
		var saved_levels = saved_lucky.get("die_levels", {})
		if saved_levels is Dictionary:
			for kind in LUCKY_DIE_KINDS:
				die_levels[kind] = maxi(1, int(saved_levels.get(kind, 1)))
			for kind in saved_levels:
				if bdr.is_custom(str(kind)):
					die_levels[str(kind)] = maxi(1, int(saved_levels.get(kind, 1)))
		accountant_count = maxi(0, int(saved_lucky.get("accountant_count", 0)))
		accountant_unlocked = bool(saved_lucky.get("accountant_unlocked", accountant_count > 0))
		var saved_special_counts = saved_lucky.get("special_counts", {})
		var saved_special_unlocked = saved_lucky.get("special_unlocked", {})
		var has_separate_unlock_state: bool = saved_special_unlocked is Dictionary and not saved_special_unlocked.is_empty()
		if saved_special_counts is Dictionary:
			for kind in SPECIAL_DICE_KINDS:
				var saved_count: = maxi(0, int(saved_special_counts.get(kind, 0)))
				if has_separate_unlock_state:
					special_dice_counts[kind] = saved_count
					special_dice_unlocked[kind] = bool(saved_special_unlocked.get(kind, saved_count > 0))
				else:
					special_dice_unlocked[kind] = saved_count > 0
					special_dice_counts[kind] = maxi(0, saved_count - 1)
		crypto_market_value = clampi(int(str(saved_lucky.get("crypto_value", str(CRYPTO_MIN_VALUE)))), CRYPTO_MIN_VALUE, CRYPTO_MAX_VALUE)
		crypto_market_elapsed = clampf(float(saved_lucky.get("crypto_elapsed", 0.0)), 0.0, CRYPTO_REFRESH_SECONDS)
		var saved_pending = saved_lucky.get("pending_reward", {})
		if saved_pending is Dictionary and not _pending_lucky_rewards_from(saved_pending).is_empty():
			pending_lucky_reward = saved_pending.duplicate(true)
	else:
		lucky_cubes_purchased = 0
	var saved_extra = data.get("extra_counts", {})
	if saved_extra is Dictionary:
		for key in extra_counts:
			extra_counts[key] = maxi(0, int(saved_extra.get(key, 0)))
	var saved_upgrades = data.get("upgrades", {})
	if saved_upgrades is Dictionary:
		for key in upgrades:
			upgrades[key] = bool(saved_upgrades.get(key, false))
		if not saved_upgrades.has("golden") and int(extra_counts.get("golden", 0)) > 0:
			upgrades["golden"] = true
	_migrate_legacy_talent_cards()
	var saved_talents = data.get("talents", {})
	if saved_talents is Dictionary:
		for key in talents:
			talents[key] = bool(saved_talents.get(key, false))
	_repair_talent_ancestry()
	_migrate_demo_dice_reserve(data)
	_apply_edition_progress_limits()
	if not DiceRushEdition.is_demo():
		extra_counts["golden"] = mini(int(extra_counts.get("golden", 0)), _dice_limit("golden"))
	crypto_market_value = clampi(crypto_market_value, _crypto_minimum_value(), CRYPTO_MAX_VALUE)
	for kind in SPECIAL_DICE_KINDS:
		special_dice_counts[kind] = maxi(0, int(special_dice_counts.get(kind, 0)))
	dice_50_count = maxi(1, dice_50_count)
	dice_d4_count = maxi(0, dice_d4_count)
	npc_count = clampi(npc_count, 0, _worker_limit())
	for count_kind in extra_counts:
		extra_counts[count_kind] = maxi(0, int(extra_counts[count_kind]))
	var saved_dice_by_kind: Dictionary = {}
	var saved_dice = data.get("dice", [])
	if saved_dice is Array:
		for entry in saved_dice:
			if entry is not Dictionary:
				continue
			var kind: = str(entry.get("kind", ""))
			if kind.is_empty():
				continue
			var entries: Array = saved_dice_by_kind.get(kind, [])
			entries.append(entry)
			saved_dice_by_kind[kind] = entries
	var counts_to_spawn: = {
		"cat": cat_count,
		"50_50": dice_50_count,
		"d4": dice_d4_count,
		"3x4": int(extra_counts.get("3x4", 0)),
		"d2": int(extra_counts.get("d2", 0)),
		"777": int(extra_counts.get("777", 0)),
		"prehistoric": int(extra_counts.get("prehistoric", 0)),
		"golden": int(extra_counts.get("golden", 0)),
		"npc_die": int(extra_counts.get("npc_die", 0)),
		"crypto": int(special_dice_counts.get("crypto", 0)),
		"diamond": int(special_dice_counts.get("diamond", 0)),
		"pi": int(special_dice_counts.get("pi", 0)),
	}
	for custom_kind in bdr.custom_dice_counts():
		counts_to_spawn[custom_kind] = bdr.count(custom_kind)
	var spawn_budget: = MAX_PURCHASABLE_DICE_ACTORS
	for kind in counts_to_spawn:
		var entries: Array = saved_dice_by_kind.get(kind, [])
		for index in range(int(counts_to_spawn[kind])):
			if spawn_budget <= 0:
				break
			spawn_budget -= 1
			var spawn_position: = _random_spawn_position()
			var saved_streak: = 0
			var saved_skull_streak: = 0
			var saved_combo_streak: = 0
			var entry: Dictionary = {}
			if index < entries.size():
				entry = entries[index]
				spawn_position = _saved_board_position(entry, migrate_board_layout)
				saved_streak = maxi(0, int(entry.get("streak_777", 0)))
				saved_skull_streak = maxi(0, int(entry.get("streak_50_skulls", 0)))
				saved_combo_streak = maxi(0, int(entry.get("streak_777_combos", 0)))
			var die: = _spawn_die(kind, spawn_position)
			die.streak_777 = saved_streak
			die.streak_50_skulls = saved_skull_streak
			die.streak_777_combos = saved_combo_streak
			if entry.has("m"):
				bdr.die_load_state(die, entry.get("m"))
			if entry.has("nid"):
				bdr.coop.register_die(die, int(entry.get("nid")))
			if kind == "cat" and index < entries.size():
				die.restore_feeding_state(int(entries[index].get("cat_eaten", 0)), int(entries[index].get("cat_pending", 0)))
	var saved_npcs = data.get("npcs", [])
	for index in range(npc_count):
		var npc: = _spawn_npc()
		if saved_npcs is Array and index < saved_npcs.size() and saved_npcs[index] is Dictionary:
			npc.position = _saved_board_position(saved_npcs[index], migrate_board_layout)
	game_started = true
	menu_controller.show_game()
	autosave_timer.start()
	bdr.on_loaded()
	_update_all_labels()
	_report_achievement_snapshot()
	if DiceRushEdition.is_demo() or migrate_board_layout:
		_save_game()
	if golden_bone_offer_time_left > 0.0:
		_spawn_golden_bone_offer(golden_bone_offer_time_left)
	elif golden_bone_storm_time_left > 0.0:
		_spawn_golden_bone_storm_wave()
	_update_golden_bone_effect_icon()
	if money >= QUADRILLION_STORY_THRESHOLD and not quadrillion_story_seen:
		_show_quadrillion_story.call_deferred()
	return true
