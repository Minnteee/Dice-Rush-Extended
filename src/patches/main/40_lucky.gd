func _owned_lucky_kinds() -> Array[String]:
	var result: Array[String] = ["50_50"]
	if dice_d4_count > 0:
		result.append("d4")
	for kind in ["3x4", "d2", "777", "prehistoric", "golden", "npc_die"]:
		if int(extra_counts.get(kind, 0)) > 0:
			result.append(kind)
	for kind in SPECIAL_DICE_KINDS:
		if int(special_dice_counts.get(kind, 0)) > 0:
			result.append(kind)
		elif bool(special_dice_unlocked.get(kind, false)):
			result.append(kind)
	if accountant_unlocked:
		result.append("accountant")
	if DiceRushEdition.is_full() and cat_unlocked:
		result.append("cat")
	result.append_array(bdr.lucky.owned_kinds())
	return result


func _lucky_reward_pool(projected_purchases: int = -1) -> Array[String]:
	var result: = _owned_lucky_kinds()
	result.erase("cat")
	if DiceRushEdition.is_demo():
		var owned_demo_dice: Array[String] = []
		for kind in result:
			if kind in DEMO_LUCKY_KINDS and _product_count(kind) > 0:
				owned_demo_dice.append(kind)
		return owned_demo_dice
	var purchase_total: = lucky_cubes_purchased if projected_purchases < 0 else projected_purchases
	for kind in SPECIAL_DICE_KINDS:
		if purchase_total >= int(SPECIAL_LUCKY_GATES.get(kind, MAX_INT64)) and kind not in result:
			result.append(kind)
	for kind in bdr.lucky.gate_kinds_in_pool(purchase_total):
		if kind not in result:
			result.append(kind)
	if _price_progress_count("npc_die", int(extra_counts.get("npc_die", 0))) < ACCOUNTANT_NPC_DICE_REQUIREMENT:
		result.erase("accountant")
	elif "accountant" not in result:
		result.append("accountant")
	return result


func _roll_lucky_reward_counts(pool: Array[String], purchase_count: int) -> Dictionary:
	var counts: = {}
	if purchase_count <= 0 or pool.is_empty():
		return counts
	if DiceRushEdition.is_demo():
		if purchase_count <= 100000:
			for _roll_index in range(purchase_count):
				var kind: = pool[rng.randi_range(0, pool.size() - 1)]
				counts[kind] = int(counts.get(kind, 0)) + 1
		else:
			var base_count: = purchase_count / pool.size()
			for kind in pool:
				counts[kind] = base_count
			for _roll_index in range(purchase_count % pool.size()):
				var kind: = pool[rng.randi_range(0, pool.size() - 1)]
				counts[kind] = int(counts.get(kind, 0)) + 1
		return counts
	var old_purchase_total: = lucky_cubes_purchased
	var new_purchase_total: = _safe_add_int64(old_purchase_total, purchase_count)
	var forced_count: = 0
	for special_kind in SPECIAL_DICE_KINDS:
		var gate: = int(SPECIAL_LUCKY_GATES.get(special_kind, MAX_INT64))
		if old_purchase_total < gate and new_purchase_total >= gate and not bool(special_dice_unlocked.get(special_kind, false)):
			counts[special_kind] = int(counts.get(special_kind, 0)) + 1
			forced_count += 1
	for lucky_kind in bdr.lucky.forced_unlocks(old_purchase_total, new_purchase_total):
		counts[lucky_kind] = int(counts.get(lucky_kind, 0)) + 1
		forced_count += 1
	var random_count: = maxi(0, purchase_count - forced_count)
	if DiceRushEdition.is_full() and not cat_unlocked and random_count > 0:
		var cat_batch_chance: = 1.0 - pow(0.995, float(random_count))
		if rng.randf() < cat_batch_chance:
			counts["cat"] = 1
			random_count -= 1
	if random_count <= 100000:
		for _roll_index in range(random_count):
			var kind: = pool[rng.randi_range(0, pool.size() - 1)]
			counts[kind] = int(counts.get(kind, 0)) + 1
	else:
		var base_count: = random_count / pool.size()
		for kind in pool:
			counts[kind] = int(counts.get(kind, 0)) + base_count
		var remainder: = random_count % pool.size()
		var shuffled_pool: = pool.duplicate()
		for index in range(shuffled_pool.size() - 1, 0, -1):
			var swap_index: = rng.randi_range(0, index)
			var swap_value = shuffled_pool[index]
			shuffled_pool[index] = shuffled_pool[swap_index]
			shuffled_pool[swap_index] = swap_value
		for index in range(remainder):
			var kind: String = shuffled_pool[index]
			counts[kind] = int(counts.get(kind, 0)) + 1
	# Dice Rush Extended: extra rewards on top of the normal drops
	var extras: Dictionary = bdr.lucky.roll_extras(purchase_count)
	for key in extras:
		counts[key] = int(counts.get(key, 0)) + int(extras[key])
	return counts


