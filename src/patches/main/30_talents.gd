# Dice Rush Extended - main.gd patch: extended talent tree.

const TREE_BASE_SIZE: = Vector2(7720, 8000)

var _talent_positions_cache: Dictionary = {}


func _initialize_talents() -> void :
	for limit in [10, 20, 30, 40, 50]:
		var key: = "workers_%d" % limit
		talents[key] = false
	talent_prerequisites.merge({
		"d4": "",
		"fifty_d4_synergy": "d4",
		"ordinary_variety_synergy": "3x4",
		"worker_d4_synergy": "worker_speed_1",
		"lucky_pair_synergy": "777",
		"ancient_worker_synergy": "prehistoric_radius",
		"golden_diamond_synergy": "golden_payout_2",
		"crypto_pi_synergy": "crypto_floor_2",
		"achievement_god": "golden_diamond_synergy",
		"d4_profit_1": "fifty_profit_1",
		"d4_profit_2": "d4_profit_1",
		"d4_profit_3": "d4_profit_2",
		"d4_profit_4": "d4_profit_3",
		"d4_profit_5": "d4_profit_4",
		"workers_10": "d4",
		"workers_20": "workers_10",
		"workers_30": "workers_20",
		"workers_40": "workers_30",
		"workers_50": "workers_40",
		"worker_speed_1": "workers_10",
		"worker_speed_2": "worker_speed_1",
		"worker_speed_3": "worker_speed_2",
		"npc_die": "workers_20",
		"npc_profit": "npc_die",
		"3x4": "d4",
		"d2": "3x4",
		"777": "d2",
		"seven_combo": "777",
		"prehistoric": "777",
		"prehistoric_radius": "prehistoric",
		"guaranteed_income_1": "d4",
		"guaranteed_income_2": "guaranteed_income_1",
		"guaranteed_income_3": "guaranteed_income_2",
		"golden": "guaranteed_income_2",
		"gold_aura_radius_1": "golden",
		"gold_aura_radius_2": "gold_aura_radius_1",
		"gold_aura_power": "gold_aura_radius_2",
		"fifty_profit_1": "fifty_d4_synergy",
		"fifty_profit_2": "fifty_profit_1",
		"fifty_profit_3": "fifty_profit_2",
		"fifty_profit_4": "fifty_profit_3",
		"fifty_profit_5": "fifty_profit_4",
		"fifty_profit_6": "fifty_profit_5",
		"three_by_four_multiplier_1": "3x4",
		"three_by_four_multiplier_2": "three_by_four_multiplier_1",
		"three_by_four_multiplier_3": "three_by_four_multiplier_2",
		"three_by_four_multiplier_4": "three_by_four_multiplier_3",
		"three_by_four_multiplier_5": "three_by_four_multiplier_4",
		"three_by_four_multiplier_6": "three_by_four_multiplier_5",
		"d2_guaranteed_1": "d2",
		"d2_guaranteed_2": "d2_guaranteed_1",
		"d2_guaranteed_3": "d2_guaranteed_2",
		"d2_guaranteed_4": "d2_guaranteed_3",
		"d2_guaranteed_5": "d2_guaranteed_4",
		"golden_payout_1": "gold_aura_power",
		"golden_payout_2": "golden_payout_1",
		"golden_payout_3": "golden_payout_2",
		"crypto_floor_1": "prehistoric_radius",
		"crypto_floor_2": "crypto_floor_1",
		"diamond_payout_1": "golden_payout_3",
		"diamond_payout_2": "diamond_payout_1",
		"diamond_payout_3": "diamond_payout_2",
		"pi_suffix_1": "npc_profit",
		"pi_suffix_2": "pi_suffix_1",
		"pi_suffix_3": "pi_suffix_2",
		"accountant_efficiency_1": "npc_profit",
		"accountant_efficiency_2": "accountant_efficiency_1",
		"accountant_efficiency_3": "accountant_efficiency_2",
		"accountant_efficiency_4": "accountant_efficiency_3",
		"hover_roll": "workers_20",
		"hover_roll_radius": "hover_roll",
	}, true)
	if _edition_full:
		talent_prerequisites["fifty_profit_1"] = "d4"
	var ext = bdr.talents_ext(_original_talent_positions())
	for key in ext.order:
		talents[key] = bool(talents.get(key, false))
		talent_prerequisites[key] = str(ext.defs[key].prereq)


