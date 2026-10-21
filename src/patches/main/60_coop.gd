# Dice Rush Extended - main.gd patch: coop (see res://bdr/net/coop.gd).

var _bdr_buy_callbacks: Dictionary = {}
var _coop_hover_contacts: Dictionary = {}
var _coop_bone_button: TextureButton
var _coop_storm_buttons: Array = []


# ---------------------------------------------------------------- host: snapshot and state
## Complete table for a joining partner (like a save, plus the network id of every dice).
func _coop_snapshot() -> Dictionary:
	var dice_state: Array = []
	for die in dice:
		if not is_instance_valid(die):
			continue
		var entry: = _dice_save_entry(die, die.persistent_position())
		entry["nid"] = bdr.coop.nid_of(die)
		dice_state.append(entry)
	var npc_state: Array = []
	for npc in npcs:
		if is_instance_valid(npc):
			npc_state.append({"x": npc.position.x, "y": npc.position.y})
	return _bdr_save_dict(dice_state, npc_state)


## Everything except the actors and fast changing values (those come with the status).
func _coop_state() -> Dictionary:
	var data: = _bdr_save_dict([], [])
	for key in ["dice", "npcs", "money", "total_money_earned", "updated_unix", "play_time_seconds"]:
		data.erase(key)
	var lucky: Dictionary = data.get("lucky", {})
	lucky.erase("pending_reward")
	lucky.erase("crypto_elapsed")
	var bone: Dictionary = data.get("golden_bone_event", {})
	for key in ["next_spawn", "offer_left", "luck_left", "storm_left"]:
		bone.erase(key)
	var mod: Dictionary = data.get("bdr", {})
	mod.erase("stats")
	mod.erase("mech")
	return data


# ---------------------------------------------------------------- client: building and updating the view
func _coop_client_load(data: Dictionary) -> void:
	_bdr_load_data(data)
	if is_instance_valid(autosave_timer):
		autosave_timer.stop()
	AchievementService.set_progress_suppressed(true)
	for npc in npcs:
		if is_instance_valid(npc):
			npc._trailer_mode = true
	if golden_bone_offer_button and is_instance_valid(golden_bone_offer_button):
		_despawn_golden_bone_offer(false)
	_clear_golden_bone_storm()
	bdr.coop_ui.hide_connecting()
	bdr.toast(bdr.I18N.t("coop.joined"))


func _coop_apply_state(data: Dictionary) -> void:
	quadrillion_story_seen = bool(data.get("quadrillion_story_seen", quadrillion_story_seen))
	golden_coins = maxi(0, int(str(data.get("golden_coins", golden_coins))))
	next_golden_coin = maxf(100.0, _bdr_parse_money(data.get("next_golden_coin", "100")))
	bdr.coop_apply_data(data.get("bdr", {}))
	_load_dog_shrine_save_data(data.get("dog_shrine", {}))
	dice_50_count = maxi(1, int(data.get("dice_50_count", dice_50_count)))
	dice_d4_count = maxi(0, int(data.get("dice_d4_count", dice_d4_count)))
	npc_count = maxi(0, int(data.get("npc_count", npc_count)))
	var saved_extra = data.get("extra_counts", {})
	if saved_extra is Dictionary:
		for key in saved_extra:
			extra_counts[key] = maxi(0, int(saved_extra[key]))
	var saved_upgrades = data.get("upgrades", {})
	if saved_upgrades is Dictionary:
		for key in saved_upgrades:
			upgrades[key] = bool(saved_upgrades[key])
	var saved_talents = data.get("talents", {})
	if saved_talents is Dictionary:
		for key in saved_talents:
			talents[key] = bool(saved_talents[key])
	var saved_lucky = data.get("lucky", {})
	if saved_lucky is Dictionary:
		lucky_cubes_purchased = maxi(0, int(str(saved_lucky.get("cubes_purchased", lucky_cubes_purchased))))
		var saved_levels = saved_lucky.get("die_levels", {})
		if saved_levels is Dictionary:
			for kind in saved_levels:
				die_levels[str(kind)] = maxi(1, int(saved_levels[kind]))
		accountant_count = maxi(0, int(saved_lucky.get("accountant_count", accountant_count)))
		accountant_unlocked = bool(saved_lucky.get("accountant_unlocked", accountant_unlocked))
		var saved_special_counts = saved_lucky.get("special_counts", {})
		if saved_special_counts is Dictionary:
			for kind in saved_special_counts:
				special_dice_counts[str(kind)] = maxi(0, int(saved_special_counts[kind]))
		var saved_special_unlocked = saved_lucky.get("special_unlocked", {})
		if saved_special_unlocked is Dictionary:
			for kind in saved_special_unlocked:
				special_dice_unlocked[str(kind)] = bool(saved_special_unlocked[kind])
		crypto_market_value = clampi(int(str(saved_lucky.get("crypto_value", str(crypto_market_value)))), CRYPTO_MIN_VALUE, CRYPTO_MAX_VALUE)
	var saved_cat = data.get("cat", {})
	if saved_cat is Dictionary and not saved_cat.is_empty():
		cat_unlocked = bool(saved_cat.get("unlocked", cat_unlocked))
		cat_purchased = bool(saved_cat.get("purchased", cat_purchased))
		cat_count = int(saved_cat.get("count", cat_count))
	_invalidate_eco()
	_price_memo.clear()
	bdr.tarot.invalidate()
	_update_all_labels()
	if upgrade_overlay and upgrade_overlay.visible:
		for key in talent_visuals:
			_update_talent_node(str(key))
	_refresh_lucky_ui()