func _commit_lucky_purchase() -> void :
	var purchase_count: = _selected_lucky_purchase_count()
	if bdr.is_coop_client():
		lucky_transaction_active = true
		_refresh_lucky_ui()
		bdr.coop_request("lucky_buy", [purchase_count])
		return
	var purchase_cost: = _selected_lucky_purchase_cost()
	if purchase_count <= 0 or money < purchase_cost:
		_refresh_lucky_ui()
		return
	lucky_transaction_active = true
	lucky_status_label.text = ""
	lucky_status_label.add_theme_color_override("font_color", Color("f7d66b"))
	_refresh_lucky_ui()
	var result: = _bdr_lucky_transaction(purchase_count)
	lucky_transaction_active = false
	if not bool(result.get("ok", false)):
		lucky_status_label.text = str(result.get("error", GameSession.text("save_failed")))
		UITextFitterScript.fit(lucky_status_label)
		lucky_status_label.add_theme_color_override("font_color", PRICE_UNAFFORDABLE_COLOR)
		_refresh_lucky_ui(true)
		return
	lucky_status_label.text = _lucky_text("lucky_rewards_count") % purchase_count
	UITextFitterScript.fit(lucky_status_label)
	lucky_status_label.add_theme_color_override("font_color", Color("75ff64"))
	GameSession.play_sfx("purchase")
	_refresh_lucky_ui(true)
	await _reveal_lucky_reward()


## Buys lucky cubes and applies all rewards (used by the lucky panel and by the coop partner).
func _bdr_lucky_transaction(purchase_count: int) -> Dictionary:
	var purchase_cost: = _lucky_purchase_cost(purchase_count)
	if purchase_count <= 0 or money < purchase_cost:
		return {"ok": false, "error": _lucky_text("lucky_not_enough")}
	var old_money: = money
	var old_transaction_id: = lucky_transaction_id
	var old_cubes_purchased: = lucky_cubes_purchased
	var old_levels: = die_levels.duplicate(true)
	var old_special_counts: = special_dice_counts.duplicate(true)
	var old_special_unlocked: = special_dice_unlocked.duplicate(true)
	var old_accountant_count: = accountant_count
	var old_accountant_unlocked: = accountant_unlocked
	var old_cat_unlocked: = cat_unlocked
	var old_bdr: Dictionary = bdr.lucky.snapshot()
	var rewards: Array = []
	var projected_purchase_total: = _safe_add_int64(lucky_cubes_purchased, purchase_count)
	var pool: = _lucky_reward_pool(projected_purchase_total)
	var reward_counts: = _roll_lucky_reward_counts(pool, purchase_count)
	money -= purchase_cost
	lucky_cubes_purchased = projected_purchase_total
	var average_cube_price: float = purchase_cost / float(maxi(1, purchase_count))
	var reward_kinds: Array[String] = pool.duplicate()
	for key in reward_counts:
		if str(key) not in reward_kinds:
			reward_kinds.append(str(key))
	for reward_kind in reward_kinds:
		var drop_count: = int(reward_counts.get(reward_kind, 0))
		if drop_count <= 0:
			continue
		if reward_kind == "cat":
			cat_unlocked = true
			rewards.append({"kind": "cat", "count": 1, "unlock": true})
			continue
		if bdr.lucky.is_bonus(reward_kind):
			rewards.append(bdr.lucky.apply_bonus(reward_kind, drop_count, average_cube_price))
			continue
		if bdr.is_custom(reward_kind) and not bdr.is_unlocked(reward_kind):
			rewards.append(bdr.lucky.apply_unlock(reward_kind, drop_count))
			continue
		var first_special_unlock: bool = reward_kind in SPECIAL_DICE_KINDS and not bool(special_dice_unlocked.get(reward_kind, false))
		var first_accountant_unlock: bool = reward_kind == "accountant" and not accountant_unlocked
		var old_level: = 0 if first_special_unlock or first_accountant_unlock else _die_level(reward_kind)
		var new_level: = _safe_add_int64(old_level, _lucky_level_gain(drop_count))
		die_levels[reward_kind] = new_level
		if reward_kind == "accountant":
			accountant_unlocked = true
		elif first_special_unlock:
			special_dice_unlocked[reward_kind] = true
		rewards.append({"kind": reward_kind, "count": drop_count, "old_level": old_level, "new_level": new_level})
	lucky_transaction_id += 1
	pending_lucky_reward = {
		"transaction_id": str(lucky_transaction_id),
		"count": purchase_count,
		"rewards": rewards,
	}
	if not _save_lucky_state_immediately():
		money = old_money
		lucky_cubes_purchased = old_cubes_purchased
		die_levels = old_levels
		special_dice_counts = old_special_counts
		special_dice_unlocked = old_special_unlocked
		accountant_count = old_accountant_count
		accountant_unlocked = old_accountant_unlocked
		cat_unlocked = old_cat_unlocked
		bdr.lucky.restore(old_bdr)
		lucky_transaction_id = old_transaction_id
		pending_lucky_reward.clear()
		return {"ok": false, "error": GameSession.text("save_failed")}
	bdr.lucky.after_commit(rewards)
	bdr.stat("lucky_cubes", purchase_count)
	_update_all_labels()
	_report_achievement_snapshot()
	return {"ok": true, "count": purchase_count, "rewards": rewards}