func _talent_tree_order() -> Array[String]:
	var order: Array[String] = [
		"d4",
		"fifty_d4_synergy", "ordinary_variety_synergy", "worker_d4_synergy", "lucky_pair_synergy", "ancient_worker_synergy", "golden_diamond_synergy", "crypto_pi_synergy", "achievement_god",
		"crypto_floor_1", "crypto_floor_2",
		"diamond_payout_1", "diamond_payout_2", "diamond_payout_3",
		"pi_suffix_1", "pi_suffix_2", "pi_suffix_3",
		"accountant_efficiency_1", "accountant_efficiency_2", "accountant_efficiency_3", "accountant_efficiency_4",
		"fifty_profit_1", "fifty_profit_2", "fifty_profit_3", "fifty_profit_4", "fifty_profit_5", "fifty_profit_6",
		"d4_profit_1", "d4_profit_2", "d4_profit_3", "d4_profit_4", "d4_profit_5",
		"hover_roll", "hover_roll_radius",
		"workers_10", "workers_20", "workers_30", "workers_40", "workers_50",
		"worker_speed_1", "worker_speed_2", "worker_speed_3",
		"npc_die",
		"npc_profit",
		"3x4",
		"three_by_four_multiplier_1", "three_by_four_multiplier_2", "three_by_four_multiplier_3", "three_by_four_multiplier_4", "three_by_four_multiplier_5", "three_by_four_multiplier_6",
		"d2",
		"d2_guaranteed_1", "d2_guaranteed_2", "d2_guaranteed_3", "d2_guaranteed_4", "d2_guaranteed_5",
		"777", "seven_combo",
		"prehistoric",
		"prehistoric_radius",
		"guaranteed_income_1", "guaranteed_income_2", "guaranteed_income_3",
		"golden",
		"gold_aura_radius_1", "gold_aura_radius_2", "gold_aura_power",
		"golden_payout_1", "golden_payout_2", "golden_payout_3",
	]
	if _edition_full:
		for moved_id in DogShrineCards.LEGACY_TALENT_IDS:
			order.erase(str(moved_id))
	if bdr and bdr.talent_ext:
		for key in bdr.talent_ext.order:
			order.append(key)
	return order