func _coop_apply_status(data: Dictionary) -> void:
	var new_money: = float(data.get("m", money))
	var money_changed: = not is_equal_approx(new_money, money)
	money = new_money
	total_money_earned = float(data.get("t", total_money_earned))
	golden_coins = int(data.get("g", golden_coins))
	golden_bone_luck_time_left = float(data.get("gl", 0.0))
	golden_bone_storm_time_left = float(data.get("gs", 0.0))
	_update_golden_bone_effect_icon()
	var boost: = float(data.get("lb", 0.0))
	if boost > 0.0:
		bdr.extra["lucky_boost"] = boost
	else:
		bdr.extra.erase("lucky_boost")
	bdr.staff.coop_set_dj(float(data.get("dj", 0.0)))
	var bone = data.get("bone")
	if bone is Array and bone.size() >= 3:
		_coop_show_bone(Vector2(float(bone[1]), float(bone[2])))
	elif _coop_bone_button and is_instance_valid(_coop_bone_button):
		_coop_bone_button.queue_free()
		_coop_bone_button = null
	if golden_bone_storm_time_left <= 0.0 and not _coop_storm_buttons.is_empty():
		_coop_clear_storm()
	if money_changed:
		if money_value_label:
			money_value_label.text = _format_number(money)
			UITextFitterScript.fit(money_value_label)
		_request_all_labels_update()


func _coop_client_spawn(nid: int, kind: String, at: Vector2) -> void:
	if bdr.coop.die_by_nid(nid) != null:
		return
	var die: = _spawn_die(kind, at)
	bdr.coop.register_die(die, nid)


func _coop_client_remove(die: DiceActor) -> void:
	bdr.remove_die_actor(die)


func _coop_client_roll(die: DiceActor, target: Vector2, animated: bool, interactive: bool, face: int, duration: float) -> void:
	if not is_instance_valid(die) or die.die_kind == "cat" or die.special_motion:
		return
	if die.rolling:
		_coop_client_abort_roll(die)
	die.forced_face = face
	die.forced_duration = duration
	_start_die_roll(die, 0, target, false, true, interactive, not animated)


func _coop_client_abort_roll(die: DiceActor) -> void:
	var die_id: = die.get_instance_id()
	if active_roll_ids.has(die_id):
		active_roll_ids.erase(die_id)
		active_roll_count = maxi(0, active_roll_count - 1)
	if active_animated_roll_ids.has(die_id):
		active_animated_roll_ids.erase(die_id)
		active_animated_roll_count = maxi(0, active_animated_roll_count - 1)
	active_interactive_animated_roll_ids.erase(die_id)
	if die.spin3d:
		die.spin3d = false
		_spin3d_active = maxi(0, _spin3d_active - 1)
	die.abort_roll()
	_bdr_rest_die(die)


## Client: a dice of the view finished its roll (the payout was made by the host).
func _coop_client_landed(die: DiceActor) -> void:
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
	if die.has_meta("dog_strength_eligible"):
		die.remove_meta("dog_strength_eligible")
	die.pending_mult = 1.0
	_fs_landing_sound = true
	if is_instance_valid(die) and not die.rolling:
		_bdr_rest_die(die)


# ---------------------------------------------------------------- client: golden bone proxies
func _coop_show_bone(at: Vector2) -> void:
	if _coop_bone_button and is_instance_valid(_coop_bone_button):
		_coop_bone_button.position = at
		return
	var size: = Vector2(150, 150)
	_coop_bone_button = TextureButton.new()
	_coop_bone_button.texture_normal = load(GOLDEN_BONE_TEXTURE) as Texture2D
	_coop_bone_button.ignore_texture_size = true
	_coop_bone_button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	_coop_bone_button.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_coop_bone_button.material = _golden_bone_material()
	_coop_bone_button.position = at
	_coop_bone_button.size = size
	_coop_bone_button.pivot_offset = size * 0.5
	_coop_bone_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_coop_bone_button.z_index = 45
	_coop_bone_button.pressed.connect(func() -> void: bdr.coop_request("bone", []))
	add_child(_coop_bone_button)
	var pulse: = _coop_bone_button.create_tween().set_loops()
	pulse.tween_property(_coop_bone_button, "scale", Vector2(1.1, 1.1), 0.42).set_trans(Tween.TRANS_SINE)
	pulse.tween_property(_coop_bone_button, "scale", Vector2(0.94, 0.94), 0.42).set_trans(Tween.TRANS_SINE)