func _bdr_known_lucky_reward(kind: String) -> bool:
	return kind in LUCKY_DIE_KINDS or bdr.lucky.is_known_reward(kind)


func _pending_lucky_rewards_from(data: Dictionary) -> Array:
	var result: Array = []
	var saved_rewards = data.get("rewards", [])
	if saved_rewards is Array:
		for saved_reward in saved_rewards:
			if saved_reward is Dictionary and _bdr_known_lucky_reward(str(saved_reward.get("kind", ""))):
				result.append(saved_reward.duplicate(true))
	if result.is_empty() and str(data.get("kind", "")) in LUCKY_DIE_KINDS:
		result.append({
			"kind": str(data.get("kind")),
			"count": 1,
			"old_level": int(data.get("old_level", 1)),
			"new_level": int(data.get("new_level", 1)),
		})
	return result


func _bdr_lucky_reward_icon(reward: Dictionary) -> Texture2D:
	var reward_kind: = str(reward.get("kind", "50_50"))
	if reward_kind == "cat":
		return CatDiceActorScript.get_idle_texture()
	if bdr.lucky.is_bonus(reward_kind):
		return CleanTextureLoaderScript.load_texture(bdr.lucky.icon(reward_kind))
	return CleanTextureLoaderScript.load_texture(_lucky_kind_icon_path(reward_kind))


func _bdr_lucky_reward_name(reward: Dictionary) -> String:
	var reward_kind: = str(reward.get("kind", "50_50"))
	if bdr.lucky.is_bonus(reward_kind):
		return bdr.lucky.bonus_name(reward_kind)
	return _lucky_kind_name(reward_kind)


func _bdr_lucky_reward_level_text(reward: Dictionary, single: = false) -> String:
	var reward_kind: = str(reward.get("kind", "50_50"))
	if reward_kind == "cat":
		return _cat_text("unlock_reward")
	if bdr.lucky.is_bonus(reward_kind) or (bool(reward.get("unlock", false)) and not single):
		return bdr.lucky.reward_detail(reward)
	return _lucky_text("lucky_level") % int(reward.get("new_level", _die_level(reward_kind)))


func _bdr_lucky_reward_title(reward: Dictionary) -> String:
	var reward_kind: = str(reward.get("kind", "50_50"))
	if reward_kind == "cat":
		return _cat_text("unlock_reward")
	if bdr.lucky.is_bonus(reward_kind):
		return bdr.lucky.bonus_title()
	if bool(reward.get("unlock", false)):
		return bdr.lucky.reward_detail(reward)
	return _lucky_text("lucky_reward")