func _original_talent_positions() -> Dictionary:
	var positions: = {
		"d4": Vector2(2082, 3182),
		"fifty_d4_synergy": Vector2(2082, 2782),
		"fifty_profit_1": Vector2(2082, 2782),
		"fifty_profit_2": Vector2(2082, 2382),
		"fifty_profit_3": Vector2(2082, 1982),
		"fifty_profit_4": Vector2(2082, 1582),
		"fifty_profit_5": Vector2(2082, 1182),
		"fifty_profit_6": Vector2(2082, 782),
		"d4_profit_1": Vector2(2482, 2382),
		"d4_profit_2": Vector2(2882, 2382),
		"d4_profit_3": Vector2(2882, 1982),
		"d4_profit_4": Vector2(2882, 1582),
		"d4_profit_5": Vector2(2882, 1182),
		"hover_roll": Vector2(1682, 2782),
		"hover_roll_radius": Vector2(1682, 2382),
		"worker_d4_synergy": Vector2(1282, 3982),
		"workers_10": Vector2(1682, 3182),
		"workers_20": Vector2(1282, 3182),
		"workers_30": Vector2(882, 3182),
		"workers_40": Vector2(482, 3182),
		"workers_50": Vector2(82, 3182),
		"worker_speed_1": Vector2(1682, 3582),
		"worker_speed_2": Vector2(1282, 3582),
		"worker_speed_3": Vector2(882, 3582),
		"npc_die": Vector2(1282, 2782),
		"npc_profit": Vector2(882, 2782),
		"pi_suffix_1": Vector2(482, 2782),
		"pi_suffix_2": Vector2(82, 2782),
		"pi_suffix_3": Vector2(82, 2382),
		"accountant_efficiency_1": Vector2(882, 2382),
		"accountant_efficiency_2": Vector2(882, 1982),
		"accountant_efficiency_3": Vector2(882, 1582),
		"accountant_efficiency_4": Vector2(882, 1182),
		"3x4": Vector2(2482, 3182),
		"ordinary_variety_synergy": Vector2(2482, 3582),
		"lucky_pair_synergy": Vector2(3482, 3782),
		"ancient_worker_synergy": Vector2(3882, 3382),
		"d2": Vector2(2882, 3182),
		"777": Vector2(3282, 3182),
		"prehistoric": Vector2(3682, 3182),
		"three_by_four_multiplier_1": Vector2(2482, 2782),
		"three_by_four_multiplier_2": Vector2(2882, 2782),
		"three_by_four_multiplier_3": Vector2(3282, 2782),
		"three_by_four_multiplier_4": Vector2(3682, 2782),
		"three_by_four_multiplier_5": Vector2(4082, 2782),
		"three_by_four_multiplier_6": Vector2(4082, 2382),
		"d2_guaranteed_1": Vector2(2882, 3582),
		"d2_guaranteed_2": Vector2(3282, 3582),
		"d2_guaranteed_3": Vector2(3682, 3582),
		"d2_guaranteed_4": Vector2(3682, 3982),
		"d2_guaranteed_5": Vector2(3682, 4382),
		"seven_combo": Vector2(3282, 2382),
		"prehistoric_radius": Vector2(4082, 3182),
		"crypto_floor_1": Vector2(4082, 3582),
		"crypto_floor_2": Vector2(4082, 3982),
		"crypto_pi_synergy": Vector2(4082, 4382),
		"guaranteed_income_1": Vector2(2082, 3582),
		"guaranteed_income_2": Vector2(2082, 3982),
		"guaranteed_income_3": Vector2(2082, 4382),
		"golden": Vector2(2482, 3982),
		"gold_aura_radius_1": Vector2(2482, 4382),
		"gold_aura_radius_2": Vector2(2882, 4382),
		"gold_aura_power": Vector2(3282, 4382),
		"golden_payout_1": Vector2(3282, 4782),
		"golden_payout_2": Vector2(3682, 4782),
		"golden_payout_3": Vector2(4082, 4782),
		"golden_diamond_synergy": Vector2(3682, 5182),
		"achievement_god": Vector2(3682, 5582),
		"diamond_payout_1": Vector2(4082, 5182),
		"diamond_payout_2": Vector2(4082, 5582),
		"diamond_payout_3": Vector2(4082, 5982),
	}
	if not _edition_full:
		for tier in range(1, 7):
			positions["fifty_profit_%d" % tier] = Vector2(2082, 2782 - tier * 400)
	var root_position: Vector2 = positions["d4"]
	var presentation_spacing: = 0.65 if _edition_full else 0.82
	var offset: Vector2 = bdr.talent_offset()
	for key in positions:
		positions[key] = root_position + (Vector2(positions[key]) - root_position) * presentation_spacing + offset
	return positions


func _talent_tree_positions() -> Dictionary:
	if not _talent_positions_cache.is_empty():
		return _talent_positions_cache
	var positions: = _original_talent_positions()
	if bdr and bdr.talent_ext:
		for key in bdr.talent_ext.order:
			positions[key] = bdr.talent_ext.defs[key].pos
	_talent_positions_cache = positions
	return positions


func _worker_limit() -> int:
	var limit: = 5
	for unlocked_limit in [10, 20, 30, 40, 50]:
		if bool(talents.get("workers_%d" % unlocked_limit, false)):
			limit = unlocked_limit
	for unlocked_limit in [60, 70, 80, 90, 100]:
		if bool(talents.get("bdr_workers_%d" % unlocked_limit, false)):
			limit = unlocked_limit
	return limit


func _talent_cost(key: String) -> int:
	return bdr.talent_cost(key)


func _buy_upgrade(key: String) -> void :
	if key not in _talent_tree_order():
		return
	if _is_talent_owned(key):
		return
	if key.begins_with("accountant_efficiency_") and not accountant_unlocked:
		return
	var special_kind: = _special_kind_from_talent(key)
	if not special_kind.is_empty() and not bool(special_dice_unlocked.get(special_kind, false)):
		return
	var visual: = talent_visuals.get(key) as Control
	var prerequisite: String = talent_prerequisites.get(key, "")
	if not prerequisite.is_empty() and not _is_talent_owned(prerequisite):
		_flash_talent_visual(visual)
		return
	var cost: = _talent_cost(key)
	if golden_coins < cost:
		_flash_talent_visual(visual)
		GameSession.play_sfx("denied")
		return
	if bdr.is_coop_client():
		bdr.coop_request("talent", [key])
		return
	golden_coins -= cost
	if upgrades.has(key):
		upgrades[key] = true
	else:
		talents[key] = true
	_apply_talent_side_effect(key)
	GameSession.play_sfx("purchase")
	_report_achievement_snapshot()
	_update_all_labels()