## Host: tells the partner where the cubes of a golden storm wave are.
func _coop_storm_wave() -> void:
	if not bdr.coop.is_host() or not bdr.coop.is_active():
		return
	var points: = PackedVector2Array()
	for index in range(golden_bone_storm_buttons.size()):
		var button: = golden_bone_storm_buttons[index]
		if not is_instance_valid(button):
			continue
		button.set_meta("storm_index", index)
		points.append(button.position)
	bdr.coop.on_event_message(["storm", points])


func _coop_storm_hit(button: TextureButton) -> void:
	if bdr.coop.is_host() and is_instance_valid(button) and button.has_meta("storm_index"):
		bdr.coop.on_event_message(["storm_hit", int(button.get_meta("storm_index"))])


func _coop_storm_click(index: int) -> void:
	for button in golden_bone_storm_buttons:
		if is_instance_valid(button) and int(button.get_meta("storm_index", -1)) == index:
			_collect_golden_bone_storm_cube(button, int(button.get_meta("storm_percent", 1)))
			return


## Client: shows the cubes of a storm wave (clicks are sent to the host).
func _coop_client_storm(points: PackedVector2Array) -> void:
	_coop_clear_storm()
	var bone_size: = Vector2(52, 52)
	for index in range(points.size()):
		var button: = TextureButton.new()
		button.texture_normal = load(GOLDEN_BONE_TEXTURE) as Texture2D
		button.ignore_texture_size = true
		button.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
		button.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		button.material = _golden_bone_material()
		button.size = bone_size
		button.position = points[index]
		button.pivot_offset = bone_size * 0.5
		button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		button.z_index = 46
		button.set_meta("storm_index", index)
		button.pressed.connect(_coop_client_storm_pressed.bind(button, index))
		add_child(button)
		_coop_storm_buttons.append(button)


func _coop_client_storm_pressed(button: TextureButton, index: int) -> void:
	if is_instance_valid(button):
		button.disabled = true
		button.modulate.a = 0.4
	bdr.coop_request("storm", [index])


func _coop_client_storm_hit(index: int) -> void:
	for button in _coop_storm_buttons:
		if is_instance_valid(button) and int(button.get_meta("storm_index", -1)) == index:
			button.queue_free()


func _coop_clear_storm() -> void:
	for button in _coop_storm_buttons:
		if is_instance_valid(button):
			button.queue_free()
	_coop_storm_buttons.clear()


# ---------------------------------------------------------------- host: requests of the partner
func _coop_handle_request(action: String, args: Array) -> void:
	match action:
		"click":
			var die: = bdr.coop.die_by_nid(int(args[0]))
			if die != null:
				_coop_click(die)
		"buy":
			_coop_buy(str(args[0]), int(args[1]) if args.size() > 1 else 1)
		"sell":
			bdr.shop.sell(str(args[0]), int(args[1]))
		"unlock":
			bdr.shop.unlock(str(args[0]))
		"design_buy":
			bdr.design_buy(str(args[0]), int(args[1]))
		"design_equip":
			bdr.design_equip(str(args[0]), int(args[1]))
		"talent":
			_buy_upgrade(str(args[0]))
		"lucky_buy":
			bdr.coop.reply("lucky", _coop_lucky_purchase(int(args[0])))
		"tarot_donate":
			bdr.coop.reply("tarot_offer", _bdr_tarot_donate(str(args[0]), int(args[1])))
		"tarot_bless":
			bdr.coop.reply("tarot_bless", _bdr_tarot_bless(str(args[0])))
		"bone":
			_claim_golden_bone_offer()
		"storm":
			_coop_storm_click(int(args[0]))
		"event_click":
			bdr.events.coop_click(int(args[0]), int(args[1]))
	_request_all_labels_update()


func _coop_click(die: DiceActor) -> void:
	if not is_instance_valid(die) or not game_started or autosave_pending or not pending_safe_action.is_empty():
		return
	if die.die_kind == "cat":
		if _cat_can_accept_feed(die):
			die.queue_feed()
		return
	if die.rolling:
		_queue_player_reroll(die)
		return
	_launch_player_die(die)


func _coop_buy(kind: String, amount: int) -> void:
	var callback: Callable = _bdr_buy_callbacks.get(kind, Callable())
	if not callback.is_valid():
		return
	_suppress_label_updates = true
	for _index in range(clampi(amount, 1, 50)):
		if _buy_shop_product(kind, callback, false) <= 0:
			break
	_suppress_label_updates = false
	_update_all_labels()