func _populate_lucky_reward_card(rewards: Array) -> void :
	for child in lucky_reward_list.get_children():
		child.free()
	var total_count: = _lucky_reward_total_count(rewards)
	var is_batch: = rewards.size() > 1 or total_count > 1
	lucky_reward_rays.visible = not is_batch and GameSession.visual_effects_enabled
	lucky_reward_icon.visible = not is_batch
	lucky_reward_name_label.visible = not is_batch
	lucky_reward_level_label.visible = not is_batch
	lucky_reward_scroll.visible = is_batch
	if not is_batch:
		var reward: Dictionary = rewards[0]
		lucky_reward_card.size = Vector2(400, 510)
		lucky_reward_title_label.position = Vector2(24, 22)
		lucky_reward_title_label.size = Vector2(352, 58)
		lucky_reward_title_label.text = _bdr_lucky_reward_title(reward)
		lucky_reward_icon.texture = _bdr_lucky_reward_icon(reward)
		lucky_reward_name_label.text = _bdr_lucky_reward_name(reward)
		_fit_shop_title(lucky_reward_name_label)
		lucky_reward_level_label.text = _bdr_lucky_reward_level_text(reward, true)
		lucky_take_button.position = Vector2(48, 430)
		lucky_take_button.size = Vector2(304, 58)
	else:
		lucky_reward_card.size = Vector2(720, 590)
		lucky_reward_title_label.position = Vector2(30, 18)
		lucky_reward_title_label.size = Vector2(660, 54)
		lucky_reward_title_label.text = _lucky_text("lucky_rewards_count") % total_count
		lucky_take_button.position = Vector2(208, 520)
		lucky_take_button.size = Vector2(304, 54)
		var ordered: Array = rewards.duplicate()
		ordered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return _bdr_lucky_reward_rank(a) > _bdr_lucky_reward_rank(b))
		for reward in ordered:
			var reward_kind: = str(reward.get("kind", "50_50"))
			var drop_count: = maxi(1, int(reward.get("count", 1)))
			var special: = reward_kind == "cat" or bool(reward.get("unlock", false)) or bdr.lucky.is_bonus(reward_kind)
			var row: = Panel.new()
			row.custom_minimum_size = Vector2(624, 92)
			row.add_theme_stylebox_override("panel", _lucky_style(Color("3a2c08e8") if special else Color("0a321de8"), Color("f7bd31") if special else Color("3e7c4c"), 2, 11))
			lucky_reward_list.add_child(row)
			var icon: = TextureRect.new()
			icon.position = Vector2(18, 6)
			icon.size = Vector2(80, 80)
			icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			icon.texture = _bdr_lucky_reward_icon(reward)
			icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
			icon.z_index = 2
			row.add_child(icon)
			var name_label: = _make_label(_bdr_lucky_reward_name(reward), Rect2(112, 7, 310, 40), 11, HORIZONTAL_ALIGNMENT_LEFT, 2, row)
			_fit_shop_title(name_label)
			name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			var level_label: = _make_label(_bdr_lucky_reward_level_text(reward), Rect2(112, 45, 310, 34), 9, HORIZONTAL_ALIGNMENT_LEFT, 2, row)
			level_label.add_theme_color_override("font_color", Color("ffd166") if special else Color("75ff64"))
			UITextFitterScript.fit(level_label)
			var count_label: = _make_label(_lucky_text("lucky_drop_count") % drop_count, Rect2(425, 15, 180, 60), 12, HORIZONTAL_ALIGNMENT_CENTER, 2, row)
			count_label.add_theme_color_override("font_color", Color("ffd166"))
	_center_lucky_reward_card()
	lucky_take_button.text = _lucky_text("lucky_take")
	UITextFitterScript.fit(lucky_reward_title_label)
	UITextFitterScript.fit(lucky_reward_name_label)
	UITextFitterScript.fit(lucky_reward_level_label)
	UITextFitterScript.fit(lucky_take_button)


## Sort order on the batch reward card: unlocks and bonus rewards first.
func _bdr_lucky_reward_rank(reward: Dictionary) -> int:
	var reward_kind: = str(reward.get("kind", ""))
	if reward_kind == "cat" or bool(reward.get("unlock", false)):
		return 3
	if reward_kind == "bdr_gold" or reward_kind == "bdr_boost":
		return 2
	if bdr.lucky.is_bonus(reward_kind):
		return 1
	return 0