func _apply_talent_side_effect(key: String) -> void :
	if key == "npc_profit" and DiceRushEdition.is_demo():
		accountant_unlocked = true
	elif key.begins_with("worker_speed_"):
		_refresh_worker_stats()
	elif key.begins_with("gold_aura_"):
		_refresh_gold_auras()
	elif key.begins_with("crypto_floor_"):
		crypto_market_value = maxi(crypto_market_value, _crypto_minimum_value())
	bdr.on_talent_bought(key)
	_invalidate_eco()


func _update_talent_node(key: String) -> void :
	var owned: = _is_talent_owned(key)
	var prerequisite: String = talent_prerequisites.get(key, "")
	var available: = prerequisite.is_empty() or _is_talent_owned(prerequisite)
	var special_kind: = _special_kind_from_talent(key)
	var special_unlocked: = special_kind.is_empty() or bool(special_dice_unlocked.get(special_kind, false))
	if key.begins_with("accountant_efficiency_"):
		special_unlocked = accountant_unlocked
	var visible_in_tree: = special_unlocked and (available or owned)
	var visual: = talent_visuals.get(key) as Control
	var icon: = upgrade_icons.get(key) as CanvasItem
	var check: = talent_checks.get(key) as TextureRect
	var button: = talent_buttons.get(key) as Button
	var connection: = talent_connections.get(key) as Line2D
	var node_style: = talent_node_styles.get(key) as Control
	if visual:
		visual.visible = visible_in_tree
	if node_style:
		node_style.set_state(owned, available, golden_coins >= _talent_cost(key))
	if icon:
		icon.modulate.a = 0.82 if owned else 1.0
	if check:
		check.visible = owned
	if button:
		button.disabled = not visible_in_tree
	if connection:
		connection.visible = special_unlocked and not prerequisite.is_empty() and _is_talent_owned(prerequisite)
		connection.default_color = _talent_branch_color(key) if owned else Color("f3d281")


func _talent_tooltip_text(key: String) -> String:
	var owned: = _is_talent_owned(key)
	var prerequisite: String = talent_prerequisites.get(key, "")
	var available: = prerequisite.is_empty() or _is_talent_owned(prerequisite)
	var cost_text: = bdr.talent_cost_text(_talent_cost(key))
	var status: = GameSession.text("owned") if owned else (cost_text if available else GameSession.text("locked"))
	var requirement: = ""
	if not owned and not available:
		requirement = "\n[color=#ff7a7a]%s[/color]" % GameSession.text("requires_previous")
	return "[color=#ffd166][font_size=18]%s[/font_size][/color]\n\n%s\n\n[color=#8aa0bd]%s:[/color] %s\n[color=#8aa0bd]%s:[/color] %s\n[color=#8aa0bd]%s:[/color] %d%s" % [
		_talent_title(key),
		_talent_effect(key),
		GameSession.text("status"), status,
		GameSession.text("cost"), cost_text,
		GameSession.text("gold_balance"), golden_coins,
		requirement,
	]


func _talent_branch_color(key: String) -> Color:
	if key.begins_with("bdr_"):
		return bdr.talent_color(key)
	if key.begins_with("workers_") or key.begins_with("worker_speed_") or key.begins_with("accountant_efficiency_") or key in ["npc_die", "npc_profit", "worker_d4_synergy"]:
		return Color("b18cff")
	if key.begins_with("crypto_") or key.begins_with("pi_suffix_") or key in ["777", "seven_combo", "lucky_pair_synergy", "crypto_pi_synergy", "achievement_god"]:
		return Color("eba858")
	if key.begins_with("fifty_profit_") or key.begins_with("d4_profit_") or key.begins_with("guaranteed_income_") or key.begins_with("gold_") or key.begins_with("golden") or key.begins_with("diamond_"):
		return Color("74ce95")
	return Color("5dabf6")