func _coop_lucky_purchase(purchase_count: int) -> Dictionary:
	var result: = _bdr_lucky_transaction(purchase_count)
	if bool(result.get("ok", false)):
		pending_lucky_reward.clear()
		_save_lucky_state_immediately()
		_refresh_lucky_ui(true)
	return result


## Host: the partner moves the mouse over the table (hover rolling talent).
func _coop_remote_hover(cursor_start: Vector2, cursor_end: Vector2) -> void:
	if not bool(upgrades.get("hover_roll", false)) or not game_started or autosave_pending or not pending_safe_action.is_empty():
		return
	var nearby: = _hover_dice_along(cursor_start, cursor_end, _hover_roll_radius())
	var radius_squared: = _hover_roll_radius() * _hover_roll_radius()
	var contacts: Dictionary = {}
	var entered: Array[DiceActor] = []
	for die in nearby:
		if not is_instance_valid(die):
			continue
		var die_id: = die.get_instance_id()
		if die.position.distance_squared_to(cursor_end) <= radius_squared:
			contacts[die_id] = true
		if not _coop_hover_contacts.has(die_id) or die.position.distance_squared_to(cursor_start) > radius_squared:
			entered.append(die)
	_coop_hover_contacts = contacts
	if not entered.is_empty():
		_launch_hover_dice_along(entered, cursor_start, cursor_end, false)


# ---------------------------------------------------------------- client: answers of the host
func _coop_client_reply(kind: String, data: Variant) -> void:
	if data is not Dictionary:
		return
	var result: Dictionary = data
	match kind:
		"lucky":
			lucky_transaction_active = false
			if not bool(result.get("ok", false)):
				lucky_status_label.text = str(result.get("error", _lucky_text("lucky_not_enough")))
				lucky_status_label.add_theme_color_override("font_color", PRICE_UNAFFORDABLE_COLOR)
				UITextFitterScript.fit(lucky_status_label)
				GameSession.play_sfx("denied")
				_refresh_lucky_ui(true)
				return
			pending_lucky_reward = {"transaction_id": "coop", "count": int(result.get("count", 1)), "rewards": result.get("rewards", [])}
			GameSession.play_sfx("purchase")
			_refresh_lucky_ui(true)
			_reveal_lucky_reward()
		"tarot_offer":
			if not is_instance_valid(dog_shrine_controller):
				return
			if not bool(result.get("ok", false)):
				dog_shrine_controller.show_error(str(result.get("error", "")))
				return
			var kind_id: = str(result.get("kind", ""))
			var cards: Array[Dictionary] = []
			for card in result.get("cards", []):
				if card is Dictionary:
					cards.append(card)
			dog_shrine_controller.set_inventory(_dog_shrine_inventory_items(), _dog_shrine_offerings_left(), false)
			dog_shrine_controller.play_donation_success(kind_id, _lucky_kind_icon_path(kind_id), cards, _dog_shrine_offerings_left())
		"tarot_bless":
			if not is_instance_valid(dog_shrine_controller):
				return
			if not bool(result.get("ok", false)):
				dog_shrine_controller.show_error(str(result.get("error", "")))
				return
			pending_dog_shrine_offer.clear()
			dog_shrine_controller.set_grimoire_cards(_dog_shrine_grimoire_data())
			dog_shrine_controller.play_blessing_success(str(result.get("id", "")), _dog_shrine_inventory_items(), _dog_shrine_offerings_left())


# ---------------------------------------------------------------- dice clicks and workers in coop
func _on_die_clicked(die: DiceActor) -> void :
	if bdr.is_coop_client():
		bdr.coop_request_click(die)
		return
	if not is_instance_valid(die) or not game_started or get_tree().paused or _visual_overlay_blocks_wave() or upgrade_overlay.visible or dog_shrine_transaction_active or autosave_pending or not pending_safe_action.is_empty():
		return
	if die.die_kind == "cat":
		if _cat_can_accept_feed(die):
			die.queue_feed()
		return
	if die.rolling:
		_queue_player_reroll(die)
		return
	_launch_player_die(die)


func _on_npc_attack_ready(_npc: NPCActor, die: DiceActor) -> void :
	if bdr.is_coop_client():
		return
	if lucky_transaction_active or (dog_shrine_transaction_active and not bdr.world_runs_during_menus()) or autosave_pending or not pending_safe_action.is_empty():
		if is_instance_valid(die):
			die.reserved_by = 0
		_npc.cancel_target()
		_finish_pending_safe_action()
		return
	if is_instance_valid(die) and not die.rolling:
		die.reserved_by = 0
		die.set_meta("dog_strength_eligible", true)
		_start_die_roll(die)
